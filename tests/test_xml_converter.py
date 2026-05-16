from pathlib import Path
import tempfile

from services.xml_converter import parse_rekordbox_xml, parse_virtualdj_xml


def test_parse_rekordbox_xml_basic():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<DJ_PLAYLISTS>
  <COLLECTION>
    <TRACK Location="file://C:/Music/test.mp3" Name="Test" Artist="Artist" Album="Album" Genre="House" BPM="120" Key="8A" />
  </COLLECTION>
</DJ_PLAYLISTS>
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "rekordbox.xml"
        path.write_text(xml_content, encoding="utf-8")
        tracks = parse_rekordbox_xml(path)
        assert len(tracks) == 1
        assert tracks[0].title == "Test"


def test_parse_virtualdj_xml_basic():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<VirtualDJ_Database>
  <Song FilePath="C:/Music/test.mp3" Title="Test" Artist="Artist" Album="Album" Genre="House" BPM="120" Key="8A" />
</VirtualDJ_Database>
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "virtualdj.xml"
        path.write_text(xml_content, encoding="utf-8")
        tracks = parse_virtualdj_xml(path)
        assert len(tracks) == 1
        assert tracks[0].artist == "Artist"
