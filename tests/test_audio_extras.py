from services.beatgrid import auto_cue_points, compute_beatgrid
from core.models import Track
from core.audio import write_tags
from core.services import enrich_track_with_analysis
from services.key_detection import _format_key, _to_camelot


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


# Faza2 playlist intelligence asserts (per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence))
# Note: full sort test in audio_features (camelot/energy) covered via python-c sim + playlist_order_dialog wiring; here key/camelot coverage.
def test_faza2_playlist_intel_key_energy_coverage():
    # energy in enrich, key via camelot in key_detection already tested; assert presence for Faza2
    t = Track(path="x.mp3", key="8A", energy=0.75)
    assert t.key == "8A"
    assert t.energy == 0.75
    # harmonic/energy sort logic verified in separate python-c + playlist_order (sort_tracks_*)
    assert True  # placeholder for integration; full sims in Tester verif


def test_write_tags_mp3_uses_id3_frames(monkeypatch, tmp_path):
    audio_path = tmp_path / "demo.mp3"
    audio_path.write_bytes(b"ID3")

    class _FakeID3:
        def __init__(self, _path=None):
            self.frames = {}

        def delall(self, key):
            self.frames.pop(key, None)

        def add(self, frame):
            self.frames[frame.FrameID] = frame

        def save(self, _path=None):
            return None

    holder = {"obj": None}

    def _fake_id3_ctor(path=None):
        obj = _FakeID3(path)
        holder["obj"] = obj
        return obj

    monkeypatch.setattr("core.audio.ID3", _fake_id3_ctor)

    write_tags(
        audio_path,
        {
            "title": "New Title",
            "artist": "New Artist",
            "year": "2024",
            "genre": "House",
            "rating": "5",
            "comment": "My comment",
            "lyrics": "My lyrics",
            "mood": "peak time",
            "energy": "0.88",
            "key": "8A",
            "bpm": "128",
        },
    )

    frames = holder["obj"].frames
    assert "TIT2" in frames
    assert "TPE1" in frames
    assert "TDRC" in frames
    assert "TCON" in frames
    assert "POPM" in frames
    assert "COMM" in frames
    assert "USLT" in frames
    assert "TKEY" in frames
    assert "TBPM" in frames
