"""
Playback backend types, enums, and data structures.

UI-agnostic. Safe to import from any thread.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional


class PlaybackState(Enum):
    """Canonical playback state for a single deck."""
    IDLE = auto()       # No media loaded
    LOADING = auto()    # Media is being parsed / prepared
    READY = auto()      # Loaded and ready to play (stopped at position 0 or cue)
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()    # Stopped after explicit stop (position may be non-zero)
    ERROR = auto()      # Unrecoverable error for this deck (see last_error)


class BackendErrorCode(Enum):
    """Machine-readable error categories."""
    NONE = auto()
    BACKEND_UNAVAILABLE = auto()   # VLC / QtMultimedia not present or failed init
    VLC_MISSING_DLL = auto()
    VLC_INIT_FAILED = auto()
    VLC_PLUGIN_PATH = auto()
    FILE_NOT_FOUND = auto()
    UNSUPPORTED_FORMAT = auto()
    PARSE_FAILED = auto()          # Duration / metadata parse timeout
    PLAYBACK_FAILED = auto()
    SEEK_FAILED = auto()
    RESOURCE_EXHAUSTED = auto()    # e.g. too many instances
    UNKNOWN = auto()


@dataclass(frozen=True)
class DeckState:
    """
    Immutable snapshot of a deck's state.
    Safe to read from any thread.
    Per SZPIEG research 2026-06-15 playback reliability + finalny efekt końcowy (no silent, visible error_code + last_error + install guidance "Pobierz VLC", graceful + targeted + file/stream guards, EFFECT, booth) + must document identical.
    """
    state: PlaybackState
    is_playing: bool = False
    position_ms: int = 0
    duration_ms: int = 0
    volume: float = 1.0           # 0.0 .. 1.0
    error_code: BackendErrorCode = BackendErrorCode.NONE
    last_error: Optional[str] = None
    # active_backend surfaced for UI status/diagnostics (VLC / qtmultimedia / noop)
    balance: float = 0.0          # -1.0 (full left) .. +1.0 (full right)
    rate: float = 1.0             # Playback rate multiplier
    keylock_enabled: bool = False
    loop_enabled: bool = False
    loop_start_ms: Optional[int] = None
    loop_end_ms: Optional[int] = None
    error_code: BackendErrorCode = BackendErrorCode.NONE
    error_message: Optional[str] = None
    # Extra diagnostic info (backend-specific, may be large)
    extra: dict = field(default_factory=dict)


# Callback types (callers must be thread-aware)
PositionCallback = Callable[[int], None]          # receives current position in ms
EndReachedCallback = Callable[[], None]


@dataclass
class BackendInfo:
    """Static information returned by diagnostics."""
    backend_name: str
    version: Optional[str] = None
    available: bool = False
    details: dict = field(default_factory=dict)
