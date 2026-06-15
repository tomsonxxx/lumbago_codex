from __future__ import annotations

from pathlib import Path

from core.metadata_quality import (
    album_matches_parent_folder,
    strip_album_folder_artifact,
)
from core.models import Track
from services.autotag_rewrite import _clear_album_if_title_duplicate, _sanitize_album_value


def test_album_matches_parent_folder_detects_catalog_name():
    path = r"D:\Music\bib5\Farruko - Pepas.mp3"
    assert album_matches_parent_folder("bib5", path) is True
    assert album_matches_parent_folder("BIB5", path) is True


def test_album_matches_parent_folder_allows_real_album_in_subfolder():
    path = r"D:\Music\Metallica\Ride The Lightning\01.mp3"
    assert album_matches_parent_folder("Ride The Lightning", path) is True
    assert album_matches_parent_folder("Master of Puppets", path) is False


def test_strip_album_folder_artifact_clears_track():
    track = Track(path=r"D:\Music\bib5\track.mp3", title="Song", album="bib5")
    assert strip_album_folder_artifact(track) is True
    assert track.album is None


def test_sanitize_album_value_rejects_parent_folder_name():
    path = r"D:\Music\bib5\track.mp3"
    assert _sanitize_album_value("bib5", "Song", track_path=path) is None
    assert _sanitize_album_value("Real Album", "Song", track_path=path) == "Real Album"


def test_clear_album_if_title_duplicate_clears_folder_artifact(tmp_path: Path):
    folder = tmp_path / "bib5"
    folder.mkdir()
    track = Track(path=str(folder / "song.mp3"), title="Song", album="bib5")
    assert _clear_album_if_title_duplicate(track) is True
    assert track.album is None