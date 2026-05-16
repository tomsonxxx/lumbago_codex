from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lumbago_app.core.audio import write_tags
from lumbago_app.core.models import Track
from lumbago_app.data.repository import (
    add_change_log,
    replace_track_tags,
    save_metadata_consensus_report,
    update_track,
    update_tracks,
)
from lumbago_app.services.metadata_consensus import FieldEvidence, MetadataConsensusEngine


@dataclass
class PendingTrackWrite:
    track: Track
    fields: dict[str, str]
    source: str
    confidence: float | None = None
    change_log_source: str = "ai"
    old_values: dict[str, str | None] = field(default_factory=dict)


@dataclass
class WritebackResult:
    track_count: int = 0
    file_write_errors: list[str] = field(default_factory=list)
    applied_fields: int = 0


def apply_track_writes(
    writes: Iterable[PendingTrackWrite],
    *,
    max_workers: int = 4,
    update_mode: str = "bulk",
) -> WritebackResult:
    pending = [item for item in writes if item.fields]
    if not pending:
        return WritebackResult()

    consensus_engine = MetadataConsensusEngine()
    touched_tracks: list[Track] = []
    file_jobs: list[tuple[str, dict[str, str]]] = []
    applied_fields = 0

    for item in pending:
        report, resolved_fields = _resolve_pending_write(item, consensus_engine)
        save_metadata_consensus_report(
            item.track.path,
            report,
            operation=item.change_log_source or "writeback",
        )
        if not resolved_fields:
            continue
        tag_rows: list[str] = []
        for field_name, serialized in resolved_fields.items():
            old_value = item.old_values.get(field_name)
            new_value = getattr(item.track, field_name, None)
            tag_rows.append(f"{field_name}:{new_value}")
            add_change_log(
                item.track.path,
                field_name,
                old_value,
                serialized,
                source=item.change_log_source,
            )
            applied_fields += 1
        replace_track_tags(
            item.track.path,
            tag_rows,
            source=item.source,
            confidence=item.confidence,
        )
        touched_tracks.append(item.track)
        file_jobs.append((item.track.path, resolved_fields))

    if update_mode == "single":
        for track in touched_tracks:
            update_track(track)
    else:
        update_tracks(touched_tracks)

    errors = _write_file_tags(file_jobs, max_workers=max_workers)
    return WritebackResult(
        track_count=len(touched_tracks),
        file_write_errors=errors,
        applied_fields=applied_fields,
    )


def _resolve_pending_write(
    item: PendingTrackWrite,
    engine: MetadataConsensusEngine,
):
    observed_at = datetime.utcnow()
    evidence_by_field: dict[str, list[FieldEvidence]] = {}
    chosen_source = _write_source_name(item)
    chosen_confidence = _write_confidence(item)

    for field_name, serialized in item.fields.items():
        candidates: list[FieldEvidence] = []
        old_value = item.old_values.get(field_name)
        if old_value not in (None, ""):
            candidates.append(
                FieldEvidence(
                    field_name=field_name,
                    value=_coerce_field_value(field_name, old_value),
                    source="existing_tags",
                    confidence=0.72,
                    verified=False,
                    timestamp=observed_at,
                )
            )
        candidates.append(
            FieldEvidence(
                field_name=field_name,
                value=_coerce_field_value(field_name, serialized),
                source=chosen_source,
                confidence=chosen_confidence,
                verified=chosen_source in {"manual_user", "manual_confirmation"},
                timestamp=observed_at,
            )
        )
        evidence_by_field[field_name] = candidates

    report = engine.resolve(evidence_by_field)
    resolved_fields: dict[str, str] = {}
    for field_name, result in report.fields.items():
        old_value = _coerce_field_value(field_name, item.old_values.get(field_name))
        if result.resolved is None:
            setattr(item.track, field_name, old_value)
            continue
        resolved_value = _coerce_field_value(field_name, result.resolved.value)
        setattr(item.track, field_name, resolved_value)
        if resolved_value == old_value:
            continue
        resolved_fields[field_name] = str(resolved_value)
    return report, resolved_fields


def _write_file_tags(
    jobs: list[tuple[str, dict[str, str]]],
    *,
    max_workers: int,
) -> list[str]:
    if not jobs:
        return []

    worker_count = max(1, min(16, int(max_workers)))
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        future_map = {
            pool.submit(write_tags, Path(track_path), tags): track_path
            for track_path, tags in jobs
        }
        for future in as_completed(future_map):
            track_path = future_map[future]
            try:
                future.result()
            except Exception as exc:
                errors.append(f"{Path(track_path).name}: {exc}")
    return errors


def _write_source_name(item: PendingTrackWrite) -> str:
    raw = (item.change_log_source or item.source or "writeback").strip().lower()
    if raw in {"user", "manual", "manual_user"}:
        return "manual_user"
    if "confirm" in raw:
        return "manual_confirmation"
    if raw.startswith("ai"):
        return "ai_enrichment"
    return raw


def _write_confidence(item: PendingTrackWrite) -> float:
    if item.confidence is not None:
        return float(item.confidence)
    source_name = _write_source_name(item)
    if source_name in {"manual_user", "manual_confirmation"}:
        return 0.99
    if source_name == "ai_enrichment":
        return 0.35
    return 0.72


def _coerce_field_value(field_name: str, value):
    if value is None:
        return None
    if field_name in {"bpm", "energy"}:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if field_name == "rating":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    text = str(value).strip()
    return text or None
