"""
Lumbago Music AI — Professional Audio Playback Backend

Clean, robust, UI-agnostic foundation for dual-deck DJ playback.

Public API (recommended imports):
    from services.playback import (
        AudioBackend,
        PlaybackEngine,
        create_backend,
        VlcAudioBackend,
        QtAudioBackend,
        PlaybackState,
        DeckState,
        BackendErrorCode,
    )

Factory helper `create_backend()` chooses the best available implementation
with graceful fallback (VLC → QtMultimedia → silent no-op).

See DESIGN.md in this package for full architecture, threading contract,
and integration guidance with core.models.Track / CuePoint / BeatMarker.
"""
from __future__ import annotations

from typing import Callable, Optional

from .base import AudioBackend
from .engine import PlaybackEngine
from .qt_backend import QtAudioBackend
from .types import (
    BackendErrorCode,
    BackendInfo,
    DeckState,
    PlaybackState,
)
from .vlc_backend import VlcAudioBackend

__version__ = "1.0.0"
__all__ = [
    "AudioBackend",
    "PlaybackEngine",
    "create_backend",
    "get_available_backends",
    "VlcAudioBackend",
    "QtAudioBackend",
    "PlaybackState",
    "DeckState",
    "BackendErrorCode",
    "BackendInfo",
]


def create_backend(prefer: str = "auto") -> AudioBackend:
    """
    Create the best available audio backend for a single deck.

    VLC is ALWAYS preferred over Qt when present (unless explicitly prefer="qt" or "noop").
    This guarantees professional DJ features (EQ, keylock/scaletempo, low-jitter loops) on target systems.

    Args:
        prefer: "auto" | "vlc" | "qt" | "noop"

    Returns:
        Concrete AudioBackend instance (never raises for missing backends).
    """
    vlc_ok = VlcAudioBackend.is_available()
    qt_ok = QtAudioBackend.is_available()

    # Strong VLC preference for pro DJ use (rock-solid requirement)
    if prefer in ("auto", "vlc"):
        if vlc_ok:
            try:
                return VlcAudioBackend()
            except Exception:
                pass  # fallthrough to next

    if prefer == "qt":
        if qt_ok:
            try:
                return QtAudioBackend()
            except Exception:
                pass

    if prefer in ("auto", "qt") and qt_ok:
        # Only reach here for auto if VLC failed above
        try:
            return QtAudioBackend()
        except Exception:
            pass

    if prefer == "noop":
        pass

    # Ultimate safe fallback (never fails, produces no sound)
    from .engine import _NoopAudioBackend
    return _NoopAudioBackend()


def get_available_backends() -> list[str]:
    """Return list of backend names that can currently be instantiated."""
    available = []
    if VlcAudioBackend.is_available():
        available.append("vlc")
    if QtAudioBackend.is_available():
        available.append("qt")
    available.append("noop")
    return available
