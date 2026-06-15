from __future__ import annotations

import tempfile

from core.models import Track
from data.db import reset_engine
from data.repository import init_db, list_tracks, resolve_track_ids, upsert_tracks


def test_resolve_track_ids_returns_database_ids(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        reset_engine()
        init_db()
        upsert_tracks([Track(path=r"D:\Music\a.mp3", title="A")])
        rows = list_tracks()
        assert rows[0].id is not None

        ids = resolve_track_ids([r"D:\Music\a.mp3", r"D:\Music\b.mp3"])
        assert len(ids) == 2
        assert rows[0].id in ids
        assert all(isinstance(track_id, int) for track_id in ids)

        reset_engine()