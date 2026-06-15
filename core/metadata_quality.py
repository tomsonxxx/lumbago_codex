from __future__ import annotations

from pathlib import Path

from core.models import Track


def parent_folder_name(track_path: str | Path | None) -> str | None:
    if not track_path:
        return None
    try:
        name = Path(track_path).parent.name
        return name or None
    except Exception:
        return None


def album_matches_parent_folder(album: str | None, track_path: str | Path | None) -> bool:
    """True when album tag is just the immediate parent directory name (rip/catalog artifact)."""
    if not album or not str(album).strip():
        return False
    parent = parent_folder_name(track_path)
    if not parent:
        return False
    return str(album).strip().casefold() == parent.strip().casefold()


def strip_album_folder_artifact(track: Track) -> bool:
    """Clear album when it mirrors the containing folder. Returns True if cleared."""
    if not track.album:
        return False
    if album_matches_parent_folder(track.album, track.path):
        track.album = None
        return True
    return False