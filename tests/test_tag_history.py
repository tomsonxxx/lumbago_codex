import tempfile

from lumbago_app.core.models import Track
from lumbago_app.data.db import reset_engine
from lumbago_app.data.repository import (
    add_change_log,
    init_db,
    list_change_log,
    upsert_tracks,
)


def test_tag_history_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        init_db()
        track = Track(path="x.mp3", title="Test")
        upsert_tracks([track])
        add_change_log(track.path, "title", "Test", "Test 2", "user")
        rows = list_change_log(track.path)
        assert len(rows) == 1
        assert rows[0]["field"] == "title"
        assert rows[0]["old"] == "Test"
        assert rows[0]["new"] == "Test 2"
        reset_engine()
