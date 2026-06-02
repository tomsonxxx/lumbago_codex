from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Any

from PyQt6 import QtCore, QtWidgets

from core.models import Track
from services.playback import PlaybackEngine

# ------------------------------------------------------------------
# Waveform support for simple controller – self-contained copy of pattern
# (from deck_controller, but kept minimal and independent; no hotcue etc.)
# Uses core.waveform exclusively.
# ------------------------------------------------------------------
from core.waveform import extract_peaks as _core_extract_peaks

logger = logging.getLogger(__name__)


def _safe_extract_peaks(audio_path: str | Path, num_points: int = 900) -> list[float]:
    """Bezpieczny wrapper wokół core.waveform.extract_peaks (fallback zawsze działa)."""
    try:
        return _core_extract_peaks(audio_path, num_points=num_points)
    except Exception as exc:
        logger.warning(f"extract_peaks nieudane dla {audio_path}: {exc}")
        # Ostatni fallback identyczny z core + deck_controller
        import math
        import random
        peaks: list[float] = []
        for i in range(num_points):
            t = (i / num_points) * 180
            base = 0.3 + 0.5 * abs(math.sin(t * 1.7)) + 0.2 * abs(math.sin(t * 0.35))
            noise = random.uniform(-0.06, 0.06)
            peaks.append(max(0.08, min(0.97, base + noise)))
        return peaks


class SimpleDeckController(QtCore.QObject):
    """
    Lekki kontroler tylko dla minimalnego single playera "Odtwarzacz" MVP.

    Zadania (exactly per spec):
    - load_track: DB lookup jeśli brak id, playback_engine.load_deck, get state, waveform token,
      basic bpm; _main_cue_ms=0 zawsze na load. (hotcues minimal – pominięte, brak managera)
    - unload, play(), pause(), stop() z cue logic (play preferuje _main_cue jeśli pos near 0)
    - seek, set_cue (ustawia _main_cue_ms na bieżącej pozycji)
    - Basic playhead timer (40ms) + lepsze używanie backend state (is_playing, position z DeckState)
    - Emituje TYLKO podstawowe sygnały: track_loaded, track_unloaded, playhead_changed,
      bpm_changed, play_state_changed, status_changed
    - request_waveform_load dla widoku (używa prostego runnable opartego na core.waveform)
    - ZERO: HotcueManager, memory, loops, sync, quantize, pitch, trim, eq

    Używa wyłącznie istniejącego PlaybackEngine
    (load_deck/play_deck/.../get_deck_state).
    Wspiera drag&drop lookup z repo (w view + load).

    Zgodne z from __future__ annotations, black 100, wzorce.
    """
    # Tylko podstawowe sygnały (per spec)
    track_loaded = QtCore.pyqtSignal(object)          # Track
    track_unloaded = QtCore.pyqtSignal()
    playhead_changed = QtCore.pyqtSignal(int)         # ms
    bpm_changed = QtCore.pyqtSignal(object)           # float | None
    play_state_changed = QtCore.pyqtSignal(bool)      # is_playing
    status_changed = QtCore.pyqtSignal(str)           # status tekst

    def __init__(
        self,
        deck_id: str,  # "A" (single only)
        playback_engine: PlaybackEngine,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.deck_id = deck_id
        self.playback_engine = playback_engine

        # Minimalny stan wewnętrzny
        self.current_track: Track | None = None
        self._main_cue_ms: int = 0
        self._original_bpm: float | None = None
        self._current_waveform_token: str | None = None

        # Timer playhead (basic)
        self._playhead_timer = QtCore.QTimer(self)
        self._playhead_timer.setInterval(40)
        self._playhead_timer.timeout.connect(self._on_playhead_tick)

        logger.debug(
            f"SimpleDeckController {self.deck_id} utworzony "
            f"(MVP Odtwarzacz, engine={playback_engine.__class__.__name__})"
        )
        self._compact: bool = False  # for future sync / state (view drives UI compact)

    # ------------------------------------------------------------------
    # Public API – basics only
    # ------------------------------------------------------------------
    def load_track(self, track: Track) -> None:
        """
        Załaduj utwór (z DB lookup dla pełnych danych jak w full path).
        Ustawia _main_cue_ms=0, load engine, emit track + bpm + status.
        Waveform request jest delegowany do widoku (po sygnale) via request_waveform_load.

        FILE vs STREAM: ta metoda = FILE load (ścieżka, DB, engine.load_deck przygotowuje plik).
        Nie uruchamia streamu (playback). Cue reset do 0.
        """
        if not track:
            return

        # DB lookup dla id (potrzebne w przyszłości, tu dla spójności z drop + full)
        if not getattr(track, "id", None):
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(track.path)
                if dbt and dbt.id:
                    track = dbt
            except Exception as exc:
                logger.debug(f"SimpleDeck {self.deck_id}: DB lookup nieudany: {exc}")

        self.current_track = track
        self._main_cue_ms = 0
        bpm = getattr(track, "bpm", None)
        self._original_bpm = bpm if bpm and bpm > 10 else None

        success = False
        duration = 0
        if self.playback_engine:
            try:
                success = self.playback_engine.load_deck(self.deck_id, track.path)  # FILE prep
            except Exception as e:
                logger.exception(f"SimpleDeck {self.deck_id}: wyjątek przy load_deck: {e}")
                success = False

            if success:
                try:
                    state = self.playback_engine.get_deck_state(self.deck_id)
                    duration = state.duration_ms if state else 0
                    self._current_waveform_token = str(track.path) if track.path else None
                    self.status_changed.emit("✓ Utwór załadowany")
                    if self._original_bpm:
                        self.bpm_changed.emit(self._original_bpm)
                    logger.info(f"SimpleDeck {self.deck_id}: załadowano {Path(track.path).name}")
                except Exception as e:
                    logger.exception(f"SimpleDeck {self.deck_id}: błąd po load_deck")
                    self.status_changed.emit("✗ Błąd po załadowaniu")
            else:
                self.status_changed.emit("✗ Błąd ładowania")
        else:
            self.status_changed.emit("⚠ Brak silnika audio")

        self.track_loaded.emit(track)

    def unload(self) -> None:
        """Zatrzymaj + wyczyść (dla single)."""
        self.current_track = None
        self._main_cue_ms = 0
        self._original_bpm = None
        if self.playback_engine:
            try:
                self.playback_engine.stop_deck(self.deck_id)
            except Exception:
                pass
        self._playhead_timer.stop()
        self.track_unloaded.emit()
        self.status_changed.emit("— Wyczyszczono")

    def play(self) -> None:
        """Start playback. Jeśli pos near 0 – preferuj _main_cue_ms (per spec).
        To jest STREAM op (play_deck na załadowanym pliku).
        Cue logic: prefer cue jeśli blisko 0 (bezpieczne preview z punktu).
        """
        if not self.playback_engine:
            return
        try:
            state = self.playback_engine.get_deck_state(self.deck_id)
            pos = state.position_ms if state else 0
            if pos < 150:  # "near 0"
                cue = getattr(self, "_main_cue_ms", 0) or 0
                if cue > 0:
                    try:
                        self.playback_engine.seek_deck(self.deck_id, cue)
                        self.playhead_changed.emit(cue)
                    except Exception:
                        pass
            self.playback_engine.play_deck(self.deck_id)  # STREAM start
            if not self._playhead_timer.isActive():
                self._playhead_timer.start()
            self.play_state_changed.emit(True)
            self.status_changed.emit("▶ Odtwarzanie")
        except Exception as e:
            logger.warning(f"SimpleDeck {self.deck_id} play błąd: {e}")

    def pause(self) -> None:
        """Pauza + stop timera. STREAM op."""
        if not self.playback_engine:
            return
        try:
            self.playback_engine.pause_deck(self.deck_id)
            self._playhead_timer.stop()
            self.play_state_changed.emit(False)
            self.status_changed.emit("❚❚ Pauza")
        except Exception as e:
            logger.warning(f"SimpleDeck {self.deck_id} pause błąd: {e}")

    def stop(self) -> None:
        """Stop + timer off + playhead do cue (lub 0). STREAM + cue reset."""
        if not self.playback_engine:
            return
        try:
            self.playback_engine.stop_deck(self.deck_id)
            self._playhead_timer.stop()
            cue = getattr(self, "_main_cue_ms", 0) or 0
            self.playhead_changed.emit(cue)
            self.play_state_changed.emit(False)
            self.status_changed.emit("■ Stop")
        except Exception as e:
            logger.warning(f"SimpleDeck {self.deck_id} stop błąd: {e}")

    def seek(self, time_ms: int) -> None:
        """Seek bez snap (brak quantize w MVP). STREAM position change."""
        if not self.playback_engine:
            return
        try:
            dur = 0
            st = self.playback_engine.get_deck_state(self.deck_id)
            if st and st.duration_ms:
                dur = st.duration_ms
            t = max(0, min(int(time_ms), dur))
            self.playback_engine.seek_deck(self.deck_id, t)
            self.playhead_changed.emit(t)
        except Exception as e:
            logger.warning(f"SimpleDeck {self.deck_id} seek błąd: {e}")

    def set_cue(self) -> None:
        """Ustaw _main_cue_ms na bieżącej pozycji (dla play prefer logic).
        Nie zmienia pliku, tylko pozycję cue dla tego streamu.
        """
        if not self.playback_engine:
            return
        try:
            state = self.playback_engine.get_deck_state(self.deck_id)
            pos = state.position_ms if state else 0
            self._main_cue_ms = max(0, int(pos))
            self.status_changed.emit("CUE SET")
            logger.debug(
                f"SimpleDeck {self.deck_id}: _main_cue_ms = {self._main_cue_ms}"
            )
        except Exception as e:
            logger.warning(f"SimpleDeck {self.deck_id} set_cue błąd: {e}")

    def request_waveform_load(self, waveform_widget: Any, audio_path: str,
                              duration_ms: int) -> None:
        """
        Dla widoku: async peak extract (prosty runnable).
        Chroni tokenem. View woła po track_loaded.
        """
        if not audio_path or waveform_widget is None:
            return
        token = str(audio_path)
        self._current_waveform_token = token
        runnable = _SimpleWaveformRunnable(audio_path, duration_ms, waveform_widget, token)
        QtCore.QThreadPool.globalInstance().start(runnable)

    # ------------------------------------------------------------------
    # Timer + state
    # ------------------------------------------------------------------
    def _on_playhead_tick(self) -> None:
        """Tick – lepszy use of backend state (position + is_playing z DeckState)."""
        if not self.playback_engine:
            return
        try:
            state = self.playback_engine.get_deck_state(self.deck_id)
            if state:
                self.playhead_changed.emit(state.position_ms)
                try:
                    is_play = bool(getattr(state, "is_playing", False))
                    self.play_state_changed.emit(is_play)
                    if not is_play:
                        self._playhead_timer.stop()
                except Exception:
                    pass
        except Exception:
            pass

    def set_compact_mode(self, compact: bool) -> None:
        """Store compact flag (UI driven in view; controller for consistency/extend).
        Per spec: extend compact to simple + odt.
        """
        self._compact = bool(compact)
        # No direct UI here; view listens/reacts. Status for debug.
        self.status_changed.emit("compact on" if compact else "compact off")


# ------------------------------------------------------------------
# Prosty wewnętrzny runnable (skopiowany wzorzec, uproszczony)
# ------------------------------------------------------------------
class _SimpleWaveformRunnable(QtCore.QRunnable):
    """QRunnable do ekstrakcji peaków w tle dla Odtwarzacz MVP.
    Używa _safe_extract_peaks (core.waveform + fallback).
    Chroni tokenem, wywołuje load_waveform queued.
    """

    def __init__(self, audio_path: str, duration_ms: int, waveform_widget: Any, token: str):
        super().__init__()
        self.setAutoDelete(True)
        self._path = str(audio_path)
        self._duration = int(duration_ms)
        self._wave = waveform_widget
        self._token = token

    def run(self) -> None:
        try:
            peaks = _safe_extract_peaks(self._path, 900)
            QtCore.QMetaObject.invokeMethod(
                self._wave,
                "load_waveform",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(list, peaks),
                QtCore.Q_ARG(int, self._duration),
                QtCore.Q_ARG(str, self._token or ""),
            )
        except Exception as e:
            logger.warning(f"_SimpleWaveformRunnable błąd dla {self._path}: {e}")
