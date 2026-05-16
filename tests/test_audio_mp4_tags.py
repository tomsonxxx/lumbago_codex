from pathlib import Path

from core import audio


class _Mp4Stub:
    def __init__(self, tags=None):
        self.tags = tags if tags is not None else {}
        self.saved = False

    def save(self):
        self.saved = True


def test_read_tags_mp4_includes_dj_fields(monkeypatch):
    stub = _Mp4Stub(
        {
            "\xa9nam": ["Track Name"],
            "\xa9ART": ["Artist Name"],
            "tmpo": [129],
            "trkn": [(4, 0)],
            "----:com.apple.iTunes:INITIALKEY": [b"8A"],
            "----:com.apple.iTunes:MOOD": [b"uplifting"],
            "----:com.apple.iTunes:ENERGY": [b"0.73"],
        }
    )
    monkeypatch.setattr(audio, "MutagenFile", lambda path, easy=False: stub)

    tags = audio.read_tags(Path("demo.m4a"))

    assert tags["title"] == "Track Name"
    assert tags["artist"] == "Artist Name"
    assert tags["bpm"] == "129"
    assert tags["tracknumber"] == "4"
    assert tags["key"] == "8A"
    assert tags["mood"] == "uplifting"
    assert tags["energy"] == "0.73"


def test_write_tags_mp4_persists_dj_fields(monkeypatch):
    stub = _Mp4Stub({})
    monkeypatch.setattr(audio, "MutagenFile", lambda path, easy=False: stub)

    audio.write_tags(
        Path("demo.m4a"),
        {
            "title": "My Title",
            "artist": "My Artist",
            "bpm": "128.6",
            "key": "2A",
            "mood": "dark",
            "energy": "0.66",
            "tracknumber": "5/12",
        },
    )

    assert stub.saved is True
    assert stub.tags["\xa9nam"] == ["My Title"]
    assert stub.tags["\xa9ART"] == ["My Artist"]
    assert stub.tags["tmpo"] == [129]
    assert stub.tags["trkn"] == [(5, 0)]
    assert bytes(stub.tags["----:com.apple.iTunes:INITIALKEY"][0]) == b"2A"
    assert bytes(stub.tags["----:com.apple.iTunes:MOOD"][0]) == b"dark"
    assert bytes(stub.tags["----:com.apple.iTunes:ENERGY"][0]) == b"0.66"


def test_write_tags_mp4_does_not_delete_unspecified_fields(monkeypatch):
    stub = _Mp4Stub(
        {
            "\xa9nam": ["Old Title"],
            "\xa9ART": ["Old Artist"],
            "\xa9alb": ["Old Album"],
        }
    )
    monkeypatch.setattr(audio, "MutagenFile", lambda path, easy=False: stub)

    audio.write_tags(Path("demo.m4a"), {"key": "9A"})

    assert stub.saved is True
    assert stub.tags["\xa9nam"] == ["Old Title"]
    assert stub.tags["\xa9ART"] == ["Old Artist"]
    assert stub.tags["\xa9alb"] == ["Old Album"]
    assert bytes(stub.tags["----:com.apple.iTunes:INITIALKEY"][0]) == b"9A"
