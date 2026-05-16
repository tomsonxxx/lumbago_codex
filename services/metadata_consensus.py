from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


AI_SOURCE_PREFIXES = ("ai", "openai", "gemini", "grok", "deepseek")
AI_RESTRICTED_FIELDS = {
    "title",
    "artist",
    "album",
    "albumartist",
    "year",
    "tracknumber",
    "discnumber",
    "composer",
    "isrc",
    "publisher",
    "copyright",
    "remixer",
}
AI_ENRICHMENT_FIELDS = {"genre", "mood", "comment", "grouping", "rating", "bpm", "key", "energy", "lyrics"}
DEFAULT_FIELD_THRESHOLD = 0.45

SOURCE_WEIGHTS: dict[str, float] = {
    "manual_user": 1.0,
    "manual_confirmation": 0.99,
    "acoustid": 0.98,
    "chromaprint": 0.98,
    "shazamio": 0.96,
    "audd": 0.95,
    "musicbrainz": 0.9,
    "discogs": 0.89,
    "beatport": 0.88,
    "spotify": 0.86,
    "deezer": 0.82,
    "lastfm": 0.78,
    "existing_tags": 0.72,
    "file_tags": 0.72,
    "local_library": 0.74,
    "filename": 0.52,
    "filename_pattern": 0.52,
    "folder_structure": 0.45,
    "spectral_analysis": 0.68,
    "key_detection": 0.7,
    "audio_features": 0.68,
    "ai_enrichment": 0.2,
}


@dataclass(frozen=True)
class FieldEvidence:
    field_name: str
    value: Any
    source: str
    confidence: float
    verified: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


@dataclass(frozen=True)
class FieldConflict:
    field_name: str
    chosen: FieldEvidence | None
    candidates: list[FieldEvidence]
    reason: str


@dataclass(frozen=True)
class ConsensusFieldResult:
    field_name: str
    resolved: FieldEvidence | None
    candidates: list[FieldEvidence]
    conflict: FieldConflict | None = None


@dataclass(frozen=True)
class MetadataConsensusReport:
    fields: dict[str, ConsensusFieldResult]
    accepted_fields: list[str]
    rejected_fields: list[str]
    conflicts: list[FieldConflict]
    created_at: datetime = field(default_factory=datetime.utcnow)


class MetadataConsensusEngine:
    def __init__(self, *, field_threshold: float = DEFAULT_FIELD_THRESHOLD):
        self.field_threshold = field_threshold

    def resolve(self, evidence_by_field: dict[str, list[FieldEvidence]]) -> MetadataConsensusReport:
        fields: dict[str, ConsensusFieldResult] = {}
        accepted_fields: list[str] = []
        rejected_fields: list[str] = []
        conflicts: list[FieldConflict] = []

        for field_name, evidence_list in evidence_by_field.items():
            result = self._resolve_field(field_name, evidence_list)
            fields[field_name] = result
            if result.resolved is not None:
                accepted_fields.append(field_name)
            else:
                rejected_fields.append(field_name)
            if result.conflict is not None:
                conflicts.append(result.conflict)

        return MetadataConsensusReport(
            fields=fields,
            accepted_fields=accepted_fields,
            rejected_fields=rejected_fields,
            conflicts=conflicts,
        )

    def _resolve_field(self, field_name: str, candidates: list[FieldEvidence]) -> ConsensusFieldResult:
        cleaned = [candidate for candidate in candidates if _has_meaningful_value(candidate.value)]
        cleaned.sort(key=lambda item: _score_evidence(item), reverse=True)
        if not cleaned:
            return ConsensusFieldResult(field_name=field_name, resolved=None, candidates=[])

        grouped: dict[str, list[FieldEvidence]] = {}
        for candidate in cleaned:
            key = _normalized_value(candidate.value)
            grouped.setdefault(key, []).append(candidate)

        ranked_groups = sorted(
            grouped.values(),
            key=lambda items: (_aggregate_group_score(field_name, items, grouped), max(_score_evidence(item) for item in items)),
            reverse=True,
        )
        top_group = ranked_groups[0]
        top_choice = max(top_group, key=_score_evidence)
        top_score = _aggregate_group_score(field_name, top_group, grouped)

        resolved: FieldEvidence | None = None
        if _is_ai_restricted(field_name, top_choice.source):
            if _has_non_ai_corroboration(top_group):
                resolved = top_choice
        elif _is_ai_source(top_choice.source) and field_name in AI_ENRICHMENT_FIELDS:
            if float(top_choice.confidence) >= 0.65:
                resolved = top_choice
        elif top_score >= self.field_threshold or top_choice.verified:
            resolved = top_choice

        conflict: FieldConflict | None = None
        if len(ranked_groups) > 1:
            second_score = _aggregate_group_score(field_name, ranked_groups[1], grouped)
            if second_score >= (top_score * 0.3) or any(item.verified for item in cleaned[1:]) or resolved is not None:
                conflict = FieldConflict(
                    field_name=field_name,
                    chosen=resolved,
                    candidates=cleaned,
                    reason="multiple competing metadata variants",
                )

        return ConsensusFieldResult(
            field_name=field_name,
            resolved=resolved,
            candidates=cleaned,
            conflict=conflict,
        )


def _aggregate_group_score(
    field_name: str,
    grouped_items: list[FieldEvidence],
    all_groups: dict[str, list[FieldEvidence]],
) -> float:
    score = 0.0
    normalized_group = _normalized_value(grouped_items[0].value)
    corroborated_non_ai = any(not _is_ai_source(item.source) for item in grouped_items)
    for item in grouped_items:
        item_score = _score_evidence(item)
        if _is_ai_restricted(field_name, item.source) and not corroborated_non_ai:
            item_score = min(item_score, 0.05)
        score += item_score
    if corroborated_non_ai and len(grouped_items) > 1:
        score += 0.08
    if any(item.verified for item in grouped_items):
        score += 0.12
    if normalized_group in all_groups and len(all_groups[normalized_group]) >= 2:
        score += 0.03
    return score


def _score_evidence(evidence: FieldEvidence) -> float:
    source_weight = SOURCE_WEIGHTS.get(_canonical_source(evidence.source), 0.4)
    bounded_confidence = max(0.0, min(1.0, float(evidence.confidence)))
    score = source_weight * bounded_confidence
    if evidence.verified:
        score += 0.25
    if _is_ai_source(evidence.source):
        score = min(score, 0.3)
    return score


def _has_non_ai_corroboration(grouped_items: list[FieldEvidence]) -> bool:
    return any(not _is_ai_source(item.source) for item in grouped_items)


def _canonical_source(source: str) -> str:
    lowered = (source or "").strip().lower()
    if lowered.startswith("autotag:file_sync"):
        return "existing_tags"
    if lowered.startswith("ai"):
        return "ai_enrichment"
    return lowered


def _is_ai_source(source: str) -> bool:
    lowered = _canonical_source(source)
    return any(lowered.startswith(prefix) for prefix in AI_SOURCE_PREFIXES)


def _is_ai_restricted(field_name: str, source: str) -> bool:
    return _is_ai_source(source) and field_name in AI_RESTRICTED_FIELDS


def _has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "unknown", "n/a", "none", "null", "brak"}
    return True


def _normalized_value(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().casefold().split())
    return str(value).strip().casefold()
