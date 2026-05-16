from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import md5
from pathlib import Path, PureWindowsPath
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Any, Callable

import requests

from lumbago_app.core.config import cache_dir
from lumbago_app.core.models import AnalysisResult, Tag, Track
from lumbago_app.core.renamer import parse_filename_tags
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
    albumartist: str | None = None
    year: str | None = None
    tracknumber: str | None = None
    discnumber: str | None = None
    composer: str | None = None
    genre: str | None = None
    rating: int | None = None
    mood: str | None = None
    bpm: float | None = None
    key: str | None = None
    energy: float | None = None
    comment: str | None = None
    lyrics: str | None = None
    isrc: str | None = None
    publisher: str | None = None
    grouping: str | None = None
    copyright: str | None = None
    remixer: str | None = None
    tags: list[str] = field(default_factory=list)
    artwork_url: str | None = None
    error: str | None = None


@dataclass
class EnrichmentResult:
    candidates: list[Candidate] = field(default_factory=list)
    best_match: Candidate | None = None


class UnifiedAutoTagger:
    def __init__(self, settings, logger: Callable[[str], None] | None = None):
        self.settings = settings
        self._logger = logger
        self._ai_batch_cache: dict[str, AnalysisResult] = {}

    def preload_ai_batch(self, tracks: list[Track]) -> None:
        """Run batch AI tagging for all tracks upfront; results cached by path."""
        tagger = self._build_multi_ai_tagger()
        if tagger is None:
            return
        cloud_taggers = [t for t in getattr(tagger, "taggers", []) if isinstance(t, CloudAiTagger)]
        if not cloud_taggers:
            return
        primary = cloud_taggers[0]
        if self._logger:
            self._logger(f"[autotag] ai_batch_preload tracks={len(tracks)}")
        try:
            results = primary.analyze_batch(tracks)
        except Exception as exc:
            if self._logger:
                self._logger(f"[autotag] ai_batch_preload error={exc}")
            return
        for track, result in zip(tracks, results):
            self._ai_batch_cache[track.path] = result
        if self._logger:
            self._logger(f"[autotag] ai_batch_preload done cached={len(self._ai_batch_cache)}")

    def enrich_track(self, track: Track) -> EnrichmentResult:
        candidates: list[Candidate] = []
        supplemental_only_sources = {"LRCLIB", "Lyrics.ovh"}
        providers = (
            self._search_musicbrainz,
            self._search_itunes,
            self._search_deezer,
            self._search_discogs,
            self._search_lrclib,
            self._search_lyrics_ovh,
            self._search_ai,
        )
        max_workers = int(getattr(self.settings, "provider_parallel_workers", 6) or 6)
        max_workers = max(2, min(max_workers, len(providers)))
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="autotag-src") as pool:
            future_map = {pool.submit(self._timed_provider_call, fn, track): fn for fn in providers}
            for future in as_completed(future_map):
                fn = future_map[future]
                try:
                    candidate = future.result()
                    if candidate is not None:
                        candidates.append(candidate)
                except Exception as exc:
                    candidates.append(Candidate(source=fn.__name__, score=0, error=str(exc)))

        valid = [candidate for candidate in candidates if candidate.error is None and candidate.score > 0]
        valid.sort(key=lambda candidate: candidate.score, reverse=True)
        valid_for_best = [candidate for candidate in valid if candidate.source not in supplemental_only_sources]
        best_match = valid_for_best[0] if valid_for_best else (valid[0] if valid else None)
        if self._logger is not None:
            top = best_match
            if top is not None:
                self._logger(f"[autotag] source_summary best={top.source} score={top.score} total_candidates={len(candidates)}")
            else:
                self._logger(f"[autotag] source_summary best=none total_candidates={len(candidates)}")
        return EnrichmentResult(candidates=candidates, best_match=best_match)

    def _timed_provider_call(self, fn, track: Track) -> Candidate | None:
        start = perf_counter()
        name = fn.__name__
        if self._logger is not None:
            self._logger(f"[autotag] source={name} stage=start file={Path(track.path).name}")
        result = fn(track)
        elapsed_ms = int((perf_counter() - start) * 1000)
        if self._logger is not None:
            if result is None:
                self._logger(f"[autotag] source={name} stage=done elapsed_ms={elapsed_ms} status=miss")
            elif result.error:
                self._logger(f"[autotag] source={name} stage=done elapsed_ms={elapsed_ms} status=error error={result.error}")
            else:
                self._logger(f"[autotag] source={name} stage=done elapsed_ms={elapsed_ms} status=hit score={result.score}")
        return result

    def apply_best_match(self, track: Track, result: EnrichmentResult) -> bool:
        raw_candidates = getattr(result, "candidates", []) or []
        candidates = [candidate for candidate in raw_candidates if candidate.error is None and candidate.score > 0]
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        best = result.best_match
        if best is None and not candidates:
            return False
        changed = False
        filename_artist, filename_title = parse_filename_tags(track.path)
        protect_filename_identity = bool(
            filename_title and not filename_artist and _normalize(filename_title) == _normalize(track.title)
        )

        mapping: dict[str, Any] = {}
        for field_name in _CANDIDATE_TRACK_FIELDS:
            if (
                protect_filename_identity
                and field_name in {"title", "artist"}
                and any(candidate.source in {"Apple Music", "MusicBrainz"} for candidate in candidates)
            ):
                incoming = None
            else:
                incoming = _best_field_value(candidates, field_name)
            if incoming is None and best is not None and not (
                protect_filename_identity
                and field_name in {"title", "artist"}
                and best.source in {"Apple Music", "MusicBrainz"}
            ):
                incoming = getattr(best, field_name, None)
            mapping[field_name] = incoming

        # Fields measured locally — don't overwrite with external guesses
        _LOCALLY_MEASURED = {"bpm", "key", "energy", "loudness_lufs", "fingerprint", "file_hash"}

        for field_name, incoming in mapping.items():
            if incoming is None:
                continue
            current = getattr(track, field_name, None)
            if (
                field_name == "album"
                and _has_value(current)
                and _has_value(incoming)
                and _normalize(str(current)) != _normalize(str(incoming))
            ):
                # Protect existing album values from weak/untrusted replacements.
                winning_album = _candidate_for_field(candidates, "album")
                if winning_album is None or winning_album.score < 72:
                    continue
            if field_name in _LOCALLY_MEASURED and _has_value(current):
                continue
            if current != incoming:
                setattr(track, field_name, incoming)
                changed = True

        if best is not None and best.artist and not track.albumartist:
            track.albumartist = best.artist
            changed = True

        if not _has_value(track.artwork_path):
            artwork_url = _best_artwork_url(candidates)
            if artwork_url:
                path_hash = md5(track.path.encode()).hexdigest()[:12]
                dest = cache_dir() / f"cover_{path_hash}.jpg"
                if _download_artwork(artwork_url, dest):
                    track.artwork_path = str(dest)
                    changed = True

        genre_tags: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            for tag_value in candidate.tags:
                clean = str(tag_value).strip()
                if clean and clean.lower() not in seen:
                    seen.add(clean.lower())
                    genre_tags.append(clean)
        if genre_tags:
            track.tags = [Tag(value=t, source="genre_tags") for t in genre_tags[:20]]
            changed = True

        return changed

    def _search_musicbrainz(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        artist = _clean_text(track.artist)
        title = _clean_text(track.title)
        stem = _clean_text(PureWindowsPath(track.path).stem.replace("_", " ").replace(".", " "))
        if not artist and not title and stem:
            title = stem

        # Build multiple fallback queries — try most specific first.
        queries: list[str] = []
        if artist and title:
            queries.append(f'recording:"{title[:60]}" AND artist:"{artist[:60]}"')
        if title:
            queries.append(f'recording:"{title[:60]}"')
        if artist and not title and stem:
            queries.append(f'recording:"{stem[:60]}" AND artist:"{artist[:60]}"')
        if stem and stem != title:
            queries.append(f'recording:"{stem[:60]}"')
        if not queries:
            return None

        recordings: list = []
        used_query = queries[0]
        for query in queries:
            try:
                response = requests.get(
                    f"{_MB_BASE}/recording/",
                    params={"query": query, "limit": "10", "fmt": "json"},
                    headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                    timeout=15,
                )
                response.raise_for_status()
                payload = response.json()
                recordings = payload.get("recordings", [])
                if recordings:
                    used_query = query
                    break
            except Exception:
                continue

        if not recordings:
            return None

        best = max(recordings[:10], key=lambda r: _musicbrainz_recording_score(track, r))
        rec_title = best.get("title")
        rec_artist = ", ".join(
            entry.get("name") or (entry.get("artist") or {}).get("name") or ""
            for entry in (best.get("artist-credit") or [])
            if isinstance(entry, dict)
        ).strip(", ")
        release = (best.get("releases") or [{}])[0]
        year = str((release.get("date") or "")[:4]).strip() or None
        score = int(round(_musicbrainz_recording_score(track, best) * 100))
        if not artist:
            score = min(score, 68)

        genre = None
        tags: list[str] = []
        albumartist = None
        publisher = None
        comment_parts: list[str] = []
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
        release_artists = release.get("artist-credit", [])
        if release_artists:
            albumartist = ", ".join(
                entry.get("name") or (entry.get("artist") or {}).get("name") or ""
                for entry in release_artists
                if isinstance(entry, dict)
            ).strip(", ") or None
        label_info = release.get("label-info", [])
        if label_info and isinstance(label_info, list):
            first_label = label_info[0] if isinstance(label_info[0], dict) else {}
            label_name = None
            if isinstance(first_label, dict):
                label = first_label.get("label")
                if isinstance(label, dict):
                    label_name = label.get("name")
            publisher = str(label_name).strip() if label_name else None
        disambiguation = str(best.get("disambiguation") or "").strip()
        release_disambiguation = str(release.get("disambiguation") or "").strip()
        if disambiguation:
            comment_parts.append(disambiguation)
        if release_disambiguation and release_disambiguation not in comment_parts:
            comment_parts.append(release_disambiguation)
        remixer = _extract_remixer_name(rec_title) or _extract_remixer_name(track.title)

        sim = _similarity_bonus(track, rec_title, rec_artist)
        final_score = max(0, min(100, score + sim))
        if not artist:
            final_score = min(final_score, 68)
        release_mbid = release.get("id")
        mb_artwork_url = f"https://coverartarchive.org/release/{release_mbid}/front-500" if release_mbid else None
        return Candidate(
            source="MusicBrainz",
            score=final_score,
            title=rec_title or track.title,
            artist=rec_artist or track.artist,
            album=release.get("title") or None,
            albumartist=albumartist,
            year=year,
            genre=genre,
            comment=" / ".join(comment_parts) or None,
            publisher=publisher,
            remixer=remixer,
            tags=tags,
            artwork_url=mb_artwork_url,
        )

    def _search_itunes(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        query = " ".join(part for part in [_clean_text(track.artist), _clean_text(track.title)] if part)
        if not query:
            return None

        response = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "song", "limit": "8"},
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        results = [item for item in payload.get("results", []) if isinstance(item, dict)]
        if not results:
            return None

        best = max(results, key=lambda item: _itunes_result_score(track, item))
        score = int(round(_itunes_result_score(track, best) * 100))
        min_score = 30 if not track.artist else 45
        if score < min_score:
            return None
        if not track.artist:
            score = min(score, 72)
        release_date = str(best.get("releaseDate") or "")
        year = release_date[:4] if release_date[:4].isdigit() else None
        raw_artwork = _to_clean_str(best.get("artworkUrl100"))
        artwork_url = raw_artwork.replace("100x100bb", "600x600bb") if raw_artwork else None
        return Candidate(
            source="Apple Music",
            score=max(1, min(95, score)),
            title=_to_clean_str(best.get("trackName")) or track.title,
            artist=_to_clean_str(best.get("artistName")) or track.artist,
            album=_to_clean_str(best.get("collectionName")),
            albumartist=_to_clean_str(best.get("collectionArtistName")) or _to_clean_str(best.get("artistName")),
            year=year,
            genre=_to_clean_str(best.get("primaryGenreName")),
            artwork_url=artwork_url,
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

    def _search_deezer(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        artist = _clean_text(track.artist)
        title = _clean_text(track.title)
        if not title and not artist:
            return None

        # Deezer supports artist:"X" track:"Y" syntax
        parts: list[str] = []
        if artist:
            parts.append(f'artist:"{artist[:50]}"')
        if title:
            parts.append(f'track:"{title[:60]}"')
        query = " ".join(parts) if parts else (artist or title)

        try:
            response = requests.get(
                "https://api.deezer.com/search",
                params={"q": query, "limit": "10", "order": "RANKING"},
                headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None

        results = payload.get("data", [])
        if not results:
            # Retry with simpler query
            simple = f"{artist} {title}".strip()
            try:
                resp2 = requests.get(
                    "https://api.deezer.com/search",
                    params={"q": simple[:80], "limit": "10"},
                    headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                    timeout=12,
                )
                resp2.raise_for_status()
                results = resp2.json().get("data", [])
            except Exception:
                pass
        if not results:
            return None

        best = max(results[:10], key=lambda r: _deezer_result_score(track, r))
        score = int(round(_deezer_result_score(track, best) * 100))
        if score < 30:
            return None

        rec_title = _to_clean_str(best.get("title")) or _to_clean_str(best.get("title_short"))
        rec_artist = _to_clean_str((best.get("artist") or {}).get("name"))
        rec_album = _to_clean_str((best.get("album") or {}).get("title"))
        return Candidate(
            source="Deezer",
            score=max(1, min(90, score)),
            title=rec_title or track.title,
            artist=rec_artist or track.artist,
            album=rec_album,
        )

    def _search_discogs(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
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
            artwork_url=_to_clean_str(best.get("cover_image")) or _to_clean_str(best.get("thumb")),
        )

    def _search_ai(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        cached = self._ai_batch_cache.get(track.path)
        if cached is not None:
            result = cached
        else:
            tagger = self._build_multi_ai_tagger()
            if tagger is None:
                return None
            result = tagger.analyze(track)
        useful_fields = [
            result.album,
            result.year,
            result.genre,
            result.comment,
            result.lyrics,
            result.isrc,
            result.publisher,
            result.grouping,
            result.copyright,
            result.remixer,
        ]
        if not any(_has_meaningful_candidate_value("ai", value) for value in useful_fields):
            if not (result.confidence or 0.0):
                return Candidate(source="AI", score=0, error=result.description or "AI returned no usable fields")
            # confidence > 0 but useful_fields list is empty — fall through and build
            # candidate from whatever the AI did return (title, artist, key, bpm, etc.)
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
            albumartist=result.albumartist or track.albumartist,
            year=result.year or track.year,
            tracknumber=result.tracknumber or track.tracknumber,
            discnumber=result.discnumber or track.discnumber,
            composer=result.composer or track.composer,
            genre=result.genre or track.genre,
            rating=result.rating if result.rating is not None else track.rating,
            mood=result.mood,
            bpm=result.bpm,
            key=result.key,
            energy=result.energy,
            comment=result.comment or track.comment,
            lyrics=result.lyrics or track.lyrics,
            isrc=result.isrc or track.isrc,
            publisher=result.publisher or track.publisher,
            grouping=result.grouping or track.grouping,
            copyright=result.copyright or track.copyright,
            remixer=result.remixer or track.remixer,
            tags=tags,
        )

    def _search_lrclib(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        artist = _clean_text(track.artist)
        title = _clean_text(track.title)
        if not artist or not title:
            return None
        try:
            response = requests.get(
                "https://lrclib.net/api/search",
                params={
                    "track_name": title[:120],
                    "artist_name": artist[:120],
                    "album_name": (_clean_text(track.album) or "")[:120],
                },
                headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None
        if not isinstance(payload, list) or not payload:
            return None
        best = None
        best_score = -1.0
        for item in payload[:10]:
            if not isinstance(item, dict):
                continue
            item_title = _to_clean_str(item.get("trackName"))
            item_artist = _to_clean_str(item.get("artistName"))
            local_score = _token_similarity(_normalize(title), _normalize(item_title))
            local_score = (local_score * 0.7) + (_token_similarity(_normalize(artist), _normalize(item_artist)) * 0.3)
            if local_score > best_score:
                best = item
                best_score = local_score
        if not isinstance(best, dict) or best_score < 0.45:
            return None
        lyrics = _to_clean_str(best.get("plainLyrics")) or _to_clean_str(best.get("syncedLyrics"))
        if not lyrics:
            return None
        comment = "Lyrics source: LRCLIB"
        score = int(min(90, max(35, round(best_score * 100))))
        return Candidate(
            source="LRCLIB",
            score=score,
            title=_to_clean_str(best.get("trackName")) or track.title,
            artist=_to_clean_str(best.get("artistName")) or track.artist,
            album=_to_clean_str(best.get("albumName")) or track.album,
            lyrics=lyrics,
            comment=comment,
        )

    def _search_lyrics_ovh(self, track: Track) -> Candidate | None:
        track = _track_with_filename_identity(track)
        artist = _clean_text(track.artist)
        title = _clean_text(track.title)
        if not artist or not title:
            return None
        try:
            response = requests.get(
                f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist)}/{requests.utils.quote(title)}",
                headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
                timeout=10,
            )
            if response.status_code >= 400:
                return None
            payload = response.json()
        except Exception:
            return None
        lyrics = _to_clean_str(payload.get("lyrics")) if isinstance(payload, dict) else None
        if not lyrics:
            return None
        return Candidate(
            source="Lyrics.ovh",
            score=48,
            lyrics=lyrics,
            comment="Lyrics source: lyrics.ovh",
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


def _best_artwork_url(candidates: list[Candidate]) -> str | None:
    source_priority = ("Apple Music", "Discogs", "MusicBrainz")
    for source in source_priority:
        for candidate in candidates:
            if candidate.source == source and candidate.artwork_url:
                return candidate.artwork_url
    for candidate in candidates:
        if candidate.artwork_url:
            return candidate.artwork_url
    return None


def _download_artwork(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return False
        dest.write_bytes(resp.content)
        return True
    except Exception:
        return False


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


def _to_clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "—", "unknown", "n/a", "none", "null", "brak"}
    return True


def _looks_like_track_number(value: str | None) -> bool:
    """Return True when value is a bare track/disc number (e.g. '01', '2', '14')."""
    if not value:
        return False
    return bool(re.fullmatch(r"\d{1,3}", value.strip()))


def _looks_like_opaque_id(value: str | None) -> bool:
    """Return True for filenames that look like hashes or download IDs rather than real titles.

    Opaque IDs tend to be hex strings or purely alphanumeric blobs without
    spaces that are at least 8 characters long (e.g. '3a7f2b1c', 'abc123def456').
    """
    if not value:
        return False
    s = value.strip()
    # Hex hash: 8+ consecutive hex characters, no spaces or non-hex letters
    return bool(re.fullmatch(r"[0-9a-f]{8,}", s, re.IGNORECASE))


def _looks_like_download_quality_title(value: str | None) -> bool:
    if not value:
        return False
    return bool(re.fullmatch(r" {0,4}\d{2,4} {0,2}(?:kbps|k)? {0,4}", str(value), re.IGNORECASE))


def _strip_download_quality_suffix(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    previous = None
    while previous != text:
        previous = text
        text = re.sub(
            r" {1,4}- {1,4}(?:\d{2,4} {0,2}(?:kbps|k)?|mp3|flac|wav|m4a|aac)$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip(" .-_")
    return text or None


def _extract_remixer_name(title: str | None) -> str | None:
    if not title:
        return None
    match = re.search(r"\((?P<name>[^()]{2,60}?)\s+remix\)", title, re.IGNORECASE)
    if not match:
        return None
    raw = match.group("name").strip(" -_/")
    return raw or None


def _track_with_filename_identity(track: Track) -> Track:
    artist_from_file, title_from_file = parse_filename_tags(track.path)
    cleaned_current_title = _strip_download_quality_suffix(track.title)
    artist = track.artist
    if (
        title_from_file
        and not artist_from_file
        and artist
        and _normalize(artist) == _normalize(title_from_file)
    ):
        artist = None
    if not title_from_file:
        if cleaned_current_title and cleaned_current_title != track.title:
            return replace(track, title=cleaned_current_title, artist=artist)
        if artist != track.artist:
            return replace(track, artist=artist)
        return track
    if _looks_like_download_quality_title(track.title):
        safe_artist = artist_from_file if (artist_from_file and not _looks_like_track_number(artist_from_file)) else None
        return replace(track, title=title_from_file, artist=safe_artist)
    if cleaned_current_title and cleaned_current_title != track.title:
        safe_artist = artist_from_file if (artist_from_file and not _looks_like_track_number(artist_from_file)) else artist
        return replace(track, title=cleaned_current_title, artist=safe_artist)
    # Use filename title only when track title is absent or the filename-derived
    # title is clearly not an opaque hash/ID (avoids clobbering good tags with noise)
    if title_from_file and not _looks_like_opaque_id(title_from_file) and not artist_from_file and not artist and track.title != title_from_file:
        return replace(track, title=title_from_file, artist=None)
    if artist_from_file and not _looks_like_track_number(artist_from_file) and title_from_file and (not artist or not track.title):
        return replace(
            track,
            artist=artist or artist_from_file,
            title=track.title or title_from_file,
        )
    if artist != track.artist:
        return replace(track, artist=artist)
    return track


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


def _candidate_for_field(candidates: list[Candidate], field_name: str) -> Candidate | None:
    for candidate in candidates:
        value = getattr(candidate, field_name, None)
        if _has_meaningful_candidate_value(field_name, value):
            return candidate
    return None


_CANDIDATE_TRACK_FIELDS = (
    "title",
    "artist",
    "album",
    "albumartist",
    "year",
    "tracknumber",
    "discnumber",
    "composer",
    "genre",
    "rating",
    "mood",
    "key",
    "bpm",
    "energy",
    "comment",
    "lyrics",
    "isrc",
    "publisher",
    "grouping",
    "copyright",
    "remixer",
)


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


def _itunes_result_score(track: Track, result: dict[str, Any]) -> float:
    title = result.get("trackName")
    artist = result.get("artistName")
    base = _token_similarity(_normalize(track.title), _normalize(title))
    if track.artist:
        base = (base * 0.65) + (_token_similarity(_normalize(track.artist), _normalize(artist)) * 0.35)
    score = base * 0.76
    bonus = 0.0
    if result.get("collectionName"):
        bonus += 0.08
    if result.get("releaseDate"):
        bonus += 0.08
    if result.get("primaryGenreName"):
        bonus += 0.08
    return min(1.0, score + bonus)


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


def _deezer_result_score(track: Track, result: dict[str, Any]) -> float:
    rec_title = str(result.get("title") or result.get("title_short") or "").strip()
    rec_artist = str((result.get("artist") or {}).get("name") or "").strip()
    base = _token_similarity(_normalize(track.title), _normalize(rec_title))
    if track.artist:
        base = (base * 0.65) + (_token_similarity(_normalize(track.artist), _normalize(rec_artist)) * 0.35)
    bonus = 0.0
    if result.get("album"):
        bonus += 0.06
    if result.get("duration"):
        bonus += 0.04
    if result.get("rank") and int(result.get("rank") or 0) > 100000:
        bonus += 0.05
    return min(1.0, base * 0.82 + bonus)


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
