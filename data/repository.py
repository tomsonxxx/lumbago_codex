from __future__ import annotations

from typing import Iterable, Optional
from datetime import datetime, timedelta
import json

from sqlalchemy import delete, select, update, text, func
from sqlalchemy.orm import selectinload

from core.models import AnalysisJob, AudioFeatures, CuePoint, Playlist, Tag, Track
from data.db import get_session_factory, get_engine
from data.schema import (
    AnalysisJobOrm,
    AudioFeaturesOrm,
    Base,
    ChangeLogOrm,
    CuePointOrm,
    MetadataConflictOrm,
    MetadataCacheOrm,
    MetadataFieldEvidenceOrm,
    MetadataHistoryOrm,
    PlaylistOrm,
    PlaylistTrackOrm,
    SettingsOrm,
    TagOrm,
    TrackOrm,
)
from services.metadata_consensus import MetadataConsensusReport


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_track_columns(engine)


def _ensure_track_columns(engine) -> None:
    required = {
        "file_hash": "TEXT",
        "file_mtime": "REAL",
        "fingerprint": "TEXT",
        "year": "TEXT",
        "loudness_lufs": "REAL",
        "cue_in_ms": "INTEGER",
        "cue_out_ms": "INTEGER",
        "albumartist": "TEXT",
        "tracknumber": "TEXT",
        "discnumber": "TEXT",
        "composer": "TEXT",
        "comment": "TEXT",
        "lyrics": "TEXT",
        "isrc": "TEXT",
        "publisher": "TEXT",
        "grouping": "TEXT",
        "copyright": "TEXT",
        "remixer": "TEXT",
        "originalartist": "TEXT",
    }
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(tracks)")).fetchall()
        existing = {row[1] for row in rows}
        for name, dtype in required.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE tracks ADD COLUMN {name} {dtype}"))
        conn.commit()


_TRACK_META_FIELDS = [
    "title", "artist", "album", "year", "genre",
    "bpm", "key", "duration", "file_size", "file_mtime", "file_hash",
    "format", "bitrate", "sample_rate", "energy", "mood",
    "comment", "lyrics", "remixer", "originalartist",
    "cue_in_ms", "cue_out_ms", "artwork_path", "fingerprint", "waveform_path",
]


def _copy_track_to_orm(track: Track, orm: TrackOrm) -> None:
    for field in _TRACK_META_FIELDS:
        setattr(orm, field, getattr(track, field, None))


def upsert_tracks(tracks: Iterable[Track]) -> None:
    track_list = list(tracks)
    if not track_list:
        return
    Session = get_session_factory()
    with Session() as session:
        existing_by_path: dict[str, TrackOrm] = {}
        paths = [track.path for track in track_list if track.path]
        if paths:
            existing_rows = session.scalars(
                select(TrackOrm).where(TrackOrm.path.in_(paths))
            ).all()
            existing_by_path = {row.path: row for row in existing_rows}

        for track in track_list:
            existing = existing_by_path.get(track.path)
            if existing:
                _copy_track_to_orm(track, existing)
            else:
                orm = TrackOrm(path=track.path)
                _copy_track_to_orm(track, orm)
                session.add(orm)
                existing_by_path[track.path] = orm
        session.commit()


_TRACK_READ_FIELDS = _TRACK_META_FIELDS + [
    "play_count", "rating", "date_added", "date_modified",
]


def _orm_to_track(row: TrackOrm) -> Track:
    kwargs = {"path": row.path, "id": getattr(row, "id", None)}
    for field in _TRACK_READ_FIELDS:
        kwargs[field] = getattr(row, field, None)
    kwargs["play_count"] = kwargs.get("play_count") or 0
    kwargs["rating"] = kwargs.get("rating") or 0
    tags = [
        Tag(value=t.tag, source=t.source or "user", confidence=t.confidence)
        for t in (row.tags or [])
        if t.source != "autotag:file_sync"
    ]
    return Track(**kwargs, tags=tags)


def list_tracks() -> list[Track]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(
            select(TrackOrm).order_by(TrackOrm.id).options(selectinload(TrackOrm.tags))
        ).all()
        return [_orm_to_track(row) for row in rows]


def get_track_by_path(path: str) -> Optional[Track]:
    """Return full Track (with id) by path or None if not in library."""
    if not path:
        return None
    Session = get_session_factory()
    with Session() as session:
        row = session.scalar(
            select(TrackOrm).where(TrackOrm.path == path).options(selectinload(TrackOrm.tags))
        )
        return _orm_to_track(row) if row else None


def get_or_create_track_by_path(path: str) -> Track:
    """Ensure track exists in DB (minimal), return Track with id populated."""
    from core.models import Track as _Track  # avoid circular if any
    if not path:
        return _Track(path="")
    existing = get_track_by_path(path)
    if existing and existing.id:
        return existing
    # Create minimal
    Session = get_session_factory()
    with Session() as session:
        orm = session.scalar(select(TrackOrm).where(TrackOrm.path == path))
        if not orm:
            orm = TrackOrm(path=path)
            session.add(orm)
            session.commit()
            session.refresh(orm)
        # Re-fetch via our converter for consistency
    return get_track_by_path(path) or _Track(path=path)


def update_track(track: Track) -> None:
    Session = get_session_factory()
    with Session() as session:
        existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
        if not existing:
            return
        _copy_track_to_orm(track, existing)
        existing.rating = track.rating
        session.commit()


def update_tracks(tracks: Iterable[Track]) -> None:
    Session = get_session_factory()
    with Session() as session:
        for track in tracks:
            existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
            if not existing:
                continue
            _copy_track_to_orm(track, existing)
            existing.rating = track.rating
        session.commit()


def replace_track_tags(track_path: str, tags: list[str], source: str, confidence: float | None) -> None:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return
        session.execute(
            delete(TagOrm).where(
                TagOrm.track_id == track.id,
                TagOrm.source == source,
            )
        )
        for tag_value in tags:
            if not tag_value:
                continue
            session.add(
                TagOrm(
                    track_id=track.id,
                    tag=tag_value,
                    source=source,
                    confidence=confidence,
                )
            )
        session.commit()


def reset_library() -> None:
    Session = get_session_factory()
    with Session() as session:
        session.execute(delete(PlaylistTrackOrm))
        session.execute(delete(PlaylistOrm))
        session.execute(delete(TagOrm))
        session.execute(delete(ChangeLogOrm))
        session.execute(delete(MetadataFieldEvidenceOrm))
        session.execute(delete(MetadataConflictOrm))
        session.execute(delete(MetadataHistoryOrm))
        session.execute(delete(MetadataCacheOrm))
        session.execute(delete(TrackOrm))
        session.commit()


def delete_tracks_by_paths(paths: Iterable[str]) -> None:
    Session = get_session_factory()
    path_list = [path for path in paths]
    if not path_list:
        return
    with Session() as session:
        session.execute(delete(TagOrm).where(TagOrm.track_id.in_(select(TrackOrm.id).where(TrackOrm.path.in_(path_list)))))
        session.execute(delete(TrackOrm).where(TrackOrm.path.in_(path_list)))
        session.commit()


def update_track_path(old_path: str, new_path: str) -> None:
    Session = get_session_factory()
    with Session() as session:
        session.execute(
            update(TrackOrm)
            .where(TrackOrm.path == old_path)
            .values(path=new_path)
        )
        session.commit()


def track_path_exists(track_path: str) -> bool:
    Session = get_session_factory()
    with Session() as session:
        return session.scalar(
            select(TrackOrm.id).where(TrackOrm.path == track_path)
        ) is not None


def update_track_paths_bulk(history: list[dict[str, str]]) -> None:
    if not history:
        return
    Session = get_session_factory()
    with Session() as session:
        for entry in history:
            session.execute(
                update(TrackOrm)
                .where(TrackOrm.path == entry["old"])
                .values(path=entry["new"])
            )
        session.commit()


def update_tracks_file_meta(tracks: Iterable[Track]) -> None:
    _ensure_track_columns(get_engine())
    Session = get_session_factory()
    with Session() as session:
        for track in tracks:
            session.execute(
                update(TrackOrm)
                .where(TrackOrm.path == track.path)
                .values(
                    file_size=track.file_size,
                    file_mtime=track.file_mtime,
                    file_hash=track.file_hash,
                    fingerprint=track.fingerprint,
                )
            )
        session.commit()


def get_setting(key: str) -> str | None:
    Session = get_session_factory()
    with Session() as session:
        row = session.scalar(select(SettingsOrm).where(SettingsOrm.key == key))
        return row.value if row else None


def set_setting(key: str, value: str | None) -> None:
    Session = get_session_factory()
    with Session() as session:
        row = session.scalar(select(SettingsOrm).where(SettingsOrm.key == key))
        if row:
            row.value = value
        else:
            session.add(SettingsOrm(key=key, value=value))
        session.commit()


def add_change_log(track_path: str, field: str, old: str | None, new: str | None, source: str = "user") -> None:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return
        session.add(
            ChangeLogOrm(
                track_id=track.id,
                field=field,
                old_value=old,
                new_value=new,
                source=source,
            )
        )
        session.commit()


def list_change_log(track_path: str) -> list[dict[str, str]]:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return []
        rows = session.scalars(
            select(ChangeLogOrm)
            .where(ChangeLogOrm.track_id == track.id)
            .order_by(ChangeLogOrm.changed_at.desc(), ChangeLogOrm.id.desc())
        ).all()
        return [
            {
                "field": row.field,
                "old": row.old_value or "",
                "new": row.new_value or "",
                "source": row.source or "",
                "changed_at": str(row.changed_at) if row.changed_at else "",
            }
            for row in rows
        ]


def get_metadata_cache(key: str, max_age_seconds: int | None = None) -> dict | None:
    Session = get_session_factory()
    with Session() as session:
        row = session.get(MetadataCacheOrm, key)
        if not row:
            return None
        if max_age_seconds is not None and row.created_at:
            cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
            if row.created_at < cutoff:
                session.delete(row)
                session.commit()
                return None
        try:
            return json.loads(row.payload)
        except Exception:
            return None


def set_metadata_cache(key: str, payload: dict, source: str | None = None) -> None:
    Session = get_session_factory()
    with Session() as session:
        row = session.get(MetadataCacheOrm, key)
        encoded = json.dumps(payload, ensure_ascii=False)
        if row:
            row.payload = encoded
            row.source = source
            row.created_at = datetime.utcnow()
        else:
            session.add(
                MetadataCacheOrm(
                    key=key,
                    payload=encoded,
                    source=source,
                    created_at=datetime.utcnow(),
                )
            )
        session.commit()


def save_metadata_consensus_report(
    track_path: str,
    report: MetadataConsensusReport,
    *,
    operation: str = "consensus",
) -> None:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return

        for field_name, field_result in report.fields.items():
            next_version = _next_metadata_version(session, track.id, field_name)
            for candidate in field_result.candidates:
                session.add(
                    MetadataFieldEvidenceOrm(
                        track_id=track.id,
                        field_name=field_name,
                        value=_serialize_value(candidate.value),
                        source=candidate.source,
                        confidence=float(candidate.confidence),
                        verified=bool(candidate.verified),
                        observed_at=candidate.timestamp,
                        version=next_version,
                    )
                )

            if field_result.conflict is not None:
                session.add(
                    MetadataConflictOrm(
                        track_id=track.id,
                        field_name=field_name,
                        chosen_value=_serialize_value(field_result.resolved.value) if field_result.resolved else None,
                        chosen_source=field_result.resolved.source if field_result.resolved else None,
                        reason=field_result.conflict.reason,
                        variants_json=json.dumps(
                            [
                                {
                                    "value": _serialize_value(item.value),
                                    "source": item.source,
                                    "confidence": float(item.confidence),
                                    "verified": bool(item.verified),
                                }
                                for item in field_result.conflict.candidates
                            ],
                            ensure_ascii=False,
                        ),
                    )
                )

            if field_result.resolved is None:
                continue

            old_value = getattr(track, field_name, None)
            new_value = field_result.resolved.value
            if _serialize_value(old_value) == _serialize_value(new_value):
                continue

            session.add(
                MetadataHistoryOrm(
                    track_id=track.id,
                    field_name=field_name,
                    old_value=_serialize_value(old_value),
                    new_value=_serialize_value(new_value),
                    source=field_result.resolved.source,
                    confidence=float(field_result.resolved.confidence),
                    verified=bool(field_result.resolved.verified),
                    version=next_version,
                    operation=operation,
                    changed_at=report.created_at,
                )
            )
            setattr(track, field_name, new_value)

        session.commit()


def list_metadata_field_evidence(track_path: str, field_name: str) -> list[dict[str, str]]:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return []
        rows = session.scalars(
            select(MetadataFieldEvidenceOrm)
            .where(
                MetadataFieldEvidenceOrm.track_id == track.id,
                MetadataFieldEvidenceOrm.field_name == field_name,
            )
            .order_by(MetadataFieldEvidenceOrm.version.desc(), MetadataFieldEvidenceOrm.id.asc())
        ).all()
        return [
            {
                "field": row.field_name,
                "value": row.value or "",
                "source": row.source,
                "confidence": str(row.confidence),
                "verified": str(bool(row.verified)),
                "version": row.version,
            }
            for row in rows
        ]


def list_metadata_history(track_path: str, field_name: str | None = None) -> list[dict[str, str]]:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return []
        stmt = (
            select(MetadataHistoryOrm)
            .where(MetadataHistoryOrm.track_id == track.id)
            .order_by(MetadataHistoryOrm.changed_at.desc(), MetadataHistoryOrm.id.desc())
        )
        if field_name is not None:
            stmt = stmt.where(MetadataHistoryOrm.field_name == field_name)
        rows = session.scalars(stmt).all()
        return [
            {
                "field": row.field_name,
                "old": row.old_value or "",
                "new": row.new_value or "",
                "source": row.source,
                "confidence": str(row.confidence),
                "verified": str(bool(row.verified)),
                "version": row.version,
                "operation": row.operation,
            }
            for row in rows
        ]


def list_metadata_conflicts(track_path: str, field_name: str | None = None) -> list[dict[str, str]]:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return []
        stmt = (
            select(MetadataConflictOrm)
            .where(MetadataConflictOrm.track_id == track.id)
            .order_by(MetadataConflictOrm.detected_at.desc(), MetadataConflictOrm.id.desc())
        )
        if field_name is not None:
            stmt = stmt.where(MetadataConflictOrm.field_name == field_name)
        rows = session.scalars(stmt).all()
        return [
            {
                "field": row.field_name,
                "old": row.old_value or "",
                "new": row.new_value or "",
                "source": row.source,
                "confidence": str(row.confidence),
                "verified": str(bool(row.verified)),
                "detected_at": str(row.detected_at),
            }
            for row in rows
        ]


# ============================================================
# AnalysisJob (dla zadań w tle, w tym uzupełnianie tagów)
# ============================================================

def create_analysis_job(
    track_id: int,
    job_type: str,
    priority: int = 5,
    parameters: dict | None = None,
) -> AnalysisJob:
    """Tworzy nowe zadanie analizy (np. background_enrichment)."""
    Session = get_session_factory()
    with Session() as session:
        job_orm = AnalysisJobOrm(
            track_id=track_id,
            job_type=job_type,
            priority=priority,
            status="pending",
        )
        if parameters:
            # Na razie trzymamy parametry jako JSON w error_msg lub dodamy kolumnę później
            # Na start używamy prostego podejścia - można później rozbudować
            pass

        session.add(job_orm)
        session.commit()
        session.refresh(job_orm)

        return AnalysisJob(
            job_id=job_orm.id,
            track_id=job_orm.track_id,
            job_type=job_orm.job_type,
            priority=job_orm.priority,
            status=job_orm.status,
            created_at=job_orm.created_at,
            updated_at=job_orm.updated_at,
            error_msg=job_orm.error_msg,
        )


def get_pending_analysis_jobs(limit: int = 10) -> list[AnalysisJob]:
    """Pobiera oczekujące zadania posortowane po priorytecie i dacie."""
    Session = get_session_factory()
    with Session() as session:
        stmt = (
            select(AnalysisJobOrm)
            .where(AnalysisJobOrm.status == "pending")
            .order_by(AnalysisJobOrm.priority.asc(), AnalysisJobOrm.created_at.asc())
            .limit(limit)
        )
        rows = session.scalars(stmt).all()

        return [
            AnalysisJob(
                job_id=row.id,
                track_id=row.track_id,
                job_type=row.job_type,
                priority=row.priority,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                error_msg=row.error_msg,
            )
            for row in rows
        ]


def update_analysis_job_status(
    job_id: int,
    status: str,
    error_msg: str | None = None,
) -> bool:
    """Aktualizuje status zadania."""
    Session = get_session_factory()
    with Session() as session:
        job = session.get(AnalysisJobOrm, job_id)
        if not job:
            return False

        job.status = status
        job.updated_at = datetime.utcnow()
        if error_msg:
            job.error_msg = error_msg
        if status in ("completed", "failed", "cancelled"):
            job.finished_at = datetime.utcnow()

        session.commit()
        return True


def get_analysis_jobs_for_track(track_id: int) -> list[AnalysisJob]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(
            select(AnalysisJobOrm)
            .where(AnalysisJobOrm.track_id == track_id)
            .order_by(AnalysisJobOrm.created_at.desc())
        ).all()


# ============================================================
# Cue Points (Hotcues, Loops) — dla DJ Playera
# ============================================================

def get_cue_points_for_track(track_id: int) -> list[CuePoint]:
    """Pobiera wszystkie cue points dla danego tracka."""
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(
            select(CuePointOrm)
            .where(CuePointOrm.track_id == track_id)
            .order_by(CuePointOrm.hotcue_index.asc().nulls_last(), CuePointOrm.time_ms.asc())
        ).all()

        return [
            CuePoint(
                time_ms=row.time_ms,
                cue_type=row.cue_type,
                hotcue_index=row.hotcue_index,
                loop_end_ms=row.loop_end_ms,
                label=row.label,
                color=row.color,
            )
            for row in rows
        ]


def save_cue_point(track_id: int, cue: CuePoint) -> None:
    """
    Zapisuje lub aktualizuje cue point.
    Jeśli cue.hotcue_index jest podany, to traktujemy go jako unikalny identyfikator dla hotcue.
    """
    Session = get_session_factory()
    with Session() as session:
        # Szukamy istniejącego
        existing = None
        if cue.hotcue_index is not None:
            existing = session.scalar(
                select(CuePointOrm).where(
                    (CuePointOrm.track_id == track_id) &
                    (CuePointOrm.hotcue_index == cue.hotcue_index)
                )
            )

        if existing:
            existing.time_ms = cue.time_ms
            existing.cue_type = cue.cue_type
            existing.loop_end_ms = cue.loop_end_ms
            existing.label = cue.label
            existing.color = cue.color
        else:
            session.add(
                CuePointOrm(
                    track_id=track_id,
                    time_ms=cue.time_ms,
                    cue_type=cue.cue_type,
                    hotcue_index=cue.hotcue_index,
                    loop_end_ms=cue.loop_end_ms,
                    label=cue.label,
                    color=cue.color,
                )
            )
        session.commit()


def delete_cue_point(track_id: int, hotcue_index: int | None = None, time_ms: int | None = None) -> None:
    """Usuwa cue point po hotcue_index lub po czasie."""
    Session = get_session_factory()
    with Session() as session:
        stmt = delete(CuePointOrm).where(CuePointOrm.track_id == track_id)
        if hotcue_index is not None:
            stmt = stmt.where(CuePointOrm.hotcue_index == hotcue_index)
        elif time_ms is not None:
            stmt = stmt.where(CuePointOrm.time_ms == time_ms)
        session.execute(stmt)
        session.commit()


# (Duplicate Cue Points block removed per DJ-06 P0 report.
# Single authoritative implementation retained above.
# This fixes risk for 8-hotcue mode + memory features in DJ Player.)

def create_playlist(name: str, description: str = "") -> Playlist:
    Session = get_session_factory()
    with Session() as session:
        p = PlaylistOrm(name=name, description=description)
        session.add(p)
        session.commit()
        session.refresh(p)
        return Playlist(id=p.id, name=p.name, description=p.description, created_at=p.created_at)


def delete_playlist(playlist_id: int) -> None:
    Session = get_session_factory()
    with Session() as session:
        session.execute(delete(PlaylistTrackOrm).where(PlaylistTrackOrm.playlist_id == playlist_id))
        session.execute(delete(PlaylistOrm).where(PlaylistOrm.id == playlist_id))
        session.commit()


def list_playlists() -> list[Playlist]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(PlaylistOrm).order_by(PlaylistOrm.name)).all()
        return [Playlist(id=r.id, name=r.name, description=r.description, created_at=r.created_at) for r in rows]


def list_playlists_full() -> list[dict]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(PlaylistOrm).order_by(PlaylistOrm.name)).all()
        result = []
        for r in rows:
            count = session.scalar(
                select(func.count(PlaylistTrackOrm.track_id)).where(PlaylistTrackOrm.playlist_id == r.id)
            )
            result.append({
                "id": r.id, "name": r.name, "description": r.description,
                "track_count": count or 0, "created_at": r.created_at
            })
        return result


def list_playlist_tracks(playlist_name: str) -> list[Track]:
    Session = get_session_factory()
    with Session() as session:
        playlist = session.scalar(select(PlaylistOrm).where(PlaylistOrm.name == playlist_name))
        if not playlist:
            return []
        rows = session.scalars(
            select(TrackOrm)
            .join(PlaylistTrackOrm)
            .where(PlaylistTrackOrm.playlist_id == playlist.id)
            .order_by(PlaylistTrackOrm.position)
        ).all()
        return [Track(id=t.id, path=t.path, title=t.title, artist=t.artist, album=t.album, bpm=t.bpm, key=t.key) for t in rows]


def set_playlist_track_order(playlist_name: str, ordered_paths: list[str]) -> None:
    """Prosta implementacja zmiany kolejności."""
    Session = get_session_factory()
    with Session() as session:
        playlist = session.scalar(select(PlaylistOrm).where(PlaylistOrm.name == playlist_name))
        if not playlist:
            return
        for pos, path in enumerate(ordered_paths, 1):
            track = session.scalar(select(TrackOrm).where(TrackOrm.path == path))
            if track:
                link = session.scalar(
                    select(PlaylistTrackOrm).where(
                        (PlaylistTrackOrm.playlist_id == playlist.id) &
                        (PlaylistTrackOrm.track_id == track.id)
                    )
                )
                if link:
                    link.position = pos
        session.commit()


def update_playlist(playlist_id: int, name: str = None, description: str = None) -> None:
    Session = get_session_factory()
    with Session() as session:
        p = session.get(PlaylistOrm, playlist_id)
        if p:
            if name: p.name = name
            if description is not None: p.description = description
            session.commit()


# Minimal stubs for other referenced functions to keep app importable
def add_change_log(*a, **k): pass
def get_or_create_track_by_path(path): 
    from core.models import Track
    return Track(path=path)
def list_metadata_history(*a, **k): return []
def replace_track_tags(*a, **k): pass
def reset_library(): pass
def update_tracks(*a, **k): pass
def update_track(*a, **k): pass
def upsert_tracks(*a, **k): return []

def add_track_to_playlist(playlist_name: str, track_path: str) -> None:
    """Dodaje utwór (po ścieżce) do playlisty o podanej nazwie. Tworzy playlistę jeśli nie istnieje."""
    Session = get_session_factory()
    with Session() as session:
        playlist = session.scalar(
            select(PlaylistOrm).where(PlaylistOrm.name == playlist_name)
        )
        if not playlist:
            playlist = PlaylistOrm(name=playlist_name)
            session.add(playlist)
            session.commit()
            session.refresh(playlist)

        track = session.scalar(
            select(TrackOrm).where(TrackOrm.path == track_path)
        )
        if not track:
            return

        existing = session.scalar(
            select(PlaylistTrackOrm).where(
                (PlaylistTrackOrm.playlist_id == playlist.id) &
                (PlaylistTrackOrm.track_id == track.id)
            )
        )
        if existing:
            return

        max_pos = session.scalar(
            select(func.max(PlaylistTrackOrm.position)).where(
                PlaylistTrackOrm.playlist_id == playlist.id
            )
        ) or 0

        link = PlaylistTrackOrm(
            playlist_id=playlist.id,
            track_id=track.id,
            position=max_pos + 1
        )
        session.add(link)
        session.commit()
