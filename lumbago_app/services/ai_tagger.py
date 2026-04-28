from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.services.analysis_engine import (
    AI_FIELDS,
    AnalysisEngine,
    AnalysisEnvelope,
    MergePolicy,
    ProviderConfig,
    build_prompt,
    missing_fields,
    normalize_payload,
)

# Backward-compatible exports used by tests and UI.
_ALL_AI_FIELDS = AI_FIELDS


class LocalAiTagger:
    """Legacy stub kept for import compatibility. Local provider is no longer supported."""

    provider_name = "local"

    def analyze(self, _track: Track) -> AnalysisResult:
        return AnalysisResult(
            description="Local AI provider has been removed in vNext. Configure cloud providers.",
            confidence=0.0,
        )

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
        self.base_url = base_url or _default_base_url(provider or "")
        self.model = model or _default_model(provider or "")
        self.timeout = timeout
        self.retries = max(0, retries)
        self._engine = AnalysisEngine()
        self._last_envelope: AnalysisEnvelope | None = None
        self._resolved_base_url, self._resolved_model = _resolve_runtime_config(
            self.provider,
            self.base_url,
            self.model,
        )

    def analyze(self, track: Track) -> AnalysisResult:
        if not self.provider or not self.api_key:
            return AnalysisResult(description="Cloud AI not configured", confidence=0.0)
        if not self.base_url or not self.model:
            return AnalysisResult(description="Cloud AI missing base URL or model", confidence=0.0)
        config = ProviderConfig(
            provider=self.provider,
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            timeout=self.timeout,
            retries=self.retries,
            priority=10,
            enabled=True,
        )
        envelope = self._engine.analyze_track(track, [config], MergePolicy(mode="aggressive"))
        self._last_envelope = envelope
        return envelope.merged_result

    def cache_key(self) -> str:
        base_url, model = self._resolved_base_url, self._resolved_model
        return f"{self.provider_name}|{base_url or ''}|{model or ''}"


class MultiAiTagger:
    """Runs configured cloud providers and merges results via aggressive merge policy."""

    def __init__(self, taggers: list[Any], max_workers: int = 3):
        # Keep the old constructor shape, but internal engine does the merge.
        self.taggers = [tagger for tagger in taggers if tagger is not None]
        self.max_workers = max(1, int(max_workers))
        self._engine = AnalysisEngine()
        self._last_envelope: AnalysisEnvelope | None = None

    def analyze(self, track: Track) -> AnalysisResult:
        provider_configs: list[ProviderConfig] = []
        for idx, tagger in enumerate(self.taggers):
            if isinstance(tagger, CloudAiTagger):
                if not tagger.provider or not tagger.api_key:
                    continue
                provider_configs.append(
                    ProviderConfig(
                        provider=tagger.provider,
                        api_key=tagger.api_key,
                        base_url=tagger.base_url or _default_base_url(tagger.provider),
                        model=tagger.model or _default_model(tagger.provider),
                        timeout=tagger.timeout,
                        retries=tagger.retries,
                        priority=idx,
                        enabled=True,
                    )
                )
        if not provider_configs:
            return AnalysisResult(description="No cloud providers configured", confidence=0.0)
        envelope = self._engine.analyze_track(track, provider_configs, MergePolicy(mode="aggressive"))
        self._last_envelope = envelope
        return envelope.merged_result

    def cache_key(self) -> str:
        keys: list[str] = []
        for tagger in self.taggers:
            cache_fn = getattr(tagger, "cache_key", None)
            if callable(cache_fn):
                keys.append(str(cache_fn()))
            else:
                keys.append(getattr(tagger, "provider_name", tagger.__class__.__name__))
        return "multi:" + "|".join(sorted(keys))


def _missing_fields(track: Track) -> list[str]:
    return missing_fields(track)


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


_MISSING_SENTINEL = {"", "-", "â€”", "unknown", "n/a", "none", "null"}

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


def _missing_fields(track: Track) -> list[str]:
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip().lower() in _MISSING_SENTINEL
        if isinstance(value, (int, float)):
            return False
        return False

    return [f for f in _ALL_AI_FIELDS if _is_missing(getattr(track, f, None))]


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


def _build_prompt(track: Track, missing: list[str]) -> str:
    return build_prompt(track, missing)


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_payload(payload)


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



def _default_base_url(provider: str) -> str:
    if provider == "gemini":
        return "https://generativelanguage.googleapis.com/v1beta"
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "grok":
        return "https://api.x.ai/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com/v1"
    return "https://api.openai.com/v1"


def _default_model(provider: str) -> str:
    if provider == "gemini":
        return "gemini-2.5-flash"
    if provider == "openai":
        return "gpt-4.1-mini"
    if provider == "grok":
        return "grok-2-latest"
    if provider == "deepseek":
        return "deepseek-chat"
    return "gpt-4.1-mini"


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


