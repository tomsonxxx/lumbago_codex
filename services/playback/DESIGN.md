# Lumbago Music AI — Playback Backend Abstraction (v1 Design)

**Status**: First iteration deliverable. Pure services layer. UI-agnostic.  
**Owner**: Playback Backend Engineer  
**Date**: 2026-05-29  
**References**: core/models.py (Track, CuePoint, BeatMarker), existing services/vlc_audio_backend.py (VlcDeckPlayer), AGENTS.md / CLAUDE.md architecture.

---

## Goals

- Provide a clean, professional, robust audio backend for the future dual-deck DJ player (and any other playback needs).
- Abstract away VLC vs QtMultimedia (and future backends such as GStreamer or direct WASAPI).
- Support two fully independent decks.
- Coordinated mixing (crossfader, per-deck volume/balance/EQ) lives in a higher-level `PlaybackEngine`.
- First-class error states and diagnostics — especially critical for VLC on Windows (missing DLLs, plugin paths, corrupted installs).
- Thread-safe position reporting and callbacks (VLC events and polling occur off the main thread).
- Proper resource lifecycle (no leaks, no crashes on app exit or rapid load/unload).
- Graceful degradation: full-featured VLC when available → QtMultimedia fallback → silent no-op backend.
- Clear, documented API that UI code (primarily dj_player_window.py using the new professional DJPlayerWindow) can consume **without any knowledge of VLC, QtMultimedia, or threading details**.

Note: ui/player_widget.py is legacy (see deprecation header in the file) and has not been migrated. The main dedicated pro DJ player lives in dj_player_window.py.

Non-goals for v1:
- Actual sample-accurate DSP mixing in Python (we control volumes on the native players; OS mixer combines).
- Full beatgrid sync / master tempo (future; will build on BeatMarker model).
- Low-latency ASIO / WASAPI exclusive mode (documented as future extension).
- Recording / master output capture.

---

## Integration with Domain Models

- `AudioBackend.load(path)` accepts filesystem path (from `Track.path`).
- Higher layers (PlaybackEngine or UI controller) are responsible for:
  - Loading `Track` → extract `path`, `duration`, `bpm`, `cue_in_ms` etc.
  - Converting `CuePoint` (with `loop_end_ms`) → `set_loop_points(...)`.
  - Using `BeatMarker` list for visual beatgrid / sync later (backend only provides raw position).
- Backend itself stays **lightweight**: no DB, no mutagen, no heavy analysis. It only plays bytes from disk.

Example future usage (not implemented in v1):
```python
from core.models import Track, CuePoint
from services.playback import create_backend, PlaybackEngine

engine = PlaybackEngine(create_backend)
track = repo.get_track(...)
engine.load_deck("A", track.path)
if track.cue_in_ms:
    engine.deck_a.seek(track.cue_in_ms)
# Convert CuePoint objects to loop points etc.
```

---

## Core Abstractions

### 1. `AudioBackend` (ABC / Protocol)

Located in `base.py`.

Key interface (full details in code):

```python
class AudioBackend(ABC):
    # Lifecycle & availability
    @classmethod
    def is_available(cls) -> bool: ...
    def get_diagnostics(self) -> dict: ...
    def get_last_error(self) -> str | None: ...
    def release(self) -> None: ...

    # Loading
    def load(self, path: str | Path) -> bool: ...
    def unload(self) -> None: ...

    # Transport
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
    def seek(self, position_ms: int) -> None: ...
    def toggle_play(self) -> bool: ...

    # Core parameters (thread-safe getters)
    def get_position_ms(self) -> int: ...
    def get_duration_ms(self) -> int: ...
    def is_playing(self) -> bool: ...

    # DJ controls
    def set_volume(self, volume: float) -> None: ...          # 0.0..1.0
    def get_volume(self) -> float: ...
    def set_balance(self, balance: float) -> None: ...        # -1.0 (L) .. +1.0 (R)
    def set_rate(self, rate: float) -> None: ...              # 0.5..2.0 typical
    def get_rate(self) -> float: ...
    def set_keylock_enabled(self, enabled: bool) -> None: ...
    def is_keylock_enabled(self) -> bool: ...

    # 3-band EQ (dB, typical -12..+12)
    def set_eq(self, low_db: float, mid_db: float, high_db: float) -> None: ...
    def reset_eq(self) -> None: ...

    # Loops (backend handles auto-seek when enabled)
    def set_loop_points(self, start_ms: int | None, end_ms: int | None) -> None: ...
    def set_loop_enabled(self, enabled: bool) -> None: ...
    def is_loop_enabled(self) -> bool: ...
    def get_loop_points(self) -> tuple[int | None, int | None]: ...

    # Callbacks (may be called from worker threads — marshal in UI!)
    def set_position_callback(self, cb: Callable[[int], None] | None) -> None: ...
    def set_end_reached_callback(self, cb: Callable[[], None] | None) -> None: ...

    # State snapshot (atomic)
    def get_state(self) -> "DeckState": ...
```

**Design decisions**:
- Normalized floats (0-1 volume) for modern code; convenience % helpers can live in engine or adapters.
- `set_rate` + `keylock` separation: when keylock=True the backend attempts pitch-preserving tempo (VLC via `scaletempo` filter where possible).
- Loops are **owned by the backend** for tight timing (avoids jitter from Python timer roundtrips).
- Callbacks are **fire-and-forget**; no return value expected. Heavy work must not be done inside them.

### 2. Supporting Types (`types.py`)

- `PlaybackState` Enum (IDLE, LOADING, READY, PLAYING, PAUSED, STOPPED, ERROR)
- `DeckState` dataclass (immutable snapshot)
- `BackendErrorCode` Enum (VLC_MISSING, VLC_INIT_FAILED, FILE_NOT_FOUND, PARSE_FAILED, PLAYBACK_FAILED, ...)
- `LoopMode` (future extension)
- Typed callbacks: `PositionCallback = Callable[[int], None]`

Error objects carry both code + human message + optional technical details (for logs/crash reports).

### 3. `PlaybackEngine` (engine.py)

Coordinates two decks + mixing. Still UI-agnostic.

Responsibilities in v1:
- Owns two `AudioBackend` instances (A + B) via factory.
- Crossfader position (-1.0 .. +1.0) with selectable curve (linear, constant-power approx).
- Master volume.
- Per-deck volume trim + balance (combined with crossfader result).
- Convenience: `load_deck("A", path)`, `play_deck("A")`, `set_deck_eq("B", ...)` etc. that delegate.
- Optional sync logic hooks (BPM, beat phase) — stubs for future.
- Global `release_all()`.

Crossfader math (v1):
```python
# Simple equal-power approximation
def _apply_crossfader(self, pos: float):
    a_gain = (1 - pos) ** 0.5 if pos > 0 else 1.0
    b_gain = (1 + pos) ** 0.5 if pos < 0 else 1.0
    ...
```

Higher-order features (set recording, harmonic mixing using key from Track) belong outside this layer.

### 4. Concrete Implementations

#### `VlcAudioBackend` (vlc_backend.py) — Hardened

Addresses all known fragility in the old `VlcDeckPlayer`:

1. **Discovery & Environment** (`_ensure_vlc_environment()`):
   - Checks `VLC_PATH` env var.
   - Scans standard Windows install locations (Program Files + (x86)).
   - Reads registry (HKLM/HKCU `VideoLAN\VLC` → `InstallDir` + Wow6432Node).
   - Sets `PATH` and `VLC_PLUGIN_PATH` **before** `import vlc`.
   - Graceful failure with rich diagnostic dict.

2. **Instance Creation**:
   - Single shared `vlc.Instance` per process (or per backend instance for isolation in v1; future: manager).
   - Rich flags: `--no-video --no-osd --quiet --intf=dummy --no-stats --audio-filter=scaletempo` (conditionally).
   - Version check + warning for old VLC (< 3.0).

3. **Lifecycle**:
   - `release()` always safe (multiple calls, exceptions swallowed).
   - `__del__` + context manager support.
   - Proper `media_player.release()` + `instance.release()`.
   - Unload stops + clears media.

4. **Error Model**:
   - Every public method checks `_state != ERROR` and `_enabled`.
   - `load()` failures set `ERROR` state + populate `last_error` + diagnostics.
   - `is_available()` classmethod does a full probe without side effects.

5. **Threading & Position**:
   - Dedicated `_poller_thread` (daemon) running at ~40 Hz.
   - Uses `threading.RLock` for all mutable state (`_position_ms`, `_loop_*`, callbacks).
   - Position callback only fired on meaningful change (debounced by 5-10 ms).
   - End-reached handled via VLC `MediaPlayerEndReached` event (marshaled to poller) + fallback polling.
   - Loop enforcement inside poller (seek when crossing boundary; handles wrap-around).

6. **Keylock / Rate**:
   - `set_keylock_enabled(True)` → attempts to (re)load media with `scaletempo` filter for pitch preservation on rate changes.
   - Fallback: rate still works (pitch will shift); warning logged + exposed in diagnostics.
   - Separate internal `_apply_rate()`.

7. **Duration Parsing**:
   - After `set_media`, calls `media.parse_with_options` (async) + waits up to 800 ms with timeout for valid `get_length()`.
   - Getters retry a few times (common VLC race).

8. **EQ & Balance**:
   - Re-uses 10-band internal equalizer mapped to 3-band (same logic as old code, hardened).
   - `audio_set_balance` / `audio_get_balance`.

9. **Diagnostics** (critical for support):
   ```python
   {
       "backend": "vlc",
       "vlc_version": "3.0.20",
       "libvlc_version": "...",
       "plugin_path": "C:\\Program Files\\VideoLAN\\VLC\\plugins",
       "instance_created": True,
       "last_error": None,
       "discovered_paths": [...],
       "scaletempo_available": True,
   }
   ```

#### `QtAudioBackend` (qt_backend.py) — Fallback Skeleton

- Attempts `from PyQt6 import QtMultimedia`
- If unavailable or `QMediaPlayer` fails to instantiate → `is_available() == False`, all ops become no-ops + set error state.
- Implements the full `AudioBackend` surface using `QMediaPlayer` + `QAudioOutput`.
- Limitations acknowledged in docstring and diagnostics:
  - No native 3-band EQ (stubbed or very basic via Qt effects if available).
  - Rate/pitch limited (Qt 6.5+ has `playbackRate`; keylock not supported — always pitch shifts).
  - Loop points implemented via position polling + timer (Qt signals).
  - No low-level balance/EQ guarantees across platforms.
- Purpose: allow the app to run and show UI / waveform preview even without VLC installed. Real DJ use requires VLC.

**Graceful degradation order** (in `create_backend()`):
1. VLC (if `VlcAudioBackend.is_available()`)
2. QtMultimedia (if available)
3. `NoopAudioBackend` (always succeeds, does nothing — useful for headless tests / CI)

---

## Package Structure (v1)

```
services/playback/
├── __init__.py          # Public API + create_backend() factory + __version__
├── DESIGN.md            # This document (explicitly requested)
├── base.py              # AudioBackend ABC + common mixins
├── types.py             # Enums, DeckState, error codes, type aliases
├── vlc_backend.py       # Hardened production implementation
├── qt_backend.py        # QtMultimedia fallback (skeleton + docs)
├── engine.py            # PlaybackEngine (dual deck + crossfader)
└── utils.py             # (optional) _discover_vlc(), shared helpers
```

Public exports (from `services.playback`):
- `AudioBackend`, `PlaybackEngine`
- `create_backend`, `get_available_backends`
- `PlaybackState`, `DeckState`, `BackendErrorCode`
- `VlcAudioBackend`, `QtAudioBackend` (for advanced users / testing only)

---

## Thread Safety Contract

- All getters (`get_position_ms`, `get_state`, `is_playing`...) are safe from any thread.
- Callbacks (`position`, `end_reached`) **may** be delivered from a non-Qt / non-main thread.
- Mutating calls (`play`, `seek`, `set_loop...`) should be called from the same thread that owns the UI (or protected).
- Internal implementation uses RLock + careful queuing for VLC event handlers.

UI team rule: **Never do Qt GUI work directly inside a callback.** Use `QtCore.QMetaObject.invokeMethod`, `QTimer.singleShot`, or `pyqtSignal`.

---

## Error Handling & Diagnostics Philosophy

- Never raise from normal playback operations (except programming errors / wrong usage).
- All failures → transition to `ERROR` state + populate `last_error` + enrich diagnostics.
- `PlaybackEngine` and consumers can query any deck's `get_diagnostics()` and surface friendly messages:
  > "VLC not found. Install from videolan.org or the player will run in preview-only mode."
- On import of the package itself, no hard failure — discovery is lazy.

---

## Testing Strategy (v1)

- `tests/test_playback_base.py` — ABC protocol checks, state machine, noop backend.
- `tests/test_playback_engine.py` — crossfader math, delegation, dual-deck lifecycle (mocks).
- `tests/test_playback_vlc.py` — when python-vlc present: monkeypatch the vlc module, test init paths, error paths, loop logic, polling.
- `tests/test_playback_qt.py` — mock QtMultimedia, verify fallback.
- Use `unittest.mock` heavily. No real audio hardware required.
- Smoke: `LUMBAGO_SAFE_MODE=1 python -c "from services.playback import create_backend; b=create_backend(); print(b.get_diagnostics())"`

---

## Migration Path from Old Code

- Old `services/vlc_audio_backend.py:VlcDeckPlayer` remains untouched (for now) to avoid breaking `dj_player_window.py`.
- New package is additive.
- Future PR (after UI team review): 
  - dj_player_window and player_widget will import from `services.playback` instead of old module.
  - Old file can be deprecated / removed after full cutover.

---

## Future Extensions (Post v1)

- `SoundTouchAudioBackend` or `RubberBandBackend` for true independent keylock + high-quality time-stretch.
- WASAPI exclusive / ASIO via `sounddevice` + `soundfile`.
- Per-deck sample peak / RMS metering callbacks (for channel meters).
- Master bus with limiter / recording.
- MIDI / HID controller mapping layer on top of Engine.
- Integration with `core.waveform` for sample-accurate playhead (using BeatMarker + position).

---

## Summary for UI Team (and future consumers)

You only need:

```python
from services.playback import create_backend, PlaybackEngine, DeckState

backend = create_backend()          # or pass explicit "vlc" / "qt"
engine = PlaybackEngine(lambda: create_backend())

engine.load_deck("A", "/path/to/track.mp3")
engine.play_deck("A")
engine.set_crossfader(0.3)
pos = engine.deck_a.get_position_ms()
state: DeckState = engine.deck_a.get_state()
```

Zero VLC imports, zero QtMultimedia imports, zero threading worries in calling code.

This is the contract.

---

**End of v1 Design Document**
