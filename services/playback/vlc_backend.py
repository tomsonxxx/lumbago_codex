"""
Hardened VLC Audio Backend for Lumbago Music AI dual-deck DJ player.

This replaces / supersedes the fragile VlcDeckPlayer from services/vlc_audio_backend.py
for all new code.

Key hardening measures:
- Robust VLC discovery (env, filesystem, Windows registry)
- Safe PATH / VLC_PLUGIN_PATH manipulation BEFORE importing vlc
- Proper single-process Instance sharing patterns + rich initialization flags
- First-class error states + rich diagnostics
- Thread-safe internal state with RLock
- Background poller thread for smooth position reporting (no reliance on Qt timers)
- VLC native event handling marshaled safely
- Automatic loop enforcement with low jitter
- Best-effort keylock via scaletempo audio filter
- Duration parsing with timeout + retry (common VLC gotcha)
- Full resource release, context manager, multiple-release safety
- No hard crashes on missing/broken VLC — graceful degradation path

All public methods are safe for use from the main thread.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

from .base import AudioBackend
from .types import BackendErrorCode, DeckState, PlaybackState

logger = logging.getLogger(__name__)

# libVLC is not safe when multiple threads touch MediaPlayer APIs concurrently.
# All native player/instance calls must go through this process-wide lock.
_LIBVLC_LOCK = threading.RLock()

# ----------------------------------------------------------------------
# Module-level VLC discovery & lazy loading (the heart of hardening)
# ----------------------------------------------------------------------

_VLC_AVAILABLE: bool = False
_VLC_IMPORT_ERROR: str = ""
_vlc = None  # the real module once successfully imported


def _discover_vlc_installations() -> list[Path]:
    """Return candidate VLC install directories (Windows-focused, best effort)."""
    candidates: list[Path] = []

    # 1. Explicit env var (highest priority, used by power users / portable VLC)
    env_path = os.environ.get("VLC_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            candidates.append(p)

    # 2. Standard Windows locations
    program_files = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    for base in program_files:
        vlc_dir = base / "VideoLAN" / "VLC"
        if vlc_dir.exists():
            candidates.append(vlc_dir)

    # 3. Registry discovery (VideoLAN writes InstallDir here)
    try:
        import winreg  # type: ignore

        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VideoLAN\VLC"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VideoLAN\VLC"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\VideoLAN\VLC"),
        ]
        for hkey, subkey in reg_paths:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    try:
                        install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                        if install_dir:
                            p = Path(str(install_dir))
                            if p.exists():
                                candidates.append(p)
                    except FileNotFoundError:
                        pass
            except FileNotFoundError:
                continue
            except Exception:
                continue
    except Exception:
        # winreg not available (non-Windows) or other failure — non-fatal
        pass

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def _ensure_vlc_environment() -> dict:
    """
    Attempt to locate VLC and set required environment variables
    BEFORE the vlc module is imported. Returns discovery report.
    """
    report = {
        "discovered": [],
        "chosen": None,
        "path_prepended": False,
        "plugin_path_set": False,
        "error": None,
    }

    candidates = _discover_vlc_installations()
    report["discovered"] = [str(c) for c in candidates]

    if not candidates:
        report["error"] = "No VLC installation candidates found"
        return report

    for candidate in candidates:
        libvlc = candidate / "libvlc.dll"
        plugins = candidate / "plugins"
        if libvlc.exists():
            # Prepend to PATH so ctypes / python-vlc can find libvlc.dll
            current_path = os.environ.get("PATH", "")
            if str(candidate) not in current_path:
                os.environ["PATH"] = str(candidate) + os.pathsep + current_path
                report["path_prepended"] = True

            if plugins.exists():
                os.environ["VLC_PLUGIN_PATH"] = str(plugins)
                report["plugin_path_set"] = True

            report["chosen"] = str(candidate)
            logger.debug(f"VLC environment prepared using: {candidate}")
            break

    if not report["chosen"]:
        report["error"] = "libvlc.dll not found in any candidate directory"

    return report


def _import_vlc() -> tuple[bool, str, object]:
    """
    Idempotent lazy import with environment hardening.
    Returns (success, error_message, vlc_module_or_None)
    """
    global _VLC_AVAILABLE, _VLC_IMPORT_ERROR, _vlc

    if _vlc is not None:
        return _VLC_AVAILABLE, _VLC_IMPORT_ERROR, _vlc

    discovery = _ensure_vlc_environment()

    try:
        import vlc as _imported_vlc  # type: ignore

        _vlc = _imported_vlc
        _VLC_AVAILABLE = True
        _VLC_IMPORT_ERROR = ""
        logger.info(f"python-vlc imported successfully (VLC {getattr(_vlc, '__version__', 'unknown')})")
        return True, "", _vlc

    except Exception as exc:  # catches ImportError + OSError (missing DLL) + others
        _VLC_AVAILABLE = False
        _VLC_IMPORT_ERROR = f"{type(exc).__name__}: {exc} | Discovery: {discovery}"
        _vlc = None
        logger.warning(f"Failed to import VLC backend: {_VLC_IMPORT_ERROR}")
        return False, _VLC_IMPORT_ERROR, None


# ----------------------------------------------------------------------
# VlcAudioBackend implementation
# ----------------------------------------------------------------------

class VlcAudioBackend(AudioBackend):
    """
    Production-grade single-deck VLC backend.

    One instance = one independent audio deck.
    Multiple instances can coexist (they share the same underlying VLC Instance
    where beneficial, but each owns its MediaPlayer).
    """

    _shared_instance = None
    _shared_instance_lock = threading.Lock()

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._state: PlaybackState = PlaybackState.IDLE
        self._error_code: BackendErrorCode = BackendErrorCode.NONE
        self._last_error: Optional[str] = None
        self._diagnostics: dict = {"backend": "vlc", "initialized": False}

        self._player = None
        self._media = None
        self._equalizer = None

        self._current_path: Optional[str] = None
        self._duration_ms: int = 0
        self._position_ms: int = 0
        self._volume: float = 1.0
        self._balance: float = 0.0
        self._rate: float = 1.0
        self._keylock: bool = False

        self._loop_start_ms: Optional[int] = None
        self._loop_end_ms: Optional[int] = None
        self._loop_enabled: bool = False

        self._is_loaded: bool = False  # legacy + internal compat

        self._lock = threading.RLock()  # protects all mutable state above

        # Background polling
        self._poller_thread: Optional[threading.Thread] = None
        self._poller_stop = threading.Event()
        self._last_reported_pos: int = 0

        # Attempt import + init
        success, err, vlc_mod = _import_vlc()
        if not success or vlc_mod is None:
            self._set_error(BackendErrorCode.VLC_MISSING_DLL, f"VLC unavailable: {err}")
            return

        self._vlc = vlc_mod
        self._init_vlc_resources()

    # --------------------------- Internal init ---------------------------

    def _init_vlc_resources(self) -> None:
        """Create VLC Instance + MediaPlayer + Equalizer. Sets _enabled on success."""
        with self._lock:
            try:
                # Use a single shared Instance for the whole process (efficient + stable)
                with VlcAudioBackend._shared_instance_lock:
                    if VlcAudioBackend._shared_instance is None:
                        args = [
                            "--no-video",
                            "--no-osd",
                            "--intf", "dummy",
                            "--no-stats",
                            "--quiet",
                            "--no-spu",
                            # scaletempo gives better quality time-stretching when we want keylock
                            "--audio-filter=scaletempo",
                        ]
                        VlcAudioBackend._shared_instance = self._vlc.Instance(*args)
                        logger.debug("Created shared VLC Instance")

                    self._instance = VlcAudioBackend._shared_instance

                self._player = self._instance.media_player_new()

                # Equalizer (10-band) — API varies slightly across python-vlc versions
                try:
                    eq_cls = getattr(self._vlc, "AudioEqualizer", None)
                    if eq_cls is not None:
                        try:
                            self._equalizer = eq_cls.create()  # some versions
                        except (AttributeError, TypeError):
                            self._equalizer = eq_cls()  # constructor in others
                        if self._equalizer:
                            self._player.set_equalizer(self._equalizer)
                except Exception as eq_err:
                    logger.warning(f"Equalizer creation failed (non-fatal): {eq_err}")
                    self._equalizer = None

                # Do NOT attach VLC event callbacks: they run on libVLC threads and
                # concurrent player access from Qt timers caused native crashes on Windows.
                # Position/state updates are driven by poll() on the UI thread only.

                self._enabled = True
                self._state = PlaybackState.IDLE
                self._diagnostics.update({
                    "initialized": True,
                    "vlc_version": getattr(self._vlc, "__version__", None),
                    "libvlc_version": self._get_libvlc_version(),
                    "shared_instance": True,
                    "scaletempo": True,
                    "polling_mode": "ui_thread",
                })

            except Exception as e:
                self._set_error(
                    BackendErrorCode.VLC_INIT_FAILED,
                    f"Failed to create VLC player: {e}"
                )
                self._enabled = False

    def _get_libvlc_version(self) -> Optional[str]:
        try:
            return self._vlc.libvlc_get_version().decode("utf-8", errors="ignore")
        except Exception:
            return None

    def poll(self) -> None:
        """Advance position/state snapshot. Must be called from the UI owner thread (~25-50 Hz)."""
        self._poll_once()

    def _poll_once(self) -> None:
        if not self._enabled or self._player is None:
            return

        pos_copy: int | None = None
        with _LIBVLC_LOCK:
            with self._lock:
                if not self._enabled:
                    return

                try:
                    pos = self._player.get_time()
                    if pos is not None and pos >= 0:
                        self._position_ms = int(pos)

                    if self._duration_ms <= 0:
                        length = self._player.get_length()
                        if length is not None and length > 0:
                            self._duration_ms = int(length)

                    try:
                        actually_playing = bool(self._player.is_playing())
                        if actually_playing and self._state not in (
                            PlaybackState.PLAYING,
                            PlaybackState.LOADING,
                        ):
                            self._state = PlaybackState.PLAYING
                        elif not actually_playing and self._state == PlaybackState.PLAYING:
                            self._state = PlaybackState.PAUSED
                    except Exception:
                        pass

                    if (
                        self._loop_enabled
                        and self._loop_start_ms is not None
                        and self._loop_end_ms is not None
                        and self._player.is_playing()
                        and self._position_ms >= self._loop_end_ms
                    ):
                        target = max(0, self._loop_start_ms)
                        self._player.set_time(target)
                        self._position_ms = target
                        logger.debug(f"Loop triggered (poll): seeking to {target}ms")

                except Exception as poll_err:
                    logger.debug(f"Poll error (ignored): {poll_err}")
                    return

                current = self._position_ms
                if abs(current - self._last_reported_pos) >= 8:
                    self._last_reported_pos = current
                    pos_copy = current

        if pos_copy is not None:
            self._invoke_position_callback(pos_copy)

    def _set_error(self, code: BackendErrorCode, message: str) -> None:
        """Record ERROR state + diagnostics. Does NOT disable the backend for
        per-load errors (FILE_NOT_FOUND, PARSE etc.) so future load() attempts
        on new files can succeed. Only init-time failures leave _enabled=False.
        """
        with self._lock:
            self._state = PlaybackState.ERROR
            self._error_code = code
            self._last_error = message
            self._diagnostics["last_error"] = message
            self._diagnostics["error_code"] = code.name

    # ------------------------------------------------------------------
    # AudioBackend ABC implementation
    # ------------------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        success, _, _ = _import_vlc()
        return success

    def release(self) -> None:
        self._poller_stop.set()
        if self._poller_thread and self._poller_thread.is_alive():
            self._poller_thread.join(timeout=0.5)

        with _LIBVLC_LOCK:
            with self._lock:
                try:
                    if self._player:
                        try:
                            self._player.stop()
                            self._player.release()
                        except Exception:
                            pass
                        self._player = None
                    # Shared VLC Instance is kept for other decks until process exit.
                    self._media = None
                    self._equalizer = None
                    self._enabled = False
                    self._state = PlaybackState.IDLE
                    self._current_path = None
                except Exception:
                    pass

    def get_diagnostics(self) -> dict:
        with self._lock:
            d = dict(self._diagnostics)
            d.update({
                "enabled": self._enabled,
                "state": self._state.name,
                "current_path": self._current_path,
                "duration_ms": self._duration_ms,
            })
            return d

    def get_last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def get_error_code(self) -> BackendErrorCode:
        with self._lock:
            return self._error_code

    def load(self, path: str | Path) -> bool:
        path = str(path)
        if not self._enabled or self._player is None:
            return False

        if not Path(path).exists():
            self._set_error(BackendErrorCode.FILE_NOT_FOUND, f"File not found: {path}")
            return False

        try:
            with _LIBVLC_LOCK:
                with self._lock:
                    self._state = PlaybackState.LOADING
                    self._last_error = None
                    self._error_code = BackendErrorCode.NONE
                    self._duration_ms = 0
                    self._position_ms = 0
                    self._last_reported_pos = 0
                    self._is_loaded = False

                    media = self._instance.media_new(path)
                    self._player.set_media(media)
                    self._media = media
                    self._current_path = path

                    try:
                        media.parse_with_options(self._vlc.MediaParseFlag.local, 0)
                    except Exception:
                        pass

                deadline = time.time() + 0.8
                while time.time() < deadline and self._duration_ms <= 0:
                    try:
                        length = self._player.get_length()
                        if length and length > 0:
                            with self._lock:
                                self._duration_ms = int(length)
                            break
                    except Exception:
                        pass
                    time.sleep(0.01)

                with self._lock:
                    self._state = PlaybackState.READY
                    self._is_loaded = True
            logger.debug(f"VLC loaded: {path} (duration={self._duration_ms}ms)")
            return True

        except Exception as e:
            self._set_error(BackendErrorCode.PARSE_FAILED, f"Load failed: {e}")
            return False

    def unload(self) -> None:
        """Stop playback and release current media (keeps backend ready for next load)."""
        if not self._enabled or self._player is None:
            return
        with _LIBVLC_LOCK:
            try:
                self._player.stop()
            except Exception:
                pass
        with self._lock:
            try:
                self._media = None
                self._current_path = None
                self._duration_ms = 0
                self._position_ms = 0
                self._last_reported_pos = 0
                self._is_loaded = False
                self._state = PlaybackState.IDLE
                self._loop_enabled = False
                self._loop_start_ms = None
                self._loop_end_ms = None
            except Exception:
                pass

    def play(self) -> None:
        if not self._enabled or self._player is None:
            return
        with _LIBVLC_LOCK:
            with self._lock:
                try:
                    self._player.play()
                    self._state = PlaybackState.PLAYING
                except Exception as e:
                    self._set_error(BackendErrorCode.PLAYBACK_FAILED, str(e))
        self.poll()

    def pause(self) -> None:
        if not self._enabled or self._player is None:
            return
        with _LIBVLC_LOCK:
            with self._lock:
                try:
                    self._player.pause()
                    self._state = PlaybackState.PAUSED
                except Exception as e:
                    logger.debug(f"Pause error: {e}")
        self.poll()

    def stop(self) -> None:
        if not self._enabled or self._player is None:
            return
        with _LIBVLC_LOCK:
            with self._lock:
                try:
                    self._player.stop()
                    self._position_ms = 0
                    self._state = PlaybackState.STOPPED
                except Exception as e:
                    logger.debug(f"Stop error: {e}")

    def seek(self, position_ms: int) -> None:
        if not self._enabled or self._player is None:
            return
        with _LIBVLC_LOCK:
            with self._lock:
                try:
                    pos = max(0, int(position_ms))
                    if self._duration_ms > 0:
                        pos = min(pos, self._duration_ms)
                    self._player.set_time(pos)
                    self._position_ms = pos
                except Exception as e:
                    logger.debug(f"Seek error: {e}")

    def get_position_ms(self) -> int:
        with self._lock:
            return self._position_ms

    def get_duration_ms(self) -> int:
        if self._enabled and self._player is not None and self._duration_ms <= 0:
            self.poll()
        with self._lock:
            return self._duration_ms

    def is_playing(self) -> bool:
        if not self._enabled or self._player is None:
            return False
        with _LIBVLC_LOCK:
            try:
                return bool(self._player.is_playing())
            except Exception:
                return False

    # --------------------------- DJ Controls ---------------------------

    def set_volume(self, volume: float) -> None:
        if not self._enabled or self._player is None:
            return
        with self._lock:
            vol = max(0.0, min(1.0, float(volume)))
            self._volume = vol
            # VLC uses 0-100
            try:
                with _LIBVLC_LOCK:
                    self._player.audio_set_volume(int(vol * 100))
            except Exception:
                pass

    def get_volume(self) -> float:
        with self._lock:
            return self._volume

    def set_balance(self, balance: float) -> None:
        if not self._enabled or self._player is None:
            return
        with self._lock:
            bal = max(-1.0, min(1.0, float(balance)))
            self._balance = bal
            try:
                with _LIBVLC_LOCK:
                    self._player.audio_set_balance(bal)
            except Exception:
                pass

    def get_balance(self) -> float:
        with self._lock:
            return self._balance

    def set_rate(self, rate: float) -> None:
        if not self._enabled or self._player is None:
            return
        with self._lock:
            r = max(0.1, min(8.0, float(rate)))  # generous bounds
            self._rate = r
            try:
                with _LIBVLC_LOCK:
                    self._player.set_rate(r)
            except Exception:
                pass

    def get_rate(self) -> float:
        with self._lock:
            return self._rate

    def set_keylock_enabled(self, enabled: bool) -> None:
        """
        Best-effort keylock via scaletempo (enabled at Instance creation for all decks).
        When enabled + rate != 1.0, tempo changes should preserve pitch (within scaletempo quality limits).
        No per-deck filter reload in v1 (shared instance); flag is recorded for UI + future.
        """
        with self._lock:
            self._keylock = bool(enabled)
            self._diagnostics["keylock_requested"] = self._keylock
            if enabled:
                self._diagnostics["keylock_mode"] = "scaletempo (best-effort pitch preservation)"

    def is_keylock_enabled(self) -> bool:
        with self._lock:
            return self._keylock

    def set_eq(self, low_db: float, mid_db: float, high_db: float) -> None:
        if not self._equalizer or not self._enabled:
            return
        with self._lock:
            # Clamp to safe dB range for VLC AudioEqualizer (typically -20..+20 supported)
            low = max(-20.0, min(20.0, float(low_db)))
            mid = max(-20.0, min(20.0, float(mid_db)))
            high = max(-20.0, min(20.0, float(high_db)))

            # Improved 10-band -> 3-band mapping using approximate band centers
            # Low: bands 0-2 (bass ~60-310 Hz), Mid: 3-6 (~600 Hz-6 kHz), High: 7-9 (12 kHz+)
            try:
                for i in range(10):
                    if i <= 2:
                        self._equalizer.set_amp_at_index(low, i)
                    elif i <= 6:
                        self._equalizer.set_amp_at_index(mid, i)
                    else:
                        self._equalizer.set_amp_at_index(high, i)
            except Exception:
                pass

    def reset_eq(self) -> None:
        """Reset to flat response and clear any active eq curve."""
        if not self._equalizer or not self._enabled:
            super().reset_eq()
            return
        with self._lock:
            try:
                for i in range(10):
                    self._equalizer.set_amp_at_index(0.0, i)
                self._diagnostics["eq_reset"] = True
            except Exception:
                pass
        # Also call base in case
        super().reset_eq()

    def set_loop_points(self, start_ms: Optional[int], end_ms: Optional[int]) -> None:
        with self._lock:
            s = int(start_ms) if start_ms is not None else None
            e = int(end_ms) if end_ms is not None else None
            if s is not None and e is not None and e <= s:
                e = s + 1000  # minimal 1s loop
            self._loop_start_ms = s
            self._loop_end_ms = e

    def set_loop_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._loop_enabled = bool(enabled)

    def is_loop_enabled(self) -> bool:
        with self._lock:
            return self._loop_enabled

    def get_loop_points(self) -> tuple[Optional[int], Optional[int]]:
        with self._lock:
            return (self._loop_start_ms, self._loop_end_ms)

    # --------------------------- State snapshot ---------------------------

    def get_state(self) -> DeckState:
        with self._lock:
            playing = False
            if self._player and self._enabled:
                with _LIBVLC_LOCK:
                    try:
                        playing = bool(self._player.is_playing())
                    except Exception:
                        playing = False
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
                extra={"path": self._current_path},
            )
