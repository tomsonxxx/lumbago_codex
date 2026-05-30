"""
PlaybackEngine — coordinates two independent decks + mixing.

This is the primary high-level API that the UI layer (DJ player window,
mixer widgets, etc.) should consume.

It is completely UI-agnostic and backend-agnostic (uses the factory).

Crossfader, master volume, per-deck trims, and convenience methods live here.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Literal, Optional

from .base import AudioBackend
from .qt_backend import QtAudioBackend
from .types import DeckState
from .vlc_backend import VlcAudioBackend

logger = logging.getLogger(__name__)


DeckName = Literal["A", "B"]


class PlaybackEngine:
    """
    Dual-deck playback coordinator.

    Example:
        engine = PlaybackEngine()                    # auto-select best backend
        engine = PlaybackEngine(backend_factory=lambda: VlcAudioBackend())

        engine.load_deck("A", "/music/track.mp3")
        engine.play_deck("A")
        engine.set_crossfader(0.4)                   # favor deck B a bit
        engine.set_deck_volume("A", 0.85)            # trim
    """

    def __init__(
        self,
        backend_factory: Optional[Callable[[], AudioBackend]] = None,
    ):
        self._factory = backend_factory or self._default_factory

        self.deck_a: AudioBackend = self._factory()
        self.deck_b: AudioBackend = self._factory()

        self._crossfader: float = 0.0          # -1.0 (A) ... 0.0 (center) ... +1.0 (B)
        self._master_volume: float = 1.0
        self._deck_trim_a: float = 1.0
        self._deck_trim_b: float = 1.0

        self._curve: str = "constant_power"    # or "linear"

        logger.info(
            f"PlaybackEngine created with decks: "
            f"A={self.deck_a.__class__.__name__}, B={self.deck_b.__class__.__name__}"
        )

    @staticmethod
    def _default_factory() -> AudioBackend:
        """Prefer VLC, fall back to Qt, then a safe no-op."""
        if VlcAudioBackend.is_available():
            try:
                return VlcAudioBackend()
            except Exception as e:
                logger.warning(f"VLC backend instantiation failed: {e}")

        if QtAudioBackend.is_available():
            try:
                return QtAudioBackend()
            except Exception as e:
                logger.warning(f"Qt backend instantiation failed: {e}")

        # Last resort — completely silent no-op backend (useful for tests/CI)
        return _NoopAudioBackend()

    # ------------------------------------------------------------------
    # Deck access
    # ------------------------------------------------------------------
    def deck(self, name: DeckName) -> AudioBackend:
        if name == "A":
            return self.deck_a
        elif name == "B":
            return self.deck_b
        raise ValueError(f"Invalid deck name: {name}. Use 'A' or 'B'.")

    # ------------------------------------------------------------------
    # High-level convenience (recommended for UI)
    # ------------------------------------------------------------------
    def load_deck(self, deck: DeckName, path: str | Path) -> bool:
        return self.deck(deck).load(path)

    def play_deck(self, deck: DeckName) -> None:
        self.deck(deck).play()

    def pause_deck(self, deck: DeckName) -> None:
        self.deck(deck).pause()

    def stop_deck(self, deck: DeckName) -> None:
        self.deck(deck).stop()

    def seek_deck(self, deck: DeckName, position_ms: int) -> None:
        self.deck(deck).seek(position_ms)

    def toggle_deck(self, deck: DeckName) -> bool:
        return self.deck(deck).toggle_play()

    # ------------------------------------------------------------------
    # Mixing
    # ------------------------------------------------------------------
    def set_crossfader(self, position: float) -> None:
        """
        -1.0 = full A, 0.0 = center (both audible), +1.0 = full B.
        Actual per-deck volumes are recomputed immediately.
        """
        pos = max(-1.0, min(1.0, float(position)))
        self._crossfader = pos
        self._apply_mixing()

    def get_crossfader(self) -> float:
        return self._crossfader

    def set_master_volume(self, volume: float) -> None:
        self._master_volume = max(0.0, min(1.0, float(volume)))
        self._apply_mixing()

    def get_master_volume(self) -> float:
        return self._master_volume

    def set_deck_trim(self, deck: DeckName, trim: float) -> None:
        """Per-deck volume trim (multiplicative, independent of crossfader)."""
        t = max(0.0, min(2.0, float(trim)))  # allow +6 dB headroom
        if deck == "A":
            self._deck_trim_a = t
        else:
            self._deck_trim_b = t
        self._apply_mixing()

    def set_deck_volume(self, deck: DeckName, volume: float) -> None:
        """Direct absolute volume for a deck (ignores crossfader temporarily)."""
        v = max(0.0, min(1.0, float(volume)))
        self.deck(deck).set_volume(v)

    def set_deck_balance(self, deck: DeckName, balance: float) -> None:
        self.deck(deck).set_balance(balance)

    def set_deck_rate(self, deck: DeckName, rate: float) -> None:
        self.deck(deck).set_rate(rate)

    def set_deck_keylock(self, deck: DeckName, enabled: bool) -> None:
        self.deck(deck).set_keylock_enabled(enabled)

    def set_deck_eq(self, deck: DeckName, low: float, mid: float, high: float) -> None:
        self.deck(deck).set_eq(low, mid, high)

    def set_deck_loop(self, deck: DeckName, start_ms: int | None, end_ms: int | None) -> None:
        self.deck(deck).set_loop_points(start_ms, end_ms)

    def enable_deck_loop(self, deck: DeckName, enabled: bool) -> None:
        self.deck(deck).set_loop_enabled(enabled)

    def clear_deck_loop(self, deck: DeckName) -> None:
        """Convenience: disable loop and clear points."""
        d = self.deck(deck)
        d.set_loop_enabled(False)
        d.set_loop_points(None, None)

    # ------------------------------------------------------------------
    # Convenience getters (symmetric to setters for UI / diagnostics)
    # ------------------------------------------------------------------
    def get_deck_volume(self, deck: DeckName) -> float:
        """Effective volume on the deck (includes last crossfader/trim/master application)."""
        return self.deck(deck).get_volume()

    def get_deck_trim(self, deck: DeckName) -> float:
        if deck == "A":
            return self._deck_trim_a
        return self._deck_trim_b

    def get_deck_balance(self, deck: DeckName) -> float:
        return self.deck(deck).get_balance()

    def get_deck_rate(self, deck: DeckName) -> float:
        return self.deck(deck).get_rate()

    def get_deck_keylock(self, deck: DeckName) -> bool:
        return self.deck(deck).is_keylock_enabled()

    def reset_deck_eq(self, deck: DeckName) -> None:
        self.deck(deck).reset_eq()

    def get_deck_loop_points(self, deck: DeckName) -> tuple[Optional[int], Optional[int]]:
        return self.deck(deck).get_loop_points()

    def is_deck_loop_enabled(self, deck: DeckName) -> bool:
        return self.deck(deck).is_loop_enabled()

    # ------------------------------------------------------------------
    # State & diagnostics (delegation)
    # ------------------------------------------------------------------
    def get_deck_state(self, deck: DeckName) -> DeckState:
        return self.deck(deck).get_state()

    def get_diagnostics(self) -> dict:
        return {
            "engine": "PlaybackEngine",
            "deck_a": self.deck_a.get_diagnostics(),
            "deck_b": self.deck_b.get_diagnostics(),
            "crossfader": self._crossfader,
            "master_volume": self._master_volume,
        }

    def release_all(self) -> None:
        """Release both decks. Call on application shutdown."""
        try:
            self.deck_a.release()
        except Exception:
            pass
        try:
            self.deck_b.release()
        except Exception:
            pass
        logger.info("PlaybackEngine released both decks")

    # ------------------------------------------------------------------
    # Internal mixing engine
    # ------------------------------------------------------------------
    def _apply_mixing(self) -> None:
        """Compute final volumes for both decks from crossfader + trims + master."""
        pos = self._crossfader

        # Crossfader contribution (equal-power approximation)
        if self._curve == "constant_power":
            # Smooth constant-power curve
            a_cross = (1.0 - pos) ** 0.5 if pos > 0 else 1.0
            b_cross = (1.0 + pos) ** 0.5 if pos < 0 else 1.0
        else:
            # Linear (simpler, more abrupt in center)
            a_cross = max(0.0, 1.0 - max(0.0, pos))
            b_cross = max(0.0, 1.0 + min(0.0, pos))

        vol_a = self._master_volume * self._deck_trim_a * a_cross
        vol_b = self._master_volume * self._deck_trim_b * b_cross

        # Clamp and apply
        self.deck_a.set_volume(max(0.0, min(1.0, vol_a)))
        self.deck_b.set_volume(max(0.0, min(1.0, vol_b)))


# ----------------------------------------------------------------------
# Private no-op backend (last-resort fallback, never fails)
# ----------------------------------------------------------------------

class _NoopAudioBackend(AudioBackend):
    """Completely silent backend used when nothing else is available (tests, CI, headless)."""

    def __init__(self):
        super().__init__()
        self._diagnostics = {"backend": "noop", "initialized": True, "warning": "No audio output available"}
        self._rate = 1.0
        self._volume = 1.0
        self._keylock = False
        self._loop_start: int | None = None
        self._loop_end: int | None = None
        self._loop_enabled: bool = False

    @classmethod
    def is_available(cls) -> bool:
        return True

    def release(self) -> None:
        pass

    def get_diagnostics(self) -> dict:
        return self._diagnostics

    def get_last_error(self) -> Optional[str]:
        return None

    def load(self, path: str | Path) -> bool:
        return False  # Can't actually play anything

    def play(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def seek(self, position_ms: int) -> None:
        pass

    def get_position_ms(self) -> int:
        return 0

    def get_duration_ms(self) -> int:
        return 0

    def is_playing(self) -> bool:
        return False

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, float(volume)))

    def get_volume(self) -> float:
        return getattr(self, "_volume", 1.0)

    def set_balance(self, balance: float) -> None:
        pass

    def set_rate(self, rate: float) -> None:
        r = max(0.1, min(8.0, float(rate)))
        self._rate = r   # track for test fidelity / convenience getters

    def get_rate(self) -> float:
        return getattr(self, "_rate", 1.0)

    def set_keylock_enabled(self, enabled: bool) -> None:
        self._keylock = bool(enabled)

    def is_keylock_enabled(self) -> bool:
        return getattr(self, "_keylock", False)

    def set_eq(self, low_db: float, mid_db: float, high_db: float) -> None:
        pass

    def set_loop_points(self, start_ms: Optional[int], end_ms: Optional[int]) -> None:
        self._loop_start = start_ms
        self._loop_end = end_ms

    def set_loop_enabled(self, enabled: bool) -> None:
        self._loop_enabled = bool(enabled)

    def is_loop_enabled(self) -> bool:
        return self._loop_enabled

    def get_loop_points(self) -> tuple[Optional[int], Optional[int]]:
        return (self._loop_start, self._loop_end)

    def get_state(self) -> DeckState:
        from .types import PlaybackState as PS, BackendErrorCode as EC
        return DeckState(
            state=PS.IDLE,
            is_playing=False,
            rate=getattr(self, "_rate", 1.0),
            keylock_enabled=getattr(self, "_keylock", False),
            loop_enabled=self._loop_enabled,
            loop_start_ms=self._loop_start,
            loop_end_ms=self._loop_end,
            volume=getattr(self, "_volume", 1.0),
            error_code=EC.BACKEND_UNAVAILABLE,
            error_message="No audio backend available",
        )
