from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(conn: sqlite3.Connection, migrations_dir: Path) -> None:
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        conn.executescript(sql_file.read_text(encoding="utf-8"))
    conn.commit()


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO settings(key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (key, value),
    )
    conn.commit()


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return None if row is None else str(row["value"])


def set_cache(conn: sqlite3.Connection, key: str, value: str, ttl_seconds: int) -> None:
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
    conn.execute(
        """
        INSERT INTO cache(key, value, expires_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, expires_at=excluded.expires_at
        """,
        (key, value, expires_at),
    )
    conn.commit()


def get_cache(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    if datetime.fromisoformat(str(row["expires_at"])) < datetime.now(timezone.utc):
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        return None
    return str(row["value"])


def add_tag_history(
    conn: sqlite3.Connection,
    track_id: int,
    field_name: str,
    old_value: str | None,
    new_value: str | None,
    source: str,
) -> None:
    conn.execute(
        """
        INSERT INTO tag_history(track_id, field_name, old_value, new_value, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (track_id, field_name, old_value, new_value, source),
    )
    conn.commit()


def list_tag_history(conn: sqlite3.Connection, track_id: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM tag_history WHERE track_id = ? ORDER BY id DESC",
        (track_id,),
    ).fetchall()
    return list(rows)
