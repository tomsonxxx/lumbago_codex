from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from lumbago_app.core.audio import write_tags
from lumbago_app.core.models import Track
from lumbago_app.data.repository import add_change_log, replace_track_tags, update_track, update_tracks


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

    touched_tracks: list[Track] = []
    file_jobs: list[tuple[str, dict[str, str]]] = []
    applied_fields = 0

    for item in pending:
        tag_rows: list[str] = []
        for field_name, serialized in item.fields.items():
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
        file_jobs.append((item.track.path, item.fields))

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
