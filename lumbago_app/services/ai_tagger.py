from __future__ import annotations

import json
import queue
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.core.services import heuristic_analysis


class LocalAiTagger:
    def analyze(self, track: Track) -> AnalysisResult:
        return heuristic_analysis(track)


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
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)

    def analyze(self, track: Track) -> AnalysisResult:
        if not self.provider or not self.api_key:
            return AnalysisResult(description="Cloud AI not configured", confidence=0.0)
        if self.provider == "gemini":
            base_url = self.base_url or "https://generativelanguage.googleapis.com/v1beta"
            model = self.model or "gemini-2.5-flash"
        else:
            base_url = self.base_url
            model = self.model
        if not base_url or not model:
            return AnalysisResult(description="Cloud AI missing base URL or model", confidence=0.0)

        missing = _missing_fields(track)
        if not missing:
            return AnalysisResult(description="No missing fields", confidence=1.0)
        prompt = _build_prompt(track, missing)
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
                return AnalysisResult(
                    bpm=_to_float(cleaned.get("bpm")),
                    key=_to_str(cleaned.get("key")),
                    mood=_to_str(cleaned.get("mood")),
                    energy=_to_float(cleaned.get("energy")),
                    genre=_to_str(cleaned.get("genre")),
                    description=_to_str(cleaned.get("description")),
                    confidence=confidence,
                )
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries or not _is_retryable_exception(exc):
                    break
                time.sleep(0.3 * (attempt + 1))
        return AnalysisResult(description=f"Cloud AI error: {last_exc}", confidence=0.0)


def _missing_fields(track: Track) -> list[str]:
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized in {"", "-", "—", "unknown", "n/a", "none", "null"}
        return False

    missing = []
    if _is_missing(track.bpm):
        missing.append("bpm")
    if _is_missing(track.key):
        missing.append("key")
    if _is_missing(track.mood):
        missing.append("mood")
    if _is_missing(track.energy):
        missing.append("energy")
    if _is_missing(track.genre):
        missing.append("genre")
    return missing


def _build_prompt(track: Track, missing: list[str]) -> str:
    return (
        "Zwroc JSON tylko dla pol: "
        + ", ".join(missing)
        + ". Wartosci puste ustaw na null. "
        "Dane wejsciowe:\n"
        f"Tytul: {track.title or ''}\n"
        f"Artysta: {track.artist or ''}\n"
        f"Album: {track.album or ''}\n"
        f"Gatunek: {track.genre or ''}\n"
        f"BPM: {track.bpm or ''}\n"
        f"Tonacja: {track.key or ''}\n"
        f"Nastroj: {track.mood or ''}\n"
        f"Energia: {track.energy or ''}\n"
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
    for field_name in ("bpm", "key", "mood", "energy", "genre"):
        value = payload.get(field_name)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        populated += 1
    if populated == 0:
        return None
    if populated >= 4:
        return 0.85
    if populated >= 2:
        return 0.75
    return 0.65


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"bpm", "key", "mood", "energy", "genre", "description", "confidence"}
    return {key: value for key, value in payload.items() if key in allowed}


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
                    fields: dict[str, Any] = {
                        "bpm": str(result.bpm) if result.bpm is not None else None,
                        "key": result.key,
                        "genre": result.genre,
                        "mood": result.mood,
                        "energy": str(result.energy) if result.energy is not None else None,
                    }
                    for fname, fval in fields.items():
                        if fval is not None and fval != "":
                            self.track_progress.emit(path, fname, fval, confidence)
                except Exception:
                    pass
                self.track_done.emit(path)
                QtCore.QCoreApplication.processEvents()
            self.batch_done.emit()
            self._running = False
