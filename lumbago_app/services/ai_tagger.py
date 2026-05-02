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
from lumbago_app.services.metadata_providers import (
    RateLimitedMusicBrainzProvider,
    _best_mbid_from_acoustid,
    _parse_mb_recording,
)


_ISRC_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}\d{7}$")
_YEAR_MIN = 1900
_YEAR_MAX = int(time.strftime("%Y")) + 1


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
        retries: int = 1,
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
                time.sleep(0.3 * (attempt + 1))
        return AnalysisResult(description=f"Cloud AI error: {last_exc}", confidence=0.0)

    def cache_key(self) -> str:
        base_url, model = self._resolved_base_url, self._resolved_model
        return f"{self.provider_name}|{base_url or ''}|{model or ''}"


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


_MISSING_SENTINEL = {'', '-', '—', 'unknown', 'n/a', 'none', 'null'}

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
    # Always check all fields — AI verifies and corrects even existing values
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
        if fname in missing:
            continue
        if fname in noisy_set:
            continue  # We'll ask AI to clean these
        value = getattr(track, fname, None)
        if value is None:
            continue
        label = _FIELD_LABELS.get(fname, fname)
        known_lines.append(f"{label}: {value}")

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
        "Jestes ekspertem metadanych muzycznych. Na podstawie ponizszych danych ZWERYFIKUJ i POPRAW wszystkie pola"
        " uzywajac swojej wiedzy o tym utworze (artysta, wydanie, rok premiery, itp.)."
        " Jesli aktualna wartosc jest bledna lub niepelna — popraw ja na wiarygodna."
        " Jesli aktualna wartosc jest poprawna — zachowaj ja.\n"
        "Zwroc TYLKO poprawny JSON z dokladnie tymi polami: "
        + fields_list
        + "."
        + clean_note
        + "\nJesli danego pola absolutnie nie mozna ustalic, uzyj null. Nie dodawaj zadnych komentarzy poza JSON.\n\n"
        "Znane dane utworu:\n"
        + known_section
    )


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
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Zwracaj tylko JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_chat_completions(data)


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
        ]
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_gemini(data)


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
        start = text.find("{")
        end = text.rfind("}")
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
    allowed = set(_ALL_AI_FIELDS) | {"description", "confidence"}
    return {key: value for key, value in payload.items() if key in allowed}


def _resolve_runtime_config(
    provider: str | None,
    base_url: str | None,
    model: str | None,
) -> tuple[str | None, str | None]:
    if provider == "gemini":
        return base_url or "https://generativelanguage.googleapis.com/v1beta", model or "gemini-2.5-flash"
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
        return response.status_code >= 500
    return False


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

        Confidence thresholds: Cloud AI â†’ 0.85, Local AI â†’ 0.60.
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


