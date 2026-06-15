from __future__ import annotations

import json
import os
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Iterable, TypeAlias

from core.config import cache_dir
from core.models import Track

PlanItem: TypeAlias = "RenamePlanItem | OrganizePlanItem"


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


def refresh_plan_conflicts(plan: list[PlanItem]) -> None:
    """Przelicz flagi konfliktu w istniejącym planie (po ręcznej edycji ścieżek)."""
    old_paths = {item.old_path for item in plan}
    target_count: dict[Path, int] = {}
    for item in plan:
        if getattr(item, "action", "rename") == "delete":
            continue
        target_count[item.new_path] = target_count.get(item.new_path, 0) + 1

    for item in plan:
        if getattr(item, "action", None) == "delete":
            item.conflict = False
            item.reason = None
            continue
        conflict = False
        reason = None
        if target_count.get(item.new_path, 0) > 1:
            conflict = True
            reason = "Konflikt nazwy w planie"
        elif (
            item.new_path.exists()
            and item.new_path != item.old_path
            and item.new_path not in old_paths
        ):
            conflict = True
            reason = (
                "Plik już istnieje w docelowej lokalizacji"
                if isinstance(item, OrganizePlanItem)
                else "Plik już istnieje"
            )
        item.conflict = conflict
        item.reason = reason


def _path_is_taken(
    path: Path,
    *,
    reserved: set[Path],
    old_paths: set[Path],
) -> bool:
    if path in reserved:
        return True
    return path.exists() and path not in old_paths


def _allocate_unique_path(
    desired: Path,
    *,
    reserved: set[Path],
    old_paths: set[Path],
    strategy: str = "suffix",
) -> Path:
    """Zwróć wolną ścieżkę: sufiks _2/_3… lub podfolder _Konflikty."""
    if not _path_is_taken(desired, reserved=reserved, old_paths=old_paths):
        return desired

    stem, suffix = desired.stem, desired.suffix
    parent = desired.parent

    if strategy == "duplicates_folder":
        parent = parent / "_Konflikty"
        candidate = parent / f"{stem}{suffix}"
        if not _path_is_taken(candidate, reserved=reserved, old_paths=old_paths):
            return candidate
        n = 2
        while True:
            candidate = parent / f"{stem}_{n}{suffix}"
            if not _path_is_taken(candidate, reserved=reserved, old_paths=old_paths):
                return candidate
            n += 1

    n = 2
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not _path_is_taken(candidate, reserved=reserved, old_paths=old_paths):
            return candidate
        n += 1


def auto_resolve_plan_conflicts(
    plan: list[PlanItem],
    *,
    strategy: str = "suffix",
) -> int:
    """Automatycznie rozwiąż konflikty w planie. Zwraca liczbę zmienionych pozycji."""
    if not plan:
        return 0
    changed_total = 0
    max_passes = max(len(plan) * 3, 1)
    for _ in range(max_passes):
        refresh_plan_conflicts(plan)
        conflicts = [
            item
            for item in plan
            if item.conflict and getattr(item, "action", "rename") != "delete"
        ]
        if not conflicts:
            break
        old_paths = {item.old_path for item in plan}
        changed_pass = 0
        for item in conflicts:
            reserved_other = {
                p.new_path
                for p in plan
                if getattr(p, "action", "rename") != "delete" and p is not item
            }
            new_path = _allocate_unique_path(
                item.new_path,
                reserved=reserved_other,
                old_paths=old_paths,
                strategy=strategy,
            )
            if new_path != item.new_path:
                item.new_path = new_path
                changed_pass += 1
        changed_total += changed_pass
        if changed_pass == 0:
            break
    refresh_plan_conflicts(plan)
    return changed_total


def resolve_plan_item_with_suffix(item: PlanItem, plan: list[PlanItem]) -> bool:
    """Dodaj sufiks numerowany do docelowej nazwy jednej pozycji planu."""
    if getattr(item, "action", "rename") == "delete":
        return False
    old_paths = {p.old_path for p in plan}
    reserved = {
        p.new_path for p in plan if getattr(p, "action", "rename") != "delete" and p is not item
    }
    new_path = _allocate_unique_path(
        item.new_path,
        reserved=reserved,
        old_paths=old_paths,
        strategy="suffix",
    )
    if new_path == item.new_path:
        return False
    item.new_path = new_path
    refresh_plan_conflicts(plan)
    return True


def resolve_plan_item_to_conflicts_folder(item: PlanItem, plan: list[PlanItem]) -> bool:
    """Przenieś docelową ścieżkę do podfolderu _Konflikty."""
    if getattr(item, "action", "rename") == "delete":
        return False
    old_paths = {p.old_path for p in plan}
    reserved = {
        p.new_path for p in plan if getattr(p, "action", "rename") != "delete" and p is not item
    }
    new_path = _allocate_unique_path(
        item.new_path,
        reserved=reserved,
        old_paths=old_paths,
        strategy="duplicates_folder",
    )
    if new_path == item.new_path:
        return False
    item.new_path = new_path
    refresh_plan_conflicts(plan)
    return True


def set_plan_item_target_path(item: PlanItem, new_path: Path, plan: list[PlanItem]) -> None:
    item.new_path = _normalize_fs_path(Path(new_path))
    refresh_plan_conflicts(plan)


def remove_plan_items_at_indices(plan: list[PlanItem], indices: Iterable[int]) -> int:
    """Usuń pozycje z planu (pomiń w operacji). Zwraca liczbę usuniętych."""
    to_remove = sorted({i for i in indices if 0 <= i < len(plan)}, reverse=True)
    for idx in to_remove:
        plan.pop(idx)
    if to_remove:
        refresh_plan_conflicts(plan)
    return len(to_remove)


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
    # Per SZPIEG Build Spec + Plan review 2026-06-15 (organizer improvements) + "must document identical".
    # Dynamically support more Track fields for patterns (fixes limited mapping)
    # e.g. now supports {year}, {tracknumber}, {albumartist}, {composer} etc.
    # Enhanced for organizer: supports {field|default}, {field:02d} padding, basic conditional {field?val:}.
    # Creative robust parser added while keeping 100% backward compat for old simple {field} patterns.
    dynamic_fields = [
        "artist", "title", "album", "albumartist", "genre", "bpm", "key",
        "year", "tracknumber", "discnumber", "composer", "remixer",
        "originalartist", "publisher", "isrc", "comment", "mood", "energy",
    ]
    mapping = {
        "index": str(index),
    }
    if "{index:03}" in pattern:
        mapping["index:03"] = f"{index:03d}"

    for field in dynamic_fields:
        raw = getattr(track, field, None)
        if field in ("bpm", "energy") and raw is not None:
            try:
                raw = f"{float(raw):.1f}".rstrip("0").rstrip(".")
            except Exception:
                raw = str(raw or "")
        mapping[field] = _cleanup_metadata_fragment(str(raw or ""))

    result = pattern

    # Support advanced syntax for organizer (creative enhancement, backward safe):
    # 1. {field|default} fallback
    for key, value in list(mapping.items()):
        result = re.sub(rf"\{{{key}\|([^}}]+)\}}", value or r"\1", result)
    # 2. {field:02d} style padding (for numeric like tracknumber:02)
    for key, value in list(mapping.items()):
        m = re.search(rf"\{{{key}:(\d+)d\}}", result)
        if m and value and value.isdigit():
            width = int(m.group(1))
            result = result.replace(m.group(0), f"{int(value):0{width}d}")
    # 3. Simple conditional {field?value:}  (if field truthy use value else empty)
    for key, value in list(mapping.items()):
        if value:
            result = re.sub(rf"\{{{key}\?([^:}}]+):?\}}", r"\1", result)
        else:
            result = re.sub(rf"\{{{key}\?[^}}]*\}}", "", result)

    # Original simple replace for bare {field}
    for key, value in mapping.items():
        result = result.replace(f"{{{key}}}", value)

    # Remove dangling separators caused by empty fields:
    # e.g. " - Tytuł" when artist is empty, or "Artysta - " when title is empty.
    result = re.sub(r"^\s*[-–—|]+\s*", "", result)
    result = re.sub(r"\s*[-–—|]+\s*$", "", result)
    # Collapse multiple consecutive separators: "A -  - B" → "A - B"
    result = re.sub(r"(\s*-\s*){2,}", " - ", result)
    # Fix for empty brackets/parentheses/groups from empty fields e.g. "Artist - Title []" or "A () - B"
    # This addresses pattern bugs with empty fields and special grouping chars.
    result = re.sub(r"\s*[\(\[\{]\s*[\)\]\}]\s*", "", result)
    result = re.sub(r"[\(\[\{]\s*[\)\]\}]", "", result)
    # Clean common leftover seps after brackets removed
    result = re.sub(r"\s*[-–—|]+\s*$", "", result)
    result = re.sub(r"^\s*[-–—|]+\s*", "", result)
    result = re.sub(r"\s+", " ", result)
    return result.strip(" .-_") or f"track_{index}"

# Presets for organizer (inspired by SZPIEG research: beets, Picard, MediaMonkey, Rekordbox, etc.)
# Exposed for UI presets combo and reuse. Creative addition for better UX.
ORGANIZE_PRESETS: dict[str, dict[str, str]] = {
    "Rekordbox-like": {
        "folder": "{genre}/{artist}/{album} ({year})",
        "filename": "{tracknumber:02} - {title}",
    },
    "Genre / Artist / Album": {
        "folder": "{genre}/{artist}/{album}",
        "filename": "{artist} - {title}",
    },
    "Year - Artist - Album": {
        "folder": "{year}/{artist}/{album}",
        "filename": "{tracknumber:02} - {title}",
    },
    "Simple Artist/Album": {
        "folder": "{artist}/{album}",
        "filename": "{title}",
    },
    "Electronic / BPM - Title": {
        "folder": "{genre}/{bpm} BPM",
        "filename": "{artist} - {title}",
    },
}

def get_organize_presets() -> dict[str, dict[str, str]]:
    """Return copy of organizer folder/filename presets for UI (per SZPIEG 2026-06-15 Build Spec)."""
    return {k: v.copy() for k, v in ORGANIZE_PRESETS.items()}


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


# ============================================================
# FILE MANAGER / LIBRARY ORGANIZER (integrated into renamer module per no-new-files rule)
# Organizes updated audio files after autotag/rename into structured folders based on tags.
# Supports move/copy, custom folder structure e.g. {genre}/{artist}/{album} ({year}),
# preview, conflict detection (intra-plan + FS), undo-ish (reverts moves), updates repo.
# ============================================================

@dataclass
class OrganizePlanItem:
    old_path: Path
    new_path: Path
    action: str = "move"  # "move", "copy", or "delete" (for post-tag cleanup)
    conflict: bool = False
    reason: str | None = None


@dataclass
class OrganizeApplyResult:
    history: list[dict[str, str]]
    errors: list[str]
    skipped: int = 0


def _normalize_fs_path(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path.expanduser().absolute()


def _audio_suffix(path: Path) -> str:
    if path.suffix:
        return path.suffix.lower()
    return ".mp3"


def _verify_audio_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Plik nie istnieje: {path}")
    if path.stat().st_size < 1:
        raise ValueError(f"Plik jest pusty: {path}")


def _safe_move_file(src: Path, dst: Path) -> None:
    """Przeniesienie z fallbackiem copy+unlink (różne wolumeny Windows)."""
    _verify_audio_file(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(f"Cel już istnieje: {dst}")
    try:
        src.rename(dst)
    except OSError:
        shutil.copy2(src, dst)
        _verify_audio_file(dst)
        src.unlink()
    _verify_audio_file(dst)


def _safe_copy_file(src: Path, dst: Path) -> None:
    _verify_audio_file(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(f"Cel już istnieje: {dst}")
    shutil.copy2(src, dst)
    _verify_audio_file(dst)


def _render_structure_segment(track: Track, segment: str, index: int) -> str:
    """Render one folder segment, reusing cleanup. Empty -> 'Unknown' for structure."""
    # Use the improved _render_pattern logic but for single segment (no index usually)
    rendered = _render_pattern(track, segment, index)
    cleaned = _sanitize_filename(rendered)
    if not cleaned or cleaned == "untitled" or cleaned.lower().startswith("track"):
        cleaned = "Unknown"
    return cleaned


def build_organize_plan(
    tracks: Iterable[Track],
    folder_structure: str,
    filename_pattern: str,
    target_base: Path,
    action: str = "move",
) -> list[OrganizePlanItem]:
    """Build plan for batch organize into tag-based folder tree.
    folder_structure e.g. "{genre}/{artist}/{album} ({year})" or "{genre}/{artist}"
    filename_pattern e.g. "{artist} - {title}" or "{tracknumber:02} - {title}"
    Creates subfolders under target_base. Supports move (default, updates library path), copy (adds duplicate entry), or delete (post-tagging cleanup, removes from FS + DB).
    For delete, folder_structure/filename_pattern are ignored.
    """
    prepared: list[OrganizePlanItem] = []
    target_base = _normalize_fs_path(Path(target_base))
    for index, track in enumerate(tracks, 1):
        old_path = _normalize_fs_path(Path(track.path))
        if action == "delete":
            # For delete, ignore folder/fname templates. Mark for removal.
            prepared.append(
                OrganizePlanItem(
                    old_path=old_path,
                    new_path=old_path,  # dummy, not used
                    action="delete",
                    conflict=False,
                    reason=None,
                )
            )
            continue

        # Render folder parts - split by / or \ , render/sanitize each
        structure = folder_structure.strip().replace("\\", "/")
        if not structure:
            structure = "{genre}/{artist}"
        parts = [p for p in structure.split("/") if p]
        folder_rel_parts: list[str] = []
        for part_tmpl in parts:
            seg = _render_structure_segment(track, part_tmpl, index)
            folder_rel_parts.append(seg)
        folder_rel = Path(*folder_rel_parts) if folder_rel_parts else Path(".")

        # Filename
        fname = _render_pattern(track, filename_pattern or "{artist} - {title}", index)
        fname = _sanitize_filename(fname)
        if not fname or fname == "untitled":
            fname = f"track_{index}"
        suffix = _audio_suffix(old_path)
        new_name = f"{fname}{suffix}"
        new_path = _normalize_fs_path(target_base / folder_rel / new_name)

        prepared.append(
            OrganizePlanItem(
                old_path=old_path,
                new_path=new_path,
                action=action,
                conflict=False,
                reason=None,
            )
        )

    # Detect conflicts similar to rename
    old_paths = {item.old_path for item in prepared}
    target_count: dict[Path, int] = {}
    for item in prepared:
        if item.action != "delete":
            target_count[item.new_path] = target_count.get(item.new_path, 0) + 1

    plan: list[OrganizePlanItem] = []
    for item in prepared:
        conflict = False
        reason = None
        if item.action == "delete":
            # Delete has no target conflict (existence checked at apply time)
            pass
        elif target_count.get(item.new_path, 0) > 1:
            conflict = True
            reason = "Konflikt nazwy w planie"
        elif item.new_path.exists() and item.new_path != item.old_path and item.new_path not in old_paths:
            conflict = True
            reason = "Plik już istnieje w docelowej lokalizacji"
        elif item.action == "move" and item.new_path.parent == item.old_path.parent and item.new_path.name == item.old_path.name:
            # no-op same location
            pass
        plan.append(
            OrganizePlanItem(
                old_path=item.old_path,
                new_path=item.new_path,
                action=item.action,
                conflict=conflict,
                reason=reason,
            )
        )
    return plan


def apply_organize_plan(
    plan: Iterable[OrganizePlanItem],
    *,
    do_write_tags: bool = False,
    track_lookup: dict[str, Track] | None = None,
) -> OrganizeApplyResult:
    """Wykonaj organizację: move/copy/delete na FS. DB aktualizuje wyłącznie caller po weryfikacji."""
    plan_list = list(plan)
    executable = []
    skipped = 0
    for item in plan_list:
        if item.conflict:
            skipped += 1
            continue
        old = _normalize_fs_path(item.old_path)
        new = _normalize_fs_path(item.new_path)
        if item.action == "delete":
            if old.exists():
                executable.append(item)
            else:
                skipped += 1
        elif old.exists() and old != new:
            executable.append(item)
        else:
            skipped += 1

    if not executable:
        _store_organize_history([])
        return OrganizeApplyResult(history=[], errors=[], skipped=skipped)

    history: list[dict[str, str]] = []
    errors: list[str] = []
    completed_moves: list[tuple[Path, Path]] = []

    for item in executable:
        old = _normalize_fs_path(item.old_path)
        new = _normalize_fs_path(item.new_path)
        try:
            if item.action == "delete":
                if not old.is_file():
                    raise FileNotFoundError(f"Plik nie istnieje: {old}")
                old.unlink()
                hist_entry = {"old": str(old), "new": "", "action": "delete"}
            elif item.action == "copy":
                _safe_copy_file(old, new)
                hist_entry = {"old": str(old), "new": str(new), "action": "copy"}
            else:
                _safe_move_file(old, new)
                completed_moves.append((old, new))
                hist_entry = {"old": str(old), "new": str(new), "action": "move"}

            if do_write_tags and track_lookup and item.action != "delete":
                lookup_keys = {str(old), str(item.old_path), str(_normalize_fs_path(item.old_path))}
                tr = None
                for key in lookup_keys:
                    tr = track_lookup.get(key)
                    if tr:
                        break
                if tr:
                    tags: dict[str, str] = {}
                    for fld in (
                        "title", "artist", "album", "albumartist", "genre", "year",
                        "bpm", "key", "tracknumber", "discnumber", "composer", "remixer",
                        "originalartist", "publisher", "isrc", "comment", "lyrics", "mood", "energy",
                    ):
                        val = getattr(tr, fld, None)
                        if val is not None:
                            tags[fld] = str(val)
                    if getattr(tr, "rating", 0):
                        tags["rating"] = str(tr.rating)
                    try:
                        from core.audio import write_tags as _wt

                        _wt(Path(hist_entry["new"]), tags)
                    except Exception as we:
                        errors.append(f"write_tags {Path(hist_entry['new']).name}: {we}")

            history.append(hist_entry)
        except Exception as e:
            errors.append(f"{item.action} {old.name} -> {new}: {e}")
            for src, dst in reversed(completed_moves):
                try:
                    if dst.exists() and not src.exists():
                        _safe_move_file(dst, src)
                except Exception:
                    pass
            completed_moves.clear()
            history.clear()
            break

    _store_organize_history(history)
    return OrganizeApplyResult(history=history, errors=errors, skipped=skipped)


def undo_last_organize() -> list[dict[str, str]]:
    """Undo-ish for last organize: revert moves by renaming back (copies are left as-is, 'undo' for copies would delete which is risky).
    Clears the organize history.
    """
    history = _load_organize_history()
    reverted: list[dict[str, str]] = []
    for entry in reversed(history):
        if entry.get("action") != "move":
            continue
        old = Path(entry["old"])
        new = Path(entry["new"])
        if new.exists() and not old.exists():
            try:
                new.rename(old)
                reverted.append(entry)
            except Exception:
                pass
    _store_organize_history([])
    return reverted


def _organize_history_path() -> Path:
    return cache_dir() / "organize_history.json"


def _store_organize_history(history: list[dict[str, str]]) -> None:
    path = _organize_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_organize_history() -> list[dict[str, str]]:
    path = _organize_history_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


# Convenience: organize_tracks high level (used by UI/tests)
def organize_tracks(
    tracks: list[Track],
    folder_structure: str,
    filename_pattern: str,
    target_base: str | Path,
    action: str = "move",
    do_write_tags: bool = False,
) -> tuple[list[OrganizePlanItem], list[dict[str, str]]]:
    """High-level: build + apply. Returns (plan, history). Caller responsible for repo updates after.
    """
    plan = build_organize_plan(tracks, folder_structure, filename_pattern, Path(target_base), action)
    track_lookup: dict[str, Track] = {}
    for t in tracks:
        p = _normalize_fs_path(Path(t.path))
        track_lookup[str(p)] = t
        track_lookup[str(t.path)] = t
    result = apply_organize_plan(plan, do_write_tags=do_write_tags, track_lookup=track_lookup)
    return plan, result
