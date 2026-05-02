from pathlib import Path

from lumbago_app.core.audio import extract_metadata
from lumbago_app.services.metadata_enricher import (
    LOCAL_SOURCE_LABELS,
    MetadataEnricher,
    available_metadata_methods,
)


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
            "rating": ["5"],
            "mood": ["peak time"],
            "energy": ["0.87"],
        }


class _FakeAudioNoTags:
    mime = ["audio/mpeg"]
    info = _FakeInfo()
    tags = {}


def test_available_metadata_methods_exposes_extended_catalog():
    methods = available_metadata_methods()
    assert len(methods) == 3
    assert {"offline", "online", "mix"} == set(methods)


def test_metadata_sources_catalog_exposes_many_sources():
    assert len(LOCAL_SOURCE_LABELS) >= 10
    assert {"file_tags", "filename_pattern", "folder_structure", "sidecar_json", "folder_json", "cue_sheet", "local_library", "musicbrainz_search"} <= set(LOCAL_SOURCE_LABELS)


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
    assert track.rating == 5
    assert track.mood == "peak time"
    assert track.energy == 0.87


def test_extract_metadata_ignores_trailing_download_bitrate_in_filename(monkeypatch, tmp_path: Path):
    audio_path = tmp_path / "Poylow, ATHYN - Good In Goodbye - 320.mp3"
    audio_path.write_bytes(b"ID3")

    monkeypatch.setattr("lumbago_app.core.audio.MutagenFile", lambda _path: _FakeAudioNoTags())
    monkeypatch.setattr("lumbago_app.core.audio._apply_folder_metadata", lambda track, path: None)

    track = extract_metadata(audio_path)

    assert track.artist == "Poylow ATHYN"
    assert track.title == "Good In Goodbye"


def test_extract_metadata_treats_single_name_before_bitrate_as_title(monkeypatch, tmp_path: Path):
    audio_path = tmp_path / "Diamond Heart - 320.mp3"
    audio_path.write_bytes(b"ID3")

    monkeypatch.setattr("lumbago_app.core.audio.MutagenFile", lambda _path: _FakeAudioNoTags())
    monkeypatch.setattr("lumbago_app.core.audio._apply_folder_metadata", lambda track, path: None)

    track = extract_metadata(audio_path)

    assert track.artist is None
    assert track.title == "Diamond Heart"


def test_extract_metadata_does_not_use_date_folder_as_album(monkeypatch, tmp_path: Path):
    folder = tmp_path / "01.03.2025"
    folder.mkdir()
    audio_path = folder / "Diamond Heart - 320.mp3"
    audio_path.write_bytes(b"ID3")

    monkeypatch.setattr("lumbago_app.core.audio.MutagenFile", lambda _path: _FakeAudioNoTags())

    track = extract_metadata(audio_path)

    assert track.album is None
    assert track.title == "Diamond Heart"


def test_copy_missing_fields_treats_placeholders_as_empty():
    from lumbago_app.core.models import Track
    from lumbago_app.services.metadata_enricher import _copy_missing_fields

    target = Track(path="target.mp3", title="\\", artist="unknown", album="-")
    source = Track(path="source.mp3", title="Fixed Title", artist="Fixed Artist", album="Fixed Album")

    changed = _copy_missing_fields(target, source, {"title", "artist", "album"})

    assert changed == ["album", "artist", "title"]
    assert target.title == "Fixed Title"
    assert target.artist == "Fixed Artist"
    assert target.album == "Fixed Album"


def test_metadata_enricher_allows_legacy_init_without_musicbrainz_app():
    enricher = MetadataEnricher()
    assert enricher.musicbrainz_app == "LumbagoMusicAI"
