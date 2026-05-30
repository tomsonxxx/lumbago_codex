from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.models import Track
from core.renamer import parse_filename_tags
from services.autotag_rewrite import UnifiedAutoTagger
from services.metadata_consensus import FieldEvidence, MetadataConsensusEngine, MetadataConsensusReport
from services.metadata_writeback import PendingTrackWrite, apply_track_writes
from services.track_filters import is_system_like_path

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


@dataclass(frozen=True)
class DuplicateMergeFieldDecision:
    field_name: str
    current_value: Any
    resolved_value: Any
    source: str
    confidence: float
    reason: str


@dataclass
class DuplicateMergePlan:
    survivor: Track
    resolved_track: Track
    consensus: MetadataConsensusReport
    field_decisions: list[DuplicateMergeFieldDecision] = field(default_factory=list)
    ai_used: bool = False
    source_tracks: list[Track] = field(default_factory=list)

    @property
    def changed_fields(self) -> dict[str, str]:
        changed: dict[str, str] = {}
        for decision in self.field_decisions:
            if _stringify(decision.current_value) == _stringify(decision.resolved_value):
                continue
            if decision.resolved_value is None:
                continue
            changed[decision.field_name] = _stringify(decision.resolved_value) or ""
        return changed


def build_duplicate_merge_plan(
    tracks: list[Track],
    *,
    settings: Any | None = None,
    use_ai: bool = True,
    logger=None,
    group_label: str = "",
    survivor: Track | None = None,
) -> DuplicateMergePlan | None:
    cleaned = [track for track in tracks if isinstance(track, Track)]
    if len(cleaned) < 2:
        return None

    survivor = _preferred_survivor(cleaned, survivor)
    if logger is not None:
        try:
            logger(
                f"[dupmerge] start | group={group_label or Path(survivor.path).name} "
                f"| tracks={len(cleaned)} | use_ai={int(bool(use_ai))} | survivor={Path(survivor.path).name}"
            )
        except Exception:
            pass
    resolver = MetadataConsensusEngine()
    evidence_by_field: dict[str, list[FieldEvidence]] = {}
    observed_at = _now()

    for track in cleaned:
        confidence = _track_metadata_confidence(track)
        filename_artist, filename_title = parse_filename_tags(track.path)
        parent_name = Path(track.path).parent.name.strip()

        for field_name in TRACK_METADATA_FIELDS:
            value = getattr(track, field_name, None)
            if _has_value(value):
                evidence_by_field.setdefault(field_name, []).append(
                    FieldEvidence(
                        field_name=field_name,
                        value=value,
                        source="file_tags",
                        confidence=confidence,
                        verified=False,
                        timestamp=observed_at,
                    )
                )

        if _has_value(filename_title):
            evidence_by_field.setdefault("title", []).append(
                FieldEvidence(
                    field_name="title",
                    value=filename_title,
                    source="filename",
                    confidence=0.56,
                    verified=False,
                    timestamp=observed_at,
                )
            )
        if _has_value(filename_artist):
            evidence_by_field.setdefault("artist", []).append(
                FieldEvidence(
                    field_name="artist",
                    value=filename_artist,
                    source="filename",
                    confidence=0.52,
                    verified=False,
                    timestamp=observed_at,
                )
            )
        if _has_value(parent_name) and not is_system_like_path(Path(track.path).parent):
            evidence_by_field.setdefault("album", []).append(
                FieldEvidence(
                    field_name="album",
                    value=parent_name,
                    source="folder_structure",
                    confidence=0.46,
                    verified=False,
                    timestamp=observed_at,
                )
            )

    ai_used = False
    if use_ai and settings is not None:
        try:
            autotagger = UnifiedAutoTagger(settings, logger=logger)
            ai_result = autotagger.enrich_track(deepcopy(survivor))
            ai_candidate = ai_result.best_match
            if ai_candidate is not None and ai_candidate.score > 0:
                ai_used = True
                ai_confidence = max(0.35, min(0.95, float(ai_candidate.score) / 100.0))
                for field_name in TRACK_METADATA_FIELDS:
                    value = getattr(ai_candidate, field_name, None)
                    if not _has_value(value):
                        continue
                    evidence_by_field.setdefault(field_name, []).append(
                        FieldEvidence(
                            field_name=field_name,
                            value=value,
                            source="AI",
                            confidence=ai_confidence,
                            verified=True,
                            timestamp=observed_at,
                        )
                    )
        except Exception:
            pass

    consensus = resolver.resolve(evidence_by_field)
    resolved_track = deepcopy(survivor)
    field_decisions: list[DuplicateMergeFieldDecision] = []
    for field_name, result in consensus.fields.items():
        if result.resolved is None:
            continue
        current_value = getattr(resolved_track, field_name, None)
        resolved_value = result.resolved.value
        setattr(resolved_track, field_name, resolved_value)
        field_decisions.append(
            DuplicateMergeFieldDecision(
                field_name=field_name,
                current_value=current_value,
                resolved_value=resolved_value,
                source=result.resolved.source,
                confidence=float(result.resolved.confidence),
                reason=_field_reason(field_name, current_value, resolved_value, result),
            )
        )

    plan = DuplicateMergePlan(
        survivor=survivor,
        resolved_track=resolved_track,
        consensus=consensus,
        field_decisions=field_decisions,
        ai_used=ai_used,
        source_tracks=cleaned,
    )
    if logger is not None:
        try:
            logger(
                f"[dupmerge] done | group={group_label or Path(survivor.path).name} "
                f"| changed_fields={len(plan.changed_fields)} | ai_used={int(plan.ai_used)}"
            )
        except Exception:
            pass
    return plan


def apply_duplicate_merge_plan(plan: DuplicateMergePlan) -> list[str]:
    changed_fields = plan.changed_fields
    if not changed_fields:
        return []
    old_values = {name: getattr(plan.survivor, name, None) for name in changed_fields}
    for field_name, value in changed_fields.items():
        setattr(plan.survivor, field_name, getattr(plan.resolved_track, field_name, None))
    apply_track_writes(
        [
            PendingTrackWrite(
                track=plan.survivor,
                fields=changed_fields,
                source="duplicate_merge",
                confidence=0.85 if plan.ai_used else 0.75,
                change_log_source="duplicate_merge_ai" if plan.ai_used else "duplicate_merge",
                old_values=old_values,
            )
        ],
        update_mode="single",
    )
    return list(changed_fields.keys())


def _choose_survivor(tracks: list[Track]) -> Track:
    return max(tracks, key=_track_score)


def _preferred_survivor(tracks: list[Track], survivor: Track | None) -> Track:
    if survivor is None:
        return _choose_survivor(tracks)
    for track in tracks:
        if track is survivor or track.path == survivor.path:
            return track
    return _choose_survivor(tracks)


def _track_score(track: Track) -> float:
    score = 0.0
    for field_name in TRACK_METADATA_FIELDS:
        if _has_value(getattr(track, field_name, None)):
            score += 1.0
    if _has_value(track.title):
        score += 1.5
    if _has_value(track.artist):
        score += 1.5
    if _has_value(track.album):
        score += 1.0
    if track.duration:
        score += min(2.0, float(track.duration) / 60.0)
    if track.file_size:
        score += min(2.0, float(track.file_size) / 2_000_000.0)
    if not is_system_like_path(track.path):
        score += 2.0
    else:
        score -= 4.0
    return score


def _track_metadata_confidence(track: Track) -> float:
    present = sum(1 for field_name in TRACK_METADATA_FIELDS if _has_value(getattr(track, field_name, None)))
    total = len(TRACK_METADATA_FIELDS)
    density = present / total if total else 0.0
    bonus = 0.12 if _has_value(track.title) and _has_value(track.artist) else 0.0
    bonus += 0.08 if _has_value(track.album) else 0.0
    bonus += 0.08 if track.duration else 0.0
    if is_system_like_path(track.path):
        bonus -= 0.18
    return max(0.35, min(0.86, 0.48 + density * 0.32 + bonus))


def _field_reason(
    field_name: str,
    current_value: Any,
    resolved_value: Any,
    result,
) -> str:
    if _stringify(current_value) == _stringify(resolved_value):
        return "already matched"
    if result.conflict is not None:
        return "consensus resolved a conflict"
    return f"best source: {result.resolved.source}"


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return bool(normalized) and normalized not in {"-", "unknown", "n/a", "none", "null", "brak"}
    return True


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
