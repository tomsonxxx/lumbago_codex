"""
Abstract Base Class / Protocol for audio playback backends.

This is the contract that all concrete implementations (VLC, QtMultimedia, future)
must honor. It is intentionally free of any UI framework, Qt signals, or
platform-specific audio details.

All implementations must be thread-safe for read operations and callback
registration. Write operations (play/seek/etc.) are expected to be called
from a single "owner" thread (typically the main UI thread).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .types import (
    BackendErrorCode,
    DeckState,
    EndReachedCallback,
    PlaybackState,
    PositionCallback,
)


logger = logging.getLogger(__name__)


class AudioBackend(ABC):
    """
    Abstract audio playback backend for a single independent deck.

    Key contracts:
    - load(path) → bool
    - Full transport control + DJ parameters (rate, keylock, 3-band EQ, balance)
    - Loop points with automatic enforcement inside the backend (tight timing)
    - Thread-safe getters + optional position/end callbacks (callbacks may arrive
      from worker threads — caller must marshal to UI thread if needed)
    - First-class error model via DeckState + get_last_error()
    - Proper lifecycle: always call release() when done (supports context manager)
    - Diagnostics for troubleshooting missing/corrupt backends (especially VLC)
    """

    # ------------------------------------------------------------------
    # Class-level availability (cheap probe, no side effects on success path)
    # ------------------------------------------------------------------
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if this backend can be instantiated and used right now."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._position_callback: Optional[PositionCallback] = None
        self._end_reached_callback: Optional[EndReachedCallback] = None

    def __enter__(self) -> AudioBackend:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    @abstractmethod
    def release(self) -> None:
        """Release all native resources. Safe to call multiple times."""
        ...

    def close(self) -> None:
        """Alias for release() for compatibility with contextlib."""
        self.release()

    # ------------------------------------------------------------------
    # Diagnostics & Errors (first-class citizens)
    # ------------------------------------------------------------------
    @abstractmethod
    def get_diagnostics(self) -> dict:
        """
        Rich diagnostic information useful for logs, health dashboard, and
        user-facing error messages.

        Must be safe to call even when backend failed to initialize.
        Example keys: "backend", "version", "available", "last_error",
        "plugin_path", "discovered_locations", "scaletempo_available"...
        """
        ...

    @abstractmethod
    def get_last_error(self) -> Optional[str]:
        """Human-readable last error message (or None)."""
        ...

    def get_error_code(self) -> BackendErrorCode:
        """Override in subclasses for precise error categorization."""
        return BackendErrorCode.NONE

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    @abstractmethod
    def load(self, path: str | Path) -> bool:
        """
        Load an audio file from disk.

        Returns True on success (state should become READY or PLAYING).
        On failure: state → ERROR, populate last_error + diagnostics.
        Must be idempotent for the same path.
        """
        ...

    def unload(self) -> None:
        """Optional: unload current media while keeping backend alive. Default no-op."""
        pass

    # ------------------------------------------------------------------
    # Transport controls
    # ------------------------------------------------------------------
    @abstractmethod
    def play(self) -> None:
        ...

    @abstractmethod
    def pause(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    def toggle_play(self) -> bool:
        """Convenience: returns True if now playing."""
        if self.is_playing():
            self.pause()
            return False
        else:
            self.play()
            return True

    @abstractmethod
    def seek(self, position_ms: int) -> None:
        """Seek to absolute position in milliseconds. Clamped to [0, duration]."""
        ...

    # ------------------------------------------------------------------
    # Read-only state (thread-safe)
    # ------------------------------------------------------------------
    @abstractmethod
    def get_position_ms(self) -> int:
        ...

    @abstractmethod
    def get_duration_ms(self) -> int:
        ...

    @abstractmethod
    def is_playing(self) -> bool:
        ...

    def get_state(self) -> DeckState:
        """
        Return an atomic snapshot of the current deck state.
        Subclasses should override for richer data; default implementation
        builds a minimal snapshot from the basic getters.
        """
        playing = self.is_playing()
        state = PlaybackState.PLAYING if playing else PlaybackState.READY
        if self.get_duration_ms() == 0 and self.get_position_ms() == 0:
            state = PlaybackState.IDLE

        return DeckState(
            state=state,
            is_playing=playing,
            position_ms=self.get_position_ms(),
            duration_ms=self.get_duration_ms(),
            volume=self.get_volume(),
            rate=self.get_rate(),
            error_code=self.get_error_code(),
            last_error=self.get_last_error(),
            # error_code/last_error explicit per SZPIEG research 2026-06-15 playback reliability + finalny efekt (visible '⚠' + guidance no silent) + must document identical
        )

    # ------------------------------------------------------------------
    # DJ Parameters
    # ------------------------------------------------------------------
    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """0.0 (silent) to 1.0 (full). Implementations should clamp."""
        ...

    @abstractmethod
    def get_volume(self) -> float:
        ...

    @abstractmethod
    def set_balance(self, balance: float) -> None:
        """-1.0 = full left, 0.0 = center, +1.0 = full right."""
        ...

    def get_balance(self) -> float:
        """Default implementation returns center. Override if supported."""
        return 0.0

    @abstractmethod
    def set_rate(self, rate: float) -> None:
        """Playback rate. 1.0 = normal. Typical DJ range 0.5–2.0."""
        ...

    @abstractmethod
    def get_rate(self) -> float:
        ...

    @abstractmethod
    def set_keylock_enabled(self, enabled: bool) -> None:
        """
        When True, attempt to change tempo without changing pitch (keylock).
        Backends that cannot fully support this should still change tempo
        and expose the limitation via diagnostics + log warning.
        """
        ...

    def is_keylock_enabled(self) -> bool:
        return False

    @abstractmethod
    def set_eq(self, low_db: float, mid_db: float, high_db: float) -> None:
        """3-band EQ in decibels. Typical useful range -12.0 to +12.0."""
        ...

    def reset_eq(self) -> None:
        """Reset EQ to flat. Default calls set_eq(0,0,0)."""
        self.set_eq(0.0, 0.0, 0.0)

    # ------------------------------------------------------------------
    # Loop points (backend-enforced for low jitter)
    # ------------------------------------------------------------------
    @abstractmethod
    def set_loop_points(self, start_ms: Optional[int], end_ms: Optional[int]) -> None:
        """
        Set loop region. Both values in milliseconds from start of track.
        Passing None clears the point. Invalid ranges are clamped or ignored.
        """
        ...

    @abstractmethod
    def set_loop_enabled(self, enabled: bool) -> None:
        """Enable/disable automatic looping when playback reaches loop_end."""
        ...

    def is_loop_enabled(self) -> bool:
        return False

    def get_loop_points(self) -> tuple[Optional[int], Optional[int]]:
        """Return (start_ms, end_ms) or (None, None)."""
        return (None, None)

    # ------------------------------------------------------------------
    # Callbacks (threading contract is critical — see class docstring)
    # ------------------------------------------------------------------
    def set_position_callback(self, callback: Optional[PositionCallback]) -> None:
        """
        Register a callback that will be invoked with the current position (ms)
        at regular intervals while playing (typically 20-60 Hz).

        The callback may be invoked from a background thread.
        The implementation must never block inside the callback.
        """
        self._position_callback = callback

    def set_end_reached_callback(self, callback: Optional[EndReachedCallback]) -> None:
        """
        Called (approximately) when natural playback reaches the end of the file
        or a loop boundary (if loops are not enabled).
        May be called from background thread.
        """
        self._end_reached_callback = callback

    # ------------------------------------------------------------------
    # Internal helpers for subclasses
    # ------------------------------------------------------------------
    def _invoke_position_callback(self, position_ms: int) -> None:
        if self._position_callback is not None:
            try:
                self._position_callback(position_ms)
            except Exception:
                logger.exception("Position callback raised an exception")

    def _invoke_end_reached_callback(self) -> None:
        if self._end_reached_callback is not None:
            try:
                self._end_reached_callback()
            except Exception:
                logger.exception("End-reached callback raised an exception")
