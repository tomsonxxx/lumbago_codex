from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import requests

from lumbago_app.core.models import Track
from lumbago_app.services.ai_tagger import CloudAiTagger, MultiAiTagger


_MB_BASE = "https://musicbrainz.org/ws/2"
_DISCOGS_BASE = "https://api.discogs.com"
_USER_AGENT = "LumbagoMusicAI/1.0 (local)"
_SEARCH_STOPWORDS = {
    "official",
    "video",
    "audio",
    "lyrics",
    "lyric",
    "hq",
    "hd",
    "4k",
    "8k",
    "remaster",
    "remastered",
    "live",
}


@dataclass
class Candidate:
    source: str
    score: int
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    year: str | None = None
    genre: str | None = None
    mood: str | None = None
    bpm: float | None = None
    key: str | None = None
    energy: float | None = None
    tags: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class EnrichmentResult:
    candidates: list[Candidate] = field(default_factory=list)
    best_match: Candidate | None = None


class UnifiedAutoTagger:
    def __init__(self, settings):
        self.settings = settings

    def enrich_track(self, track: Track) -> EnrichmentResult:
        candidates: list[Candidate] = []

        for fn in (
            self._search_musicbrainz,
            self._search_discogs,
            self._search_ai,
        ):
            try:
                candidate = fn(track)
                if candidate is not None:
                    candidates.append(candidate)
            except Exception as exc:
                candidates.append(Candidate(source=fn.__name__, score=0, error=str(exc)))

        valid = [candidate for candidate in candidates if candidate.error is None and candidate.score > 0]
        valid.sort(key=lambda candidate: candidate.score, reverse=True)
        return EnrichmentResult(candidates=candidates, best_match=(valid[0] if valid else None))

    def apply_best_match(self, track: Track, result: EnrichmentResult) -> bool:
        raw_candidates = getattr(result, "candidates", []) or []
        candidates = [candidate for candidate in raw_candidates if candidate.error is None and candidate.score > 0]
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        best = result.best_match
        if best is None and not candidates:
            return False
        changed = False

        mapping: dict[str, Any] = {}
        for field_name in ("title", "artist", "album", "year", "genre", "mood", "key", "bpm", "energy"):
            incoming = _best_field_value(candidates, field_name)
            if incoming is None and best is not None:
                incoming = getattr(best, field_name, None)
            mapping[field_name] = incoming

        for field_name, incoming in mapping.items():
            if incoming is None:
                continue
            current = getattr(track, field_name, None)
            if current != incoming:
                setattr(track, field_name, incoming)
                changed = True

        if best.artist and not track.albumartist:
            track.albumartist = best.artist
            changed = True
        return changed

    def _search_musicbrainz(self, track: Track) -> Candidate | None:
        artist = _clean_text(track.artist)
        title = _clean_text(track.title)
        if not artist and not title:
            base = _clean_text(Path(track.path).stem.replace("_", " ").replace(".", " "))
            if base:
                title = base
        if not artist and not title:
            return None

        query_parts = []
        if title:
            query_parts.append(f'recording:"{title[:60]}"')
        if artist:
            query_parts.append(f'artist:"{artist[:60]}"')
        query = " AND ".join(query_parts)

        response = requests.get(
            f"{_MB_BASE}/recording/",
            params={"query": query, "limit": "5", "fmt": "json"},
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        recordings = payload.get("recordings", [])
        if not recordings:
            return None

        best = max(recordings[:5], key=lambda recording: _musicbrainz_recording_score(track, recording))
        rec_title = best.get("title")
        rec_artist = ", ".join(
            entry.get("name") or (entry.get("artist") or {}).get("name") or ""
            for entry in (best.get("artist-credit") or [])
            if isinstance(entry, dict)
        ).strip(", ")
        release = (best.get("releases") or [{}])[0]
        year = str((release.get("date") or "")[:4]).strip() or None
        score = int(best.get("score") or 0)

        genre = None
        tags: list[str] = []
        mbid = best.get("id")
        if mbid:
            detail = self._musicbrainz_detail(mbid)
            tags = detail.get("tags", [])
            if detail.get("genres"):
                genre = detail["genres"][0]
            elif tags:
                genre = tags[0]
            if not genre:
                release_group_id = _musicbrainz_release_group_id(best)
                if release_group_id:
                    release_group_detail = self._musicbrainz_release_group_detail(release_group_id)
                    rg_genres = release_group_detail.get("genres", [])
                    rg_tags = release_group_detail.get("tags", [])
                    if rg_genres:
                        genre = rg_genres[0]
                    elif rg_tags:
                        genre = rg_tags[0]

        sim = _similarity_bonus(track, rec_title, rec_artist)
        return Candidate(
            source="MusicBrainz",
            score=max(0, min(100, score + sim)),
            title=rec_title or track.title,
            artist=rec_artist or track.artist,
            album=release.get("title") or None,
            year=year,
            genre=genre,
            tags=tags,
        )

    def _musicbrainz_detail(self, mbid: str) -> dict[str, list[str]]:
        try:
            response = requests.get(
                f"{_MB_BASE}/recording/{mbid}",
                params={"inc": "tags+genres", "fmt": "json"},
                headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return {"tags": [], "genres": []}

        tags = sorted(payload.get("tags", []), key=lambda item: item.get("count", 0), reverse=True)
        genres = sorted(payload.get("genres", []), key=lambda item: item.get("count", 0), reverse=True)
        return {
            "tags": [str(item.get("name")).strip() for item in tags[:8] if item.get("name")],
            "genres": [str(item.get("name")).strip() for item in genres[:4] if item.get("name")],
        }

    def _musicbrainz_release_group_detail(self, release_group_id: str) -> dict[str, list[str]]:
        try:
            response = requests.get(
                f"{_MB_BASE}/release-group/{release_group_id}",
                params={"inc": "tags+genres", "fmt": "json"},
                headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return {"tags": [], "genres": []}

        tags = sorted(payload.get("tags", []), key=lambda item: item.get("count", 0), reverse=True)
        genres = sorted(payload.get("genres", []), key=lambda item: item.get("count", 0), reverse=True)
        return {
            "tags": [str(item.get("name")).strip() for item in tags[:8] if item.get("name")],
            "genres": [str(item.get("name")).strip() for item in genres[:4] if item.get("name")],
        }

    def _search_discogs(self, track: Track) -> Candidate | None:
        token = self.settings.discogs_token
        if not token:
            return None
        query = " ".join(part for part in [_clean_text(track.artist), _clean_text(track.title)] if part)
        if not query:
            return None

        response = requests.get(
            f"{_DISCOGS_BASE}/database/search",
            params={"q": query, "type": "release", "token": token},
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            return None

        best = max(results[:5], key=lambda result: _discogs_result_score(track, result))
        title_field = str(best.get("title") or "").strip()
        artist_part = None
        title_part = None
        if " - " in title_field:
            left, right = title_field.split(" - ", 1)
            artist_part = left.strip() or None
            title_part = right.strip() or None

        base_score = 50
        have = ((best.get("community") or {}).get("have") or 0)
        if have:
            base_score = min(99, round(have / 10))
        score = max(0, min(100, base_score + _similarity_bonus(track, title_part, artist_part)))
        tags = [*best.get("genre", []), *best.get("style", [])]
        return Candidate(
            source="Discogs",
            score=score,
            title=title_part or track.title,
            artist=artist_part or track.artist,
            album=title_field or track.album,
            year=str(best.get("year") or "") or None,
            genre=((best.get("genre") or [None])[0]),
            tags=[str(tag).strip() for tag in tags[:8] if str(tag).strip()],
        )

    def _search_ai(self, track: Track) -> Candidate | None:
        tagger = self._build_multi_ai_tagger()
        if tagger is None:
            return None
        result = tagger.analyze(track)
        confidence = float(result.confidence or 0.0)
        score = int(max(0.0, min(1.0, confidence if confidence > 0 else 0.7)) * 100)
        tags: list[str] = []
        if result.genre:
            tags.append(result.genre)
        if result.mood:
            tags.append(result.mood)
        return Candidate(
            source="AI",
            score=score,
            title=result.title or track.title,
            artist=result.artist or track.artist,
            album=result.album or track.album,
            year=result.year or track.year,
            genre=result.genre or track.genre,
            mood=result.mood,
            bpm=result.bpm,
            key=result.key,
            energy=result.energy,
            tags=tags,
        )

    def _build_multi_ai_tagger(self) -> MultiAiTagger | None:
        taggers: list[CloudAiTagger] = []
        for provider in ("openai", "gemini", "grok", "deepseek"):
            api_key, base_url, model = _resolve_provider_config(provider, self.settings)
            if not api_key:
                continue
            taggers.append(
                CloudAiTagger(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    timeout=20,
                    retries=1,
                )
            )
        if not taggers:
            return None
        return MultiAiTagger(taggers, max_workers=min(4, len(taggers)))


def _resolve_provider_config(provider: str, settings) -> tuple[str | None, str | None, str | None]:
    if provider == "gemini":
        return settings.gemini_api_key or settings.cloud_ai_api_key, settings.gemini_base_url, settings.gemini_model
    if provider == "openai":
        return settings.openai_api_key or settings.cloud_ai_api_key, settings.openai_base_url, settings.openai_model
    if provider == "grok":
        return settings.grok_api_key or settings.cloud_ai_api_key, settings.grok_base_url, settings.grok_model
    if provider == "deepseek":
        return settings.deepseek_api_key or settings.cloud_ai_api_key, settings.deepseek_base_url, settings.deepseek_model
    return None, None, None


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\((official|lyric|audio|video|hq|hd|4k|8k|remaster|live)[^)]*\)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    text = " ".join(part for part in text.split() if part.lower() not in _SEARCH_STOPWORDS)
    return text.strip()


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()


def _token_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _similarity_bonus(track: Track, title: str | None, artist: str | None) -> int:
    title_score = _token_similarity(_normalize(track.title), _normalize(title))
    artist_score = _token_similarity(_normalize(track.artist), _normalize(artist))
    combo = (title_score * 0.65) + (artist_score * 0.35)
    return int(round(combo * 20))


def _best_field_value(candidates: list[Candidate], field_name: str) -> Any:
    for candidate in candidates:
        value = getattr(candidate, field_name, None)
        if _has_meaningful_candidate_value(field_name, value):
            return value
    return None


def _has_meaningful_candidate_value(field_name: str, value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        lowered = text.lower()
        if lowered in {"unknown", "n/a", "none", "null", "-"}:
            return False
        if field_name == "year":
            return bool(re.match(r"^(19\d{2}|20\d{2}|2100)$", text) or re.match(r"^\d{4}$", text))
        return True
    return True


def _musicbrainz_recording_score(track: Track, recording: dict[str, Any]) -> float:
    title = recording.get("title")
    artist = _musicbrainz_recording_artist(recording)
    base = _token_similarity(_normalize(track.title), _normalize(title))
    base = (base * 0.65) + (_token_similarity(_normalize(track.artist), _normalize(artist)) * 0.35)
    bonus = 0.0
    release = (recording.get("releases") or [{}])[0]
    if release.get("date"):
        bonus += 0.12
    if release.get("title"):
        bonus += 0.08
    if recording.get("isrcs"):
        bonus += 0.05
    if _musicbrainz_recording_genre(recording):
        bonus += 0.10
    return base + bonus


def _musicbrainz_recording_artist(recording: dict[str, Any]) -> str | None:
    artists = recording.get("artist-credit", []) or recording.get("artists", [])
    if not artists:
        return None
    names: list[str] = []
    for entry in artists:
        if isinstance(entry, dict):
            names.append(entry.get("name") or (entry.get("artist") or {}).get("name") or "")
    joined = ", ".join(part for part in names if part).strip(", ")
    return joined or None


def _musicbrainz_recording_genre(recording: dict[str, Any]) -> str | None:
    detail = recording if recording.get("genres") or recording.get("tags") else None
    if detail is None:
        return None
    genres = detail.get("genres", []) or []
    if genres:
        first = genres[0]
        if isinstance(first, dict):
            name = first.get("name")
            if name:
                return str(name).strip() or None
        elif first:
            return str(first).strip() or None
    tags = detail.get("tags", []) or []
    if tags:
        first = tags[0]
        if isinstance(first, dict):
            name = first.get("name")
            if name:
                return str(name).strip() or None
        elif first:
            return str(first).strip() or None
    return None


def _musicbrainz_release_group_id(recording: dict[str, Any]) -> str | None:
    releases = recording.get("releases", []) or []
    if not releases:
        return None
    release = releases[0] if isinstance(releases[0], dict) else None
    if not release:
        return None
    release_group = release.get("release-group", {})
    if isinstance(release_group, dict):
        rg_id = release_group.get("id")
        if rg_id:
            return str(rg_id)
    return None


def _discogs_result_score(track: Track, result: dict[str, Any]) -> float:
    title_field = str(result.get("title") or "").strip()
    artist_part = None
    title_part = None
    if " - " in title_field:
        left, right = title_field.split(" - ", 1)
        artist_part = left.strip() or None
        title_part = right.strip() or None
    elif title_field:
        title_part = title_field

    base = _token_similarity(_normalize(track.title), _normalize(title_part))
    base = (base * 0.65) + (_token_similarity(_normalize(track.artist), _normalize(artist_part)) * 0.35)
    bonus = 0.0
    if result.get("year"):
        bonus += 0.15
    if result.get("genre"):
        bonus += 0.10
    if result.get("style"):
        bonus += 0.05
    if result.get("community") and (result.get("community") or {}).get("have"):
        bonus += 0.05
    return base + bonus
