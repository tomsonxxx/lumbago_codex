from __future__ import annotations

from typing import Iterable
from datetime import datetime, timedelta
import json

from sqlalchemy import delete, select, update, text

from lumbago_app.core.models import Playlist, Track
from lumbago_app.data.db import get_session_factory, get_engine
from lumbago_app.core.models import AudioFeatures
from lumbago_app.data.schema import (
    AudioFeaturesOrm,
    Base,
    ChangeLogOrm,
    MetadataCacheOrm,
    PlaylistOrm,
    PlaylistTrackOrm,
    SettingsOrm,
    TagOrm,
    TrackOrm,
)


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
    "title", "artist", "album", "albumartist", "year", "genre",
    "tracknumber", "discnumber", "composer", "bpm", "key",
    "loudness_lufs", "duration", "file_size", "file_mtime", "file_hash",
    "format", "bitrate", "sample_rate", "energy", "mood",
    "comment", "lyrics", "isrc", "publisher", "grouping", "copyright", "remixer",
    "cue_in_ms", "cue_out_ms", "artwork_path", "fingerprint",
]


def _copy_track_to_orm(track: Track, orm: TrackOrm) -> None:
    for field in _TRACK_META_FIELDS:
        setattr(orm, field, getattr(track, field, None))


def upsert_tracks(tracks: Iterable[Track]) -> None:
    Session = get_session_factory()
    with Session() as session:
        for track in tracks:
            existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
            if existing:
                _copy_track_to_orm(track, existing)
            else:
                orm = TrackOrm(path=track.path)
                _copy_track_to_orm(track, orm)
                session.add(orm)
        session.commit()


_TRACK_READ_FIELDS = _TRACK_META_FIELDS + [
    "play_count", "rating", "waveform_path", "date_added", "date_modified",
]


def _orm_to_track(row: TrackOrm) -> Track:
    kwargs = {"path": row.path}
    for field in _TRACK_READ_FIELDS:
        kwargs[field] = getattr(row, field, None)
    # Ensure int defaults
    kwargs["play_count"] = kwargs.get("play_count") or 0
    kwargs["rating"] = kwargs.get("rating") or 0
    return Track(**kwargs)


def list_tracks() -> list[Track]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(TrackOrm).order_by(TrackOrm.id)).all()
        return [_orm_to_track(row) for row in rows]


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


def list_playlists() -> list[str]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(PlaylistOrm).order_by(PlaylistOrm.id)).all()
        if not rows:
            return ["Favorites", "Recent Imports", "Set Preparation"]
        return [row.name for row in rows]


def list_playlists_full() -> list[Playlist]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(PlaylistOrm).order_by(PlaylistOrm.id)).all()
        return [
            Playlist(
                name=row.name,
                description=row.description,
                is_smart=bool(row.is_smart),
                rules=row.rules,
                playlist_id=row.id,
            )
            for row in rows
        ]


def create_playlist(name: str, description: str | None = None, is_smart: bool = False, rules: str | None = None) -> None:
    Session = get_session_factory()
    with Session() as session:
        existing = session.scalar(select(PlaylistOrm).where(PlaylistOrm.name == name))
        if existing:
            return
        session.add(
            PlaylistOrm(
                name=name,
                description=description,
                is_smart=1 if is_smart else 0,
                rules=rules,
            )
        )
        session.commit()


def update_playlist(playlist_id: int, name: str, description: str | None, is_smart: bool, rules: str | None) -> None:
    Session = get_session_factory()
    with Session() as session:
        session.execute(
            update(PlaylistOrm)
            .where(PlaylistOrm.id == playlist_id)
            .values(
                name=name,
                description=description,
                is_smart=1 if is_smart else 0,
                rules=rules,
            )
        )
        session.commit()


def delete_playlist(playlist_id: int) -> None:
    Session = get_session_factory()
    with Session() as session:
        session.execute(delete(PlaylistTrackOrm).where(PlaylistTrackOrm.playlist_id == playlist_id))
        session.execute(delete(PlaylistOrm).where(PlaylistOrm.id == playlist_id))
        session.commit()


def list_playlist_tracks(playlist_id: int) -> list[Track]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.execute(
            select(TrackOrm, PlaylistTrackOrm.position)
            .join(PlaylistTrackOrm, TrackOrm.id == PlaylistTrackOrm.track_id)
            .where(PlaylistTrackOrm.playlist_id == playlist_id)
            .order_by(PlaylistTrackOrm.position, PlaylistTrackOrm.track_id)
        ).all()
        return [_orm_to_track(row[0]) for row in rows]


def set_playlist_track_order(playlist_id: int, ordered_paths: list[str]) -> None:
    Session = get_session_factory()
    with Session() as session:
        for position, path in enumerate(ordered_paths):
            track = session.scalar(select(TrackOrm).where(TrackOrm.path == path))
            if not track:
                continue
            session.execute(
                update(PlaylistTrackOrm)
                .where(
                    PlaylistTrackOrm.playlist_id == playlist_id,
                    PlaylistTrackOrm.track_id == track.id,
                )
                .values(position=position)
            )
        session.commit()


def add_track_to_playlist(playlist_name: str, track_path: str) -> None:
    Session = get_session_factory()
    with Session() as session:
        playlist = session.scalar(select(PlaylistOrm).where(PlaylistOrm.name == playlist_name))
        if playlist is None:
            playlist = PlaylistOrm(name=playlist_name)
            session.add(playlist)
            session.flush()
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if track is None:
            return
        existing = session.scalar(
            select(PlaylistTrackOrm).where(
                PlaylistTrackOrm.playlist_id == playlist.id,
                PlaylistTrackOrm.track_id == track.id,
            )
        )
        if existing is None:
            max_pos = session.scalar(
                select(PlaylistTrackOrm.position)
                .where(PlaylistTrackOrm.playlist_id == playlist.id)
                .order_by(PlaylistTrackOrm.position.desc())
            )
            next_pos = (max_pos or 0) + 1
            session.add(
                PlaylistTrackOrm(
                    playlist_id=playlist.id,
                    track_id=track.id,
                    position=next_pos,
                )
            )
        session.commit()


def upsert_audio_features(track_path: str, features: AudioFeatures) -> None:
    Session = get_session_factory()
    with Session() as session:
        track = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if not track:
            return
        existing = session.get(AudioFeaturesOrm, track.id)
        if existing:
            existing.mfcc_json = features.mfcc_json
            existing.tempo = features.tempo
            existing.spectral_centroid = features.spectral_centroid
            existing.spectral_rolloff = features.spectral_rolloff
            existing.brightness = features.brightness
            existing.roughness = features.roughness
            existing.zero_crossing_rate = features.zero_crossing_rate
            existing.chroma_json = features.chroma_json
            existing.danceability = features.danceability
            existing.valence = features.valence
        else:
            session.add(
                AudioFeaturesOrm(
                    id=track.id,
                    mfcc_json=features.mfcc_json,
                    tempo=features.tempo,
                    spectral_centroid=features.spectral_centroid,
                    spectral_rolloff=features.spectral_rolloff,
                    brightness=features.brightness,
                    roughness=features.roughness,
                    zero_crossing_rate=features.zero_crossing_rate,
                    chroma_json=features.chroma_json,
                    danceability=features.danceability,
                    valence=features.valence,
                )
            )
        session.commit()
