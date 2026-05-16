from __future__ import annotations

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.services.ai_tagger_merge import _merge_analysis_into_track


def test_merge_keeps_good_local_values() -> None:
    track = Track(path="x.mp3", album="Existing Album", artist="Known Artist")
    ai = AnalysisResult(album="Other Album", artist="Other Artist", confidence=0.7)
    merged = _merge_analysis_into_track(track, ai)
    assert merged.album == "Existing Album"
    assert merged.artist == "Known Artist"


def test_merge_overwrites_garbage_local_values() -> None:
    track = Track(path="x.mp3", title="unknown", artist="www.site.com")
    ai = AnalysisResult(title="Real Title", artist="Real Artist", confidence=0.8)
    merged = _merge_analysis_into_track(track, ai)
    assert merged.title == "Real Title"
    assert merged.artist == "Real Artist"

