from __future__ import annotations

from typing import Iterable
from datetime import datetime, timedelta
import json

from sqlalchemy import delete, select, update, text

from lumbago_app.core.models import Playlist, Track
from lumbago_app.data.db import get_session_factory, get_engine, ensure_fts, fts_search
from lumbago_app.data.schema import (
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
    try:
        ensure_fts(engine)
    except Exception:
        pass
    _seed_default_playlists()


def _seed_default_playlists() -> None:
    """Tworzy domyślne playlisty jeśli baza jest pusta."""
    defaults = [
        ("Favorites", "Ulubione utwory", False, None),
        ("Recent Imports", "Ostatnio zaimportowane", False, None),
        (
            "Nowo dodane (30 dni)",
            "Automatyczna playlista — tracki dodane w ostatnich 30 dniach",
            True,
            '{"date_added_days": 30}',
        ),
    ]
    Session = get_session_factory()
    with Session() as session:
        for name, desc, is_smart, rules in defaults:
            existing = session.scalar(select(PlaylistOrm).where(PlaylistOrm.name == name))
            if existing is None:
                session.add(PlaylistOrm(name=name, description=desc, is_smart=1 if is_smart else 0, rules=rules))
        session.commit()


def search_tracks_fts(query: str) -> list[Track]:
    ids = fts_search(query)
    if not ids:
        return []
    Session = get_session_factory()
    with Session() as session:
        id_order = {track_id: pos for pos, track_id in enumerate(ids)}
        rows = session.scalars(select(TrackOrm).where(TrackOrm.id.in_(ids))).all()
        rows_sorted = sorted(rows, key=lambda r: id_order.get(r.id, 9999))
        return [_orm_to_track(r) for r in rows_sorted]


def _ensure_track_columns(engine) -> None:
    required = {
        "file_hash": "TEXT",
        "file_mtime": "REAL",
        "fingerprint": "TEXT",
        "year": "TEXT",
        "loudness_lufs": "REAL",
        "cue_in_ms": "INTEGER",
        "cue_out_ms": "INTEGER",
    }
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(tracks)")).fetchall()
        existing = {row[1] for row in rows}
        for name, dtype in required.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE tracks ADD COLUMN {name} {dtype}"))
        # Indeks przyspieszający filtrowanie po dacie dodania
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_tracks_date_added ON tracks(date_added)"
        ))
        conn.commit()


def vacuum_database() -> None:
    """Wykonuje VACUUM SQLite — zmniejsza rozmiar bazy po usunięciach."""
    eng = get_engine()
    with eng.connect() as conn:
        conn.execute(text("VACUUM"))
        conn.commit()


def upsert_tracks(tracks: Iterable[Track]) -> None:
    Session = get_session_factory()
    with Session() as session:
        for track in tracks:
            existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
            if existing:
                existing.title = track.title
                existing.artist = track.artist
                existing.album = track.album
                existing.year = track.year
                existing.genre = track.genre
                existing.bpm = track.bpm
                existing.key = track.key
                existing.loudness_lufs = track.loudness_lufs
                existing.duration = track.duration
                existing.file_size = track.file_size
                existing.file_mtime = track.file_mtime
                existing.file_hash = track.file_hash
                existing.format = track.format
                existing.bitrate = track.bitrate
                existing.sample_rate = track.sample_rate
                existing.energy = track.energy
                existing.mood = track.mood
                existing.cue_in_ms = track.cue_in_ms
                existing.cue_out_ms = track.cue_out_ms
                existing.artwork_path = track.artwork_path
                existing.fingerprint = track.fingerprint
            else:
                session.add(
                    TrackOrm(
                        path=track.path,
                        title=track.title,
                        artist=track.artist,
                        album=track.album,
                        year=track.year,
                        genre=track.genre,
                        bpm=track.bpm,
                        key=track.key,
                        loudness_lufs=track.loudness_lufs,
                        duration=track.duration,
                        file_size=track.file_size,
                        file_mtime=track.file_mtime,
                        file_hash=track.file_hash,
                        format=track.format,
                        bitrate=track.bitrate,
                        sample_rate=track.sample_rate,
                        energy=track.energy,
                        mood=track.mood,
                        cue_in_ms=track.cue_in_ms,
                        cue_out_ms=track.cue_out_ms,
                        artwork_path=track.artwork_path,
                        fingerprint=track.fingerprint,
                    )
                )
        session.commit()


def list_tracks() -> list[Track]:
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(select(TrackOrm).order_by(TrackOrm.id)).all()
        return [
            Track(
                path=row.path,
                title=row.title,
                artist=row.artist,
                album=row.album,
                year=row.year,
                genre=row.genre,
                bpm=row.bpm,
                key=row.key,
                loudness_lufs=row.loudness_lufs,
                duration=row.duration,
                file_size=row.file_size,
                file_mtime=row.file_mtime,
                file_hash=row.file_hash,
                format=row.format,
                bitrate=row.bitrate,
                sample_rate=row.sample_rate,
                play_count=row.play_count,
                rating=row.rating,
                energy=row.energy,
                mood=row.mood,
                cue_in_ms=row.cue_in_ms,
                cue_out_ms=row.cue_out_ms,
                fingerprint=row.fingerprint,
                waveform_path=row.waveform_path,
                artwork_path=row.artwork_path,
                date_added=row.date_added,
                date_modified=row.date_modified,
            )
            for row in rows
        ]


def update_track(track: Track) -> None:
    Session = get_session_factory()
    with Session() as session:
        existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
        if not existing:
            return
        existing.title = track.title
        existing.artist = track.artist
        existing.album = track.album
        existing.year = track.year
        existing.genre = track.genre
        existing.bpm = track.bpm
        existing.key = track.key
        existing.loudness_lufs = track.loudness_lufs
        existing.rating = track.rating
        existing.energy = track.energy
        existing.mood = track.mood
        existing.cue_in_ms = track.cue_in_ms
        existing.cue_out_ms = track.cue_out_ms
        existing.artwork_path = track.artwork_path
        existing.file_hash = track.file_hash
        existing.file_mtime = track.file_mtime
        existing.fingerprint = track.fingerprint
        session.commit()


def update_tracks(tracks: Iterable[Track]) -> None:
    Session = get_session_factory()
    with Session() as session:
        for track in tracks:
            existing = session.scalar(select(TrackOrm).where(TrackOrm.path == track.path))
            if not existing:
                continue
            existing.title = track.title
            existing.artist = track.artist
            existing.album = track.album
            existing.year = track.year
            existing.genre = track.genre
            existing.bpm = track.bpm
            existing.key = track.key
            existing.loudness_lufs = track.loudness_lufs
            existing.rating = track.rating
            existing.energy = track.energy
            existing.mood = track.mood
            existing.cue_in_ms = track.cue_in_ms
            existing.cue_out_ms = track.cue_out_ms
            existing.artwork_path = track.artwork_path
            existing.file_hash = track.file_hash
            existing.file_mtime = track.file_mtime
            existing.fingerprint = track.fingerprint
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


def list_all_change_log(limit: int = 500) -> list[dict[str, str]]:
    """Zwraca globalną historię zmian dla wszystkich tracków."""
    Session = get_session_factory()
    with Session() as session:
        rows = session.scalars(
            select(ChangeLogOrm)
            .order_by(ChangeLogOrm.changed_at.desc(), ChangeLogOrm.id.desc())
            .limit(limit)
        ).all()
        result = []
        for row in rows:
            # Pobierz ścieżkę tracku
            track = session.get(TrackOrm, row.track_id)
            track_path = track.path if track else ""
            result.append({
                "track_path": track_path,
                "field": row.field,
                "old": row.old_value or "",
                "new": row.new_value or "",
                "source": row.source or "",
                "changed_at": str(row.changed_at) if row.changed_at else "",
            })
        return result


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
        return [
            Track(
                path=row[0].path,
                title=row[0].title,
                artist=row[0].artist,
                album=row[0].album,
                year=row[0].year,
                genre=row[0].genre,
                bpm=row[0].bpm,
                key=row[0].key,
                loudness_lufs=row[0].loudness_lufs,
                duration=row[0].duration,
                file_size=row[0].file_size,
                file_mtime=row[0].file_mtime,
                file_hash=row[0].file_hash,
                format=row[0].format,
                bitrate=row[0].bitrate,
                sample_rate=row[0].sample_rate,
                play_count=row[0].play_count,
                rating=row[0].rating,
                energy=row[0].energy,
                mood=row[0].mood,
                cue_in_ms=row[0].cue_in_ms,
                cue_out_ms=row[0].cue_out_ms,
                fingerprint=row[0].fingerprint,
                waveform_path=row[0].waveform_path,
                artwork_path=row[0].artwork_path,
                date_added=row[0].date_added,
                date_modified=row[0].date_modified,
            )
            for row in rows
        ]


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
