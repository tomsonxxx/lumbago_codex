from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from core.models import AnalysisResult, Track


AI_FIELDS: list[str] = [
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
    "bpm",
    "key",
    "mood",
    "energy",
    "isrc",
    "publisher",
    "grouping",
    "copyright",
    "remixer",
    "comment",
]

_NUMERIC_FIELDS = {"bpm", "energy"}
_MISSING_SENTINEL = {"", "-", "—", "unknown", "n/a", "none", "null"}
_FIELD_PRIORITY = {
    "title": 0.72,
    "artist": 0.72,
    "album": 0.72,
    "albumartist": 0.72,
    "year": 0.7,
    "tracknumber": 0.68,
    "discnumber": 0.68,
    "composer": 0.68,
    "genre": 0.6,
    "rating": 0.55,
    "bpm": 0.58,
    "key": 0.58,
    "mood": 0.58,
    "energy": 0.58,
    "isrc": 0.8,
    "publisher": 0.75,
    "grouping": 0.65,
    "copyright": 0.8,
    "remixer": 0.7,
    "comment": 0.55,
}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    priority: int = 100
    timeout: int = 25
    retries: int = 1
    enabled: bool = True


@dataclass(frozen=True)
class MergePolicy:
    mode: str = "aggressive"
    default_threshold: float = 0.62
    thresholds: dict[str, float] = field(default_factory=dict)

    def threshold_for(self, field_name: str) -> float:
        if field_name in self.thresholds:
            return float(self.thresholds[field_name])
        return _FIELD_PRIORITY.get(field_name, self.default_threshold)


@dataclass
class ProviderResult:
    provider: str
    values: dict[str, Any]
    field_confidence: dict[str, float]
    overall_confidence: float
    raw_text: str = ""
    error: str | None = None


@dataclass
class FieldDecision:
    field: str
    old_value: Any
    new_value: Any
    winner_provider: str
    confidence: float
    accepted: bool
    reason: str


@dataclass
class AnalysisEnvelope:
    track_path: str
    provider_results: list[ProviderResult]
    decisions: list[FieldDecision]
    merged_values: dict[str, Any]
    merged_result: AnalysisResult
    provider_chain: str
    confidence: float


def missing_fields(track: Track) -> list[str]:
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip().lower() in _MISSING_SENTINEL
        return False

    return [field for field in AI_FIELDS if _is_missing(getattr(track, field, None))]


def build_prompt(track: Track, fields: list[str]) -> str:
    known_lines: list[str] = []
    for name in AI_FIELDS:
        value = getattr(track, name, None)
        if value is None:
            continue
        if isinstance(value, str) and value.strip().lower() in _MISSING_SENTINEL:
            continue
        known_lines.append(f"{name}: {value}")

    known = "\n".join(known_lines) if known_lines else "(brak danych)"
    ask_for = ", ".join(fields or AI_FIELDS)
    return (
        "Jestes ekspertem metadanych muzycznych. Zwracaj tylko poprawny JSON.\n"
        "Wypelnij pola: "
        + ask_for
        + ".\n"
        "Zasady:\n"
        "- jesli nie masz pewnosci: null\n"
        "- bez komentarzy, bez markdown, tylko obiekt JSON\n"
        "- dla bpm/energy zwracaj liczby\n\n"
        "- dla ratingu zwracaj liczbe calkowita 0-5\n\n"
        "Dane wejściowe utworu:\n"
        + known
    )


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = set(AI_FIELDS) | {"confidence", "description"}
    return {k: v for k, v in payload.items() if k in allowed}


class AnalysisEngine:
    def analyze_track(
        self,
        track: Track,
        providers: list[ProviderConfig],
        policy: MergePolicy | None = None,
    ) -> AnalysisEnvelope:
        active = [provider for provider in providers if provider.enabled]
        if not active:
            return _empty_envelope(track.path, "No providers configured")
        policy = policy or MergePolicy()
        fields = missing_fields(track)
        prompt = build_prompt(track, fields or AI_FIELDS)
        ordered = sorted(active, key=lambda p: p.priority)

        results: list[ProviderResult] = []
        for provider in ordered:
            results.append(_call_provider(provider, prompt))

        decisions, merged_values = _merge_aggressive(track, results, policy)
        merged_result = _to_analysis_result(merged_values, results)
        confidence = (
            sum(decision.confidence for decision in decisions if decision.accepted) / max(1, len(decisions))
        )
        provider_chain = "+".join([provider.provider for provider in ordered]) if ordered else "none"
        return AnalysisEnvelope(
            track_path=track.path,
            provider_results=results,
            decisions=decisions,
            merged_values=merged_values,
            merged_result=merged_result,
            provider_chain=provider_chain,
            confidence=confidence,
        )


def _call_provider(config: ProviderConfig, prompt: str) -> ProviderResult:
    last_exc: Exception | None = None
    for attempt in range(config.retries + 1):
        try:
            if config.provider == "gemini":
                raw_text = _call_gemini(config, prompt)
            else:
                raw_text = _call_openai_compatible(config, prompt)
            payload = _safe_json(raw_text)
            if not isinstance(payload, dict):
                return ProviderResult(
                    provider=config.provider,
                    values={},
                    field_confidence={},
                    overall_confidence=0.0,
                    raw_text=raw_text,
                    error="Provider returned non-JSON payload",
                )
            cleaned = normalize_payload(payload)
            provider_conf = _to_float(cleaned.get("confidence")) or _infer_confidence(cleaned)
            values: dict[str, Any] = {}
            field_conf: dict[str, float] = {}
            for field_name in AI_FIELDS:
                if field_name not in cleaned:
                    continue
                value = cleaned[field_name]
                if _is_empty(value):
                    continue
                if field_name in _NUMERIC_FIELDS:
                    numeric = _to_float(value)
                    if numeric is None:
                        continue
                    values[field_name] = numeric
                else:
                    values[field_name] = str(value).strip()
                field_conf[field_name] = provider_conf
            return ProviderResult(
                provider=config.provider,
                values=values,
                field_confidence=field_conf,
                overall_confidence=provider_conf,
                raw_text=raw_text,
            )
        except Exception as exc:
            last_exc = exc
            if attempt >= config.retries:
                break
            time.sleep(0.25 * (attempt + 1))
    return ProviderResult(
        provider=config.provider,
        values={},
        field_confidence={},
        overall_confidence=0.0,
        error=str(last_exc) if last_exc is not None else "Unknown error",
    )


def _merge_aggressive(
    track: Track, provider_results: list[ProviderResult], policy: MergePolicy
) -> tuple[list[FieldDecision], dict[str, Any]]:
    merged_values: dict[str, Any] = {}
    decisions: list[FieldDecision] = []
    for field_name in AI_FIELDS:
        old_value = getattr(track, field_name, None)
        winner_provider = "none"
        winner_conf = 0.0
        winner_value = None
        for result in provider_results:
            value = result.values.get(field_name)
            if _is_empty(value):
                continue
            score = float(result.field_confidence.get(field_name, result.overall_confidence or 0.0))
            if score > winner_conf:
                winner_conf = score
                winner_value = value
                winner_provider = result.provider
        threshold = policy.threshold_for(field_name)
        accepted = winner_value is not None and winner_conf >= threshold
        if accepted:
            merged_values[field_name] = winner_value
        elif not _is_empty(old_value):
            merged_values[field_name] = old_value
        decisions.append(
            FieldDecision(
                field=field_name,
                old_value=old_value,
                new_value=winner_value if accepted else old_value,
                winner_provider=winner_provider,
                confidence=winner_conf,
                accepted=accepted,
                reason=(
                    f"accepted: confidence {winner_conf:.2f} >= threshold {threshold:.2f}"
                    if accepted
                    else f"rejected: confidence {winner_conf:.2f} < threshold {threshold:.2f}"
                ),
            )
        )
    return decisions, merged_values


def _to_analysis_result(values: dict[str, Any], results: list[ProviderResult]) -> AnalysisResult:
    confidence_values = [
        float(value) for value in (result.overall_confidence for result in results) if value is not None and value > 0
    ]
    overall = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    return AnalysisResult(
        bpm=_to_float(values.get("bpm")),
        key=_to_str(values.get("key")),
        mood=_to_str(values.get("mood")),
        energy=_to_float(values.get("energy")),
        genre=_to_str(values.get("genre")),
        rating=_to_int(values.get("rating")),
        title=_to_str(values.get("title")),
        artist=_to_str(values.get("artist")),
        album=_to_str(values.get("album")),
        albumartist=_to_str(values.get("albumartist")),
        year=_to_str(values.get("year")),
        tracknumber=_to_str(values.get("tracknumber")),
        discnumber=_to_str(values.get("discnumber")),
        composer=_to_str(values.get("composer")),
        isrc=_to_str(values.get("isrc")),
        publisher=_to_str(values.get("publisher")),
        grouping=_to_str(values.get("grouping")),
        copyright=_to_str(values.get("copyright")),
        remixer=_to_str(values.get("remixer")),
        comment=_to_str(values.get("comment")),
        description="Aggressive merge result",
        confidence=overall,
    )


def _call_openai_compatible(config: ProviderConfig, prompt: str) -> str:
    url = f"{config.base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=config.timeout)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return str(message.get("content", "") or "")


def _call_gemini(config: ProviderConfig, prompt: str) -> str:
    url = f"{config.base_url.rstrip('/')}/models/{config.model}:generateContent"
    headers = {
        "x-goog-api-key": config.api_key,
        "Content-Type": "application/json",
    }
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=payload, timeout=config.timeout)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        return ""
    return str(parts[0].get("text", "") or "")


def _empty_envelope(path: str, reason: str) -> AnalysisEnvelope:
    return AnalysisEnvelope(
        track_path=path,
        provider_results=[],
        decisions=[],
        merged_values={},
        merged_result=AnalysisResult(description=reason, confidence=0.0),
        provider_chain="none",
        confidence=0.0,
    )


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


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _MISSING_SENTINEL
    return False


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


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        return None
    if rating > 5:
        rating = max(0, min(5, round(rating / 2)))
    return rating if 0 <= rating <= 5 else None


def _infer_confidence(payload: dict[str, Any]) -> float:
    populated = 0
    for field_name in AI_FIELDS:
        if field_name not in payload:
            continue
        if _is_empty(payload.get(field_name)):
            continue
        populated += 1
    if populated == 0:
        return 0.0
    if populated >= 6:
        return 0.85
    if populated >= 3:
        return 0.75
    return 0.65
