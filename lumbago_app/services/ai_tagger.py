from __future__ import annotations

import json
import queue
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace as _dc_replace
from pathlib import Path
from typing import Any

import requests

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.core.services import heuristic_analysis
from lumbago_app.services.ai_tagger_merge import _harmonize_batch_results
from lumbago_app.services.metadata_providers import (
    RateLimitedMusicBrainzProvider,
    _best_mbid_from_acoustid,
    _parse_mb_recording,
)


_ISRC_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}\d{7}$")
_YEAR_MIN = 1900
_YEAR_MAX = int(time.strftime("%Y")) + 1
_BATCH_MAX_CHUNK = 25
_BATCH_COOLDOWN_SECONDS = 3.5
_MUSIC_ARCHIVIST_SYSTEM_PROMPT = (
    "You are an expert music archivist with access to a vast database of music "
    "information, equivalent to searching across MusicBrainz, Discogs, AllMusic, "
    "Spotify, and Apple Music. You receive a batch of audio files (filename + existing "
    "tags). Some files may belong to the same album or artist.\n\n"
    "YOUR TASK: Identify each track and return complete, accurate ID3 metadata.\n\n"
    "CRITICAL RULES:\n"
    "1. ALBUM CONSISTENCY: Files with sequential numbers (e.g. '01-song.mp3', "
    "'02-another.mp3') or the same folder must have IDENTICAL 'artist', 'album', "
    "and 'albumArtist' fields.\n"
    "2. STUDIO FIRST: Always prefer the original studio album over Greatest Hits, "
    "Best Of, DJ mixes, compilations, or re-releases. Correct the album if the "
    "existing tag points to a compilation.\n"
    "3. TITLE CLEANING: Remove YouTube/download suffixes from titles: "
    "'(Official Video)', '(Official Music Video)', '[4K]', 'HD', 'HQ', 'tekst', "
    "'lyrics', 'prod. X' (move producer to composer field), 'feat.' stays in artist.\n"
    "4. ARTIST FORMATTING: Correct 'ArtistA ArtistB' to 'ArtistA feat. ArtistB' "
    "when applicable. Use '&' for equal collaborations, 'feat.' for features.\n"
    "5. PRODUCER TO COMPOSER: If the filename contains 'prod. X', 'prod X', or "
    "similar — put the producer name in the 'composer' field, not the title.\n"
    "6. ORIGINAL ARTIST: For cover versions, put the original artist in 'originalArtist'.\n"
    "7. NO PLACEHOLDERS: Never return 'Unknown', 'Various', empty strings. "
    "Return null if uncertain.\n"
    "8. COMMENTS: Add a short factual comment (1 sentence) about the track.\n"
    "9. COPYRIGHT: Return label and year, e.g. '2007 Universal Records'.\n"
    "10. Latin alphabet only in all text fields.\n\n"
    "Return ONLY a JSON array. Each item: "
    "{originalFilename, tags: {title, artist, albumArtist, album, year, genre, "
    "trackNumber, discNumber, composer, originalArtist, mood, copyright, comment, "
    "bpm, key}}. No markdown, no explanation."
)


def _validate_result(result: AnalysisResult) -> AnalysisResult:
    """Sanitize AI-returned values — replace out-of-range / malformed fields with None."""
    kw: dict[str, Any] = {}

    if result.year is not None:
        digits = re.sub(r"\D", "", str(result.year))[:4]
        if digits and _YEAR_MIN <= int(digits) <= _YEAR_MAX:
            kw["year"] = digits
        else:
            kw["year"] = None

    if result.isrc is not None:
        compact = result.isrc.replace("-", "").upper()
        kw["isrc"] = compact if _ISRC_RE.match(compact) else None

    if result.bpm is not None:
        kw["bpm"] = result.bpm if 40.0 <= result.bpm <= 250.0 else None

    if result.energy is not None:
        kw["energy"] = max(0.0, min(1.0, result.energy))

    if result.confidence is not None:
        kw["confidence"] = max(0.0, min(1.0, result.confidence))

    return _dc_replace(result, **kw) if kw else result


class DatabaseTagger:
    """Enriches tracks using AcoustID fingerprint → MusicBrainz lookup.
    Falls back to MusicBrainz text search when no AcoustID key is configured."""

    provider_name = "database"

    def __init__(
        self,
        acoustid: Any | None = None,
        mb: RateLimitedMusicBrainzProvider | None = None,
    ):
        self._acoustid = acoustid
        self._mb = mb or RateLimitedMusicBrainzProvider()

    def analyze(self, track: Track) -> AnalysisResult:
        # --- path 1: AcoustID fingerprint → MB MBID lookup ---
        mbid = self._resolve_mbid_via_acoustid(track)
        if mbid:
            recording = self._mb.get_recording(mbid)
            if recording:
                meta = _parse_mb_recording(recording)
                if meta:
                    return _mb_meta_to_result(meta, confidence=0.93,
                                              source="AcoustID+MusicBrainz")

        # --- path 2: MB text search → fetch full recording by MBID ---
        query = " ".join(filter(None, [track.artist, track.title])).strip()
        if not query:
            query = Path(track.path).stem
        recordings = self._mb.search(query, limit=1)
        if recordings:
            rec = recordings[0]
            rec_id = rec.get("id")
            if rec_id:
                full = self._mb.get_recording(rec_id)
                if full:
                    meta = _parse_mb_recording(full)
                    if meta:
                        return _mb_meta_to_result(meta, confidence=0.78,
                                                  source="MusicBrainz text search")

        return AnalysisResult(description="Database: no match", confidence=0.0)

    def _resolve_mbid_via_acoustid(self, track: Track) -> str | None:
        if not self._acoustid:
            return None
        try:
            from lumbago_app.services.recognizer import AcoustIdRecognizer  # local import avoids circular
            if not isinstance(self._acoustid, AcoustIdRecognizer):
                return None
            payload = self._acoustid.recognize(Path(track.path))
            if payload:
                return _best_mbid_from_acoustid(payload)
        except Exception:
            pass
        return None

    def cache_key(self) -> str:
        return "database"


def _mb_meta_to_result(meta: dict, confidence: float, source: str) -> AnalysisResult:
    return AnalysisResult(
        title=meta.get("title"),
        artist=meta.get("artist"),
        albumartist=meta.get("albumartist"),
        album=meta.get("album"),
        year=meta.get("year"),
        isrc=meta.get("isrc"),
        publisher=meta.get("publisher"),
        tracknumber=meta.get("tracknumber"),
        comment=meta.get("comment"),
        remixer=meta.get("remixer"),
        confidence=confidence,
        description=source,
    )


class LocalAiTagger:
    provider_name = "local"

    def analyze(self, track: Track) -> AnalysisResult:
        return heuristic_analysis(track)

    def cache_key(self) -> str:
        return "local"


class CloudAiTagger:
    def __init__(
        self,
        provider: str | None,
        api_key: str | None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 25,
        retries: int = 3,
    ):
        self.provider = provider
        self.provider_name = provider or "cloud"
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)
        self._resolved_base_url, self._resolved_model = _resolve_runtime_config(
            self.provider,
            self.base_url,
            self.model,
        )

    def analyze(self, track: Track) -> AnalysisResult:
        if not self.provider or not self.api_key:
            return AnalysisResult(description="Cloud AI not configured", confidence=0.0)
        base_url, model = self._resolved_base_url, self._resolved_model
        if not base_url or not model:
            return AnalysisResult(description="Cloud AI missing base URL or model", confidence=0.0)

        missing = _missing_fields(track)
        noisy = _noisy_fields(track)
        fields_to_fill = list(dict.fromkeys(missing + [f for f in noisy if f not in missing]))
        if not fields_to_fill:
            return AnalysisResult(description="No missing fields", confidence=1.0)
        prompt = _build_prompt(track, fields_to_fill, noisy_fields=noisy)
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                if self.provider == "gemini":
                    text = _call_gemini_generate_content(base_url, self.api_key, model, prompt, self.timeout)
                else:
                    text = _call_openai_compatible_chat(
                        base_url, self.api_key, model, prompt, self.timeout
                    )
                payload = _safe_json(text)
                if not isinstance(payload, dict):
                    return AnalysisResult(description="Cloud AI returned non-JSON response", confidence=0.0)
                cleaned = _normalize_payload(payload)
                confidence = _to_float(cleaned.get("confidence"))
                if confidence is None:
                    confidence = _infer_confidence(cleaned)
                raw = AnalysisResult(
                    bpm=_to_float(cleaned.get("bpm")),
                    key=_to_str(cleaned.get("key")),
                    mood=_to_str(cleaned.get("mood")),
                    energy=_to_float(cleaned.get("energy")),
                    genre=_to_str(cleaned.get("genre")),
                    rating=_parse_rating(cleaned.get("rating")),
                    description=_to_str(cleaned.get("description")),
                    confidence=confidence,
                    title=_to_str(cleaned.get("title")),
                    artist=_to_str(cleaned.get("artist")),
                    album=_to_str(cleaned.get("album")),
                    albumartist=_to_str(cleaned.get("albumartist")),
                    year=_to_str(cleaned.get("year")),
                    tracknumber=_to_str(cleaned.get("tracknumber")),
                    discnumber=_to_str(cleaned.get("discnumber")),
                    composer=_to_str(cleaned.get("composer")),
                    isrc=_to_str(cleaned.get("isrc")),
                    publisher=_to_str(cleaned.get("publisher")),
                    lyrics=_to_str(cleaned.get("lyrics")),
                    grouping=_to_str(cleaned.get("grouping")),
                    copyright=_to_str(cleaned.get("copyright")),
                    remixer=_to_str(cleaned.get("remixer")),
                    comment=_to_str(cleaned.get("comment")),
                )
                return _validate_result(raw)
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries or not _is_retryable_exception(exc):
                    break
                time.sleep(_retry_backoff_seconds(attempt, exc))
        return AnalysisResult(description=f"Cloud AI error: {last_exc}", confidence=0.0)

    def cache_key(self) -> str:
        base_url, model = self._resolved_base_url, self._resolved_model
        return f"{self.provider_name}|{base_url or ''}|{model or ''}"

    def analyze_batch(self, tracks: list[Track], chunk_size: int = 20) -> list[AnalysisResult]:
        safe_chunk = max(1, min(_BATCH_MAX_CHUNK, int(chunk_size)))
        output: list[AnalysisResult] = []
        total = len(tracks)
        for start in range(0, total, safe_chunk):
            chunk = tracks[start : start + safe_chunk]
            chunk_results = self._analyze_batch_chunk(chunk)
            harmonized = _harmonize_batch_results(list(zip(chunk, chunk_results)))
            output.extend(result for _, result in harmonized)
            if start + safe_chunk < total:
                time.sleep(_BATCH_COOLDOWN_SECONDS)
        return output

    def _analyze_batch_chunk(self, tracks: list[Track]) -> list[AnalysisResult]:
        if not tracks:
            return []
        if not self.provider or not self.api_key:
            return [
                AnalysisResult(description="Cloud AI not configured", confidence=0.0)
                for _track in tracks
            ]
        base_url, model = self._resolved_base_url, self._resolved_model
        if not base_url or not model:
            return [
                AnalysisResult(description="Cloud AI missing base URL or model", confidence=0.0)
                for _track in tracks
            ]

        prompt = _build_batch_prompt(tracks)
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                if self.provider == "gemini":
                    text = _call_gemini_generate_batch_content(
                        base_url, self.api_key, model, prompt, self.timeout
                    )
                else:
                    text = _call_openai_compatible_batch_chat(
                        base_url, self.api_key, model, prompt, self.timeout
                    )
                parsed = _safe_json(text)
                return _batch_payload_to_results(parsed, tracks)
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries or not _is_retryable_exception(exc):
                    break
                time.sleep(_retry_backoff_seconds(attempt, exc))

        # Preserve a useful degraded mode: if one batch request fails, try the
        # older per-track path instead of losing the whole album.
        results: list[AnalysisResult] = []
        for track in tracks:
            result = self.analyze(track)
            if not result.description and last_exc is not None and not result.confidence:
                result = _dc_replace(result, description=f"Cloud AI batch fallback: {last_exc}")
            results.append(result)
        return results


class MultiAiTagger:
    """Runs multiple AI providers in parallel and merges best field-level values."""

    def __init__(self, taggers: list[Any], max_workers: int = 3):
        self.taggers = [tagger for tagger in taggers if tagger is not None]
        self.max_workers = max(1, int(max_workers))

    def analyze(self, track: Track) -> AnalysisResult:
        if not self.taggers:
            return AnalysisResult(description="No AI providers selected", confidence=0.0)
        if len(self.taggers) == 1:
            return self.taggers[0].analyze(track)

        results: list[tuple[str, AnalysisResult]] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(self.taggers))) as pool:
            futures = {
                pool.submit(tagger.analyze, track): getattr(tagger, "provider_name", tagger.__class__.__name__)
                for tagger in self.taggers
            }
            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = AnalysisResult(description=f"{provider_name}: {exc}", confidence=0.0)
                results.append((provider_name, result))

        merged = _merge_results(results)
        return merged

    def cache_key(self) -> str:
        keys: list[str] = []
        for tagger in self.taggers:
            cache_fn = getattr(tagger, "cache_key", None)
            if callable(cache_fn):
                keys.append(str(cache_fn()))
            else:
                keys.append(getattr(tagger, "provider_name", tagger.__class__.__name__))
        return "multi:" + "|".join(sorted(keys))


_FLOAT_AI_FIELDS = {"bpm", "energy"}


_FLOAT_AI_FIELDS = {"bpm", "energy"}


def _merge_results(results: list[tuple[str, AnalysisResult]]) -> AnalysisResult:
    if not results:
        return AnalysisResult(description="No AI results", confidence=0.0)

    winners: dict[str, Any] = {}
    winner_confidences: list[float] = []

    for field_name in _ALL_AI_FIELDS:
        best_value = None
        best_score = -1.0
        for _provider, result in results:
            value = getattr(result, field_name, None)
            if not _has_nonempty_value(value):
                continue
            score = float(result.confidence or 0.0)
            if score <= 0:
                score = 0.6
            if score > best_score:
                best_score = score
                best_value = value
        winners[field_name] = best_value
        if best_score > 0:
            winner_confidences.append(best_score)

    provider_parts = []
    for provider, result in results:
        conf = float(result.confidence or 0.0)
        part = f"{provider}:{conf:.2f}"
        if conf == 0.0 and result.description:
            part += f"({result.description})"
        provider_parts.append(part)
    providers_info = ", ".join(provider_parts)
    merged_conf = sum(winner_confidences) / len(winner_confidences) if winner_confidences else 0.0
    return AnalysisResult(
        bpm=_to_float(winners.get("bpm")),
        key=_to_str(winners.get("key")),
        mood=_to_str(winners.get("mood")),
        energy=_to_float(winners.get("energy")),
        genre=_to_str(winners.get("genre")),
        rating=_parse_rating(winners.get("rating")),
        title=_to_str(winners.get("title")),
        artist=_to_str(winners.get("artist")),
        album=_to_str(winners.get("album")),
        albumartist=_to_str(winners.get("albumartist")),
        year=_to_str(winners.get("year")),
        tracknumber=_to_str(winners.get("tracknumber")),
        discnumber=_to_str(winners.get("discnumber")),
        composer=_to_str(winners.get("composer")),
        isrc=_to_str(winners.get("isrc")),
        publisher=_to_str(winners.get("publisher")),
        lyrics=_to_str(winners.get("lyrics")),
        grouping=_to_str(winners.get("grouping")),
        copyright=_to_str(winners.get("copyright")),
        remixer=_to_str(winners.get("remixer")),
        comment=_to_str(winners.get("comment")),
        description=f"Merged from providers ({providers_info})",
        confidence=merged_conf,
    )


def _has_nonempty_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


_MISSING_SENTINEL = {"", "-", "—", "unknown", "n/a", "none", "null"}
_TRASH_PATTERNS = (
    "unknown",
    "track ",
    "www.",
    "http://",
    "https://",
)
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:\\[^\s]+")
_UNIX_PATH_RE = re.compile(r"(?<!\w)(?:/[^/\s]+){2,}")
_BASE64_BLOB_RE = re.compile(r"^[A-Za-z0-9+/=]{300,}$")

_ALL_AI_FIELDS: list[str] = [
    "title",
    "bpm",
    "key",
    "mood",
    "energy",
    "artist",
    "album",
    "albumartist",
    "genre",
    "rating",
    "year",
    "tracknumber",
    "discnumber",
    "composer",
    "isrc",
    "publisher",
    "lyrics",
    "grouping",
    "copyright",
    "remixer",
    "comment",
]

# Patterns that indicate a title/artist contains video/quality noise
_NOISE_CHECK_RE = re.compile(
    r'[\[(]\s*('
    r'official(\s+music)?\s+video|official\s+audio|audio|lyrics?|lyric\s+video|'
    r'visualizer|hq|hd|4k|8k|remastered(\s+\d{4})?|live|full\s+album|explicit'
    r')\s*[\])]'
    r'|\b(official(\s+music)?\s+video|official\s+audio|lyric\s+video|visualizer)\b'
    r'|\b(4k|8k)\b',
    re.IGNORECASE,
)


def _noisy_fields(track: Track) -> list[str]:
    '''Return title/artist fields that contain video/quality noise markers.'''
    noisy: list[str] = []
    for fname in ('title', 'artist'):
        val = getattr(track, fname, None)
        if isinstance(val, str) and _NOISE_CHECK_RE.search(val):
            noisy.append(fname)
    return noisy


def _missing_fields(track: Track) -> list[str]:
    # Default: include all fields so AI can verify/repair.
    return list(_ALL_AI_FIELDS)


_FIELD_LABELS: dict[str, str] = {
    "title": "Tytul",
    "bpm": "BPM",
    "key": "Tonacja",
    "mood": "Nastroj",
    "energy": "Energia",
    "artist": "Artysta",
    "album": "Album",
    "albumartist": "Artysta albumu",
    "genre": "Gatunek",
    "rating": "Ocena",
    "year": "Rok",
    "tracknumber": "Numer utworu",
    "discnumber": "Numer dysku",
    "composer": "Kompozytor",
    "isrc": "ISRC",
    "publisher": "Wydawca",
    "lyrics": "Tekst",
    "grouping": "Grupowanie",
    "copyright": "Prawa autorskie",
    "remixer": "Remikser",
    "comment": "Komentarz",
}


def _build_prompt(
    track: Track,
    missing: list[str],
    noisy_fields: list[str] | None = None,
) -> str:
    noisy_set = set(noisy_fields or [])
    # Always include filename as context
    known_lines = [f"Nazwa pliku: {Path(track.path).stem}"]

    # Parent folder — often contains year, genre, label info
    folder = Path(track.path).parent.name
    if folder and folder not in (".", ".."):
        known_lines.append(f"Folder: {folder}")

    # Audio technical context
    if track.duration:
        mins, secs = divmod(int(track.duration), 60)
        known_lines.append(f"Czas trwania: {mins}:{secs:02d}")
    if track.format or track.bitrate:
        fmt_parts = []
        if track.format:
            fmt_parts.append(track.format.upper())
        if track.bitrate:
            fmt_parts.append(f"{track.bitrate}kbps")
        known_lines.append(f"Format audio: {' '.join(fmt_parts)}")

    for fname in _ALL_AI_FIELDS:
        if fname in noisy_set:
            continue  # We'll ask AI to clean these
        value = getattr(track, fname, None)
        if value is None:
            continue
        if fname in {"lyrics", "comment"}:
            continue
        label = _FIELD_LABELS.get(fname, fname)
        known_lines.append(f"{label}: {_sanitize_prompt_value(value)}")

    known_section = "\n".join(known_lines)
    fields_list = ", ".join(missing)

    clean_note = ""
    if noisy_set:
        noisy_current = []
        for fname in noisy_set:
            val = getattr(track, fname, None)
            if val:
                noisy_current.append(f"{_FIELD_LABELS.get(fname, fname)}: \"{val}\"")
        if noisy_current:
            clean_note = (
                "\nPola do oczyszczenia (usuń zbędne elementy jak '[4K Video]', "
                "'(Official Lyric Video)', '(Official Music Video)', 'HQ', 'HD', itp., "
                "zachowaj remixy i featuringi): "
                + "; ".join(noisy_current)
            )

    return (
        "You are an expert music archivist with access to a vast database equivalent "
        "to MusicBrainz, Discogs, AllMusic, Spotify, and Apple Music. "
        "Identify the track from the filename and existing tags, then return complete "
        "accurate ID3 metadata.\n\n"
        "RULES:\n"
        "1) Return ONLY valid JSON matching the schema.\n"
        "2) Fields: title, artist, album, year, genre, tracknumber, discnumber, bpm, "
        "key, albumartist, originalArtist, composer, mood, copyright, comment, "
        "lyrics, originalFilename, confidence, description.\n"
        "3) originalFilename must equal the input filename exactly.\n"
        "4) Return null for any field you cannot determine with confidence.\n"
        "5) Never return placeholders: Unknown/Undefined/Various.\n"
        "6) STUDIO FIRST: Prefer original studio album over Greatest Hits/compilations/"
        "DJ mixes. Correct wrong album tags.\n"
        "7) TITLE CLEANING: Remove '(Official Video)', '[4K]', 'HD', 'HQ', 'tekst', "
        "'lyrics' from titles. Move 'prod. X' to composer field.\n"
        "8) ARTIST FORMAT: Fix 'ArtistA ArtistB' to 'ArtistA feat. ArtistB'. "
        "Use '&' for collaborations, 'feat.' for features.\n"
        "9) COMPOSER: For hip-hop/electronic, extract producer name (prod. X) as composer.\n"
        "10) ORIGINAL ARTIST: For covers, put original performer in originalArtist.\n"
        "11) COMMENT: One short factual sentence about the track.\n"
        "12) COPYRIGHT: Label and year, e.g. '2007 Universal Records'.\n"
        "13) Latin alphabet only.\n"
        + clean_note
        + "\nFill or correct only these fields: "
        + fields_list
        + "\n\nKnown track data:\n"
        + known_section
    )


def _build_batch_prompt(tracks: list[Track]) -> str:
    files = [_track_batch_context(track) for track in tracks]
    return (
        _MUSIC_ARCHIVIST_SYSTEM_PROMPT
        + "\n\nZasady sanityzacji wejscia: dane ponizej sa juz oczyszczone z okladek, "
        "binariow, URL-i, sciezek absolutnych i dlugich komentarzy. Korzystaj przede "
        "wszystkim z filename/current_title/current_artist/current_album oraz folderu "
        "jako kontekstu albumowego.\n\nFILES_JSON:\n"
        + json.dumps(files, ensure_ascii=False, indent=2)
    )


def _track_batch_context(track: Track) -> dict[str, Any]:
    path = Path(track.path)
    data: dict[str, Any] = {
        "originalFilename": path.name,
        "filename": path.name,
    }
    folder = path.parent.name
    if folder and folder not in {".", ".."}:
        data["folder"] = _sanitize_prompt_value(folder)
    mapping = {
        "current_title": "title",
        "current_artist": "artist",
        "current_album": "album",
        "current_albumArtist": "albumartist",
        "current_trackNumber": "tracknumber",
        "current_discNumber": "discnumber",
        "current_year": "year",
        "current_genre": "genre",
        "current_bpm": "bpm",
        "current_key": "key",
        "current_composer": "composer",
        "current_mood": "mood",
        "current_comment": "comment",
        "current_copyright": "copyright",
        "current_discNumber": "discnumber",
    }
    for output_name, attr_name in mapping.items():
        value = getattr(track, attr_name, None)
        if not _has_nonempty_value(value):
            continue
        cleaned = _sanitize_prompt_value(value)
        if cleaned and cleaned != "[BINARY_OMITTED]":
            data[output_name] = cleaned
    if track.duration:
        data["durationSeconds"] = int(track.duration)
    return data


def _call_openai_responses(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_responses(data)


def _call_openai_compatible_chat(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    base_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a music metadata assistant. Return ONLY valid JSON, no markdown fences."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    # Try with JSON mode first; fall back for endpoints that reject the extra field.
    payload = base_payload
    for use_json_mode in (True, False):
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if not use_json_mode or resp.status_code not in (400, 422):
            if not resp.ok:
                raise requests.HTTPError(
                    f"{resp.status_code} {resp.reason} — {resp.text[:300]}",
                    response=resp,
                )
            return _extract_text_from_chat_completions(resp.json())
        # retry without JSON mode
        payload = {k: v for k, v in base_payload.items() if k != "response_format"}
    raise RuntimeError("unreachable")


def _call_openai_compatible_batch_chat(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _MUSIC_ARCHIVIST_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if not resp.ok:
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} — {resp.text[:300]}",
            response=resp,
        )
    return _extract_text_from_chat_completions(resp.json())


def _call_gemini_generate_content(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "responseSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "nullable": True},
                    "artist": {"type": "string", "nullable": True},
                    "album": {"type": "string", "nullable": True},
                    "year": {"type": "string", "nullable": True},
                    "genre": {"type": "string", "nullable": True},
                    "tracknumber": {"type": "string", "nullable": True},
                    "bpm": {"type": "number", "nullable": True},
                    "key": {"type": "string", "nullable": True},
                    "albumartist": {"type": "string", "nullable": True},
                    "comment": {"type": "string", "nullable": True},
                    "lyrics": {"type": "string", "nullable": True},
                    "originalFilename": {"type": "string", "nullable": True},
                    "confidence": {"type": "number", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                },
                "required": ["originalFilename"],
            },
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_gemini(data)


def _call_gemini_generate_batch_content(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "responseSchema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "originalFilename": {"type": "string"},
                        "tags": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "nullable": True},
                                "artist": {"type": "string", "nullable": True},
                                "album": {"type": "string", "nullable": True},
                                "year": {"type": "string", "nullable": True},
                                "genre": {"type": "string", "nullable": True},
                                "bpm": {"type": "number", "nullable": True},
                                "key": {"type": "string", "nullable": True},
                                "albumArtist": {"type": "string", "nullable": True},
                                "trackNumber": {"type": "string", "nullable": True},
                            },
                        },
                    },
                    "required": ["originalFilename", "tags"],
                },
            },
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return _extract_text_from_gemini(resp.json())


def _extract_text_from_responses(data: dict[str, Any]) -> str:
    output = data.get("output", [])
    if not isinstance(output, list):
        return ""
    for item in output:
        if item.get("type") == "message":
            content = item.get("content", [])
            for part in content:
                if part.get("type") in {"output_text", "text"}:
                    return part.get("text", "")
    return ""


def _extract_text_from_chat_completions(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return message.get("content", "") or ""


def _extract_text_from_gemini(data: dict[str, Any]) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        return ""
    text = parts[0].get("text", "")
    return text or ""


def _safe_json(text: str) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        object_start = text.find("{")
        object_end = text.rfind("}")
        array_start = text.find("[")
        array_end = text.rfind("]")
        if array_start != -1 and array_end != -1 and (
            object_start == -1 or array_start < object_start
        ):
            start, end = array_start, array_end
        else:
            start, end = object_start, object_end
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _infer_confidence(payload: dict[str, Any]) -> float | None:
    populated = 0
    for field_name in _ALL_AI_FIELDS:
        value = payload.get(field_name)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        populated += 1
    if populated == 0:
        return None
    if populated >= 6:
        return 0.85
    if populated >= 3:
        return 0.75
    return 0.65


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = set(_ALL_AI_FIELDS) | {"description", "confidence", "originalFilename"}
    return {key: value for key, value in payload.items() if key in allowed}


def _batch_payload_to_results(payload: Any, tracks: list[Track]) -> list[AnalysisResult]:
    if isinstance(payload, dict):
        for key in ("tracks", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                payload = value
                break
    if not isinstance(payload, list):
        return [
            AnalysisResult(description="Cloud AI returned non-JSON batch response", confidence=0.0)
            for _track in tracks
        ]

    by_name: dict[str, dict[str, Any]] = {}
    ordered_payloads: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        filename = _to_str(item.get("originalFilename") or item.get("filename"))
        tags = item.get("tags") if isinstance(item.get("tags"), dict) else item
        if not isinstance(tags, dict):
            tags = {}
        flattened = _normalize_batch_tags(tags)
        if item.get("confidence") is not None and flattened.get("confidence") is None:
            flattened["confidence"] = item.get("confidence")
        if item.get("description") is not None and flattened.get("description") is None:
            flattened["description"] = item.get("description")
        if filename:
            by_name[filename.lower()] = flattened
        ordered_payloads.append(flattened)

    results: list[AnalysisResult] = []
    for index, track in enumerate(tracks):
        name = Path(track.path).name.lower()
        cleaned = by_name.get(name)
        if cleaned is None and index < len(ordered_payloads):
            cleaned = ordered_payloads[index]
        if cleaned is None:
            results.append(AnalysisResult(description="Cloud AI omitted batch item", confidence=0.0))
            continue
        confidence = _to_float(cleaned.get("confidence"))
        if confidence is None:
            confidence = _infer_confidence(cleaned)
        raw = AnalysisResult(
            title=_to_str(cleaned.get("title")),
            artist=_to_str(cleaned.get("artist")),
            album=_to_str(cleaned.get("album")),
            albumartist=_to_str(cleaned.get("albumartist")),
            year=_to_str(cleaned.get("year")),
            genre=_to_str(cleaned.get("genre")),
            bpm=_to_float(cleaned.get("bpm")),
            key=_to_str(cleaned.get("key")),
            tracknumber=_to_str(cleaned.get("tracknumber")),
            discnumber=_to_str(cleaned.get("discnumber")),
            composer=_to_str(cleaned.get("composer")),
            originalartist=_to_str(cleaned.get("originalartist")),
            isrc=_to_str(cleaned.get("isrc")),
            publisher=_to_str(cleaned.get("publisher")),
            lyrics=_to_str(cleaned.get("lyrics")),
            grouping=_to_str(cleaned.get("grouping")),
            copyright=_to_str(cleaned.get("copyright")),
            remixer=_to_str(cleaned.get("remixer")),
            comment=_to_str(cleaned.get("comment")),
            mood=_to_str(cleaned.get("mood")),
            energy=_to_float(cleaned.get("energy")),
            rating=_parse_rating(cleaned.get("rating")),
            description=_to_str(cleaned.get("description")) or "Cloud AI batch",
            confidence=confidence,
        )
        results.append(_validate_result(raw))
    return results


def _normalize_batch_tags(tags: dict[str, Any]) -> dict[str, Any]:
    alias_map = {
        "albumArtist": "albumartist",
        "album_artist": "albumartist",
        "albumartist": "albumartist",
        "trackNumber": "tracknumber",
        "track_number": "tracknumber",
        "discNumber": "discnumber",
        "disc_number": "discnumber",
        "originalArtist": "originalartist",
        "original_artist": "originalartist",
        "originalFilename": "originalFilename",
    }
    normalized: dict[str, Any] = {}
    for key, value in tags.items():
        target = alias_map.get(str(key), str(key))
        normalized[target] = value
    return _normalize_payload(normalized)


def _sanitize_prompt_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ")
    if _BASE64_BLOB_RE.match(text):
        return "[BINARY_OMITTED]"
    text = _URL_RE.sub("[URL]", text)
    text = _WINDOWS_PATH_RE.sub("[PATH]", text)
    text = _UNIX_PATH_RE.sub("[PATH]", text)
    text = " ".join(text.split())
    if len(text) > 180:
        text = text[:180] + "..."
    return text


def _parse_rating(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        text = str(value).strip()
        if not text:
            return None
        if "/" in text:
            text = text.split("/", 1)[0].strip()
        match = re.search(r"\d+", text)
        if not match:
            return None
        rating = int(match.group(0))
    if rating > 5:
        rating = max(0, min(5, round(rating / 2)))
    return rating if 0 <= rating <= 5 else None


def _resolve_runtime_config(
    provider: str | None,
    base_url: str | None,
    model: str | None,
) -> tuple[str | None, str | None]:
    if provider == "gemini":
        return base_url or "https://generativelanguage.googleapis.com/v1beta", model or "gemini-2.0-flash"
    return base_url, model


def preflight_provider(
    provider: str,
    api_key: str,
    base_url: str | None,
    *,
    timeout: int = 8,
) -> tuple[bool, str]:
    resolved_base_url, _ = _resolve_runtime_config(provider, base_url, None)
    if not resolved_base_url:
        return False, "Brak base URL"
    if provider == "gemini":
        url = f"{resolved_base_url.rstrip('/')}/models"
        headers = {"x-goog-api-key": api_key}
    else:
        url = f"{resolved_base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return True, "OK"
        detail = f"HTTP {resp.status_code}"
        try:
            payload = resp.json()
            error = payload.get("error")
            if isinstance(error, dict):
                msg = str(error.get("message", "")).strip()
                if msg:
                    detail = f"{detail}: {msg}"
            elif isinstance(error, str) and error.strip():
                detail = f"{detail}: {error.strip()}"
        except Exception:
            pass
        return False, detail
    except Exception as exc:
        return False, str(exc)


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, requests.Timeout):
        return True
    if isinstance(exc, requests.ConnectionError):
        return True
    if isinstance(exc, requests.HTTPError):
        response = getattr(exc, "response", None)
        if response is None:
            return True
        return response.status_code >= 500 or response.status_code == 429
    return False


def _is_http_429(exc: Exception) -> bool:
    if not isinstance(exc, requests.HTTPError):
        return False
    response = getattr(exc, "response", None)
    return bool(response is not None and response.status_code == 429)


def _retry_backoff_seconds(attempt: int, exc: Exception) -> float:
    delay = min(8.0, 2.0 * (2 ** max(0, attempt)))
    text = str(exc)
    response = getattr(exc, "response", None)
    if response is not None:
        text += " " + getattr(response, "text", "")
    if _is_http_429(exc) or "RESOURCE_EXHAUSTED" in text.upper():
        return delay
    return min(delay, 4.0)


# ---------------------------------------------------------------------------
# BatchAiQueueWorker
# ---------------------------------------------------------------------------

try:
    from PyQt6 import QtCore

    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False


@dataclass(order=True)
class _QueueItem:
    priority: int
    track_path: str = field(compare=False)


@dataclass
class AiTagResult:
    track_path: str
    field: str
    value: str | None
    confidence: float


if _QT_AVAILABLE:

    class BatchAiQueueWorker(QtCore.QObject):
        """Queue-based AI tagger that processes tracks in priority order.

        Confidence thresholds: Cloud AI → 0.85, Local AI → 0.60.
        """

        CONFIDENCE_CLOUD = 0.85
        CONFIDENCE_LOCAL = 0.60

        track_progress = QtCore.pyqtSignal(str, str, str, float)  # path, field, value, confidence
        track_done = QtCore.pyqtSignal(str)  # path
        batch_done = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self._queue: queue.PriorityQueue[_QueueItem] = queue.PriorityQueue()
            self._running = False

        def enqueue(self, track_path: str, priority: int = 5) -> None:
            self._queue.put(_QueueItem(priority=priority, track_path=track_path))

        def stop(self) -> None:
            self._running = False

        def process(self, tagger, repository=None) -> None:  # type: ignore[override]
            self._running = True
            is_cloud = isinstance(tagger, CloudAiTagger)
            confidence = self.CONFIDENCE_CLOUD if is_cloud else self.CONFIDENCE_LOCAL
            from lumbago_app.data.repository import list_tracks

            track_by_path = {track.path: track for track in list_tracks()}
            while self._running:
                try:
                    item = self._queue.get_nowait()
                except queue.Empty:
                    break
                path = item.track_path
                try:
                    track = track_by_path.get(path)
                    if not track:
                        self.track_done.emit(path)
                        continue
                    result = tagger.analyze(track)
                    for fname in _ALL_AI_FIELDS:
                        raw = getattr(result, fname, None)
                        if raw is None:
                            continue
                        fval = str(raw) if not isinstance(raw, str) else raw
                        if fval.strip():
                            self.track_progress.emit(path, fname, fval, confidence)
                except Exception:
                    pass
                self.track_done.emit(path)
                QtCore.QCoreApplication.processEvents()
            self.batch_done.emit()
            self._running = False
