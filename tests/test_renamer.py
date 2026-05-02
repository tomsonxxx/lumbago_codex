from pathlib import Path
import tempfile

from lumbago_app.core.models import Track
from lumbago_app.core.renamer import (
    _sanitize_filename,
    apply_rename_plan,
    build_rename_plan,
    parse_filename_tags,
)


def test_build_rename_plan_detects_conflict():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        a = base / "a.mp3"
        b = base / "b.mp3"
        a.write_text("x", encoding="utf-8")
        b.write_text("y", encoding="utf-8")
        tracks = [
            Track(path=str(a), artist="Artist", title="Title"),
            Track(path=str(b), artist="Artist", title="Title"),
        ]
        plan = build_rename_plan(tracks, "{artist} - {title}")
        assert plan[0].conflict is True
        assert plan[1].conflict is True


def test_rename_plan_cleans_common_video_noise():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        src = base / "a.mp3"
        src.write_text("x", encoding="utf-8")
        tracks = [Track(path=str(src), artist="Artist", title="Song Name (Official Video) [HD]")]
        plan = build_rename_plan(tracks, "{artist} - {title}")
        assert "official" not in plan[0].new_path.stem.lower()
        assert "hd" not in plan[0].new_path.stem.lower()
        assert plan[0].new_path.stem == "Artist - Song Name"


def test_sanitize_filename_removes_invalid_characters():
    cleaned = _sanitize_filename('Artist:Name / Track*Title? "Official Video"')
    assert ":" not in cleaned
    assert "/" not in cleaned
    assert "*" not in cleaned
    assert "official video" not in cleaned.lower()


def test_parse_filename_tags_cleans_artist_and_title_noise():
    artist, title = parse_filename_tags("Artist Name (Official Video) - Song Title [HD].mp3")
    assert artist == "Artist Name"
    assert title == "Song Title"


def test_parse_filename_tags_strips_download_bitrate_suffix():
    artist, title = parse_filename_tags("Artist Name - Song Title - 320.mp3")
    assert artist == "Artist Name"
    assert title == "Song Title"


def test_parse_filename_tags_uses_single_name_before_bitrate_as_title():
    artist, title = parse_filename_tags("Diamond Heart - 320.mp3")
    assert artist is None
    assert title == "Diamond Heart"


def test_build_rename_plan_allows_chain_targets_within_same_plan(tmp_path: Path):
    file_a = tmp_path / "A.mp3"
    file_b = tmp_path / "B.mp3"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    tracks = [
        Track(path=str(file_a), artist="X", title="B"),
        Track(path=str(file_b), artist="X", title="C"),
    ]

    plan = build_rename_plan(tracks, "{title}")

    assert all(not item.conflict for item in plan)
    history = apply_rename_plan(plan)
    assert len(history) == 2
    assert (tmp_path / "B.mp3").exists()
    assert (tmp_path / "C.mp3").exists()


def test_build_rename_plan_marks_conflict_for_existing_external_file(tmp_path: Path):
    source = tmp_path / "A.mp3"
    source.write_text("a", encoding="utf-8")
    existing = tmp_path / "Taken.mp3"
    existing.write_text("x", encoding="utf-8")

    tracks = [Track(path=str(source), artist="Any", title="Taken")]
    plan = build_rename_plan(tracks, "{title}")

    assert len(plan) == 1
    assert plan[0].conflict is True
