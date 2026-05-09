from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
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
    prepared: list[RenamePlanItem] = []
    for index, track in enumerate(tracks, 1):
        old_path = Path(track.path)
        name = _render_pattern(track, pattern, index)
        name = _sanitize_filename(name)
        new_path = old_path.with_name(f"{name}{old_path.suffix}")
        prepared.append(
            RenamePlanItem(
                old_path=old_path,
                new_path=new_path,
                conflict=False,
                reason=None,
            )
        )

    old_paths = {item.old_path for item in prepared}
    target_count: dict[Path, int] = {}
    for item in prepared:
        target_count[item.new_path] = target_count.get(item.new_path, 0) + 1

    plan: list[RenamePlanItem] = []
    for item in prepared:
        conflict = False
        reason = None
        if target_count.get(item.new_path, 0) > 1:
            conflict = True
            reason = "Konflikt nazwy w planie"
        elif item.new_path.exists() and item.new_path != item.old_path and item.new_path not in old_paths:
            conflict = True
            reason = "Plik już istnieje"
        plan.append(
            RenamePlanItem(
                old_path=item.old_path,
                new_path=item.new_path,
                conflict=conflict,
                reason=reason,
            )
        )
    return plan


def apply_rename_plan(plan: Iterable[RenamePlanItem]) -> list[dict[str, str]]:
    executable = [
        item
        for item in plan
        if not item.conflict and item.old_path.exists() and item.old_path != item.new_path
    ]
    if not executable:
        _store_rename_history([])
        return []

    staged: list[tuple[Path, Path, Path]] = []
    moved_to_temp: list[tuple[Path, Path, Path]] = []
    history: list[dict[str, str]] = []

    # Two-phase rename avoids collisions and case-only path updates on Windows.
    for idx, item in enumerate(executable):
        temp_path = _temporary_path_for(item.old_path, idx)
        staged.append((item.old_path, temp_path, item.new_path))

    try:
        for old_path, temp_path, new_path in staged:
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(temp_path)
            moved_to_temp.append((old_path, temp_path, new_path))

        for old_path, temp_path, new_path in moved_to_temp:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.rename(new_path)
            history.append({"old": str(old_path), "new": str(new_path)})
    except Exception:
        for old_path, temp_path, _ in reversed(moved_to_temp):
            if temp_path.exists() and not old_path.exists():
                try:
                    temp_path.rename(old_path)
                except Exception:
                    pass
        raise


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
        "artist": _cleanup_metadata_fragment(track.artist or ""),
        "title": _cleanup_metadata_fragment(track.title or ""),
        "album": _cleanup_metadata_fragment(track.album or ""),
        "genre": _cleanup_metadata_fragment(track.genre or ""),
        "bpm": _cleanup_metadata_fragment(str(track.bpm or "")),
        "key": _cleanup_metadata_fragment(track.key or ""),
        "index": str(index),
    }
    if "{index:03}" in pattern:
        mapping["index:03"] = f"{index:03d}"

    result = pattern
    for key, value in mapping.items():
        result = result.replace(f"{{{key}}}", value)

    # Remove dangling separators caused by empty fields:
    # e.g. " - Tytuł" when artist is empty, or "Artysta - " when title is empty.
    result = re.sub(r"^\s*[-–—|]+\s*", "", result)
    result = re.sub(r"\s*[-–—|]+\s*$", "", result)
    # Collapse multiple consecutive separators: "A -  - B" → "A - B"
    result = re.sub(r"(\s*-\s*){2,}", " - ", result)
    return result.strip(" .-_") or f"track_{index}"


def _sanitize_filename(name: str) -> str:
    cleaned = _cleanup_metadata_fragment(name)
    cleaned = re.sub(r"[\\/:*?\"<>|]", " ", cleaned)
    cleaned = re.sub(r"[_]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-_")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:180] if len(cleaned) > 180 else cleaned


_NOISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"[\[(]\s*(official(\s+music)?\s+video|official\s+audio|audio|lyrics?|lyric\s+video|visualizer|"
        r"hq|hd|4k|8k|remastered(\s+\d{4})?|live|full\s+album|explicit)\s*[\])]",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(official(\s+music)?\s+video|official\s+audio|lyrics?|lyric\s+video|visualizer)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(hq|hd|4k|8k|remastered(\s+\d{4})?)\b", re.IGNORECASE),
)
_ORPHAN_BRACKETS_RE = re.compile(r"[\[\]{}]")
# Apostrophe and parentheses are kept — they appear in valid artist/title names.
_NOISY_PUNCT_RE = re.compile(r"[^\w\s\-\.,&+()']+", re.UNICODE)
# Only collapse runs of pure separators (not apostrophes or parens).
_MULTI_SEPARATOR_RE = re.compile(r"\s*[–—_|]+\s*")


def _cleanup_metadata_fragment(value: str) -> str:
    text = str(value or "")
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    text = _ORPHAN_BRACKETS_RE.sub(" ", text)
    text = _NOISY_PUNCT_RE.sub(" ", text)
    text = _MULTI_SEPARATOR_RE.sub(" - ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    return text


_FILENAME_NOISE_BRACKET_RE = re.compile(
    r"[\[(]\s*(?:"
    r"(?:hd|hq|4k|8k)\s+video"
    r"|(?:hd|hq|4k|8k)"
    r"|official\s+(?:music\s+)?lyric(?:s)?\s+video"
    r"|official\s+(?:music\s+)?video"
    r"|official\s+audio"
    r"|lyric\s+video"
    r"|lyrics?"
    r"|visualizer"
    r"|remastered(?:\s+\d{4})?"
    r"|full\s+album"
    r"|explicit"
    r")\s*[\])]",
    re.IGNORECASE,
)


def _clean_title_from_filename(title: str) -> str:
    title = _FILENAME_NOISE_BRACKET_RE.sub("", title)
    title = re.sub(r"\s+", " ", title).strip(" .-_")
    return title


def _strip_download_quality_suffix(value: str) -> str:
    text = value.strip()
    previous = None
    while previous != text:
        previous = text
        text = re.sub(
            r" {1,4}- {1,4}(?:\d{2,4} {0,2}(?:kbps|k)?|mp3|flac|wav|m4a|aac)$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip(" .-_")
    return text



def parse_filename_tags(path: str | Path) -> tuple[str | None, str | None]:
    stem = _strip_download_quality_suffix(PureWindowsPath(path).stem.replace("_", " ").replace(".", " "))
    # Try separators with surrounding spaces first (most reliable), then bare dash.
    for sep in (" – ", " — ", " - "):
        if sep in stem:
            left, right = stem.split(sep, 1)
            artist = _clean_title_from_filename(left.strip()) or None
            title = _clean_title_from_filename(right.strip()) or None
            if artist and title:
                return artist, title
    # Bare dash: only split when both sides are non-trivial (length > 1)
    # to avoid splitting "A-ha" → ("A", "ha").
    bare_dash_match = re.match(r"^([^-]{2,})-([^-]{2,})$", stem.strip())
    if bare_dash_match:
        left = bare_dash_match.group(1).strip()
        right = bare_dash_match.group(2).strip()
        artist = _clean_title_from_filename(left) or None
        title = _clean_title_from_filename(right) or None
        if artist and title:
            return artist, title
    title = _clean_title_from_filename(stem)
    return None, title or None


def _history_path() -> Path:
    return cache_dir() / "rename_history.json"


def _store_rename_history(history: list[dict[str, str]]) -> None:
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_rename_history() -> list[dict[str, str]]:
    path = _history_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _temporary_path_for(original_path: Path, idx: int) -> Path:
    pid = os.getpid()
    suffix = original_path.suffix
    candidate = original_path.with_name(f".lumbago_rename_tmp_{pid}_{idx}{suffix}")
    collision_counter = 0
    while candidate.exists():
        collision_counter += 1
        candidate = original_path.with_name(
            f".lumbago_rename_tmp_{pid}_{idx}_{collision_counter}{suffix}"
        )
    return candidate
