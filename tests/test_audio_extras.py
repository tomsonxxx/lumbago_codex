from lumbago_app.services.beatgrid import auto_cue_points, compute_beatgrid
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
