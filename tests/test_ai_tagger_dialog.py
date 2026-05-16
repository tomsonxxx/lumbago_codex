from __future__ import annotations

from core.models import AnalysisResult, Track
from services.metadata_enricher import MetadataFillReport
from ui.ai_tagger_dialog import (
    _PipelineWorker,
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


def test_cloud_pipeline_worker_uses_batch_ai_for_chunk(monkeypatch):
    from services.ai_tagger import CloudAiTagger

    states = [
        TrackAnalysisState(track=Track(path="01.mp3"), proposed_track=Track(path="01.mp3")),
        TrackAnalysisState(track=Track(path="02.mp3"), proposed_track=Track(path="02.mp3")),
    ]
    tagger = CloudAiTagger(
        provider="openai",
        api_key="x",
        base_url="https://example.test/v1",
        model="demo",
    )
    calls: list[list[str]] = []

    def _fake_batch(tracks, chunk_size=20):
        calls.append([track.path for track in tracks])
        return [
            AnalysisResult(title="Intro", artist="Artist", album="Album", confidence=0.9),
            AnalysisResult(title="Main", artist="Artist", album="Album", confidence=0.9),
        ]

    monkeypatch.setattr(tagger, "analyze_batch", _fake_batch)
    monkeypatch.setattr(tagger, "analyze", lambda _track: (_ for _ in ()).throw(AssertionError("single analyze called")))
    monkeypatch.setattr("ui.ai_tagger_dialog.load_analysis_cache", lambda _path: {})
    monkeypatch.setattr("ui.ai_tagger_dialog.save_analysis_cache", lambda _path, _payload: None)

    worker = _PipelineWorker(
        states,
        tagger,
        auto_filler=None,
        method="online",
        do_audio=False,
        max_workers=1,
    )
    worker.run()

    assert calls == [["01.mp3", "02.mp3"]]
    assert [state.proposed_track.title for state in states] == ["Intro", "Main"]
    assert all(state.decisions.get("title") is True for state in states)
