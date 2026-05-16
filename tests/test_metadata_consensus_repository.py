from __future__ import annotations

import tempfile

from core.models import Track
from data.db import reset_engine
from data.repository import (
    init_db,
    list_metadata_conflicts,
    list_metadata_field_evidence,
    list_metadata_history,
    save_metadata_consensus_report,
    upsert_tracks,
)
from services.metadata_consensus import (
    FieldEvidence,
    MetadataConsensusEngine,
)


def test_save_metadata_consensus_report_persists_evidence_conflicts_and_history(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("APPDATA", temp_dir)
        reset_engine()
        init_db()
        upsert_tracks([Track(path="demo.mp3", artist="Tiesto", title="Children")])

        engine = MetadataConsensusEngine()
        report = engine.resolve(
            {
                "artist": [
                    FieldEvidence(field_name="artist", value="Tiesto", source="existing_tags", confidence=0.7),
                    FieldEvidence(
                        field_name="artist",
                        value="Armin van Buuren",
                        source="acoustid",
                        confidence=0.88,
                        verified=True,
                    ),
                    FieldEvidence(field_name="artist", value="Hardwell", source="ai_enrichment", confidence=0.96),
                ],
                "mood": [
                    FieldEvidence(field_name="mood", value="uplifting", source="ai_enrichment", confidence=0.71),
                ],
            }
        )

        save_metadata_consensus_report("demo.mp3", report, operation="autotag")

        evidence_rows = list_metadata_field_evidence("demo.mp3", "artist")
        history_rows = list_metadata_history("demo.mp3", "artist")
        conflict_rows = list_metadata_conflicts("demo.mp3")

        assert len(evidence_rows) == 3
        assert evidence_rows[0]["version"] >= 1
        assert len(history_rows) == 1
        assert history_rows[0]["old"] == "Tiesto"
        assert history_rows[0]["new"] == "Armin van Buuren"
        assert history_rows[0]["source"] == "acoustid"
        assert conflict_rows
        assert conflict_rows[0]["field"] == "artist"
        assert conflict_rows[0]["chosen_value"] == "Armin van Buuren"
        reset_engine()
