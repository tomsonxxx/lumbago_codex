from pathlib import Path

from core.models import Track
from core.renamer import (
    RenamePlanItem,
    auto_resolve_plan_conflicts,
    build_organize_plan,
    build_rename_plan,
    refresh_plan_conflicts,
    remove_plan_items_at_indices,
    resolve_plan_item_to_conflicts_folder,
    resolve_plan_item_with_suffix,
    set_plan_item_target_path,
)


def test_auto_resolve_suffix_clears_intra_plan_conflicts(tmp_path: Path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_text("1", encoding="utf-8")
    b.write_text("2", encoding="utf-8")
    tracks = [
        Track(path=str(a), artist="Artist", title="Title"),
        Track(path=str(b), artist="Artist", title="Title"),
    ]
    plan = build_rename_plan(tracks, "{artist} - {title}")
    assert all(item.conflict for item in plan)

    changed = auto_resolve_plan_conflicts(plan, strategy="suffix")
    assert changed >= 1
    assert not any(item.conflict for item in plan)
    targets = {item.new_path for item in plan}
    assert len(targets) == 2


def test_auto_resolve_duplicates_folder(tmp_path: Path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_text("1", encoding="utf-8")
    b.write_text("2", encoding="utf-8")
    tracks = [
        Track(path=str(a), artist="X", title="Same"),
        Track(path=str(b), artist="Y", title="Same"),
    ]
    plan = build_rename_plan(tracks, "{title}")
    auto_resolve_plan_conflicts(plan, strategy="duplicates_folder")
    assert not any(item.conflict for item in plan)
    conflict_paths = [p for p in (item.new_path for item in plan) if "_Konflikty" in str(p)]
    assert len(conflict_paths) >= 1


def test_resolve_single_item_suffix(tmp_path: Path):
    f1 = tmp_path / "1.mp3"
    f2 = tmp_path / "2.mp3"
    f1.write_text("a", encoding="utf-8")
    f2.write_text("b", encoding="utf-8")
    plan = build_rename_plan(
        [Track(path=str(f1), title="T"), Track(path=str(f2), title="T")],
        "{title}",
    )
    assert resolve_plan_item_with_suffix(plan[1], plan)
    refresh_plan_conflicts(plan)
    assert not any(item.conflict for item in plan)


def test_remove_plan_items_and_refresh(tmp_path: Path):
    f = tmp_path / "x.mp3"
    f.write_text("x", encoding="utf-8")
    plan = build_rename_plan([Track(path=str(f), title="A")], "{title}")
    assert len(plan) == 1
    removed = remove_plan_items_at_indices(plan, [0])
    assert removed == 1
    assert plan == []


def test_set_plan_item_target_path_avoids_external_conflict(tmp_path: Path):
    src = tmp_path / "src.mp3"
    taken = tmp_path / "Taken.mp3"
    src.write_text("s", encoding="utf-8")
    taken.write_text("t", encoding="utf-8")
    plan = build_rename_plan([Track(path=str(src), title="Taken")], "{title}")
    assert plan[0].conflict
    set_plan_item_target_path(plan[0], tmp_path / "Free.mp3", plan)
    assert not plan[0].conflict
    assert plan[0].new_path.name == "Free.mp3"


def test_organize_plan_auto_resolve(tmp_path: Path):
    base = tmp_path / "src"
    base.mkdir()
    f1 = base / "a.mp3"
    f2 = base / "b.mp3"
    f1.write_text("1", encoding="utf-8")
    f2.write_text("2", encoding="utf-8")
    tracks = [
        Track(path=str(f1), artist="A", title="Song", genre="G"),
        Track(path=str(f2), artist="A", title="Song", genre="G"),
    ]
    plan = build_organize_plan(tracks, "{genre}", "{title}", tmp_path / "out", action="move")
    assert any(i.conflict for i in plan)
    auto_resolve_plan_conflicts(plan, strategy="suffix")
    assert not any(i.conflict for i in plan)


def test_resolve_to_conflicts_folder_on_organize_item(tmp_path: Path):
    base = tmp_path / "src"
    base.mkdir()
    f1 = base / "a.mp3"
    f2 = base / "b.mp3"
    f1.write_text("1", encoding="utf-8")
    f2.write_text("2", encoding="utf-8")
    tracks = [
        Track(path=str(f1), artist="A", title="S", genre="Rock"),
        Track(path=str(f2), artist="B", title="S", genre="Rock"),
    ]
    plan = build_organize_plan(tracks, "{genre}", "{title}", tmp_path / "lib", action="move")
    assert plan[1].conflict
    assert resolve_plan_item_to_conflicts_folder(plan[1], plan)
    assert "_Konflikty" in str(plan[1].new_path)
    refresh_plan_conflicts(plan)
    assert not any(i.conflict for i in plan)