from __future__ import annotations

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.services.metadata_enricher import MetadataFillReport
from lumbago_app.ui.ai_tagger_dialog import (
    TrackAnalysisState,
    _default_accept_fields,
    _field_confidence,
)


def test_field_confidence_falls_back_when_ai_result_has_values_without_confidence():
    original = Track(path="demo.mp3", title="Demo")
    proposed = Track(path="demo.mp3", title="Demo", genre="house", bpm=128.0, key="8A")
    state = TrackAnalysisState(
        track=original,
        proposed_track=proposed,
        ai_result=AnalysisResult(genre="house", bpm=128.0, key="8A", confidence=None),
    )

    assert _field_confidence(state, "genre") == 0.75
    assert _field_confidence(state, "bpm") == 0.75
    assert _field_confidence(state, "key") == 0.75


def test_default_accept_fields_includes_metadata_and_confident_ai_changes():
    original = Track(path="demo.mp3", title="Demo", artist="Artist")
    proposed = Track(
        path="demo.mp3",
        title="Demo",
        artist="Artist",
        album="Album",
        genre="house",
        bpm=128.0,
        year="1997",
    )
    report = MetadataFillReport(method="mix", changed_fields=["album"])
    state = TrackAnalysisState(
        track=original,
        proposed_track=proposed,
        ai_result=AnalysisResult(genre="house", bpm=128.0, year="1997", confidence=None),
        metadata_report=report,
    )

    accepted = _default_accept_fields(state)

    assert "album" in accepted
    assert "genre" in accepted
    assert "bpm" in accepted
    assert "year" in accepted
