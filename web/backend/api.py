from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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


def _db_path() -> Path:
    configured = os.getenv("WEB_BACKEND_DB", "").strip()
    if configured:
        return Path(configured)
    return Path(".lumbago_data") / "web_backend.sqlite3"


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


app = FastAPI(title="Lumbago Web Backend", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    migrate(conn, Path("web/backend/migrations"))
    conn.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/settings/{key}")
def read_setting(key: str) -> dict[str, str]:
    conn = connect(_db_path())
    try:
        value = get_setting(conn, key)
    finally:
        conn.close()
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": value}


@app.put("/settings/{key}")
def write_setting(key: str, payload: SettingPayload) -> dict[str, str]:
    conn = connect(_db_path())
    try:
        set_setting(conn, key, payload.value)
    finally:
        conn.close()
    return {"key": key, "value": payload.value}


@app.get("/cache/{key}")
def read_cache(key: str) -> dict[str, str]:
    conn = connect(_db_path())
    try:
        value = get_cache(conn, key)
    finally:
        conn.close()
    if value is None:
        raise HTTPException(status_code=404, detail="Cache miss")
    return {"key": key, "value": value}


@app.put("/cache/{key}")
def write_cache(key: str, payload: CachePayload) -> dict[str, str | int]:
    conn = connect(_db_path())
    try:
        set_cache(conn, key, payload.value, payload.ttl_seconds)
    finally:
        conn.close()
    return {"key": key, "value": payload.value, "ttl_seconds": payload.ttl_seconds}


@app.post("/tag-history")
def create_tag_history(payload: TagHistoryPayload) -> dict[str, str]:
    conn = connect(_db_path())
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
    return {"status": "ok"}


@app.get("/tag-history/{track_id}")
def read_tag_history(track_id: int) -> dict[str, list[dict]]:
    conn = connect(_db_path())
    try:
        rows = list_tag_history(conn, track_id)
    finally:
        conn.close()
    return {
        "items": [
            {
                "id": row["id"],
                "track_id": row["track_id"],
                "field_name": row["field_name"],
                "old_value": row["old_value"],
                "new_value": row["new_value"],
                "source": row["source"],
                "changed_at": row["changed_at"],
            }
            for row in rows
        ]
    }

