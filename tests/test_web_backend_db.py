from __future__ import annotations

from pathlib import Path

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


def test_web_backend_tables_and_crud(tmp_path: Path):
    db_path = tmp_path / "web.sqlite3"
    conn = connect(db_path)
    migrate(conn, Path("web/backend/migrations"))

    set_setting(conn, "theme", "dark")
    assert get_setting(conn, "theme") == "dark"

    set_cache(conn, "mb:track:1", '{"title":"A"}', ttl_seconds=60)
    assert get_cache(conn, "mb:track:1") == '{"title":"A"}'

    add_tag_history(conn, track_id=7, field_name="genre", old_value="house", new_value="techno", source="web")
    rows = list_tag_history(conn, track_id=7)
    assert len(rows) == 1
    assert rows[0]["field_name"] == "genre"

