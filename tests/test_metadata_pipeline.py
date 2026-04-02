from pathlib import Path

from lumbago_app.core.audio import extract_metadata
from lumbago_app.services.metadata_enricher import LOCAL_SOURCE_LABELS, available_metadata_methods


class _FakeInfo:
    length = 123.4
    bitrate = 320000
    sample_rate = 44100


class _FakeAudio:
    mime = ["audio/mpeg"]
    info = _FakeInfo()

    def __init__(self):
        self.tags = {
            "TIT2": ["Demo Title"],
            "TPE1": ["Demo Artist"],
            "TALB": ["Demo Album"],
            "TDRC": ["2024"],
            "TCON": ["House"],
            "TBPM": ["124.5"],
            "TKEY": ["8A"],
            "mood": ["peak time"],
            "energy": ["0.87"],
        }


def test_available_metadata_methods_exposes_extended_catalog():
    methods = available_metadata_methods()
    assert len(methods) == 3
    assert {"offline", "online", "mix"} == set(methods)


def test_metadata_sources_catalog_exposes_many_sources():
    assert len(LOCAL_SOURCE_LABELS) >= 10
    assert {"file_tags", "filename_pattern", "folder_structure", "sidecar_json", "folder_json", "cue_sheet", "local_library", "acoustid", "musicbrainz_search", "discogs_search"} <= set(LOCAL_SOURCE_LABELS)


def test_extract_metadata_reads_extended_tags(monkeypatch, tmp_path: Path):
    audio_path = tmp_path / "demo.mp3"
    audio_path.write_bytes(b"ID3")

    monkeypatch.setattr("lumbago_app.core.audio.MutagenFile", lambda _path: _FakeAudio())
    monkeypatch.setattr("lumbago_app.core.audio.apply_local_metadata", lambda track, path: None)

    track = extract_metadata(audio_path)

    assert track.title == "Demo Title"
    assert track.artist == "Demo Artist"
    assert track.album == "Demo Album"
    assert track.year == "2024"
    assert track.genre == "House"
    assert track.bpm == 124.5
    assert track.key == "8A"
    assert track.mood == "peak time"
    assert track.energy == 0.87
