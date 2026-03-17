from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lumbago_app.core.config import cache_dir
from lumbago_app.core.models import Track


@dataclass
class RenamePlanItem:
    old_path: Path
    new_path: Path
    conflict: bool = False
    reason: str | None = None


def build_rename_plan(tracks: Iterable[Track], pattern: str) -> list[RenamePlanItem]:
    plan: list[RenamePlanItem] = []
    used_paths: set[Path] = set()
    for index, track in enumerate(tracks, 1):
        old_path = Path(track.path)
        name = _render_pattern(track, pattern, index)
        name = _sanitize_filename(name)
        new_path = old_path.with_name(f"{name}{old_path.suffix}")
        conflict = False
        reason = None
        if new_path in used_paths:
            conflict = True
            reason = "Konflikt nazwy w planie"
        elif new_path.exists() and new_path != old_path:
            conflict = True
            reason = "Plik już istnieje"
        used_paths.add(new_path)
        plan.append(RenamePlanItem(old_path=old_path, new_path=new_path, conflict=conflict, reason=reason))
    return plan


def apply_rename_plan(plan: Iterable[RenamePlanItem]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for item in plan:
        if item.conflict:
            continue
        if not item.old_path.exists():
            continue
        item.new_path.parent.mkdir(parents=True, exist_ok=True)
        item.old_path.rename(item.new_path)
        history.append({"old": str(item.old_path), "new": str(item.new_path)})
    _store_rename_history(history)
    return history


def undo_last_rename() -> list[dict[str, str]]:
    history = _load_rename_history()
    reverted: list[dict[str, str]] = []
    for entry in reversed(history):
        old = Path(entry["old"])
        new = Path(entry["new"])
        if new.exists() and not old.exists():
            new.rename(old)
            reverted.append(entry)
    _store_rename_history([])
    return reverted


def _render_pattern(track: Track, pattern: str, index: int) -> str:
    mapping = {
        "artist": track.artist or "",
        "title": track.title or "",
        "album": track.album or "",
        "genre": track.genre or "",
        "bpm": str(int(track.bpm)) if track.bpm else "",
        "key": track.key or "",
        "year": track.year or "",
        "index": str(index),
    }
    result = pattern
    for key, value in mapping.items():
        result = result.replace(f"{{{key}}}", value)
    if "{index:03}" in result:
        result = result.replace("{index:03}", f"{index:03d}")
    return result.strip() or f"track_{index}"


def _sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\\s+", " ", name).strip()
    return name[:180] if len(name) > 180 else name


def _history_path() -> Path:
    return cache_dir() / "rename_history.json"


def _store_rename_history(history: list[dict[str, str]]) -> None:
    path = _history_path()
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_rename_history() -> list[dict[str, str]]:
    path = _history_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
