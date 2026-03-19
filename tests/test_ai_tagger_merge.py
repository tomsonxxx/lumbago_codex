from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.ui.ai_tagger_dialog import (
    _harmonize_batch_results,
    _merge_analysis_into_track,
)


def test_merge_analysis_does_not_overwrite_with_unknown():
    track = Track(path="x.mp3", artist="Daft Punk", title="One More Time")
    result = AnalysisResult(artist="Unknown", album="Discovery", comments="Classic dance track")
    _merge_analysis_into_track(track, result)
    assert track.artist == "Daft Punk"
    assert track.album == "Discovery"
    assert track.comments == "Classic dance track"


def test_batch_harmonization_enforces_artist_album_consistency():
    t1 = Track(path="a.mp3", artist="Artist A", album="Album A")
    t2 = Track(path="b.mp3", artist="Artist A", album="Album A")
    r1 = AnalysisResult(artist="Artist A", album="Album A")
    r2 = AnalysisResult(artist="Artist A", album="Album Typo")
    out = _harmonize_batch_results([(t1, r1), (t2, r2)])
    assert out[0][1].album == "Album A"
    assert out[1][1].album == "Album A"
