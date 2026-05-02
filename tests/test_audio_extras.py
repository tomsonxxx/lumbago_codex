from lumbago_app.services.beatgrid import auto_cue_points, compute_beatgrid
from lumbago_app.core.models import Track
from lumbago_app.core.services import enrich_track_with_analysis
from lumbago_app.services.key_detection import _format_key, _to_camelot


def test_compute_beatgrid_basic():
    beats = compute_beatgrid(4, 60.0)
    assert beats[0] == 0.0
    assert beats[-1] == 4.0
    assert len(beats) == 5


def test_auto_cue_points():
    cue_in, cue_out = auto_cue_points(100)
    assert cue_in == 0
    assert cue_out == 90000


def test_camelot_mapping():
    assert _to_camelot("A minor") == "8A"
    assert _to_camelot("C major") == "8B"
    assert _format_key("F# major") == "F#"


def test_enrich_track_with_detected_audio_values():
    track = Track(path="demo.mp3")
    enrich_track_with_analysis(track, detected_bpm=128.4, detected_key="8A", detected_energy=0.82)
    assert track.bpm == 128.4
    assert track.key == "8A"
    assert track.energy == 0.82
    assert track.mood == "energetic"


def test_enrich_track_with_analysis_preserves_existing_genre_and_mood():
    track = Track(path="demo.mp3", bpm=128.0, genre="House", mood="uplifting")
    enrich_track_with_analysis(track)
    assert track.genre == "House"
    assert track.mood == "uplifting"


def test_enrich_track_with_analysis_falls_back_to_heuristics():
    track = Track(path="demo.mp3", bpm=88.0)
    enrich_track_with_analysis(track)
    assert track.bpm == 88.0
    assert track.energy == 0.2
    assert track.mood == "chill"
