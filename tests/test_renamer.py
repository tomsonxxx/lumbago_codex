from pathlib import Path
import tempfile

from lumbago_app.core.models import Track
from lumbago_app.core.renamer import _sanitize_filename, build_rename_plan, parse_filename_tags


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
        assert plan[0].conflict is False
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
