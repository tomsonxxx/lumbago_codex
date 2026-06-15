from pathlib import Path
import tempfile
import shutil

from core.models import Track
from core.renamer import (
    _sanitize_filename,
    apply_rename_plan,
    build_rename_plan,
    parse_filename_tags,
    # new File Manager
    build_organize_plan,
    apply_organize_plan,
    organize_tracks,
    undo_last_organize,
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


# ============================================================
# NEW TESTS FOR FILE MANAGER / ORGANIZER (in existing test file)
# ============================================================

def test_build_organize_plan_creates_structured_paths_and_detects_conflict(tmp_path: Path):
    base = tmp_path / "src"
    base.mkdir()
    f1 = base / "a.mp3"
    f2 = base / "b.mp3"
    f1.write_text("1", encoding="utf-8")
    f2.write_text("2", encoding="utf-8")

    tracks = [
        Track(path=str(f1), artist="The Beatles", title="Hey Jude", album="Abbey Road", genre="Rock", year="1969"),
        Track(path=str(f2), artist="The Beatles", title="Hey Jude", album="Abbey Road", genre="Rock", year="1969"),  # same -> conflict
    ]
    target = tmp_path / "organized"
    plan = build_organize_plan(
        tracks,
        folder_structure="{genre}/{artist}/{album} ({year})",
        filename_pattern="{title}",
        target_base=target,
        action="move",
    )
    assert len(plan) == 2
    assert plan[0].conflict is True  # intra conflict on same target
    assert "Rock" in str(plan[0].new_path)
    assert "The Beatles" in str(plan[0].new_path)
    assert "Abbey Road (1969)" in str(plan[0].new_path)


def test_apply_organize_plan_move_updates_paths_and_creates_dirs(tmp_path: Path):
    src = tmp_path / "library"
    src.mkdir()
    f = src / "song.mp3"
    f.write_text("data", encoding="utf-8")

    tracks = [Track(path=str(f), artist="Artist X", title="Song Y", genre="Electronic", album="Album Z", year="2020")]
    target = tmp_path / "newlib"
    plan, result = organize_tracks(
        tracks,
        folder_structure="{genre}/{artist}",
        filename_pattern="{title}",
        target_base=target,
        action="move",
        do_write_tags=False,
    )
    history = result.history
    assert len(history) == 1
    moved = target / "Electronic" / "Artist X" / "Song Y.mp3"
    assert moved.exists()
    assert not f.exists()  # was moved
    assert history[0]["action"] == "move"
    # Note: DB update tested via integration in dialog/main, here FS+plan


def test_apply_organize_plan_copy_and_undo_ish(tmp_path: Path):
    src = tmp_path / "lib2"
    src.mkdir()
    f = src / "t.mp3"
    f.write_text("xx", encoding="utf-8")
    tracks = [Track(path=str(f), artist="A", title="T", genre="G", album="", year="")]
    target = tmp_path / "copydest"
    plan, result = organize_tracks(tracks, "{genre}", "{artist} - {title}", target, action="copy")
    hist = result.history
    assert len(hist) == 1
    assert hist[0]["action"] == "copy"
    copied = target / "G" / "A - T.mp3"
    assert copied.exists()
    assert f.exists()  # original remains for copy

    # undo should not affect copy
    rev = undo_last_organize()
    assert len(rev) == 0  # no moves to revert
    assert copied.exists()


def test_organize_plan_empty_fields_and_special_chars(tmp_path: Path):
    src = tmp_path / "s"
    src.mkdir()
    f = src / "f.mp3"
    f.write_text("", encoding="utf-8")
    tracks = [Track(path=str(f), artist="A/B:C*", title="", genre="", album="")]
    target = tmp_path / "o"
    plan = build_organize_plan(tracks, "{genre}/{artist}", "{title}", target)
    item = plan[0]
    assert item.conflict is False
    # empty genre -> Unknown, special in artist sanitized
    assert "Unknown" in str(item.new_path)
    # on Windows drive has :, so check no : in the path after drive or in name/folder parts from data
    pstr = item.new_path.as_posix()
    tail = pstr.split(":", 1)[-1] if ":" in pstr else pstr
    assert ":" not in tail
    assert "/" not in item.new_path.name  # filename no /
    assert "A B C" in pstr  # sanitized artist folder


def test_apply_organize_plan_delete_removes_file_and_history(tmp_path: Path):
    src = tmp_path / "libdel"
    src.mkdir()
    f = src / "delme.mp3"
    f.write_text("to-delete", encoding="utf-8")
    tracks = [Track(path=str(f), artist="Del", title="Me", genre="X")]
    target = tmp_path / "ignored_for_delete"
    plan, result = organize_tracks(tracks, "{genre}", "{title}", target, action="delete")
    hist = result.history
    assert len(hist) == 1
    assert hist[0]["action"] == "delete"
    assert not f.exists()
    # undo for delete should do nothing (risky, not supported)
    rev = undo_last_organize()
    assert len(rev) == 0
