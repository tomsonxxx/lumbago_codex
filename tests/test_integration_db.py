import tempfile

from core.models import Track
from data.db import reset_engine
from data.repository import init_db, upsert_tracks, list_tracks, update_track


def test_integration_db_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        reset_engine()
        init_db()
        track = Track(path="x.mp3", title="Test", artist="Artist", album="Album", year="2020")
        upsert_tracks([track])
        rows = list_tracks()
        assert len(rows) == 1
        assert rows[0].title == "Test"
        rows[0].title = "Test2"
        update_track(rows[0])
        rows2 = list_tracks()
        assert rows2[0].title == "Test2"
        reset_engine()
