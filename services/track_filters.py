from __future__ import annotations

from pathlib import Path

from core.audio import AUDIO_EXTENSIONS as CORE_AUDIO_EXTENSIONS

SUPPORTED_AUDIO_EXTENSIONS = {ext.lower() for ext in CORE_AUDIO_EXTENSIONS}
SYSTEM_LIKE_NON_AUDIO_EXTENSIONS = {
    ".bak",
    ".bat",
    ".cmd",
    ".cue",
    ".db",
    ".dll",
    ".exe",
    ".ico",
    ".inf",
    ".ini",
    ".iso",
    ".jpg",
    ".jpeg",
    ".json",
    ".lnk",
    ".log",
    ".m3u",
    ".m3u8",
    ".msi",
    ".nfo",
    ".old",
    ".pdf",
    ".plist",
    ".pls",
    ".png",
    ".ps1",
    ".reg",
    ".sys",
    ".txt",
    ".url",
    ".xml",
}

SYSTEM_FILE_NAMES = {
    "desktop.ini",
    "thumbs.db",
    "autorun.inf",
    ".ds_store",
}

SYSTEM_DIR_MARKERS = {
    "$recycle.bin",
    "recycler",
    "system volume information",
    "windows",
    "windowsapps",
    "winnt",
    "system32",
    "program files",
    "program files (x86)",
    "appdata",
    "localcache",
    "packages",
    "temp",
    "tmp",
    "cache",
}

SYSTEM_NAME_HINTS = {
    "thumb",
    "cache",
    "temp",
    "tmp",
    "desktop",
    "system",
    "installer",
    "update",
    "backup",
    "folder",
    "artwork",
    "cover",
    "playlist",
    "alarm",
    "notification",
    "grammarcheck",
    "monicasearch",
    "quickaction",
    "table-view",
    "sfx",
    "winsxs",
    "windows",
    "windowsapps",
    "appdata",
    "localcache",
    "packages",
    "chrome",
    "edge",
    "browser",
    "onboarding",
    "recommendation",
    "pre recommen",
    "final",
    "claude",
    "ion-dist-audio",
}


def is_audio_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def is_system_like_path(path: str | Path) -> bool:
    """Aggressive import-time filter for obvious system/helper artifacts."""
    path = Path(path)
    suffix = path.suffix.lower()
    name = path.name.lower()
    parts = [part.lower() for part in path.parts]

    if name in SYSTEM_FILE_NAMES or name.startswith("._") or name.startswith("~"):
        return True
    if _path_contains_any_marker(parts, SYSTEM_DIR_MARKERS):
        return True
    if suffix in SYSTEM_LIKE_NON_AUDIO_EXTENSIONS:
        return True

    score = 0
    if any(hint in name for hint in SYSTEM_NAME_HINTS):
        score += 2
    if suffix and suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        score += 1

    try:
        if path.stat().st_size < 250_000:
            score += 1
    except Exception:
        pass

    return score >= 3


def is_system_like_track(track) -> bool:
    """Conservative view-time filter for duplicate lists.

    Real audio tracks stored in e.g. Program Files or Windows folders should
    still remain visible if they look like actual songs with metadata.
    """
    path = Path(getattr(track, "path", track))
    suffix = path.suffix.lower()
    name = path.name.lower()
    parts = [part.lower() for part in path.parts]
    stat = None
    try:
        stat = path.stat()
    except Exception:
        pass

    if name in SYSTEM_FILE_NAMES or name.startswith("._") or name.startswith("~"):
        return True
    if suffix in SYSTEM_LIKE_NON_AUDIO_EXTENSIONS:
        return True

    track_title = getattr(track, "title", None)
    track_artist = getattr(track, "artist", None)
    track_album = getattr(track, "album", None)
    track_duration = getattr(track, "duration", None)
    track_file_size = getattr(track, "file_size", None)
    has_metadata = bool(track_title or track_artist or track_album)
    is_audio = suffix in SUPPORTED_AUDIO_EXTENSIONS
    has_system_path = _path_contains_any_marker(parts, SYSTEM_DIR_MARKERS)
    file_size = track_file_size if isinstance(track_file_size, (int, float)) else None
    if file_size is None and stat is not None:
        file_size = stat.st_size
    is_small = file_size is not None and file_size < 250_000
    is_tiny = file_size is not None and file_size < 80_000
    long_enough = bool(track_duration and track_duration >= 30)
    metadata_blob = " ".join(
        part
        for part in [
            name,
            str(track_title or ""),
            str(track_artist or ""),
            str(track_album or ""),
            str(getattr(track, "comment", "") or ""),
            str(getattr(track, "genre", "") or ""),
        ]
        if part
    ).lower()
    strong_music_signals = (
        is_audio
        and long_enough
        and has_metadata
        and file_size is not None
        and file_size >= 1_500_000
        and not _contains_any(metadata_blob, SYSTEM_NAME_HINTS)
    )

    if not is_audio:
        score = 0
        if has_system_path:
            score += 2
        if any(hint in name for hint in SYSTEM_NAME_HINTS):
            score += 2
        if stat is not None and stat.st_size < 250_000:
            score += 1
        if not has_metadata:
            score += 1
        if not track_duration:
            score += 1
        return score >= 3

    # For audio files we only hide obvious non-music artifacts.
    if not has_system_path:
        return False
    if strong_music_signals:
        return False

    score = 0
    if _contains_any(metadata_blob, SYSTEM_NAME_HINTS):
        score += 2
    if is_small:
        score += 2
    if is_tiny:
        score += 1
    if not has_metadata:
        score += 1
    if not track_duration:
        score += 1
    if has_system_path:
        score += 1
    if long_enough:
        score -= 1
    if has_metadata:
        score -= 1
    if file_size is not None and file_size >= 1_500_000:
        score -= 1

    return score >= 2


def filter_group_rows(
    rows: list[tuple[str, list]],
    *,
    audio_only: bool = False,
    hide_system_like: bool = False,
    excluded_roots: list[str] | None = None,
) -> list[tuple[str, list]]:
    filtered: list[tuple[str, list]] = []
    excluded_roots = excluded_roots or []
    for label, tracks in rows:
        kept = list(tracks)
        if audio_only:
            kept = [track for track in kept if is_audio_file(track.path)]
        if hide_system_like:
            kept = [track for track in kept if not is_system_like_track(track)]
        if excluded_roots:
            kept = [track for track in kept if not is_path_in_excluded_roots(track.path, excluded_roots)]
        if len(kept) > 1:
            filtered.append((label, kept))
    return filtered


def is_path_in_excluded_roots(path: str | Path, excluded_roots: list[str] | list[Path]) -> bool:
    track_path = _normalize_path(path)
    for root in excluded_roots:
        root_path = _normalize_path(root)
        if not root_path:
            continue
        if track_path == root_path or track_path.startswith(root_path + "/"):
            return True
    return False


def _path_contains_any_marker(parts: list[str], markers: set[str]) -> bool:
    for part in parts:
        for marker in markers:
            if marker in part:
                return True
    return False


def _contains_any(blob: str, needles: set[str]) -> bool:
    return any(needle in blob for needle in needles)


def _normalize_path(path: str | Path) -> str:
    normalized = str(Path(path)).replace("\\", "/").rstrip("/ ").lower()
    return normalized
