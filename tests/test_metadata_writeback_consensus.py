from __future__ import annotations

import tempfile

from lumbago_app.core.models import Track
from lumbago_app.data.db import reset_engine
from lumbago_app.data.repository import init_db, list_tracks, upsert_tracks
from lumbago_app.services.metadata_writeback import PendingTrackWrite, apply_track_writes


def test_apply_track_writes_does_not_allow_ai_to_overwrite_existing_artist(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        reset_engine()
        init_db()
        upsert_tracks([Track(path="demo.mp3", artist="Tiesto", title="Children")])
        monkeypatch.setattr("lumbago_app.services.metadata_writeback.write_tags", lambda *_args, **_kwargs: None)

        incoming = Track(path="demo.mp3", artist="Hardwell", title="Children")
        result = apply_track_writes(
            [
                PendingTrackWrite(
                    track=incoming,
                    fields={"artist": "Hardwell"},
                    source="ai_enrichment",
                    confidence=0.99,
                    change_log_source="ai_enrichment",
                    old_values={"artist": "Tiesto"},
                )
            ],
            max_workers=1,
            update_mode="single",
        )

        tracks = list_tracks()
        assert result.applied_fields == 0
        assert tracks[0].artist == "Tiesto"
        reset_engine()
