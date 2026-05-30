import os

from core.models import Track
from core.services import find_duplicates_by_tags
from services.duplicate_merge import build_duplicate_merge_plan
from services.track_filters import DEFAULT_EXCLUDED_ROOTS, filter_group_rows


def test_find_duplicates_by_tags_groups_tracks():
    tracks = [
        Track(path="a.mp3", title="Song", artist="Artist", duration=180),
        Track(path="b.mp3", title="Song", artist="Artist", duration=180),
        Track(path="c.mp3", title="Other", artist="Artist", duration=200),
    ]
    result = find_duplicates_by_tags(tracks)
    assert len(result.groups) == 1
    assert len(result.groups[0].track_ids) == 2


def test_duplicates_dialog_constructs_with_actions_menu():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6 import QtWidgets

    from ui.duplicates_dialog import DuplicatesDialog

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = DuplicatesDialog([Track(path="a.mp3", title="Song")])

    assert dialog.run_btn.text() == "Szukaj"
    dialog.deleteLater()


def test_duplicate_merge_plan_uses_requested_survivor():
    requested = Track(path="keep.mp3", title="Song")
    richer_duplicate = Track(
        path="dup.mp3",
        title="Song",
        artist="Artist",
        album="Album",
        genre="House",
        duration=180,
        file_size=5_000_000,
    )

    plan = build_duplicate_merge_plan(
        [requested, richer_duplicate],
        use_ai=False,
        survivor=requested,
    )

    assert plan is not None
    assert plan.survivor is requested
    assert plan.changed_fields["artist"] == "Artist"


def test_default_duplicate_exclusions_filter_program_files():
    rows = [
        (
            "Group",
            [
                Track(path=r"C:\Program Files\App\a.mp3", title="Song"),
                Track(path=r"C:\Users\tomso\AppData\Local\App\b.mp3", title="Song"),
                Track(path=r"D:\WindowsApps\App\b.mp3", title="Song"),
                Track(path=r"D:\Music\a.mp3", title="Song"),
                Track(path=r"D:\Music\b.mp3", title="Song"),
            ],
        )
    ]

    filtered = filter_group_rows(rows, audio_only=True, excluded_roots=DEFAULT_EXCLUDED_ROOTS)

    assert len(filtered) == 1
    assert [track.path for track in filtered[0][1]] == [r"D:\Music\a.mp3", r"D:\Music\b.mp3"]
