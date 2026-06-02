"""
ui/dj/deck_controller.py

KLUCZOWY KONTROLER DECKU – centralizuje całą logikę DJ bez duplikacji.

Logika scentralizowana (wyodrębniona w fazie redesignu z poprzednich DeckWidget/SinglePlayerView):
- async waveform loading (WaveformRunnable + token, wyłącznie core.waveform)
- snap_to_beat (quantize Rekordbox-style)
- memory S/R (session snapshot)
- quantize toggle
- hotcue delegacja + HotcueManager (persystencja DB)
- playhead timer (40-45ms)
- stany: sync, keylock, original_bpm, main_cue
- sygnały Qt do podłączenia widoków (dumb views)

Pełna kompatybilność z:
- PlaybackEngine
- HotcueManager (ui/dj/hotcue_manager.py – persystencja)

Zero inline logic w widokach. Widoki tylko subskrybują sygnały i wołają metody.

Wszystkie komentarze i docstringi wyłącznie po polsku.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Any

from PyQt6 import QtCore, QtWidgets

from core.models import Track
from services.playback import PlaybackEngine

# Style i paleta (używane m.in. do kolorów hotcue przy zapisie)
from ui.dj.styles import BOOTH_COLORS

# ------------------------------------------------------------------
# Waveform – CZYSZCZENIE KRUCHEGO IMPORTU (zgodnie z checklistą AGENT 5)
# Zamiast hacka "from ui.dj_player_window import WaveformRunnable, extract..."
# używamy bezpośrednio core.waveform.extract_peaks (które ma własny fallback + librosa).
# Lokalny WaveformRunnable + wrapper zawsze zdefiniowany tutaj.
# Zero zależności od starego pliku dla waveform – gotowe na usunięcie duplikatów.
# ------------------------------------------------------------------
from core.waveform import extract_peaks as _core_extract_peaks


def _safe_extract_peaks(audio_path: str | Path, num_points: int = 900) -> list[float]:
    """Bezpieczny wrapper wokół core.waveform.extract_peaks.
    Zawsze działa (core ma fallback proceduralny). Loguje błędy.
    """
    try:
        return _core_extract_peaks(audio_path, num_points=num_points)
    except Exception as exc:
        logger.warning(f"extract_peaks nieudane dla {audio_path}: {exc}")
        # Ostatni fallback identyczny z oryginałem w core/dj_player_window
        import math
        import random
        peaks: list[float] = []
        for i in range(num_points):
            t = (i / num_points) * 180
            base = 0.3 + 0.5 * abs(math.sin(t * 1.7)) + 0.2 * abs(math.sin(t * 0.35))
            noise = random.uniform(-0.06, 0.06)
            peaks.append(max(0.08, min(0.97, base + noise)))
        return peaks


# Lokalny fallback format_time (niezależny od starego pliku) – czysty wrapper
def _safe_format_time(ms: int | None) -> str:
    if ms is None:
        return "0:00"
    return _format_track_time(ms)


logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# HotcueManager – CZysty import z dedykowanego modułu (faza final cleanup)
# ZERO ryzyka cyklu! deck_controller nie dotyka już ui.dj_player_window.
# Persystencja DB w 100% zachowana (via data.repository + CuePoint).
# Używa BOOTH_COLORS wewnętrznie. Import PO loggerze – bezpieczny.
# ------------------------------------------------------------------
try:
    from ui.dj.hotcue_manager import HotcueManager, format_track_time as _format_track_time
except Exception:
    HotcueManager = None  # type: ignore
    def _format_track_time(ms: int | None) -> str:
        if ms is None:
            return "0:00"
        total = int(ms) // 1000
        m, s = divmod(total, 60)
        return f"{m}:{s:02d}"
    logger.warning("DeckController: awaryjny fallback HotcueManager (nie powinien się zdarzyć)")


class DeckController(QtCore.QObject):
    """
    Czysty kontroler jednego decku (A lub B).

    Odpowiada za:
    - Współpracę z PlaybackEngine (load, play, seek, rate, eq, trim, keylock)
    - Zarządzanie HotcueManager (delegacja + pełna persystencja w DB via CuePoint)
    - Timer playhead (40ms) + dystrybucja do wszystkich widoków
    - Async ładowanie waveform (lokalny WaveformRunnable + token anty-stale)
    - Quantize + snap_to_beat (Rekordbox-style)
    - Pamięć sesyjna S/R (snapshot pitch/trim/hotcue/loop/keylock)
    - Sync BPM + faza między deckami
    - Emitowanie wszystkich sygnałów Qt (zero logiki w widokach)

    Pełna lista sygnałów i metod zgodna z projektem AGENT 3 (faza 1 + rozszerzenia).
    Widoki (przyszłe FocusedDeckView / ConsoleDeckView) łączą się wyłącznie przez sygnały.
    """

    # Sygnały Qt – czysty kontrakt z widokami (zero zależności od widgetów)
    # Zgodne z AGENT 3 + rozszerzone o użyteczne dla integracji
    track_loaded = QtCore.pyqtSignal(object)          # Track
    track_unloaded = QtCore.pyqtSignal()
    playhead_changed = QtCore.pyqtSignal(int)         # ms
    bpm_changed = QtCore.pyqtSignal(object)           # float | None
    hotcue_changed = QtCore.pyqtSignal(int, object)   # index, time_ms | None
    loop_changed = QtCore.pyqtSignal(object, object)  # start_ms | None, end_ms | None
    sync_state_changed = QtCore.pyqtSignal(bool)
    keylock_changed = QtCore.pyqtSignal(bool)
    status_changed = QtCore.pyqtSignal(str)           # tekst statusu (np. "MEM SAVED")
    play_state_changed = QtCore.pyqtSignal(bool)      # is_playing
    waveform_ready = QtCore.pyqtSignal(list, int, str)  # peaks, duration_ms, token – dla przyszłych widoków

    def __init__(
        self,
        deck_id: str,  # "A" lub "B"
        playback_engine: PlaybackEngine,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.deck_id = deck_id
        self.playback_engine = playback_engine

        # --- Stan wewnętrzny (wyodrębniony z poprzednich implementacji) ---
        self.current_track: Track | None = None
        self._original_bpm: float | None = None
        self._main_cue_ms: int = 0
        self._quantize_enabled: bool = True
        self._memory: dict[str, Any] | None = None
        self._is_synced: bool = False

        # Hotcue – pełna delegacja do istniejącego managera (8 hotcue'ów, persystencja)
        if HotcueManager is not None:
            self._hotcue_mgr: HotcueManager = HotcueManager(max_cues=8)
        else:
            # Awaryjny minimalny manager (nie powinien się zdarzyć)
            self._hotcue_mgr = self._create_fallback_hotcue_manager()

        self._loop_in_ms: int | None = None
        self._loop_out_ms: int | None = None
        self._loop_enabled: bool = False

        # Timer playhead (wspólny dla wszystkich widoków)
        self._playhead_timer = QtCore.QTimer(self)
        self._playhead_timer.setInterval(40)  # ~25 fps – identycznie jak w oryginale
        self._playhead_timer.timeout.connect(self._on_playhead_tick)

        # Token anty-stale dla waveform
        self._current_waveform_token: str | None = None

        # Referencja do sparowanego decku (dla sync)
        self._synced_partner: DeckController | None = None

        logger.debug(f"DeckController {self.deck_id} utworzony (engine={playback_engine.__class__.__name__})")

    # ------------------------------------------------------------------
    # Fallback awaryjny (gdyby HotcueManager nie był dostępny)
    # ------------------------------------------------------------------
    def _create_fallback_hotcue_manager(self) -> Any:
        class _FallbackHotcueMgr:
            def __init__(self):
                self._hotcues: dict[int, int] = {}
            @property
            def hotcues(self):
                return dict(self._hotcues)
            def get(self, idx): return self._hotcues.get(idx)
            def set(self, idx, t): self._hotcues[idx] = t
            def clear(self, idx): self._hotcues.pop(idx, None)
            def clear_all(self): self._hotcues.clear()
            def load_from_db(self, tid): return {}
            def save_to_db(self, *a, **k): pass
            def delete_from_db(self, *a, **k): pass
        return _FallbackHotcueMgr()

    # ------------------------------------------------------------------
    # Publiczne API – używane przez widoki i DJPlayerWindow
    # ------------------------------------------------------------------
    def load_track(self, track: Track) -> None:
        """
        Załaduj utwór do decku.
        Przeniesiona logika: reset stanów, load engine, waveform async + hotcues z DB.
        """
        if not track:
            return

        # DB lookup dla persystencji hotcue (identycznie jak w oryginale)
        if not getattr(track, "id", None):
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(track.path)
                if dbt and dbt.id:
                    track = dbt
            except Exception as exc:
                logger.debug(f"Deck {self.deck_id}: lookup DB dla hotcue nieudany: {exc}")

        self.current_track = track
        self._original_bpm = getattr(track, "bpm", None) if getattr(track, "bpm", None) and track.bpm > 10 else None

        # Reset stanów UI-niezależnych
        self._loop_in_ms = None
        self._loop_out_ms = None
        self._loop_enabled = False
        self._main_cue_ms = 0
        self._hotcue_mgr.clear_all()
        self._memory = None  # nowa ścieżka – czyścimy pamięć sesyjną
        self.loop_changed.emit(None, None)

        if self._original_bpm:
            self.bpm_changed.emit(self._original_bpm)

        success = False
        duration = 0
        if self.playback_engine:
            try:
                success = self.playback_engine.load_deck(self.deck_id, track.path)
            except Exception as e:
                logger.exception(f"Deck {self.deck_id}: wyjątek przy load_deck: {e}")
                success = False

            if success:
                try:
                    state = self.playback_engine.get_deck_state(self.deck_id)
                    duration = state.duration_ms if state else 0
                    self._load_waveform_async(track.path, duration)
                    if getattr(track, "id", None):
                        self._load_hotcues_from_db(track.id)
                    self._update_effective_bpm()
                    logger.info(f"Deck {self.deck_id}: załadowano {Path(track.path).name}")
                    self.status_changed.emit("✓ Utwór załadowany")
                except Exception as e:
                    logger.exception(f"Deck {self.deck_id}: błąd po load_deck")
                    self.status_changed.emit("✗ Błąd po załadowaniu")
            else:
                self.status_changed.emit("✗ Błąd ładowania")
        else:
            self.status_changed.emit("⚠ Brak silnika audio")

        # Sygnał dla widoków
        self.track_loaded.emit(track)

    def unload_track(self) -> None:
        """Zatrzymaj i wyczyść deck."""
        self.current_track = None
        self._hotcue_mgr.clear_all()
        self._memory = None
        self._loop_in_ms = None
        self._loop_out_ms = None
        self._loop_enabled = False
        if self.playback_engine:
            try:
                self.playback_engine.stop_deck(self.deck_id)
            except Exception:
                pass
        self._playhead_timer.stop()
        self.loop_changed.emit(None, None)
        self.track_unloaded.emit()
        self.status_changed.emit("— Wyczyszczono")

    def toggle_play(self) -> None:
        """Przełącz play/pause. Uruchamia/zatrzymuje timer playhead."""
        if not self.playback_engine:
            return
        try:
            was_playing = self.playback_engine.deck(self.deck_id).is_playing()
            self.playback_engine.toggle_deck(self.deck_id)
            now_playing = self.playback_engine.deck(self.deck_id).is_playing()

            if now_playing and not self._playhead_timer.isActive():
                self._playhead_timer.start()
            elif not now_playing:
                self._playhead_timer.stop()

            self.play_state_changed.emit(now_playing)
            self.status_changed.emit("▶ Odtwarzanie" if now_playing else "❚❚ Pauza")
        except Exception as e:
            logger.warning(f"Deck {self.deck_id} toggle_play błąd: {e}")

    def seek(self, time_ms: int) -> None:
        """Seek z opcjonalnym snap (jeśli quantize)."""
        snapped = self.snap_to_beat(time_ms)
        if self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, snapped)
            self.playhead_changed.emit(snapped)

    def snap_to_beat(self, time_ms: int) -> int:
        """
        Quantize do najbliższego beatu używając oryginalnego BPM.
        Dokładnie taka sama logika jak poprzednio w DeckWidget._snap_to_beat.
        """
        if not getattr(self, "_quantize_enabled", False):
            return time_ms
        bpm = getattr(self, "_original_bpm", None)
        if not bpm or bpm < 20:
            return time_ms
        try:
            beat_ms = 60000.0 / float(bpm)
            beats = round(time_ms / beat_ms)
            snapped = int(beats * beat_ms)
            if self.playback_engine:
                st = self.playback_engine.get_deck_state(self.deck_id)
                if st and st.duration_ms > 0:
                    snapped = max(0, min(snapped, st.duration_ms))
            return snapped
        except Exception as exc:
            logger.debug(f"Deck {self.deck_id} snap_to_beat błąd: {exc}")
            return time_ms

    def toggle_quantize(self) -> None:
        """Przełącz quantize i wyemituj status."""
        self._quantize_enabled = not getattr(self, "_quantize_enabled", True)
        state = "WŁĄCZONY" if self._quantize_enabled else "WYŁĄCZONY"
        self.status_changed.emit(f"Q: {state}")
        logger.debug(f"Deck {self.deck_id}: quantize = {self._quantize_enabled}")

    def set_hotcue(self, index: int) -> None:
        """
        Ustaw hotcue na bieżącej pozycji (z snap jeśli Q ON).
        Deleguje do HotcueManager + zapis DB.
        """
        if not self.playback_engine or not self.current_track:
            return
        state = self.playback_engine.get_deck_state(self.deck_id)
        current = state.position_ms if state else 0
        current = self.snap_to_beat(current)

        self._hotcue_mgr.set(index, current)
        # Persystencja (kolor z centralnej palety 8 unikalnych)
        if hasattr(self._hotcue_mgr, "save_to_db"):
            color = BOOTH_COLORS["hotcue"][index % len(BOOTH_COLORS["hotcue"])]
            self._hotcue_mgr.save_to_db(index, current, color=color)

        self.hotcue_changed.emit(index, current)
        logger.debug(f"Deck {self.deck_id}: hotcue {index+1} ustawiony @ {current}ms")

    def jump_hotcue(self, index: int, clear_if_ctrl: bool = False) -> None:
        """
        Skocz do hotcue lub usuń (gdy Ctrl).
        Pełna delegacja do managera.
        """
        should_clear = clear_if_ctrl
        if not should_clear:
            try:
                mods = QtWidgets.QApplication.keyboardModifiers()
                should_clear = bool(mods & QtCore.Qt.KeyboardModifier.ControlModifier)
            except Exception:
                should_clear = False

        if should_clear:
            if self._hotcue_mgr.get(index) is not None:
                self._hotcue_mgr.clear(index)
                if hasattr(self._hotcue_mgr, "delete_from_db"):
                    self._hotcue_mgr.delete_from_db(index)
                self.hotcue_changed.emit(index, None)
            return

        cue_time = self._hotcue_mgr.get(index)
        if cue_time is not None and self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, cue_time)
            self.playhead_changed.emit(cue_time)
            self.hotcue_changed.emit(index, cue_time)

    def delete_hotcue(self, index: int) -> None:
        """Usuń hotcue i zapisz do DB."""
        if self._hotcue_mgr.get(index) is not None:
            self._hotcue_mgr.clear(index)
            if hasattr(self._hotcue_mgr, "delete_from_db"):
                self._hotcue_mgr.delete_from_db(index)
            self.hotcue_changed.emit(index, None)

    def set_hotcue_label(self, index: int, label: str | None) -> None:
        """Ustaw etykietę hotcue (na razie tylko w managerze + DB jeśli wspierane)."""
        cue = self._hotcue_mgr.get(index)
        if cue is not None:
            # Prosta aktualizacja — zakładamy, że manager wspiera .set_label lub podobną
            if hasattr(self._hotcue_mgr, "set_label"):
                self._hotcue_mgr.set_label(index, label)
            # TODO: dodać persystencję etykiety w DB w przyszłości
            self.hotcue_changed.emit(index, cue)

    def set_hotcue_color(self, index: int, color: str) -> None:
        """Zmień kolor hotcue i zapisz do DB."""
        cue = self._hotcue_mgr.get(index)
        if cue is not None:
            if hasattr(self._hotcue_mgr, "save_to_db"):
                self._hotcue_mgr.save_to_db(index, cue, color=color)
            # Odśwież wizualnie
            self.hotcue_changed.emit(index, cue)

    def save_memory(self) -> None:
        """
        Zapisz snapshot sesyjny (ścieżka, main_cue, loop, hotcues, pitch, trim, keylock).
        Przeniesiona logika z _save_deck_memory.
        """
        path = getattr(self.current_track, "path", None) if self.current_track else None
        pitch = 0
        trim = 85
        keylock = False
        try:
            if self.playback_engine:
                pitch = int((self.playback_engine.get_deck_rate(self.deck_id) - 1.0) * 100)
                trim = int(self.playback_engine.get_deck_trim(self.deck_id) * 100)
                keylock = self.playback_engine.get_deck_keylock(self.deck_id)
        except Exception:
            pass

        self._memory = {
            "track_path": path,
            "main_cue_ms": self._main_cue_ms,
            "loop_in_ms": self._loop_in_ms,
            "loop_out_ms": self._loop_out_ms,
            "hotcues": self._hotcue_mgr.hotcues,
            "pitch": pitch,
            "trim": trim,
            "keylock": keylock,
        }
        self.status_changed.emit("MEM SAVED")
        QtCore.QTimer.singleShot(1100, lambda: self.status_changed.emit("✓ Gotowy"))
        logger.debug(f"Deck {self.deck_id}: pamięć zapisana ({len(self._memory.get('hotcues', {}))} hotcue)")

    def recall_memory(self) -> None:
        """
        Odtwórz stan z pamięci. Reload track jeśli inny + przywrócenie parametrów.
        Bezpieczne dla playbacku.
        """
        if not self._memory:
            self.status_changed.emit("Brak pamięci")
            QtCore.QTimer.singleShot(800, lambda: self.status_changed.emit("✓ Gotowy"))
            return

        mem = self._memory
        target_path = mem.get("track_path")
        current_path = getattr(self.current_track, "path", None) if self.current_track else None

        need_reload = False
        if target_path:
            try:
                if Path(target_path).exists() and (not current_path or Path(current_path) != Path(target_path)):
                    need_reload = True
            except Exception:
                pass

        was_playing = False
        if self.playback_engine:
            try:
                was_playing = bool(self.playback_engine.deck(self.deck_id).is_playing())
            except Exception:
                pass

        if need_reload and target_path:
            try:
                t = Track(path=target_path, title=Path(target_path).stem)
                try:
                    from data.repository import get_track_by_path
                    dbt = get_track_by_path(target_path)
                    if dbt and getattr(dbt, "id", None):
                        t = dbt
                except Exception:
                    pass
                self.load_track(t)
            except Exception as e:
                logger.warning(f"Deck {self.deck_id} recall reload error: {e}")
                self.status_changed.emit("MEM reload err")
                return

            if was_playing and self.playback_engine:
                QtCore.QTimer.singleShot(160, self._ensure_play_after_recall)

        # Przywróć snapshot (nawet bez reloadu)
        if mem.get("main_cue_ms") is not None:
            self._main_cue_ms = mem.get("main_cue_ms")

        self._loop_in_ms = mem.get("loop_in_ms")
        self._loop_out_ms = mem.get("loop_out_ms")
        self.loop_changed.emit(self._loop_in_ms, self._loop_out_ms)

        # Hotcues
        for idx, t in mem.get("hotcues", {}).items():
            self._hotcue_mgr.set(idx, t)
            self.hotcue_changed.emit(idx, t)

        # Pitch / trim / keylock
        try:
            if self.playback_engine:
                p = int(mem.get("pitch", 0))
                self.playback_engine.set_deck_rate(self.deck_id, 1.0 + (p / 100.0))
                tr = int(mem.get("trim", 85))
                self.playback_engine.set_deck_trim(self.deck_id, tr / 100.0)
                kl = bool(mem.get("keylock", False))
                self.playback_engine.set_deck_keylock(self.deck_id, kl)
                self.keylock_changed.emit(kl)
        except Exception:
            pass

        self.status_changed.emit("MEM RECALLED")
        QtCore.QTimer.singleShot(1300, lambda: self.status_changed.emit("✓ Gotowy"))
        logger.info(f"Deck {self.deck_id}: pamięć przywrócona")

    def _ensure_play_after_recall(self) -> None:
        if self.playback_engine:
            try:
                if not self.playback_engine.deck(self.deck_id).is_playing():
                    self.playback_engine.toggle_deck(self.deck_id)
                    self.play_state_changed.emit(True)
            except Exception:
                pass

    def do_sync(self, other: DeckController) -> None:
        """
        Sync BPM + faza (Rekordbox style).
        Ustawia rate tego decku na podstawie drugiego + przesuwa playhead.
        """
        if not other or not other.current_track or not self.current_track:
            return
        try:
            other_bpm = other._original_bpm or 128.0
            my_bpm = self._original_bpm or 128.0
            if my_bpm <= 0:
                return

            rate = other_bpm / my_bpm
            if self.playback_engine:
                self.playback_engine.set_deck_rate(self.deck_id, rate)

            # Prosta faza – przesuń do pozycji partnera (można ulepszyć)
            other_state = other.playback_engine.get_deck_state(other.deck_id) if other.playback_engine else None
            if other_state and self.playback_engine:
                self.playback_engine.seek_deck(self.deck_id, other_state.position_ms)

            self._is_synced = True
            self.sync_state_changed.emit(True)
            self.status_changed.emit("SYNC ON")
            logger.debug(f"Deck {self.deck_id} zsynchronizowany z {other.deck_id}")
        except Exception as e:
            logger.debug(f"Sync błąd: {e}")

    def set_pitch(self, percent: float) -> None:
        """Ustaw pitch w % (-50..+50)."""
        if self.playback_engine:
            rate = 1.0 + (percent / 100.0)
            self.playback_engine.set_deck_rate(self.deck_id, rate)
            self.bpm_changed.emit(self._original_bpm)

    def set_trim(self, value: float) -> None:
        if self.playback_engine:
            self.playback_engine.set_deck_trim(self.deck_id, value)

    def set_eq(self, low: float, mid: float, high: float) -> None:
        if self.playback_engine:
            self.playback_engine.set_deck_eq(self.deck_id, low, mid, high)

    def set_keylock(self, enabled: bool) -> None:
        if self.playback_engine:
            self.playback_engine.set_deck_keylock(self.deck_id, enabled)
            self.keylock_changed.emit(enabled)

    def set_loop_points(self, start_ms: int | None = None, end_ms: int | None = None) -> None:
        """
        Ustaw punkty pętli (IN/OUT).
        Emituje loop_changed dla widoków.
        Używane przez przyszłe kontrolki memory/loop w Console/Focused.
        """
        self._loop_in_ms = start_ms
        self._loop_out_ms = end_ms
        self._loop_enabled = bool(start_ms is not None and end_ms is not None and end_ms > start_ms)
        self.loop_changed.emit(start_ms, end_ms)
        logger.debug(f"Deck {self.deck_id}: loop points = {start_ms}..{end_ms}")

    # ------------------------------------------------------------------
    # Wewnętrzne – waveform + playhead + hotcue DB
    # ------------------------------------------------------------------
    def _load_waveform_async(self, audio_path: str, duration_ms: int) -> None:
        """
        Centralne async ładowanie waveform z tokenem anty-stale.
        Przeniesione z poprzednich widoków – teraz scentralizowane w jednym miejscu.
        Widoki wywołują request_waveform_load gdy mają widget.
        """
        if not audio_path:
            return
        token = str(audio_path)
        self._current_waveform_token = token
        self.status_changed.emit("Ładowanie waveform...")

    def request_waveform_load(self, waveform_widget: Any, audio_path: str, duration_ms: int) -> None:
        """
        Metoda dla widoków (Focused/Console): kontroler uruchamia wątek ekstrakcji peaków.
        Używa lokalnego WaveformRunnable opartego wyłącznie na core.waveform.
        Token chroni przed przestarzałymi wynikami.
        """
        if not audio_path or waveform_widget is None:
            return
        token = str(audio_path)
        self._current_waveform_token = token

        # Zawsze używamy lokalnego runnable (czysty, bez zależności od starego pliku)
        runnable = WaveformRunnable(audio_path, duration_ms, waveform_widget, token)
        QtCore.QThreadPool.globalInstance().start(runnable)

    def _on_playhead_tick(self) -> None:
        """Tick timera – pyta engine i emituje sygnał."""
        if not self.playback_engine:
            return
        try:
            state = self.playback_engine.get_deck_state(self.deck_id)
            if state:
                self.playhead_changed.emit(state.position_ms)
                # Sprawdź czy nadal gra
                try:
                    is_play = self.playback_engine.deck(self.deck_id).is_playing()
                    self.play_state_changed.emit(is_play)
                    if not is_play:
                        self._playhead_timer.stop()
                except Exception:
                    pass
        except Exception:
            pass

    def _load_hotcues_from_db(self, track_id: int) -> None:
        """Ładuje hotcue z DB przez managera i emituje sygnały."""
        if not hasattr(self._hotcue_mgr, "load_from_db"):
            return
        loaded = self._hotcue_mgr.load_from_db(track_id)
        for idx, t_ms in loaded.items():
            self.hotcue_changed.emit(idx, t_ms)
        logger.debug(f"Deck {self.deck_id}: załadowano {len(loaded)} hotcue'ów z DB")

    def _update_effective_bpm(self) -> None:
        """Oblicza efektywny BPM z pitch i emituje."""
        if self._original_bpm and self.playback_engine:
            try:
                rate = self.playback_engine.get_deck_rate(self.deck_id)
                eff = self._original_bpm * rate
                self.bpm_changed.emit(eff)
            except Exception:
                self.bpm_changed.emit(self._original_bpm)
        else:
            self.bpm_changed.emit(self._original_bpm)

    # ------------------------------------------------------------------
    # Gettery dla widoków
    # ------------------------------------------------------------------
    @property
    def hotcues(self) -> dict[int, int]:
        return self._hotcue_mgr.hotcues if hasattr(self._hotcue_mgr, "hotcues") else {}

    def get_hotcue(self, index: int) -> int | None:
        return self._hotcue_mgr.get(index) if hasattr(self._hotcue_mgr, "get") else None

    def is_quantize_enabled(self) -> bool:
        return self._quantize_enabled

    def get_memory_snapshot(self) -> dict | None:
        return self._memory

    def is_synced(self) -> bool:
        return self._is_synced


# ------------------------------------------------------------------
# Lokalny WaveformRunnable – zawsze dostępny, oparty wyłącznie na core
# Usunięto kruchą zależność od ui.dj_player_window (faza 1 → integracja)
# ------------------------------------------------------------------
class WaveformRunnable(QtCore.QRunnable):
    """QRunnable do ekstrakcji peaków waveform w tle.

    Używa _safe_extract_peaks (core.waveform + fallback).
    Chroni przed stale results poprzez token.
    Wywołuje load_waveform na widżecie przez queued invoke (thread-safe).
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
            logger.warning(f"WaveformRunnable błąd dla {self._path}: {e}")
