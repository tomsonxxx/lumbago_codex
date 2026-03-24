from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.services.ai_tagger_merge import _harmonize_batch_results, _merge_analysis_into_track


def test_merge_analysis_does_not_overwrite_with_unknown():
    track = Track(path="x.mp3", genre="House", mood="Euphoric")
    result = AnalysisResult(genre="Unknown", mood="Energetic")
    _merge_analysis_into_track(track, result)
    assert track.genre == "House"
    assert track.mood == "Energetic"


def test_merge_analysis_ignores_dash_placeholder():
    track = Track(path="x.mp3", key="8A")
    result = AnalysisResult(key="\u2014")
    _merge_analysis_into_track(track, result)
    assert track.key == "8A"


def test_batch_harmonization_enforces_consistency():
    t1 = Track(path="a.mp3", genre="House", mood="Happy")
    t2 = Track(path="b.mp3", genre="House", mood="Happy")
    r1 = AnalysisResult(genre="House", mood="Happy")
    r2 = AnalysisResult(genre="House", mood="Sad")
    out = _harmonize_batch_results([(t1, r1), (t2, r2)])
    assert out[0][1].mood == "Happy"
    assert out[1][1].mood == "Happy"
