from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from lumbago_app.core.audio import apply_local_metadata, extract_metadata, iter_audio_files
from lumbago_app.core.models import Track
from lumbago_app.data.db import get_session_factory
from lumbago_app.data.repository import init_db, upsert_tracks
from lumbago_app.data.schema import TrackOrm
from web.backend.db import (
    add_tag_history,
    connect,
    get_cache,
    get_setting,
    list_tag_history,
    migrate,
    set_cache,
    set_setting,
)


def _web_db_path() -> Path:
    configured = os.getenv("WEB_BACKEND_DB", "").strip()
    if configured:
        return Path(configured)
    return Path(".lumbago_data") / "web_backend.sqlite3"


def _web_conn() -> sqlite3.Connection:
    db_path = _web_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    migrate(conn, Path("web/backend/migrations"))
    return conn


class SettingPayload(BaseModel):
    value: str = Field(default="")


class CachePayload(BaseModel):
    value: str = Field(default="")
    ttl_seconds: int = Field(default=300, ge=1)


class TagHistoryPayload(BaseModel):
    track_id: int
    field_name: str
    old_value: str | None = None
    new_value: str | None = None
    source: str = "web"


class ImportPreviewPayload(BaseModel):
    folder: str
    recursive: bool = True


class ImportCommitPayload(BaseModel):
    paths: list[str]


class DuplicatesPayload(BaseModel):
    mode: str = Field(pattern="^(hash|fingerprint|metadata)$")


app = FastAPI(title="Lumbago Web Backend", version="0.2.0")


def _serialize_track(row: TrackOrm) -> dict:
    return {
        "id": row.id,
        "path": row.path,
        "title": row.title or Path(row.path).stem,
        "artist": row.artist or "Unknown",
        "album": row.album,
        "year": row.year,
        "genre": row.genre,
        "composer": row.composer,
        "comment": row.comment,
        "lyrics": row.lyrics,
        "publisher": row.publisher,
        "key": row.key,
        "bpm": row.bpm,
        "duration": row.duration,
        "hash": row.file_hash,
        "fingerprint": row.fingerprint,
        "url": row.path,
    }


def _serialize_preview_track(track) -> dict:
    return {
        "id": 0,
        "path": track.path,
        "title": track.title or Path(track.path).stem,
        "artist": track.artist or "Unknown",
        "album": track.album,
        "year": track.year,
        "genre": track.genre,
        "composer": track.composer,
        "comment": track.comment,
        "lyrics": track.lyrics,
        "publisher": track.publisher,
        "key": track.key,
        "bpm": track.bpm,
        "duration": track.duration,
        "hash": track.file_hash,
        "fingerprint": track.fingerprint,
        "url": track.path,
    }


def _extract_track(path: Path):
    try:
        track = extract_metadata(path)
    except Exception:
        stat = path.stat()
        track = Track(path=str(path), file_size=stat.st_size, file_mtime=stat.st_mtime)
    apply_local_metadata(track, path)
    return track


def _list_track_rows() -> list[TrackOrm]:
    init_db()
    Session = get_session_factory()
    with Session() as session:
        return list(session.scalars(select(TrackOrm).order_by(TrackOrm.id)).all())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/settings/{key}")
def read_setting(key: str) -> dict[str, str | None]:
    conn = _web_conn()
    try:
        return {"key": key, "value": get_setting(conn, key)}
    finally:
        conn.close()


@app.put("/settings/{key}")
def write_setting(key: str, payload: SettingPayload) -> dict[str, str]:
    conn = _web_conn()
    try:
        set_setting(conn, key, payload.value)
    finally:
        conn.close()
    return {"key": key, "value": payload.value}


@app.get("/cache/{key}")
def read_cache(key: str) -> dict[str, str | None]:
    conn = _web_conn()
    try:
        return {"key": key, "value": get_cache(conn, key)}
    finally:
        conn.close()


@app.put("/cache/{key}")
def write_cache(key: str, payload: CachePayload) -> dict[str, str | int]:
    conn = _web_conn()
    try:
        set_cache(conn, key, payload.value, payload.ttl_seconds)
    finally:
        conn.close()
    return {"key": key, "value": payload.value, "ttl_seconds": payload.ttl_seconds}


@app.post("/tag-history")
def create_tag_history(payload: TagHistoryPayload) -> dict[str, str | int | None]:
    conn = _web_conn()
    try:
        add_tag_history(
            conn=conn,
            track_id=payload.track_id,
            field_name=payload.field_name,
            old_value=payload.old_value,
            new_value=payload.new_value,
            source=payload.source,
        )
    finally:
        conn.close()
    return payload.model_dump()


@app.get("/tag-history/{track_id}")
def read_tag_history(track_id: int) -> dict[str, list[dict]]:
    conn = _web_conn()
    try:
        rows = list_tag_history(conn, track_id)
    finally:
        conn.close()
    return {"items": [dict(row) for row in rows]}


@app.get("/tracks")
def list_tracks() -> dict[str, list[dict]]:
    return {"tracks": [_serialize_track(row) for row in _list_track_rows()]}


@app.post("/tracks/import-preview")
def import_preview(payload: ImportPreviewPayload) -> dict[str, list[dict] | list[str]]:
    folder = Path(payload.folder)
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="Folder importu nie istnieje.")

    tracks: list[dict] = []
    errors: list[str] = []
    for path in iter_audio_files(folder, recursive=payload.recursive):
        try:
            tracks.append(_serialize_preview_track(_extract_track(path)))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    return {"tracks": tracks, "errors": errors}


@app.post("/tracks/import-commit")
def import_commit(payload: ImportCommitPayload) -> dict[str, int | list[str]]:
    if not payload.paths:
        raise HTTPException(status_code=400, detail="Brak plikow do importu.")

    init_db()
    imported = []
    errors: list[str] = []
    for raw_path in payload.paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            errors.append(f"{raw_path}: plik nie istnieje")
            continue
        try:
            imported.append(_extract_track(path))
        except Exception as exc:
            errors.append(f"{raw_path}: {exc}")

    if imported:
        upsert_tracks(imported)

    return {"imported": len(imported), "errors": errors}


@app.post("/duplicates/analyze")
def analyze_duplicates(payload: DuplicatesPayload) -> dict[str, list[dict]]:
    buckets: dict[str, list[TrackOrm]] = {}

    for row in _list_track_rows():
        if payload.mode == "hash":
            bucket_key = row.file_hash or ""
            similarity = 1.0
        elif payload.mode == "fingerprint":
            bucket_key = row.fingerprint or ""
            similarity = 0.95
        else:
            title = (row.title or "").strip().lower()
            artist = (row.artist or "").strip().lower()
            duration = int(row.duration or 0)
            bucket_key = f"{title}|{artist}|{duration}"
            similarity = 0.9
        if not bucket_key:
            continue
        buckets.setdefault(bucket_key, []).append(row)

    groups = []
    for key, group_rows in buckets.items():
        if len(group_rows) < 2:
            continue
        groups.append(
            {
                "key": key,
                "similarity": similarity,
                "tracks": [_serialize_track(row) for row in group_rows],
            }
        )

    return {"groups": groups}
