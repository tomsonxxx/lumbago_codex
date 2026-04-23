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


def _missing_fields(track: Track) -> list[str]:
    return missing_fields(track)


def _build_prompt(track: Track, missing: list[str]) -> str:
    return build_prompt(track, missing)


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return normalize_payload(payload)


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

