from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from lumbago_app.core.models import Track
from lumbago_app.services.autotag_rewrite import EnrichmentResult
from lumbago_app.services.metadata_consensus import (
    FieldEvidence,
    MetadataConsensusEngine,
    MetadataConsensusReport,
)
from lumbago_app.services.metadata_enricher import MetadataFillReport


TRACK_METADATA_FIELDS = (
    "title",
    "artist",
    "album",
    "albumartist",
    "year",
    "genre",
    "tracknumber",
    "discnumber",
    "composer",
    "bpm",
    "key",
    "rating",
    "mood",
    "energy",
    "comment",
    "lyrics",
    "isrc",
    "publisher",
    "grouping",
    "copyright",
    "remixer",
)

SOURCE_NORMALIZATION = {
    "musicbrainz": "musicbrainz",
    "apple music": "apple_music",
    "deezer": "deezer",
    "discogs": "discogs",
    "ai": "ai_enrichment",
    "biblioteka lokalna": "local_library",
    "tagi pliku": "file_tags",
}


@dataclass(frozen=True)
class MetadataPipelineResult:
    track: Track
    consensus: MetadataConsensusReport
    evidence_by_field: dict[str, list[FieldEvidence]] = field(default_factory=dict)


class MetadataPipelineV2:
    def __init__(self, *, consensus_engine: MetadataConsensusEngine | None = None):
        self.consensus_engine = consensus_engine or MetadataConsensusEngine()

    def resolve_track(
        self,
        *,
        baseline_track: Track,
        candidate_track: Track,
        metadata_report: MetadataFillReport | None = None,
        enrichment_result: EnrichmentResult | None = None,
        extra_evidence_by_field: dict[str, list[dict[str, Any]]] | None = None,
    ) -> MetadataPipelineResult:
        evidence_by_field = self._collect_evidence(
            baseline_track=baseline_track,
            candidate_track=candidate_track,
            metadata_report=metadata_report,
            enrichment_result=enrichment_result,
            extra_evidence_by_field=extra_evidence_by_field,
        )
        consensus = self.consensus_engine.resolve(evidence_by_field)
        resolved_track = deepcopy(baseline_track)
        for field_name, field_result in consensus.fields.items():
            if field_result.resolved is None:
                continue
            setattr(resolved_track, field_name, field_result.resolved.value)
        return MetadataPipelineResult(
            track=resolved_track,
            consensus=consensus,
            evidence_by_field=evidence_by_field,
        )

    def _collect_evidence(
        self,
        *,
        baseline_track: Track,
        candidate_track: Track,
        metadata_report: MetadataFillReport | None,
        enrichment_result: EnrichmentResult | None,
        extra_evidence_by_field: dict[str, list[dict[str, Any]]] | None,
    ) -> dict[str, list[FieldEvidence]]:
        observed_at = datetime.utcnow()
        evidence_by_field: dict[str, list[FieldEvidence]] = {}

        for field_name in TRACK_METADATA_FIELDS:
            baseline_value = getattr(baseline_track, field_name, None)
            if _has_value(baseline_value):
                evidence_by_field.setdefault(field_name, []).append(
                    FieldEvidence(
                        field_name=field_name,
                        value=baseline_value,
                        source="existing_tags",
                        confidence=0.72,
                        verified=False,
                        timestamp=observed_at,
                    )
                )

        if metadata_report is not None:
            field_sources = _field_sources_from_report(metadata_report)
            for field_name in metadata_report.changed_fields:
                value = getattr(candidate_track, field_name, None)
                if not _has_value(value):
                    continue
                evidence_by_field.setdefault(field_name, []).append(
                    FieldEvidence(
                        field_name=field_name,
                        value=value,
                        source=field_sources.get(field_name, "metadata_fill"),
                        confidence=0.78,
                        verified=False,
                        timestamp=observed_at,
                    )
                )

        if enrichment_result is not None:
            for candidate in getattr(enrichment_result, "candidates", []) or []:
                if getattr(candidate, "error", None):
                    continue
                source = _normalize_source_name(getattr(candidate, "source", "remote"))
                confidence = max(0.0, min(1.0, float(getattr(candidate, "score", 0) or 0) / 100.0))
                for field_name in TRACK_METADATA_FIELDS:
                    value = getattr(candidate, field_name, None)
                    if not _has_value(value):
                        continue
                    evidence_by_field.setdefault(field_name, []).append(
                        FieldEvidence(
                            field_name=field_name,
                            value=value,
                            source=source,
                            confidence=confidence,
                            verified=source == "acoustid",
                            timestamp=observed_at,
                        )
                    )

        for field_name, extra_items in (extra_evidence_by_field or {}).items():
            for payload in extra_items:
                value = payload.get("value")
                if not _has_value(value):
                    continue
                evidence_by_field.setdefault(field_name, []).append(
                    FieldEvidence(
                        field_name=field_name,
                        value=value,
                        source=_normalize_source_name(payload.get("source")),
                        confidence=float(payload.get("confidence", 0.0)),
                        verified=bool(payload.get("verified", False)),
                        timestamp=payload.get("timestamp") or observed_at,
                    )
                )

        return evidence_by_field


def _field_sources_from_report(report: MetadataFillReport) -> dict[str, str]:
    field_sources: dict[str, str] = {}
    for source in report.sources:
        if source.status != "hit":
            continue
        normalized = _normalize_source_name(source.key or source.label)
        for field_name in source.fields:
            field_sources.setdefault(field_name, normalized)
    return field_sources


def _normalize_source_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in SOURCE_NORMALIZATION:
        return SOURCE_NORMALIZATION[text]
    return text.replace(" ", "_") or "unknown_source"


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "unknown", "n/a", "none", "null", "brak"}
    return True
