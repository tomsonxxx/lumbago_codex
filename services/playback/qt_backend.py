"""
QtMultimedia fallback backend for users without VLC installed.

This is intentionally a skeleton / compatibility shim.
It allows the rest of the application (waveform viewers, basic transport)
to function in a degraded "preview" mode.

Per SZPIEG research 2026-06-15 playback reliability + finalny efekt końcowy (no silent close; visible '⚠ Audio niedostępne (VLC)' + 'Pobierz VLC (videolan.org)' + portable note; graceful: wave/playhead/cue (FILE ops) live even on ERROR; targeted status; guards; EFFECT tooltips; file=load vs stream=transport explicit; booth high-contrast readable errors; A/B distinction) — must document identical. Binding Build Spec steps 2-3.

Limitations (documented for UI team):
- No professional 3-band EQ (set_eq is a no-op or very crude)
- Playback rate changes pitch (no keylock possible with stock QtMultimedia)
- Balance support varies by platform and Qt version
- Loop implementation relies on Qt timer / polling (higher jitter than VLC)
- Lower audio quality / higher latency than native VLC for DJ use
- Some formats may not be supported depending on installed codecs

If this backend is active, the UI should show prominent warnings + EFFECT that
a proper DJ experience requires VLC (https://www.videolan.org/vlc/ or portable unpack next to exe). Install guidance + last_error surfaced in diagnostics + DeckState.error_code.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Optional

from .base import AudioBackend
from .types import BackendErrorCode, DeckState, PlaybackState

logger = logging.getLogger(__name__)

try:
    from PyQt6 import QtCore, QtMultimedia
    _HAS_QT_MULTIMEDIA = True
except Exception as e:
    QtCore = None  # type: ignore
    QtMultimedia = None  # type: ignore
    _HAS_QT_MULTIMEDIA = False
    _QT_IMPORT_ERROR = str(e)
else:
    _QT_IMPORT_ERROR = ""


class QtAudioBackend(AudioBackend):
    """
    Fallback implementation using QtMultimedia.QMediaPlayer.

    All heavy lifting is done via Qt's own threads/signals where possible.
    We still expose the exact same AudioBackend surface.
    """

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._state = PlaybackState.IDLE
        self._error_code = BackendErrorCode.NONE
        self._last_error: Optional[str] = None
        self._diagnostics = {"backend": "qtmultimedia", "initialized": False}

        self._player: Optional["QtMultimedia.QMediaPlayer"] = None
        self._audio_output: Optional["QtMultimedia.QAudioOutput"] = None
        self._current_path: Optional[str] = None
        self._duration_ms: int = 0
        self._position_ms: int = 0
        self._volume: float = 1.0
        self._balance: float = 0.0
        self._rate: float = 1.0
        self._keylock = False  # Impossible with stock Qt MM — always pitch shifts

        self._loop_start_ms: Optional[int] = None
        self._loop_end_ms: Optional[int] = None
        self._loop_enabled: bool = False

        self._lock = threading.RLock()
        self._poller_stop = threading.Event()
        self._poller_thread: Optional[threading.Thread] = None
        self._last_reported_pos = 0

        if not _HAS_QT_MULTIMEDIA or QtMultimedia is None:
            self._set_error(
                BackendErrorCode.BACKEND_UNAVAILABLE,
                f"QtMultimedia unavailable: {_QT_IMPORT_ERROR}",
            )
            return

        try:
            self._audio_output = QtMultimedia.QAudioOutput()
            self._player = QtMultimedia.QMediaPlayer()
            self._player.setAudioOutput(self._audio_output)

            # Wire Qt signals (these arrive on the thread that owns the QObjects — usually main)
            self._player.durationChanged.connect(self._on_duration_changed)
            self._player.positionChanged.connect(self._on_position_changed)
            self._player.playbackStateChanged.connect(self._on_state_changed)
            self._player.mediaStatusChanged.connect(self._on_media_status_changed)

            self._enabled = True
            self._state = PlaybackState.IDLE
            self._diagnostics.update({"initialized": True, "qt_version": QtCore.QT_VERSION_STR})
            self._start_poller()  # for loop enforcement + extra safety
            logger.info("QtAudioBackend initialized (fallback mode)")
        except Exception as e:
            self._set_error(BackendErrorCode.BACKEND_UNAVAILABLE, f"QtMultimedia init failed: {e}")

    # --------------------------- Qt signal handlers ---------------------------

    def _on_duration_changed(self, duration: int) -> None:
        with self._lock:
            self._duration_ms = max(0, int(duration))

    def _on_position_changed(self, position: int) -> None:
        with self._lock:
            self._position_ms = max(0, int(position))
        # Fire our unified callback (Qt thread)
        self._invoke_position_callback(self._position_ms)

    def _on_state_changed(self, state: "QtMultimedia.QMediaPlayer.PlaybackState") -> None:
        with self._lock:
            if state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
                self._state = PlaybackState.PLAYING
            elif state == QtMultimedia.QMediaPlayer.PlaybackState.PausedState:
                self._state = PlaybackState.PAUSED
            else:
                self._state = PlaybackState.STOPPED

    def _on_media_status_changed(self, status: "QtMultimedia.QMediaPlayer.MediaStatus") -> None:
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            with self._lock:
                if not (self._loop_enabled and self._loop_start_ms is not None):
                    self._state = PlaybackState.STOPPED
            self._invoke_end_reached_callback()

    # --------------------------- Internal poller (for loops) ---------------------------

    def _start_poller(self) -> None:
        self._poller_stop.clear()
        self._poller_thread = threading.Thread(
            target=self._poller_loop, name="QtAudioPoller", daemon=True
        )
        self._poller_thread.start()

    def _poller_loop(self) -> None:
        while not self._poller_stop.is_set():
            try:
                self._enforce_loop_if_needed()
            except Exception:
                pass
            time.sleep(0.03)

    def _enforce_loop_if_needed(self) -> None:
        with self._lock:
            if (
                self._enabled
                and self._loop_enabled
                and self._loop_start_ms is not None
                and self._loop_end_ms is not None
                and self._player is not None
                and self._player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
                and self._position_ms >= self._loop_end_ms
            ):
                target = self._loop_start_ms
                self._player.setPosition(target)
                self._position_ms = target

    def _set_error(self, code: BackendErrorCode, msg: str) -> None:
        """Record ERROR state + diagnostics. Does NOT disable the backend for
        per-load errors so subsequent load() calls are still attempted (recoverable).
        Permanent backend-unavailable cases leave _enabled=False from __init__.
        """
        with self._lock:
            self._state = PlaybackState.ERROR
            self._error_code = code
            self._last_error = msg
            self._diagnostics["last_error"] = msg

    # ------------------------------------------------------------------
    # AudioBackend implementation
    # ------------------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        return _HAS_QT_MULTIMEDIA

    def release(self) -> None:
        self._poller_stop.set()
        if self._poller_thread and self._poller_thread.is_alive():
            self._poller_thread.join(timeout=0.3)

        with self._lock:
            try:
                if self._player:
                    self._player.stop()
                    self._player.setSource(QtCore.QUrl())  # clear
            except Exception:
                pass
            self._player = None
            self._audio_output = None
            self._enabled = False

    def get_diagnostics(self) -> dict:
        with self._lock:
            d = dict(self._diagnostics)
            d.update({
                "enabled": self._enabled,
                "state": self._state.name,
                "qt_multimedia_available": _HAS_QT_MULTIMEDIA,
            })
            return d

    def get_last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def get_error_code(self) -> BackendErrorCode:
        with self._lock:
            return self._error_code

    def load(self, path: str | Path) -> bool:
        if not self._enabled or self._player is None:
            return False
        path = str(Path(path).resolve())
        if not Path(path).exists():
            self._set_error(BackendErrorCode.FILE_NOT_FOUND, f"File not found: {path}")
            return False

        with self._lock:
            try:
                self._state = PlaybackState.LOADING
                url = QtCore.QUrl.fromLocalFile(path)
                self._player.setSource(url)
                self._current_path = path
                self._duration_ms = 0
                self._position_ms = 0
                self._state = PlaybackState.READY
                return True
            except Exception as e:
                self._set_error(BackendErrorCode.PARSE_FAILED, str(e))
                return False

    def unload(self) -> None:
        if self._player:
            self._player.stop()
            try:
                self._player.setSource(QtCore.QUrl())
            except Exception:
                pass
        with self._lock:
            self._current_path = None
            self._state = PlaybackState.IDLE

    def play(self) -> None:
        if self._player:
            self._player.play()

    def pause(self) -> None:
        if self._player:
            self._player.pause()

    def stop(self) -> None:
        if self._player:
            self._player.stop()
        with self._lock:
            self._position_ms = 0
            self._state = PlaybackState.STOPPED

    def seek(self, position_ms: int) -> None:
        if self._player:
            self._player.setPosition(max(0, int(position_ms)))

    def get_position_ms(self) -> int:
        with self._lock:
            return self._position_ms

    def get_duration_ms(self) -> int:
        with self._lock:
            return self._duration_ms

    def is_playing(self) -> bool:
        if not self._player:
            return False
        try:
            return self._player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
        except Exception:
            return False

    # DJ params (limited support)

    def set_volume(self, volume: float) -> None:
        if self._audio_output:
            vol = max(0.0, min(1.0, float(volume)))
            self._audio_output.setVolume(vol)
            with self._lock:
                self._volume = vol

    def get_volume(self) -> float:
        with self._lock:
            return self._volume

    def set_balance(self, balance: float) -> None:
        # QtMultimedia QAudioOutput has no direct balance in all versions.
        # We store it; real panning would require a QAudioEffect or post-processing.
        with self._lock:
            self._balance = max(-1.0, min(1.0, float(balance)))

    def get_balance(self) -> float:
        with self._lock:
            return self._balance

    def set_rate(self, rate: float) -> None:
        if self._player:
            r = max(0.1, min(8.0, float(rate)))
            try:
                self._player.setPlaybackRate(r)
            except Exception:
                pass
            with self._lock:
                self._rate = r

    def get_rate(self) -> float:
        with self._lock:
            return self._rate

    def set_keylock_enabled(self, enabled: bool) -> None:
        # Explicitly unsupported — we still accept the call for API compatibility
        with self._lock:
            self._keylock = bool(enabled)
            if enabled:
                self._diagnostics["keylock_warning"] = "QtMultimedia cannot preserve pitch on rate change"

    def is_keylock_enabled(self) -> bool:
        with self._lock:
            return self._keylock

    def set_eq(self, low_db: float, mid_db: float, high_db: float) -> None:
        # No native 3-band EQ in basic QMediaPlayer path.
        # Could be added later with QAudioEffect or by routing through a custom graph.
        logger.debug("QtAudioBackend.set_eq called — no-op (no EQ support in fallback)")

    def set_loop_points(self, start_ms: Optional[int], end_ms: Optional[int]) -> None:
        with self._lock:
            self._loop_start_ms = int(start_ms) if start_ms is not None else None
            self._loop_end_ms = int(end_ms) if end_ms is not None else None

    def set_loop_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._loop_enabled = bool(enabled)

    def is_loop_enabled(self) -> bool:
        with self._lock:
            return self._loop_enabled

    def get_loop_points(self) -> tuple[Optional[int], Optional[int]]:
        with self._lock:
            return (self._loop_start_ms, self._loop_end_ms)

    def get_state(self) -> DeckState:
        with self._lock:
            playing = False
            try:
                playing = self._player is not None and self._player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
            except Exception:
                pass
            return DeckState(
                state=self._state,
                is_playing=playing,
                position_ms=self._position_ms,
                duration_ms=self._duration_ms,
                volume=self._volume,
                balance=self._balance,
                rate=self._rate,
                keylock_enabled=self._keylock,
                loop_enabled=self._loop_enabled,
                loop_start_ms=self._loop_start_ms,
                loop_end_ms=self._loop_end_ms,
                error_code=self._error_code,
                error_message=self._last_error,
                extra={"path": self._current_path, "note": "QtMultimedia fallback"},
            )
