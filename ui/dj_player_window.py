from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets
from pathlib import Path
from typing import Optional
import logging

from core.models import Track  # CuePoint używany wyłącznie w ui/dj/hotcue_manager.py
from core.waveform import WaveformData, generate_waveform_threadsafe, extract_peaks

# Nowa architektura (faza równoległa redesignu) - sole implementation, hardcoded
from ui.dj.deck_controller import DeckController
from ui.dj.views import (
    FocusedDeckView,
    ConsoleDeckView,
    DualConsoleWidget,
    MixerStrip,
)
print("[DJ] Nowa architektura zaimportowana pomyślnie (DeckController + views) - sole impl")

# Nowy, solidny backend audio
from services.playback import PlaybackEngine, create_backend

# ------------------------------------------------------------------
# HotcueManager + format_track_time – CZYSTY MODUŁ (faza final cleanup)
# Przeniesione do ui/dj/hotcue_manager.py – ZERO zależności od tego monstrualnego pliku.
# Usunięte ryzyko cyklu importów (deck_controller nie importuje już stąd).
# Używa BOOTH_COLORS wewnętrznie. Pełna kompatybilność wstecz.
# ------------------------------------------------------------------
try:
    from ui.dj.hotcue_manager import HotcueManager, format_track_time
    _HAS_HOTCUE_MANAGER = True
except Exception:
    _HAS_HOTCUE_MANAGER = False
    HotcueManager = None  # type: ignore
    def format_track_time(ms: int | None) -> str:  # fallback awaryjny
        if ms is None:
            return "0:00"
        total = max(0, int(ms)) // 1000
        m, s = divmod(total, 60)
        return f"{m}:{s:02d}"
    print("Nie udało się zaimportować HotcueManager z ui.dj.hotcue_manager – tryb awaryjny (logger niegotowy)")

# (Usunięto martwe importy cue repo – HotcueManager + persystencja teraz wyłącznie w ui/dj/hotcue_manager.py)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# REFACTOR: format_track_time + HotcueManager przeniesione do ui/dj/hotcue_manager.py
# (patrz import na górze pliku). Ten plik używa re-eksportu – zero duplikacji.
# ------------------------------------------------------------------

class SectionLabel(QtWidgets.QLabel):
    """Spójny label sekcji w stylu Rekordbox (mały, mocny, z letter-spacing)."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {COLORS.get('section_label', COLORS['text_muted'])};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.2px;
            padding-top: 4px;
            padding-bottom: 2px;
        """)


class HotcueGrid(QtWidgets.QWidget):
    """Profesjonalny grid hotcue'ów (domyślnie 2x4 = 8 padów). Łatwo zmienić na 1x4 lub 2x4."""
    def __init__(self, num_cues: int = 8, pad_size=(88, 58), parent=None):
        super().__init__(parent)
        self.pads: list[HotcuePad] = []
        grid = QtWidgets.QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        cols = 4
        for i in range(num_cues):
            pad = HotcuePad(i)
            pad.setFixedSize(*pad_size)
            self.pads.append(pad)
            row, col = divmod(i, cols)
            grid.addWidget(pad, row, col)


# Note: extract_peaks (and its internal _generate_fallback) now lives in core/waveform.py
# for reuse by library detail panel (eliminates ffmpeg dependency for small previews).
# We keep a thin local wrapper for logging + default num_points used by WaveformWidget.
def extract_peaks_from_audio(audio_path: str | Path, num_points: int = 900) -> list[float]:
    try:
        return extract_peaks(audio_path, num_points=num_points)
    except Exception as e:
        logger.warning(f"Failed to extract peaks from {audio_path}: {e}")
        # Last-resort local fallback (should never happen)
        import math, random
        peaks = []
        for i in range(num_points):
            t = (i / num_points) * 180
            base = 0.3 + 0.5 * abs(math.sin(t * 1.7)) + 0.2 * abs(math.sin(t * 0.35))
            noise = random.uniform(-0.06, 0.06)
            peaks.append(max(0.08, min(0.97, base + noise)))
        return peaks


class WaveformRunnable(QtCore.QRunnable):
    """Safe QRunnable for offloading librosa peak extraction to QThreadPool.
    Replaces bare function (which caused TypeError on .start()).
    Includes captured path token for stale-result protection.
    """

    def __init__(self, audio_path: str, duration_ms: int, waveform_widget: "WaveformWidget", token: str):
        super().__init__()
        self.setAutoDelete(True)
        self._path = str(audio_path)
        self._duration_ms = int(duration_ms)
        self._waveform = waveform_widget
        self._token = token

    def run(self) -> None:
        try:
            peaks = extract_peaks_from_audio(self._path, num_points=900)
            QtCore.QMetaObject.invokeMethod(
                self._waveform,
                "load_waveform",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(list, peaks),
                QtCore.Q_ARG(int, self._duration_ms),
                QtCore.Q_ARG(str, self._token or ""),
            )
        except Exception as e:
            logger.warning(f"Waveform generation failed for {self._path}: {e}")


# Pro DJ booth high-contrast dark theme (Rekordbox/Traktor level readability)
# Optimized for dark rooms, quick glances, low eye strain
COLORS = {
    "bg": "#0a0e17",
    "panel": "#121a28",
    "panel_border": "#1f2a40",
    "wave_bg": "#0c111c",
    "wave_peak": "#4fd1ff",
    "wave_rms": "#1e3a52",
    "playhead": "#ff2d55",
    "playhead_glow": "#ff6b8a",
    "text": "#f4f7fc",
    "text_muted": "#c5d0e0",
    "accent": "#4fd1ff",
    "accent_green": "#22c55e",
    "warning": "#facc15",
    "hotcue": ["#14b8a6", "#f59e0b", "#ec4899", "#6366f1"],
    "hotcue_active": "#ffffff",
    "loop": "#60a5fa",
}


class WaveformWidget(QtWidgets.QWidget):
    """
    Professional DJ waveform with:
    - Real peaks (librosa or fallback)
    - BPM-aware musical beatgrid (bars + beats when BPM known)
    - High-visibility playhead with glow
    - Loop region highlight
    - Seek + Shift+click cue
    """
    seek_requested = QtCore.pyqtSignal(int)
    cue_set_requested = QtCore.pyqtSignal(int)   # Shift + click
    double_clicked = QtCore.pyqtSignal(int)      # Double-click: pro "set main cue + preview jump"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(162)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Waveform: Click=seek  •  Shift+Click=set hotcue  •  Double-click=set main CUE (quantized if deck Q ON)")

        # Data
        self._peaks: list[float] = []
        self._duration_ms: int = 0
        self._playhead_ms: int = 0
        self._show_beatgrid: bool = True
        self._bpm: float | None = None
        self._loading: bool = False
        self._current_token: Optional[str] = None  # for stale waveform update protection

        # Loop
        self._loop_start_ms: int = -1
        self._loop_end_ms: int = -1

        # Colors (pro booth)
        self._col_bg = QtGui.QColor(COLORS["wave_bg"])
        self._col_peak = QtGui.QColor(COLORS["wave_peak"])
        self._col_rms = QtGui.QColor(COLORS["wave_rms"])
        self._col_playhead = QtGui.QColor(COLORS["playhead"])
        self._col_beat = QtGui.QColor(255, 255, 255, 70)       # regular beat
        self._col_bar = QtGui.QColor(255, 255, 255, 140)       # every 4th (bar)
        self._col_beatgrid = QtGui.QColor(255, 255, 255, 55)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @QtCore.pyqtSlot(list, int, str)
    def load_waveform(self, peaks: list[float] | None, duration_ms: int, token: str = ""):
        """Load real waveform peaks (thread-safe call via QThreadPool).
        Ignores deliveries with stale token (prevents UI showing waveform for a track
        that was already unloaded/replaced).
        """
        if token and self._current_token is not None and token != self._current_token:
            return
        self._peaks = peaks or []
        self._duration_ms = max(0, duration_ms)
        self._playhead_ms = 0
        self._loading = False
        self.update()

    def set_expected_waveform_token(self, token: Optional[str]) -> None:
        """Called by deck/single view before launching async waveform load.
        Subsequent load_waveform calls must match this token or they are dropped.
        """
        self._current_token = token

    def set_playhead(self, time_ms: int):
        if time_ms != self._playhead_ms:
            self._playhead_ms = max(0, min(time_ms, self._duration_ms))
            self.update()

    def set_beatgrid_visible(self, visible: bool):
        if self._show_beatgrid != visible:
            self._show_beatgrid = visible
            self.update()

    def set_bpm(self, bpm: float | None):
        """Set track BPM for musical (not arbitrary) beatgrid divisions."""
        if bpm and bpm > 20:
            self._bpm = float(bpm)
        else:
            self._bpm = None
        if self._show_beatgrid:
            self.update()

    def set_duration(self, duration_ms: int):
        """Legacy compat."""
        self._duration_ms = max(0, duration_ms)
        self.update()

    def clear(self):
        self._peaks = []
        self._duration_ms = 0
        self._playhead_ms = 0
        self._loop_start_ms = -1
        self._loop_end_ms = -1
        self._bpm = None
        self._current_token = None
        self.update()

    def set_loop(self, start_ms: int, end_ms: int):
        self._loop_start_ms = max(0, start_ms)
        self._loop_end_ms = max(self._loop_start_ms, end_ms)
        self.update()

    def clear_loop(self):
        self._loop_start_ms = -1
        self._loop_end_ms = -1
        self.update()

    # ------------------------------------------------------------------ #
    # Drawing - pro feel
    # ------------------------------------------------------------------ #

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        mid = h // 2

        painter.fillRect(0, 0, w, h, self._col_bg)

        if not self._peaks or self._duration_ms <= 0:
            painter.setPen(QtGui.QPen(self._col_rms, 1))
            painter.drawLine(0, mid, w, mid)
            self._draw_playhead(painter, w, h)
            painter.end()
            return

        n = len(self._peaks)
        pen_peak = QtGui.QPen(self._col_peak, 1)
        pen_rms = QtGui.QPen(self._col_rms, 1)

        # Waveform (classic + gain feel)
        for px in range(w):
            idx = int(px / w * n)
            if idx >= n:
                idx = n - 1
            amp = self._peaks[idx]

            ph = int(amp * mid * 0.94)
            rh = max(1, int(amp * mid * 0.36))

            painter.setPen(pen_rms)
            painter.drawLine(px, mid - rh, px, mid + rh)
            painter.setPen(pen_peak)
            painter.drawLine(px, mid - ph, px, mid - rh)
            painter.drawLine(px, mid + rh, px, mid + ph)

        # Loop region (more visible)
        if self._loop_start_ms >= 0 and self._loop_end_ms > self._loop_start_ms and self._duration_ms > 0:
            x1 = int(self._loop_start_ms / self._duration_ms * w)
            x2 = int(self._loop_end_ms / self._duration_ms * w)
            loop_color = QtGui.QColor(COLORS["loop"] + "30")  # semi-trans
            painter.fillRect(x1, 0, max(1, x2 - x1), h, QtGui.QColor(96, 165, 250, 48))

        # Musical beatgrid (the key pro upgrade)
        if self._show_beatgrid and self._duration_ms > 0:
            self._draw_musical_beatgrid(painter, w, h)

        self._draw_playhead(painter, w, h)
        painter.end()

    def _draw_musical_beatgrid(self, painter, w, h):
        """Draw beat-accurate lines using BPM when available. Falls back to 16ths."""
        if self._bpm and self._bpm > 20:
            beat_ms = 60000.0 / self._bpm
            duration = self._duration_ms
            if duration <= 0:
                return

            # Beats
            painter.setPen(QtGui.QPen(self._col_beat, 1, QtCore.Qt.PenStyle.DotLine))
            i = 1
            while True:
                t = i * beat_ms
                if t >= duration:
                    break
                px = int((t / duration) * w)
                if 0 < px < w:
                    painter.drawLine(px, 2, px, h - 2)
                i += 1

            # Bars (every 4 beats) - stronger
            painter.setPen(QtGui.QPen(self._col_bar, 1))
            i = 4
            while True:
                t = i * beat_ms
                if t >= duration:
                    break
                px = int((t / duration) * w)
                if 0 < px < w:
                    painter.drawLine(px, 0, px, h)
                i += 4
        else:
            # Legacy 16-division fallback (arbitrary but familiar)
            painter.setPen(QtGui.QPen(self._col_beatgrid, 1, QtCore.Qt.PenStyle.DashLine))
            for i in range(1, 16):
                px = int(w * (i / 16))
                painter.drawLine(px, 0, px, h)

    def _draw_playhead(self, painter, w, h):
        if self._duration_ms <= 0:
            return
        px = max(0, min(int(self._playhead_ms / self._duration_ms * w), w - 1))

        # Glow layers for pro visibility
        for offset, alpha in ((3, 18), (2, 35), (1, 70)):
            glow = QtGui.QColor(COLORS["playhead_glow"])
            glow.setAlpha(alpha)
            painter.setPen(QtGui.QPen(glow, 1 + offset * 0.6))
            painter.drawLine(px, 0, px, h)

        # Main playhead (thick, high contrast)
        painter.setPen(QtGui.QPen(self._col_playhead, 3))
        painter.drawLine(px, 0, px, h)

        # Small arrowhead at top for instant recognition
        arrow_size = 7
        painter.setBrush(self._col_playhead)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        path = QtGui.QPainterPath()
        path.moveTo(px - arrow_size, 0)
        path.lineTo(px + arrow_size, 0)
        path.lineTo(px, arrow_size + 1)
        path.closeSubpath()
        painter.drawPath(path)

    # ------------------------------------------------------------------ #
    # Interaction
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        if self._duration_ms <= 0:
            return
        t = int(event.position().x() / self.width() * self._duration_ms)
        t = max(0, min(t, self._duration_ms))

        if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.cue_set_requested.emit(t)
        else:
            self.seek_requested.emit(t)

    def mouseDoubleClickEvent(self, event):
        """Double-click waveform = set main cue point (for CUE button) + seek (pro DJ preview behavior).
        Respects quantize from parent deck if available (via signal consumer).
        """
        if self._duration_ms <= 0:
            return
        t = int(event.position().x() / self.width() * self._duration_ms)
        t = max(0, min(t, self._duration_ms))
        self.double_clicked.emit(t)
        # Also do an immediate seek so it feels responsive even before slot
        self.seek_requested.emit(t)

    def mouseMoveEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def time_at_x(self, x: int) -> int:
        """Zwraca czas w ms odpowiadający pozycji x na waveformie."""
        if self._duration_ms <= 0 or self.width() <= 0:
            return 0
        t = int(x / self.width() * self._duration_ms)
        return max(0, min(t, self._duration_ms))


class HotcuePad(QtWidgets.QPushButton):
    """
    Pro-grade hotcue pad:
    - Large, high-contrast, booth-friendly
    - Clear set vs empty state
    - Tooltip shows stored time (set on assignment)
    - Better hover/active visuals
    """
    activated = QtCore.pyqtSignal(int)
    set_requested = QtCore.pyqtSignal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._has_cue = False
        self._cue_time_ms: int | None = None
        self.setFixedSize(72, 52)  # duże, wygodne pady w obu trybach (dual + single)
        self.setText(f"{index + 1}")
        self.setToolTip(f"Hotcue {index + 1}\nClick: jump  •  Ctrl+Click: clear  •  Right-click or long: set at playhead")
        self._update_style()

        # Make it feel more like hardware pads
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def _format_time(self, ms: int) -> str:
        if ms is None:
            return ""
        total_sec = max(0, ms) // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m}:{s:02d}"

    def _update_style(self):
        color = COLORS["hotcue"][self.index % len(COLORS["hotcue"])]
        if self._has_cue:
            # Filled, high visibility active state
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {COLORS["bg"]};
                    border: 2px solid {COLORS["hotcue_active"]};
                    border-radius: 6px;
                    font-weight: 800;
                    font-size: 16px;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background-color: #ffffff;
                    color: {COLORS["bg"]};
                    border-color: {color};
                }}
                QPushButton:pressed {{
                    background-color: #e0e7ff;
                }}
            """)
        else:
            # Empty but clearly colored outline (pro "available" look)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a2233;
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: #252f42;
                    border-color: #ffffff;
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: {color};
                    color: {COLORS["bg"]};
                }}
            """)

    def set_cue_time(self, time_ms: int | None):
        """Called when cue is set — updates tooltip with time for pro workflow."""
        self._cue_time_ms = time_ms
        if time_ms is not None:
            tstr = self._format_time(time_ms)
            self.setToolTip(f"Hotcue {self.index + 1}  •  {tstr}\nClick: jump here  •  Ctrl+Click: delete  •  Right-click: overwrite at playhead")
        else:
            self.setToolTip(f"Hotcue {self.index + 1}\nClick to jump (when set)  •  Ctrl+Click to clear  •  Right-click: set at playhead")
        self.update()

    def mouseReleaseEvent(self, event):
        """Support left-click (jump/clear via modifiers in slot) + right-click to set (pro pad behavior)."""
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.set_requested.emit(self.index)
            event.accept()
            return
        # Left / other -> normal activation (slot decides jump vs ctrl-clear)
        self.activated.emit(self.index)
        # Let QPushButton do its pressed visuals etc.
        super().mouseReleaseEvent(event)


# ------------------------------------------------------------------
# REFACTOR (final cleanup): HotcueManager + format_track_time
# PRZENIESIONE do ui/dj/hotcue_manager.py
# Ten plik importuje je u góry – brak duplikacji, zero ryzyka cyklu.
# Stara implementacja usunięta.
# ------------------------------------------------------------------

class DeckWidget(QtWidgets.QFrame):
    """Professional single-deck widget used in dual-console DJ mode.

    Contains full transport, 4/8 hotcues, loops, EQ, pitch, sync, memory, quantize.

    # REFACTOR: Hotcue data layer extracted to HotcueManager (see class docstring).
    All playback and UI behavior preserved exactly.
    """

    track_dropped = QtCore.pyqtSignal(str)  # emituje ścieżkę pliku

    def __init__(
        self,
        deck_label: str,
        playback_engine: PlaybackEngine | None = None,
        deck_id: str = "A",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        # REFACTOR: Added explicit return type + | None union for modern typing.
        super().__init__(parent)
        self.deck_label = deck_label
        self.setObjectName("DeckPanel")
        self.setStyleSheet(f"""
            #DeckPanel {{
                background-color: {COLORS["panel"]};
                border-radius: 8px;
            }}
        """)

        self.current_track: Optional[Track] = None
        self.playback_engine = playback_engine
        self.deck_id = deck_id

        self._playhead_timer = QtCore.QTimer(self)
        self._playhead_timer.setInterval(40)  # ~25 fps
        self._playhead_timer.timeout.connect(self._update_playhead)

        # Hotcues delegated to shared manager (REFACTOR: eliminates duplication with SinglePlayerView)
        # The manager owns the dict + persistence. Widgets keep only their UI + snapping concerns.
        self._hotcue_mgr: HotcueManager = HotcueManager(max_cues=8)
        # Back-compat alias for any external code that may have read _hotcues directly (kept for safety)
        self._hotcues: dict[int, int] = self._hotcue_mgr.hotcues  # will be refreshed on access where needed

        # Pętla (Loop)
        self._loop_in_ms: int | None = None
        self._loop_out_ms: int | None = None
        self._loop_enabled: bool = False

        # Pro DJ: per-deck quantize (snaps hotcue/loop sets to beat grid)
        self._quantize_enabled: bool = True
        # Main cue for CUE button (enhanced via waveform double-click)
        self._main_cue_ms: int | None = 0
        # Track whether this deck believes it is currently tempo/phase synced
        self._is_synced_to_other: bool = False
        self._pfl_enabled: bool = False

        # Per-deck session memory for advanced DJ workflow (in-memory only, survives track changes)
        self._memory: dict | None = None

        # Włączamy przyjmowanie dropów
        self.setAcceptDrops(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)  # wyraźne oddzielenie sekcji w trybie dual (transport, mixer, EQ, hotcues, loops)

        # ========== HEADER: Deck + Track + Prominent BPM (high contrast, booth optimized) ==========
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(8)

        self.label = QtWidgets.QLabel(deck_label)
        self.label.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-size: 18px;
            font-weight: 900;
            letter-spacing: 1px;
            min-width: 64px;
        """)

        self.info_label = QtWidgets.QLabel("No track loaded")
        self.info_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 500;")
        self.info_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)

        # Large, clear BPM display (will show effective BPM with pitch)
        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-size: 14px;
            font-weight: 800;
            background-color: #0f1623;
            border: 1px solid {COLORS['panel_border']};
            border-radius: 4px;
            padding: 2px 8px;
            min-width: 82px;
        """)
        self.bpm_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Defensive: _update_effective_bpm() is called from _init_audio_backend before any track
        self._original_bpm = None

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px; font-weight: 600; padding: 1px 6px;")

        header.addWidget(self.label)
        header.addWidget(self.info_label, 1)
        header.addWidget(self.bpm_label)
        header.addWidget(self.status_label)

        # Memory save/recall buttons (compact pro controls for advanced DJ state snapshots)
        # Placed in header for quick access; dark booth theme, non-intrusive sizing
        header.addSpacing(6)
        self.mem_save_btn = QtWidgets.QPushButton("S")
        self.mem_recall_btn = QtWidgets.QPushButton("R")
        for b in (self.mem_save_btn, self.mem_recall_btn):
            b.setFixedSize(22, 20)
            b.setStyleSheet("font-size: 9px; font-weight: 800; padding: 0px 2px;")
        self.mem_save_btn.setToolTip("Save Memory: snapshot track path (if valid), main CUE, loop points, current hotcues (0-7), pitch/trim/keylock. In-memory for this session only.")
        self.mem_recall_btn.setToolTip("Recall Memory: if saved track differs + exists on disk → reload it; then restore cue/loop/hotcues/pitch/trim/keylock. Playback-safe where possible (live params applied without hard stop).")
        self.mem_save_btn.clicked.connect(self._save_deck_memory)
        self.mem_recall_btn.clicked.connect(self._recall_deck_memory)
        header.addWidget(self.mem_save_btn)
        header.addWidget(self.mem_recall_btn)

        layout.addLayout(header)

        # ========== WAVEFORM (taller + musical beatgrid) ==========
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)

        # ========== TRANSPORT (large, clear, pro sizes) ==========
        transport = QtWidgets.QHBoxLayout()
        transport.setSpacing(10)

        self.play_btn = QtWidgets.QPushButton("▶")
        self.play_btn.setFixedSize(58, 38)
        self.play_btn.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.stop_btn = QtWidgets.QPushButton("■")
        self.stop_btn.setFixedSize(46, 38)
        self.stop_btn.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.cue_btn.setFixedSize(62, 38)
        self.cue_btn.setStyleSheet("font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")
        self.cue_btn.setToolTip("CUE: jump to main cue point (double-click waveform to set/adjust; uses quantize if Q ON)")

        transport.addWidget(self.play_btn)
        transport.addWidget(self.stop_btn)
        transport.addWidget(self.cue_btn)
        transport.addStretch(1)

        # Trim/Gain (DJ terminology)
        trim_lbl = QtWidgets.QLabel("TRIM")
        trim_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700;")
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(85)
        self.volume_slider.setFixedWidth(118)
        transport.addWidget(trim_lbl)
        transport.addWidget(self.volume_slider)

        layout.addLayout(transport)

        # ========== MIXER ROW: Pitch + Range selector + KEY / SYNC / PFL ==========
        mixer = QtWidgets.QHBoxLayout()
        mixer.setSpacing(14)  # luźniejszy rząd z KEY/SYNC/PFL/Q + pitch

        p_lbl = QtWidgets.QLabel("PITCH")
        p_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; font-weight: 800;")
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setFixedWidth(108)

        self.pitch_value = QtWidgets.QLabel("+0.0%")
        self.pitch_value.setFixedWidth(46)
        self.pitch_value.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {COLORS['text']};")
        self.pitch_slider.valueChanged.connect(self._update_pitch_label)

        # Pro pitch range selector
        self.pitch_range = QtWidgets.QComboBox()
        self.pitch_range.addItems(["±6%", "±8%", "±16%", "±32%", "±50%"])
        self.pitch_range.setCurrentText("±50%")
        self.pitch_range.setFixedWidth(62)
        self.pitch_range.setStyleSheet("font-size: 11px;")
        self.pitch_range.currentTextChanged.connect(self._on_pitch_range_changed)

        mixer.addWidget(p_lbl)
        mixer.addWidget(self.pitch_slider)
        mixer.addWidget(self.pitch_value)
        mixer.addWidget(self.pitch_range)
        mixer.addSpacing(8)

        # Pro controls
        self.keylock_btn = QtWidgets.QPushButton("KEY")
        self.keylock_btn.setCheckable(True)
        self.keylock_btn.setFixedSize(58, 34)
        self.keylock_btn.setToolTip("Keylock / Master Tempo — change speed without changing pitch")
        self.keylock_btn.clicked.connect(self._on_keylock_toggled)

        self.sync_btn = QtWidgets.QPushButton("SYNC")
        self.sync_btn.setFixedSize(62, 34)
        self.sync_btn.setToolTip("SYNC: match tempo + phase align to other deck (auto keylock). Click again or tweak pitch to release.")
        self.sync_btn.clicked.connect(self._do_sync)

        self.pfl_btn = QtWidgets.QPushButton("PFL")
        self.pfl_btn.setCheckable(True)
        self.pfl_btn.setFixedSize(56, 34)
        self.pfl_btn.setToolTip("Headphone cue (PFL) — visual only for now (no backend routing)")
        self.pfl_btn.clicked.connect(self._on_pfl_toggled)

        # Quantize toggle — snaps hotcue + loop points to nearest beat (Rekordbox-style pro feature)
        self.quantize_btn = QtWidgets.QPushButton("Q")
        self.quantize_btn.setCheckable(True)
        self.quantize_btn.setChecked(True)
        self.quantize_btn.setFixedSize(44, 34)
        self.quantize_btn.setToolTip("Quantize: when ON, hotcues and loop points snap to nearest beat (using track BPM)")
        self.quantize_btn.clicked.connect(self._on_quantize_toggled)

        for b in (self.keylock_btn, self.sync_btn, self.pfl_btn, self.quantize_btn):
            b.setStyleSheet("font-size: 13px; font-weight: 700;")

        mixer.addWidget(self.keylock_btn)
        mixer.addWidget(self.sync_btn)
        mixer.addWidget(self.pfl_btn)
        mixer.addWidget(self.quantize_btn)
        mixer.addStretch(1)

        layout.addLayout(mixer)

        # ========== 3-BAND EQ with clear labels ==========
        eq_outer = QtWidgets.QHBoxLayout()
        eq_outer.setSpacing(4)

        eq_title = QtWidgets.QLabel("EQ")
        eq_title.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; font-weight: 800; min-width: 22px;")
        eq_outer.addWidget(eq_title)

        self.eq_low = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        self.eq_mid = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        self.eq_high = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        for s in (self.eq_low, self.eq_mid, self.eq_high):
            s.setRange(-12, 12)
            s.setValue(0)
            s.setFixedHeight(62)  # trochę wyższe suwaki EQ w trybie dual dla lepszego czucia

        self.eq_low.valueChanged.connect(self._on_eq_changed)
        self.eq_mid.valueChanged.connect(self._on_eq_changed)
        self.eq_high.valueChanged.connect(self._on_eq_changed)

        def _make_eq_col(slider, name):
            v = QtWidgets.QVBoxLayout()
            v.setSpacing(1)
            lbl = QtWidgets.QLabel(name)
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; font-weight: 700;")
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            v.addWidget(lbl)
            v.addWidget(slider, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
            return v

        eq_outer.addLayout(_make_eq_col(self.eq_low, "LOW"))
        eq_outer.addLayout(_make_eq_col(self.eq_mid, "MID"))
        eq_outer.addLayout(_make_eq_col(self.eq_high, "HI"))
        eq_outer.addStretch(1)

        layout.addLayout(eq_outer)

        # ========== HOT CUES (large, pro pads) + 4/8 mode toggle for advanced workflow ==========
        hc_header = QtWidgets.QHBoxLayout()
        hc_header.setSpacing(6)
        hc_h = QtWidgets.QLabel("HOT CUES")
        hc_h.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 800; letter-spacing: 1px;")
        hc_header.addWidget(hc_h)

        # 4/8 toggle button (compact, booth-friendly, fits dark pro theme)
        self.hotcue_mode_btn = QtWidgets.QPushButton("4")
        self.hotcue_mode_btn.setFixedSize(26, 18)
        self.hotcue_mode_btn.setStyleSheet("font-size: 9px; font-weight: 800; padding: 0px; border-radius: 3px;")
        self.hotcue_mode_btn.setToolTip(
            "4/8 Hotcue Mode\n"
            "Click to toggle: 4 pads (default, indices 0-3) ↔ 8 pads (2 rows, indices 0-7).\n"
            "Colors cycle using the same 4-color palette. DB supports all via hotcue_index.\n"
            "Higher hotcues remain accessible via shortcuts/memory even if pads hidden."
        )
        self.hotcue_mode_btn.clicked.connect(self._toggle_hotcue_mode)
        hc_header.addWidget(self.hotcue_mode_btn)
        hc_header.addStretch(1)

        layout.addLayout(hc_header)

        # Dynamic pads container (1 or 2 rows depending on mode; replaces fixed 4-pad row)
        self.hotcue_pads: list[HotcuePad] = []
        self.hotcue_pads_layout = None  # will be QVBoxLayout with row sub-layouts
        self.hotcue_container = QtWidgets.QWidget()
        layout.addWidget(self.hotcue_container)

        # Initialize to 4-pad default (full backward compat)
        self._hotcue_mode = 4
        self._rebuild_hotcue_pads()

        # ========== LOOP section ==========
        lp_h = QtWidgets.QLabel("LOOP")
        lp_h.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; font-weight: 800; letter-spacing: 0.8px;")
        layout.addWidget(lp_h)

        loop_row = QtWidgets.QHBoxLayout()
        loop_row.setSpacing(6)

        self.loop_in_btn = QtWidgets.QPushButton("IN")
        self.loop_out_btn = QtWidgets.QPushButton("OUT")
        self.loop_toggle = QtWidgets.QPushButton("LOOP")
        self.loop_toggle.setCheckable(True)

        for b in (self.loop_in_btn, self.loop_out_btn, self.loop_toggle):
            b.setFixedSize(48, 26)
            b.setStyleSheet("font-size: 11px; font-weight: 700;")

        self.loop_in_btn.clicked.connect(self._set_loop_in)
        self.loop_out_btn.clicked.connect(self._set_loop_out)
        self.loop_toggle.toggled.connect(self._toggle_loop)

        loop_row.addWidget(self.loop_in_btn)
        loop_row.addWidget(self.loop_out_btn)
        loop_row.addWidget(self.loop_toggle)
        loop_row.addStretch(1)

        self.loop_container = QtWidgets.QWidget()
        self.loop_container.setLayout(loop_row)
        layout.addWidget(self.loop_container)

        # Backend init + signal wiring
        self._init_audio_backend()

    def _init_audio_backend(self):
        """Sprawdza dostępność silnika audio (nowy PlaybackEngine)."""
        if not self.playback_engine:
            logger.warning(f"{self.deck_label}: Brak PlaybackEngine – deck w trybie podglądu")
            self._update_status("⚠ Brak silnika audio")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.cue_btn.setEnabled(False)
            return

        self._update_status("✓ Gotowy")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.cue_btn.setEnabled(True)

        # Podłączamy przyciski (nawet jeśli player jest None – defensywnie)
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)
        self.cue_btn.clicked.connect(self._jump_to_cue)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.pitch_slider.valueChanged.connect(self._on_pitch_changed)

        # Pro controls (some already wired in layout, these are safety)
        self.keylock_btn.clicked.connect(self._on_keylock_toggled)
        self.sync_btn.clicked.connect(self._do_sync)
        self.pfl_btn.clicked.connect(self._on_pfl_toggled)
        if hasattr(self, 'quantize_btn'):
            self.quantize_btn.clicked.connect(self._on_quantize_toggled)
            # Initial pro quantize style (on by default)
            if self._quantize_enabled:
                self.quantize_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #854d0e; color: white;")

        # Seek z waveform
        self.waveform.seek_requested.connect(self._seek)
        self.waveform.cue_set_requested.connect(self._set_hotcue_from_waveform)
        self.waveform.double_clicked.connect(self._set_main_cue_from_waveform)

        # Initial BPM label state
        self._update_effective_bpm()

    def _format_time(self, ms: int) -> str:
        """Local time formatter (mm:ss) for CUE / status tooltips.

        # REFACTOR: Now delegates to module-level format_track_time to eliminate
        # duplication with SinglePlayerView while preserving exact original behavior
        # and call sites.
        """
        return format_track_time(ms)

    def _sync_hotcues_alias(self) -> None:
        """Internal: keep the legacy self._hotcues attribute in sync with the manager.

        # REFACTOR: Temporary bridge for any code that still reads the old dict directly.
        # Long-term the alias can be removed once all internal accesses are updated.
        """
        self._hotcues = self._hotcue_mgr.hotcues

    def _refresh_hotcue_remaining_tooltips(self, playhead_ms: int):
        """Update hotcue pad tooltips with remaining time/beat delta when playing (nice-to-have pro countdown)."""
        bpm = getattr(self, '_original_bpm', None) or 120.0
        beat_ms = 60000.0 / bpm if bpm > 20 else 500.0
        for idx, t_ms in list(self._hotcues.items()):
            if t_ms <= playhead_ms:
                continue
            delta_ms = t_ms - playhead_ms
            delta_sec = delta_ms / 1000.0
            beats = max(0, int(round(delta_ms / beat_ms)))
            try:
                if 0 <= idx < len(self.hotcue_pads):
                    pad = self.hotcue_pads[idx]
                    # Preserve the clean base tooltip (set by set_cue_time) and append dynamic suffix
                    base_tooltip = getattr(pad, '_base_tooltip', None)
                    if not base_tooltip:
                        # capture once the static part
                        tt = pad.toolTip() or ""
                        base_tooltip = tt.split(" • in ")[0].split("\n")[0] if tt else f"Hotcue {idx + 1}"
                        pad._base_tooltip = base_tooltip
                    extra = f" • in {delta_sec:.1f}s (~{beats}b)"
                    pad.setToolTip(f"{base_tooltip}{extra}")
            except Exception:
                pass

    def _toggle_play(self):
        if self.playback_engine:
            # Engine API is toggle_deck (not toggle_play_deck) — fixed P0 bug
            is_playing = self.playback_engine.toggle_deck(self.deck_id)
            self.play_btn.setText("❚❚" if is_playing else "▶")
            if is_playing:
                self._playhead_timer.start()
            else:
                self._playhead_timer.stop()
        else:
            logger.debug(f"{self.deck_label}: Brak silnika audio")

    def _stop(self):
        if self.playback_engine:
            self.playback_engine.stop_deck(self.deck_id)
            self.play_btn.setText("▶")
            self._playhead_timer.stop()
            self.waveform.set_playhead(0)
            # time display removed from header in pro redesign (BPM + waveform playhead sufficient)

    def _jump_to_cue(self):
        """CUE button: jump to main cue point (0 fallback, or last double-click / quantized set). Pro preview feel."""
        target = self._main_cue_ms if self._main_cue_ms is not None else 0
        if self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, target)
            self.waveform.set_playhead(target)
            # Optional: pause on cue for classic "cue" behavior (commented for non-destructive; enable if desired)
            # self.playback_engine.pause_deck(self.deck_id)

    def _on_volume_changed(self, value: int):
        if self.playback_engine:
            # Volume slider w decku = Trim/Gain (współpracuje z crossfaderem)
            self.playback_engine.set_deck_trim(self.deck_id, value / 100.0)

    def _on_pitch_changed(self, value: int):
        if self.playback_engine:
            rate = 1.0 + (value / 100.0)   # -50..+50 → 0.5x .. 1.5x
            self.playback_engine.set_deck_rate(self.deck_id, rate)
            self._update_pitch_label(value)
            # Manual pitch change breaks any active SYNC state (pro behavior)
            if getattr(self, '_is_synced_to_other', False):
                self._is_synced_to_other = False
                if hasattr(self, 'sync_btn'):
                    self.sync_btn.setStyleSheet("font-size: 11px; font-weight: 700;")

    def _on_eq_changed(self, _=None):
        if self.playback_engine:
            low = self.eq_low.value()
            mid = self.eq_mid.value()
            high = self.eq_high.value()
            self.playback_engine.set_deck_eq(self.deck_id, low, mid, high)

    # ------------------------------------------------------------------ #
    # Hotcues (4/8 pads, advanced mode toggle)
    # ------------------------------------------------------------------ #

    def _set_main_cue_from_waveform(self, time_ms: int):
        """Double-click on waveform sets the primary CUE point (snapped if quantize ON)."""
        if not self.current_track:
            return
        snapped = self._snap_to_beat(time_ms)
        self._main_cue_ms = snapped
        self.waveform.set_playhead(snapped)  # visual confirm
        if self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, snapped)
        self.cue_btn.setToolTip(f"CUE @ {self._format_time(snapped)} (double-click waveform to change)")
        self._update_status("CUE SET")
        QtCore.QTimer.singleShot(900, lambda: self._update_status("✓ Gotowy"))

    def _set_hotcue_from_waveform(self, time_ms: int):
        """Shift + click waveform → set hotcue on first free visible pad (0..mode-1). Supports 8-mode (indices to 7). Quantized when Q ON.

        # REFACTOR: Now uses HotcueManager for storage + persistence (was direct dict + duplicated save).
        # Snapping and pad selection logic unchanged.
        """
        if not self.current_track:
            return
        time_ms = self._snap_to_beat(time_ms)

        # Znajdź pierwszy wolny indeks
        max_idx = getattr(self, '_hotcue_mode', 4)
        for idx in range(max_idx):
            if self._hotcue_mgr.get(idx) is None:
                self._hotcue_mgr.set(idx, time_ms)
                self._sync_hotcues_alias()  # keep legacy _hotcues view fresh
                self._update_hotcue_pad(idx)
                self._save_hotcue_to_db(idx, time_ms)
                return

        # Jeśli wszystkie zajęte — nadpisz pierwszy widoczny
        idx = 0
        self._hotcue_mgr.set(idx, time_ms)
        self._sync_hotcues_alias()
        self._update_hotcue_pad(idx)
        self._save_hotcue_to_db(idx, time_ms)

    def _set_hotcue_from_button(self, index: int):
        """Przycisk na padzie (prawy / specjalny) — ustaw na aktualnej pozycji.

        # REFACTOR: Storage + persistence now via HotcueManager (shared with SinglePlayerView).
        """
        if not self.playback_engine or not self.current_track:
            return
        state = self.playback_engine.get_deck_state(self.deck_id)
        current_time = state.position_ms if state else 0
        self._hotcue_mgr.set(index, current_time)
        self._sync_hotcues_alias()
        self._update_hotcue_pad(index)
        self._save_hotcue_to_db(index, current_time)

    def _jump_to_hotcue(self, index: int):
        """Klik na pad → skocz do hotcue jeśli istnieje. Ctrl+klik = usuń.

        # REFACTOR: Hotcue data access now via manager (read + delete path).
        # Core jump/delete semantics identical.
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
            # Usuwanie hotcue
            if self._hotcue_mgr.get(index) is not None:
                self._hotcue_mgr.clear(index)
                self._sync_hotcues_alias()
                self._update_hotcue_pad(index)
                self._delete_hotcue_from_db(index)
            return

        # Normalny skok
        cue_time = self._hotcue_mgr.get(index)
        if cue_time is not None and self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, cue_time)
            self.waveform.set_playhead(cue_time)

    def _update_hotcue_pad(self, index: int):
        """Refresh a single pad's visual state from the (now manager-backed) hotcue data.

        # REFACTOR: Reads from HotcueManager instead of direct dict (DeckWidget path).
        """
        if index >= len(self.hotcue_pads):
            return
        pad = self.hotcue_pads[index]
        cue_time = self._hotcue_mgr.get(index)
        if cue_time is not None:
            pad._has_cue = True
            pad.set_cue_time(cue_time)
        else:
            pad._has_cue = False
            pad.set_cue_time(None)
        pad._update_style()

    # ------------------------------------------------------------------ #
    # 4/8 Hotcue mode (advanced DJ workflow, isolated to this file)
    # ------------------------------------------------------------------ #

    def _toggle_hotcue_mode(self):
        """Switch between 4 and 8 hotcue pads. Updates layout immediately, preserves _hotcues data."""
        new_mode = 8 if getattr(self, '_hotcue_mode', 4) == 4 else 4
        self._set_hotcue_mode(new_mode)

    def _set_hotcue_mode(self, mode: int):
        """Internal: apply mode and rebuild pads (no engine impact)."""
        mode = 8 if mode >= 8 else 4
        if mode == getattr(self, '_hotcue_mode', 4):
            return
        self._hotcue_mode = mode
        self._rebuild_hotcue_pads()
        self._update_status(f"{mode}-HOTCUE MODE")
        QtCore.QTimer.singleShot(1100, lambda: self._update_status("✓ Gotowy"))
        logger.debug(f"{self.deck_label}: Hotcue mode set to {mode}")

    def _rebuild_hotcue_pads(self):
        """Dynamically build 4 or 8 pads in 1-2 rows. Reuses HotcuePad (4-color cycle + index logic)."""
        # Clear previous pad widgets from the container's layout
        if self.hotcue_pads_layout is None:
            self.hotcue_pads_layout = QtWidgets.QVBoxLayout()
            self.hotcue_pads_layout.setSpacing(3)
            self.hotcue_pads_layout.setContentsMargins(0, 0, 0, 0)
            self.hotcue_container.setLayout(self.hotcue_pads_layout)
        else:
            # Remove old row widgets
            while self.hotcue_pads_layout.count() > 0:
                item = self.hotcue_pads_layout.takeAt(0)
                if item:
                    w = item.widget()
                    if w:
                        w.deleteLater()

        self.hotcue_pads.clear()

        num = getattr(self, '_hotcue_mode', 4)
        # Build rows of 4 (or less for final)
        for row_start in range(0, num, 4):
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.setSpacing(10)  # jeszcze więcej powietrza między padami w trybie dual
            row_layout.setContentsMargins(0, 0, 0, 0)
            for i in range(row_start, min(row_start + 4, num)):
                pad = HotcuePad(i)
                pad.activated.connect(self._jump_to_hotcue)
                pad.set_requested.connect(self._set_hotcue_from_button)
                self.hotcue_pads.append(pad)
                row_layout.addWidget(pad)
            row_layout.addStretch(1)
            row_widget = QtWidgets.QWidget()
            row_widget.setLayout(row_layout)
            self.hotcue_pads_layout.addWidget(row_widget)

        # Restore visual state for any hotcues already in memory (from DB or session)
        for idx in range(len(self.hotcue_pads)):
            self._update_hotcue_pad(idx)

        # Update toggle button label
        if hasattr(self, "hotcue_mode_btn") and self.hotcue_mode_btn:
            self.hotcue_mode_btn.setText(str(num))

    def _save_hotcue_to_db(self, index: int, time_ms: int):
        """Zapisuje hotcue do bazy (jeśli mamy track_id i dostęp do repo).

        # REFACTOR: Now thin delegation to HotcueManager (removes duplication of
        # CuePoint construction + save logic that lived in both DeckWidget and SinglePlayerView).
        """
        if not self.current_track or not hasattr(self.current_track, 'id') or not self.current_track.id:
            return
        # Ensure manager knows the current track
        self._hotcue_mgr.set_track_id(self.current_track.id)
        self._hotcue_mgr.save_to_db(index, time_ms)

    def _delete_hotcue_from_db(self, index: int):
        """Usuwa hotcue z bazy.

        # REFACTOR: Thin delegation to shared HotcueManager (was duplicated verbatim).
        """
        if not self.current_track or not hasattr(self.current_track, 'id') or not self.current_track.id:
            return
        self._hotcue_mgr.set_track_id(self.current_track.id)
        self._hotcue_mgr.delete_from_db(index)

    # ------------------------------------------------------------------ #
    # Pętle (Loop In / Out)
    # ------------------------------------------------------------------ #

    def _set_loop_in(self):
        if not self.playback_engine or not self.current_track:
            return
        state = self.playback_engine.get_deck_state(self.deck_id)
        current = state.position_ms if state else 0
        current = self._snap_to_beat(current)
        self._loop_in_ms = current
        if self._loop_out_ms is not None and self._loop_out_ms <= self._loop_in_ms:
            self._loop_out_ms = None

        length = state.duration_ms if state else 0
        self.waveform.set_loop(self._loop_in_ms or 0, self._loop_out_ms or length)
        logger.debug(f"{self.deck_label}: Loop In ustawiony na {current}ms")

    def _set_loop_out(self):
        if not self.playback_engine or not self.current_track:
            return
        state = self.playback_engine.get_deck_state(self.deck_id)
        current = state.position_ms if state else 0
        current = self._snap_to_beat(current)
        if self._loop_in_ms is not None and current <= self._loop_in_ms:
            return
        self._loop_out_ms = current
        self.waveform.set_loop(self._loop_in_ms or 0, self._loop_out_ms)
        logger.debug(f"{self.deck_label}: Loop Out ustawiony na {current}ms")

    def _toggle_loop(self, checked: bool):
        self._loop_enabled = checked
        if self.playback_engine:
            if checked and self._loop_in_ms is not None and self._loop_out_ms is not None:
                self.playback_engine.set_deck_loop(self.deck_id, self._loop_in_ms, self._loop_out_ms)
                self.playback_engine.enable_deck_loop(self.deck_id, True)
            else:
                self.playback_engine.enable_deck_loop(self.deck_id, False)
        # Stronger pro visual feedback for active loop (Rekordbox/Traktor style)
        if checked:
            self.loop_toggle.setStyleSheet("font-size: 11px; font-weight: 800; background-color: #1e40af; color: #bae6fd; border: 1px solid #60a5fa;")
            self._update_status("LOOP ACTIVE")
        else:
            self.loop_toggle.setStyleSheet("font-size: 11px; font-weight: 700;")
        logger.debug(f"{self.deck_label}: Pętla {'włączona' if checked else 'wyłączona'}")

    def _check_and_handle_loop(self):
        """
        Wizualna aktualizacja pętli + fallback.
        WAŻNE: Backend (VlcAudioBackend) teraz sam pilnuje pętli eventowo + pollerem
        (patrz raport agenta Playback Backend). Ta metoda już nie wykonuje seeków,
        żeby uniknąć wyścigów i mikro-zacięć na granicach pętli.
        """
        if not self._loop_enabled or not self.playback_engine:
            return
        # Tylko wizualne odświeżenie (jeśli waveform chce coś podświetlić)
        # Backend jest odpowiedzialny za faktyczne zapętlenie (event-driven + poller 45 Hz).
        pass  # Intencjonalnie puste — usunięto duplikat logiki pętli (zgodnie z zaleceniem agenta)

    # ------------------------------------------------------------------ #
    # Drag & Drop z biblioteki
    # ------------------------------------------------------------------ #

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-lumbago-track-paths") or event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + " border: 2px solid #5cc8ff;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            #DeckPanel {{
                background-color: {COLORS["panel"]};
                border-radius: 8px;
            }}
        """)

    def dropEvent(self, event):
        self.setStyleSheet(f"""
            #DeckPanel {{
                background-color: {COLORS["panel"]};
                border-radius: 8px;
            }}
        """)

        mime = event.mimeData()
        paths = []

        if mime.hasFormat("application/x-lumbago-track-paths"):
            data = mime.data("application/x-lumbago-track-paths").data().decode()
            paths = [p for p in data.split(",") if p]

        elif mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())

        if paths:
            # Bierzemy pierwszą ścieżkę
            self.track_dropped.emit(paths[0])
            event.acceptProposedAction()

    def _load_hotcues_from_track(self, track_id: int):
        """Wczytuje hotcue'e z bazy dla tracka.

        # REFACTOR: Data loading now performed by HotcueManager.load_from_db;
        # only UI pad refresh remains in the widget (structure improvement).
        """
        loaded = self._hotcue_mgr.load_from_db(track_id)
        self._sync_hotcues_alias()

        for pad in self.hotcue_pads:
            pad._has_cue = False
            pad.set_cue_time(None)
            pad._update_style()

        for idx, t_ms in loaded.items():
            if idx < len(self.hotcue_pads):
                p = self.hotcue_pads[idx]
                p._has_cue = True
                p.set_cue_time(t_ms)
                p._update_style()

        logger.debug(f"{self.deck_label}: Wczytano {len(loaded)} hotcue'ów z bazy (via HotcueManager)")

    def _seek(self, time_ms: int):
        if self.playback_engine:
            self.playback_engine.seek_deck(self.deck_id, time_ms)
            self.waveform.set_playhead(time_ms)

    def _update_playhead(self):
        if self.playback_engine:
            state = self.playback_engine.get_deck_state(self.deck_id)
            if state:
                self.waveform.set_playhead(state.position_ms)
                # Aktualizuj przycisk play/pause bezpośrednio z backendu (niezależnie od DeckState)
                is_playing = self.playback_engine.deck(self.deck_id).is_playing() if self.playback_engine else False
                self.play_btn.setText("❚❚" if is_playing else "▶")
                self._check_and_handle_loop()  # obsługa pętli
                # Nice-to-have pro feedback: live remaining-to-hotcue in tooltips (when playing)
                if is_playing and self._hotcues:
                    self._refresh_hotcue_remaining_tooltips(state.position_ms)
                # (live time label removed — waveform playhead + BPM provide pro visual feedback)

    def _update_pitch_label(self, value: int):
        self.pitch_value.setText(f"{value:+.1f}%")
        self._update_effective_bpm()
        # Push to engine already handled by valueChanged -> _on_pitch_changed

    def _update_effective_bpm(self):
        """Update the prominent BPM label with pitch-affected value (pro DJ essential)."""
        if not hasattr(self, 'bpm_label') or not hasattr(self, '_original_bpm'):
            return
        if self._original_bpm and self._original_bpm > 0:
            rate = 1.0 + (self.pitch_slider.value() / 100.0)
            eff = self._original_bpm * rate
            self.bpm_label.setText(f"{eff:.1f} BPM")
            self.bpm_label.setStyleSheet(f"""
                color: {COLORS['accent_green']};
                font-size: 14px;
                font-weight: 800;
                background-color: #0f1623;
                border: 1px solid {COLORS['panel_border']};
                border-radius: 4px;
                padding: 2px 8px;
            """)
        else:
            self.bpm_label.setText("— BPM")
            self.bpm_label.setStyleSheet(f"""
                color: {COLORS['accent']};
                font-size: 14px;
                font-weight: 800;
                background-color: #0f1623;
                border: 1px solid {COLORS['panel_border']};
                border-radius: 4px;
                padding: 2px 8px;
            """)

    def _on_pitch_range_changed(self, text: str):
        """Change pitch slider max range (common DJ feature: ±8 / ±16 etc)."""
        try:
            new_range = int(text.replace("±", "").replace("%", ""))
        except Exception:
            new_range = 50
        old_val = self.pitch_slider.value()
        self._current_pitch_range = new_range
        self.pitch_slider.setRange(-new_range, new_range)
        # Clamp current value into new range
        new_val = max(-new_range, min(new_range, old_val))
        if new_val != old_val:
            self.pitch_slider.setValue(new_val)
        # Label + effective BPM will update via the valueChanged signal

    def _on_keylock_toggled(self, checked: bool):
        if self.playback_engine:
            self.playback_engine.set_deck_keylock(self.deck_id, checked)
            if checked:
                self.keylock_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #166534; color: white;")
            else:
                self.keylock_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
            self._update_status("KEYLOCK ON" if checked else "✓ Gotowy")

    def _on_pfl_toggled(self, checked: bool):
        self._pfl_enabled = checked
        if checked:
            self.pfl_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #1e3a8a; color: white;")
            # Stronger deck-level cue indication (booth friendly)
            self.label.setStyleSheet(f"color: #67e8f9; font-size: 18px; font-weight: 900; letter-spacing: 1px; min-width: 64px; background-color: #0f172a;")
        else:
            self.pfl_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
            self.label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 18px; font-weight: 900; letter-spacing: 1px; min-width: 64px;")
        # Stub: real headphone routing would go here when backend supports per-deck monitor output

    def _on_quantize_toggled(self, checked: bool):
        self._quantize_enabled = bool(checked)
        if checked:
            self.quantize_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #854d0e; color: white;")
            self._update_status("QUANTIZE ON")
        else:
            self.quantize_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
            self._update_status("QUANTIZE OFF")
        QtCore.QTimer.singleShot(1200, lambda: self._update_status("✓ Gotowy") if not self._quantize_enabled else None)

    def _do_sync(self):
        """Tempo match + best-effort phase alignment (Rekordbox-like basic SYNC).
        Uses only public PlaybackEngine APIs for full VLC + Qt fallback compatibility.
        """
        if not self.playback_engine or not self.current_track or not self.current_track.bpm:
            self._update_status("No BPM on this deck")
            return
        try:
            win = self.window()
            if not (hasattr(win, "deck_a") and hasattr(win, "deck_b")):
                return
            other = win.deck_b if self.deck_id == "A" else win.deck_a
            if not other or not other.current_track or not other.current_track.bpm:
                self._update_status("Other deck has no BPM")
                return

            other_state = self.playback_engine.get_deck_state(other.deck_id)
            other_rate = other_state.rate if other_state else 1.0
            target_bpm = other.current_track.bpm * other_rate
            target_rate = target_bpm / self.current_track.bpm
            target_rate = max(0.5, min(2.0, target_rate))

            self.playback_engine.set_deck_rate(self.deck_id, target_rate)

            # Pro touch: engaging SYNC typically implies you want pitch preserved
            self.playback_engine.set_deck_keylock(self.deck_id, True)
            self.keylock_btn.setChecked(True)
            self.keylock_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #166534; color: white;")

            # Reflect in UI pitch slider
            pitch_pct = int(round((target_rate - 1.0) * 100))
            rmin, rmax = self.pitch_slider.minimum(), self.pitch_slider.maximum()
            pitch_pct = max(rmin, min(rmax, pitch_pct))
            self.pitch_slider.blockSignals(True)
            self.pitch_slider.setValue(pitch_pct)
            self.pitch_slider.blockSignals(False)
            self.pitch_value.setText(f"{pitch_pct:+.1f}%")
            self._update_effective_bpm()

            # --- Simple phase alignment (best-effort, position + BPM modulo, no full beatgrid) ---
            try:
                this_state = self.playback_engine.get_deck_state(self.deck_id)
                this_pos = this_state.position_ms if this_state else 0
                other_pos = other_state.position_ms if other_state else 0
                bpm = float(self.current_track.bpm)
                eff_rate = target_rate
                eff_bpm = bpm * eff_rate
                if eff_bpm > 8.0:
                    beat_ms = 60000.0 / eff_bpm
                    other_phase = other_pos % beat_ms
                    this_phase = this_pos % beat_ms
                    delta = (other_phase - this_phase + beat_ms) % beat_ms
                    if delta > beat_ms / 2.0:
                        delta -= beat_ms
                    # Only nudge if musically meaningful (> ~5-10ms) and safe
                    if abs(delta) > 6:
                        new_pos = max(0, int(this_pos + delta))
                        dur = this_state.duration_ms if this_state else 0
                        if dur > 0:
                            new_pos = min(new_pos, dur)
                        self.playback_engine.seek_deck(self.deck_id, new_pos)
                        self.waveform.set_playhead(new_pos)
            except Exception as exc:
                logger.debug(f"Deck {self.deck_label}: phase alignment during sync failed (best-effort): {exc}")  # phase is best-effort; never break sync on it

            # Persistent visual SYNC state (cleared on manual pitch adjust)
            self._is_synced_to_other = True
            self.sync_btn.setStyleSheet("font-size: 11px; font-weight: 700; background-color: #166534; color: #fff; border: 1px solid #4ade80;")
            self._update_status("SYNCED + PHASE")

            # Clear the *other* deck's sync visual (only one master usually)
            try:
                other._is_synced_to_other = False
                other.sync_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
            except Exception as exc:
                logger.debug(f"Sync: failed to clear other deck sync visual: {exc}")
        except Exception as e:
            logger.debug(f"Sync failed: {e}")
            self._update_status("Sync error")

    def _update_status(self, text: str):
        self.status_label.setText(text)

    def _snap_to_beat(self, time_ms: int) -> int:
        """Quantize helper: snap time to nearest beat using track's original BPM (Rekordbox-style).
        Graceful: returns original time if quantize off, no BPM, or no engine.
        """
        if not getattr(self, '_quantize_enabled', False):
            return time_ms
        bpm = getattr(self, '_original_bpm', None)
        if not bpm or bpm < 20:
            return time_ms
        try:
            beat_ms = 60000.0 / float(bpm)
            beats = round(time_ms / beat_ms)
            snapped = int(beats * beat_ms)
            # Clamp using live duration if available (works for both backends)
            if self.playback_engine:
                st = self.playback_engine.get_deck_state(self.deck_id)
                if st and st.duration_ms > 0:
                    snapped = max(0, min(snapped, st.duration_ms))
            return snapped
        except Exception as exc:
            logger.debug(f"Deck {self.deck_label}: quantize snap failed, using raw time: {exc}")
            return time_ms

    def _update_deck_backend_status(self):
        """Pokazuje na każdym decku jaki backend audio jest aktywny (czytelny feedback dla użytkownika)."""
        if not hasattr(self, "playback_engine") or not self.playback_engine:
            if hasattr(self, "deck_a"):
                self.deck_a._update_status("⚠ Brak silnika")
            if hasattr(self, "deck_b"):
                self.deck_b._update_status("⚠ Brak silnika")
            return

        try:
            d = self.playback_engine.get_diagnostics()
            for deck_name, deck_widget in (("A", self.deck_a), ("B", self.deck_b)):
                info = d.get(f"deck_{deck_name.lower()}", {})
                backend = info.get("backend", "unknown")
                initialized = info.get("initialized", False)
                if backend == "vlc":
                    txt = "✓ VLC"
                elif backend == "qtmultimedia":
                    txt = "⚠ Qt (fallback)"
                elif backend == "noop":
                    txt = "✗ Brak audio"
                else:
                    txt = backend[:8]
                if not initialized:
                    txt = "✗ Błąd"
                deck_widget._update_status(txt)
        except Exception as e:
            logger.debug(f"Backend status update failed: {e}")

    # ------------------------------------------------------------------ #
    # Deck Memory (Save/Recall) - basic session snapshot for advanced DJ workflow
    # All via public PlaybackEngine + UI state; graceful on fallback backends; no playback breakage when possible.
    # ------------------------------------------------------------------ #

    def _save_deck_memory(self):
        """Capture current deck state to in-memory snapshot (per-deck, lives for app session)."""
        path = getattr(self.current_track, 'path', None) if self.current_track else None
        mem = {
            "track_path": path,
            "main_cue_ms": self._main_cue_ms,
            "loop_in_ms": self._loop_in_ms,
            "loop_out_ms": self._loop_out_ms,
            "hotcues": self._hotcue_mgr.hotcues,  # supports 0-7  # REFACTOR: via manager
            "pitch": self.pitch_slider.value() if hasattr(self, "pitch_slider") else 0,
            "trim": self.volume_slider.value() if hasattr(self, "volume_slider") else 85,
            "keylock": bool(self.keylock_btn.isChecked()) if hasattr(self, "keylock_btn") else False,
        }
        self._memory = mem
        self._update_status("MEM SAVED")
        QtCore.QTimer.singleShot(1100, lambda: self._update_status("✓ Gotowy"))
        logger.debug(f"{self.deck_label}: Deck memory saved (hotcues={len(mem['hotcues'])})")

    def _recall_deck_memory(self):
        """Restore from saved memory. Reloads track only if path changed+valid. Applies live params safely."""
        if not getattr(self, '_memory', None):
            self._update_status("No memory")
            QtCore.QTimer.singleShot(800, lambda: self._update_status("✓ Gotowy"))
            return

        mem = self._memory
        target_path = mem.get("track_path")
        current_path = getattr(self.current_track, 'path', None) if self.current_track else None

        # Determine if reload needed (graceful path check)
        need_reload = False
        if target_path:
            try:
                p = Path(target_path)
                if p.exists():
                    if not current_path or Path(current_path) != p:
                        need_reload = True
            except Exception:
                pass

        # Detect current playback state (works for VLC + Qt fallback via public API)
        was_playing = False
        if self.playback_engine:
            try:
                was_playing = bool(self.playback_engine.deck(self.deck_id).is_playing())
            except Exception:
                try:
                    st = self.playback_engine.get_deck_state(self.deck_id)
                    was_playing = bool(getattr(st, "is_playing", False))
                except Exception:
                    pass

        if need_reload:
            try:
                t = Track(path=target_path, title=Path(target_path).stem)
                try:
                    from data.repository import get_track_by_path
                    dbt = get_track_by_path(target_path)
                    if dbt and getattr(dbt, "id", None):
                        t = dbt
                except Exception:
                    pass
                self.load_track(t)  # resets UI + loads hotcues from DB (we override from mem after)
            except Exception as e:
                logger.warning(f"{self.deck_label} memory recall reload error: {e}")
                self._update_status("MEM reload err")
                return

            # If it was playing before, restart after load settles (load itself stops)
            if was_playing and self.playback_engine:
                QtCore.QTimer.singleShot(160, self._ensure_play_after_recall)

        # Always restore the snapshot states (works even without reload = live tweak on current track)
        # Main cue
        if mem.get("main_cue_ms") is not None:
            self._main_cue_ms = mem.get("main_cue_ms")
            if hasattr(self, "cue_btn"):
                self.cue_btn.setToolTip(f"CUE @ {self._format_time(self._main_cue_ms)} (memory)")

        # Loops (visual + internal; engine loop if active re-applied by user if desired)
        self._loop_in_ms = mem.get("loop_in_ms")
        self._loop_out_ms = mem.get("loop_out_ms")
        self._loop_enabled = False
        if hasattr(self, "loop_toggle"):
            self.loop_toggle.setChecked(False)
            self.loop_toggle.setStyleSheet("font-size: 11px; font-weight: 700;")
        if self._loop_in_ms is not None and self._loop_out_ms is not None and hasattr(self, "waveform"):
            try:
                self.waveform.set_loop(self._loop_in_ms, self._loop_out_ms)
            except Exception:
                pass

        # Hotcues snapshot (quick UI restore; DB may differ but this is session memory override)
        # REFACTOR: Load into manager instead of raw dict
        for idx, t in mem.get("hotcues", {}).items():
            self._hotcue_mgr.set(idx, t)
        self._sync_hotcues_alias()
        for i in range(len(self.hotcue_pads)):
            self._update_hotcue_pad(i)

        # Pitch / trim / keylock (live-safe, all backends support via engine)
        if hasattr(self, "pitch_slider"):
            pval = int(mem.get("pitch", 0))
            self.pitch_slider.blockSignals(True)
            self.pitch_slider.setValue(pval)
            self.pitch_slider.blockSignals(False)
            self._update_pitch_label(pval)
            if self.playback_engine:
                try:
                    self.playback_engine.set_deck_rate(self.deck_id, 1.0 + (pval / 100.0))
                except Exception:
                    pass

        if hasattr(self, "volume_slider"):
            tval = int(mem.get("trim", 85))
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(tval)
            self.volume_slider.blockSignals(False)
            if self.playback_engine:
                try:
                    self.playback_engine.set_deck_trim(self.deck_id, tval / 100.0)
                except Exception:
                    pass

        if hasattr(self, "keylock_btn"):
            kl = bool(mem.get("keylock", False))
            self.keylock_btn.setChecked(kl)
            if self.playback_engine:
                try:
                    self.playback_engine.set_deck_keylock(self.deck_id, kl)
                except Exception:
                    pass
            self.keylock_btn.setStyleSheet(
                "font-size: 11px; font-weight: 700; background-color: #166534; color: white;"
                if kl else "font-size: 11px; font-weight: 700;"
            )

        self._update_status("MEM RECALLED")
        QtCore.QTimer.singleShot(1300, lambda: self._update_status("✓ Gotowy"))
        logger.info(f"{self.deck_label}: Memory recalled (hotcues={len(self._hotcues)})")

    def _ensure_play_after_recall(self):
        """Helper to resume playback post-recall reload without races."""
        if self.playback_engine:
            try:
                if not self.playback_engine.deck(self.deck_id).is_playing():
                    # Engine API is toggle_deck (not toggle_play_deck) — fixed P0 bug
                    self.playback_engine.toggle_deck(self.deck_id)
                    if hasattr(self, "play_btn"):
                        self.play_btn.setText("❚❚")
            except Exception:
                pass

    def load_track(self, track: Track) -> None:
        """Load a Track into this deck (engine + UI + hotcues from DB).

        # REFACTOR: Added return annotation + note that hotcue loading now goes
        # through the manager.
        """
        # Ensure we have DB id for hotcue persistence if this track is in library
        if track and not getattr(track, 'id', None):
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(track.path)
                if dbt and dbt.id:
                    track = dbt
            except Exception as exc:
                logger.debug(f"Deck {self.deck_label}: DB lookup for hotcue track id failed: {exc}")
        self.current_track = track
        title = f"{track.artist or ''} - {track.title or ''}".strip(" -") or Path(track.path).name
        self.info_label.setText(title[:52])

        self._original_bpm = getattr(track, 'bpm', None) if getattr(track, 'bpm', None) and track.bpm > 10 else None

        # Reset UI state
        self.waveform.clear()
        self._loop_in_ms = None
        self._loop_out_ms = None
        self._loop_enabled = False
        self.loop_toggle.setChecked(False)
        self.waveform.clear_loop()
        self.keylock_btn.setChecked(False)
        self.keylock_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.pfl_btn.setChecked(False)
        self.pfl_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
        self._pfl_enabled = False
        # Reset pro states on new track load
        self._is_synced_to_other = False
        if hasattr(self, 'sync_btn'):
            self.sync_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
        self._main_cue_ms = 0
        if hasattr(self, 'cue_btn'):
            self.cue_btn.setToolTip("CUE: jump to main cue point (double-click waveform to set/adjust; uses quantize if Q ON)")
        self.loop_toggle.setStyleSheet("font-size: 11px; font-weight: 700;")
        # Keep quantize preference across loads (user choice)

        if self._original_bpm:
            self.waveform.set_bpm(self._original_bpm)
            self.bpm_label.setText(f"{self._original_bpm:.1f} BPM")

        if self.playback_engine:
            try:
                success = self.playback_engine.load_deck(self.deck_id, track.path)
            except Exception as e:
                logger.exception(f"{self.deck_label}: Exception during engine.load_deck for {track.path}")
                success = False

            if success:
                try:
                    state = self.playback_engine.get_deck_state(self.deck_id)
                    duration = state.duration_ms if state else 0
                    self.waveform.set_duration(duration)
                    self._on_eq_changed()
                    self._load_waveform_async(track.path, duration)
                    if hasattr(track, 'id') and track.id:
                        self._load_hotcues_from_track(track.id)
                    logger.info(f"{self.deck_label}: Załadowano {Path(track.path).name}")
                    self._update_status("✓ Utwór załadowany")
                    self._update_effective_bpm()
                except Exception as e:
                    logger.exception(f"{self.deck_label}: Post-load error after successful load_deck")
                    self._update_status("✗ Błąd po załadowaniu")
            else:
                last_err = ""
                try:
                    if self.playback_engine:
                        last_err = self.playback_engine.deck(self.deck_id).get_last_error() or ""
                except Exception as exc:
                    logger.debug(f"{self.deck_label}: get_last_error failed after load fail: {exc}")
                msg = f"✗ Błąd ładowania" + (f" ({last_err})" if last_err else "")
                logger.warning(f"{self.deck_label}: Nie udało się załadować pliku. {last_err}")
                self._update_status(msg)
        else:
            logger.warning(f"{self.deck_label}: Brak backendu audio – tylko podgląd metadanych")
            self._update_status("⚠ Brak silnika")
            self._update_effective_bpm()

    def unload_track(self):
        """Unload current track from this deck (stops playback, clears UI + notifies)."""
        self.current_track = None
        self.info_label.setText("No track loaded")
        self.bpm_label.setText("— BPM")
        self.waveform.clear()
        self._loop_in_ms = None
        self._loop_out_ms = None
        self._loop_enabled = False
        if hasattr(self, 'loop_toggle'):
            self.loop_toggle.setChecked(False)
        self.waveform.clear_loop()
        self.keylock_btn.setChecked(False)
        self.keylock_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.pfl_btn.setChecked(False)
        self.pfl_btn.setStyleSheet("font-size: 11px; font-weight: 700;")
        self._pfl_enabled = False
        if self.playback_engine:
            try:
                self.playback_engine.stop_deck(self.deck_id)
            except Exception as exc:
                logger.debug(f"{self.deck_label}: stop_deck on unload raised (ignored): {exc}")
        self._update_status("— Unloaded")
        logger.info(f"{self.deck_label}: Track unloaded")

    def _load_waveform_async(self, audio_path: str, duration_ms: int):
        """Generuje prawdziwy waveform w tle używając bezpiecznego QRunnable + path token
        (zapobiega TypeError i aktualizacjom waveformy dla już odładowanych utworów).
        """
        if not audio_path:
            return
        token = str(audio_path)
        self.waveform.set_expected_waveform_token(token)
        runnable = WaveformRunnable(audio_path, duration_ms, self.waveform, token)
        QtCore.QThreadPool.globalInstance().start(runnable)

    def set_visible_section(self, section: str, visible: bool):
        """Pokazuje/ukrywa sekcje (Hotcues, Loops, EQ itd.)."""
        if section == "hotcues":
            self.hotcue_container.setVisible(visible)
        elif section == "loops":
            self.loop_container.setVisible(visible)
        # EQ jest na stałe widoczny w tej wersji (zgodnie z decyzją)


class SinglePlayerView(QtWidgets.QFrame):
    """
    Clean, focused "Odtwarzacz" (single-deck) view.
    Significantly less dense than the pro dual console:
    - Large readable waveform + transport
    - Basic 4 hotcue pads only
    - Simple volume
    - No EQ, no loops, no pitch/sync/memory/PFL/8-hotcues/crossfader
    Uses the shared PlaybackEngine (deck "A").

    # REFACTOR: Now uses HotcueManager for hotcue state (same as DeckWidget)
    # to eliminate the previous near-verbatim duplication of hotcue + DB code.
    """

    def __init__(self, playback_engine: PlaybackEngine, parent: QtWidgets.QWidget | None = None) -> None:
        # REFACTOR: Added type hints and return annotation.
        super().__init__(parent)
        self.playback_engine = playback_engine
        self.current_track: Optional[Track] = None
        # REFACTOR: Use shared HotcueManager (max 4 for this simple view) instead of raw dict
        self._hotcue_mgr: HotcueManager = HotcueManager(max_cues=4)
        self._hotcues: dict[int, int] = self._hotcue_mgr.hotcues  # alias for compatibility during transition
        self._main_cue_ms: int = 0
        self._quantize_enabled: bool = True   # for sync compatibility with DeckWidget

        self._playhead_timer = QtCore.QTimer(self)
        self._playhead_timer.setInterval(45)
        self._playhead_timer.timeout.connect(self._update_playhead)

        self.setAcceptDrops(True)

        # Clean card container look (breathing room vs dense pro console)
        self.setStyleSheet(f"""
            SinglePlayerView {{
                background-color: {COLORS["panel"]};
                border: 1px solid {COLORS["panel_border"]};
                border-radius: 10px;
            }}
        """)

        # === NOWY, PRAKTYCZNY UKŁAD W STYLU REKORDBOX (czysty i czytelny) ===
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # 1. Nagłówek - Track + BPM
        header = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel("Brak utworu — upuść plik lub załaduj z biblioteki")
        self.title_label.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLORS['text']};")
        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {COLORS['accent']}; padding: 2px 10px;")
        header.addWidget(self.title_label, 1)
        header.addWidget(self.bpm_label)
        layout.addLayout(header)

        # 2. WAVEFORM - największy element (ok. 55-60% wysokości)
        self.waveform = WaveformWidget()
        self.waveform.setMinimumHeight(170)
        self.waveform.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(self.waveform, 6)

        # 3. Czas - wyraźny i czytelny
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_muted']}; font-family: Consolas, monospace;")
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label, 0)

        # 4. Transport - duże, centralne przyciski
        transport = QtWidgets.QHBoxLayout()
        transport.setSpacing(16)
        transport.addStretch(1)

        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.cue_btn.setFixedSize(76, 46)
        self.cue_btn.setStyleSheet("font-size: 14px; font-weight: 800;")

        self.play_btn = QtWidgets.QPushButton("▶  ODTWÓRZ")
        self.play_btn.setFixedSize(142, 50)
        self.play_btn.setStyleSheet("font-size: 15px; font-weight: 700;")

        self.stop_btn = QtWidgets.QPushButton("■  STOP")
        self.stop_btn.setFixedSize(100, 46)
        self.stop_btn.setStyleSheet("font-size: 14px; font-weight: 700;")

        transport.addWidget(self.cue_btn)
        transport.addWidget(self.play_btn)
        transport.addWidget(self.stop_btn)
        transport.addStretch(1)
        layout.addLayout(transport, 0)

        # 5. Pitch + Volume
        sliders = QtWidgets.QHBoxLayout()
        sliders.setSpacing(16)

        # Pitch
        pitch_box = QtWidgets.QVBoxLayout()
        pitch_box.addWidget(QtWidgets.QLabel("PITCH"))
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        pitch_box.addWidget(self.pitch_slider)
        sliders.addLayout(pitch_box, 1)

        # Volume
        vol_box = QtWidgets.QVBoxLayout()
        vol_box.addWidget(QtWidgets.QLabel("VOLUME"))
        self.vol_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        vol_box.addWidget(self.vol_slider)
        sliders.addLayout(vol_box, 1)

        layout.addLayout(sliders, 0)

        # 6. Hot Cues - 4 duże pady na dole
        hc_label = QtWidgets.QLabel("HOT CUES")
        hc_label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(hc_label, 0)

        hotcue_row = QtWidgets.QHBoxLayout()
        hotcue_row.setSpacing(12)
        self.hotcue_pads = []
        for i in range(4):
            pad = HotcuePad(i)
            pad.setFixedSize(90, 58)
            pad.activated.connect(self._jump_to_hotcue)
            pad.set_requested.connect(self._set_hotcue_from_button)
            self.hotcue_pads.append(pad)
            hotcue_row.addWidget(pad)
        hotcue_row.addStretch(1)
        layout.addLayout(hotcue_row, 0)

        # 7. Mały przycisk ładowania (opcjonalny)
        self.load_file_btn = QtWidgets.QPushButton("📁 Wczytaj plik...")
        self.load_file_btn.setFixedHeight(26)
        # Always loads to deck A (single view + engine deck A)
        self.load_file_btn.clicked.connect(self._load_file_dialog)
        layout.addWidget(self.load_file_btn, 0)

        # Backend wiring
        self._wire_backend()

    def _wire_backend(self):
        if not self.playback_engine:
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.cue_btn.setEnabled(False)
            self.vol_slider.setEnabled(False)
            return

        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)
        self.cue_btn.clicked.connect(self._jump_to_cue)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)

        # Waveform interactions (reuse pro behavior where it makes sense)
        self.waveform.seek_requested.connect(self._seek)
        self.waveform.cue_set_requested.connect(self._set_hotcue_from_waveform)
        self.waveform.double_clicked.connect(self._set_main_cue_from_waveform)

        self._playhead_timer.start()

    def _sync_hotcues_alias(self) -> None:
        """Keep legacy _hotcues alias in sync with manager (SinglePlayerView).

        # REFACTOR: Bridge added for uniformity with DeckWidget + external sync code.
        """
        self._hotcues = self._hotcue_mgr.hotcues

    def resizeEvent(self, event):
        """Simple proportional scaling so nothing overlaps on window resize."""
        super().resizeEvent(event)
        if hasattr(self, 'waveform') and self.height() > 300:
            # Waveform takes roughly 45-55% of available height
            target_h = max(160, int(self.height() * 0.48))
            self.waveform.setMinimumHeight(target_h)

    # ---------------- Playback control ----------------

    def _toggle_play(self):
        if self.playback_engine:
            is_playing = self.playback_engine.toggle_deck("A")
            self.play_btn.setText("❚❚  PAUZA" if is_playing else "▶  ODTWÓRZ")
            # timer already running

    def _stop(self):
        if self.playback_engine:
            self.playback_engine.stop_deck("A")
            self.play_btn.setText("▶  ODTWÓRZ")
            self.waveform.set_playhead(0)
            self.time_label.setText("0:00 / 0:00")

    def _jump_to_cue(self):
        if self.playback_engine:
            target = self._main_cue_ms or 0
            self.playback_engine.seek_deck("A", target)
            self.waveform.set_playhead(target)

    def _on_volume_changed(self, value: int):
        if self.playback_engine:
            self.playback_engine.set_deck_trim("A", value / 100.0)
        # Note: no separate vol_val label in this view (slider is self-sufficient)

    def _seek(self, time_ms: int):
        if self.playback_engine:
            self.playback_engine.seek_deck("A", time_ms)
            self.waveform.set_playhead(time_ms)

    def _set_main_cue_from_waveform(self, time_ms: int):
        if not self.current_track:
            return
        self._main_cue_ms = time_ms
        self.waveform.set_playhead(time_ms)
        if self.playback_engine:
            self.playback_engine.seek_deck("A", time_ms)
        self.cue_btn.setToolTip(f"CUE @ {self._format_time(time_ms)} (double-click waveform to change)")

    def _set_hotcue_from_waveform(self, time_ms: int):
        """Shift+click on waveform sets next free hotcue (0-3).

        # REFACTOR: Storage + persistence delegated to HotcueManager (removes
        # duplication with the equivalent method in DeckWidget).
        """
        if not self.current_track:
            return
        for idx in range(4):
            if self._hotcue_mgr.get(idx) is None:
                self._hotcue_mgr.set(idx, time_ms)
                self._sync_hotcues_alias()
                self._update_hotcue_pad(idx)
                self._save_hotcue_to_db(idx, time_ms)
                return
        # overwrite first
        self._hotcue_mgr.set(0, time_ms)
        self._sync_hotcues_alias()
        self._update_hotcue_pad(0)
        self._save_hotcue_to_db(0, time_ms)

    def _set_hotcue_from_button(self, index: int):
        """Right-click / set button on pad — capture current playhead.

        # REFACTOR: Uses HotcueManager (shared implementation).
        """
        if not self.playback_engine or not self.current_track:
            return
        state = self.playback_engine.get_deck_state("A")
        current = state.position_ms if state else 0
        self._hotcue_mgr.set(index, current)
        self._sync_hotcues_alias()
        self._update_hotcue_pad(index)
        self._save_hotcue_to_db(index, current)

    def _jump_to_hotcue(self, index: int):
        """Jump (or Ctrl+delete) hotcue.

        # REFACTOR: Data access + delete via HotcueManager (was raw dict).
        """
        mods = QtWidgets.QApplication.keyboardModifiers()
        if mods & QtCore.Qt.KeyboardModifier.ControlModifier:
            if self._hotcue_mgr.get(index) is not None:
                self._hotcue_mgr.clear(index)
                self._sync_hotcues_alias()
                self._update_hotcue_pad(index)
                self._delete_hotcue_from_db(index)
            return
        t = self._hotcue_mgr.get(index)
        if t is not None and self.playback_engine:
            self.playback_engine.seek_deck("A", t)
            self.waveform.set_playhead(t)

    def _update_hotcue_pad(self, index: int):
        """Refresh pad visuals from manager (SinglePlayerView).

        # REFACTOR: Now reads via HotcueManager (matching DeckWidget change).
        """
        if index >= len(self.hotcue_pads):
            return
        pad = self.hotcue_pads[index]
        cue_time = self._hotcue_mgr.get(index)
        if cue_time is not None:
            pad._has_cue = True
            pad.set_cue_time(cue_time)
        else:
            pad._has_cue = False
            pad.set_cue_time(None)
        pad._update_style()

    # ---------------- DB hotcue helpers (now thin delegations — duplication removed) ----------------

    def _save_hotcue_to_db(self, index: int, time_ms: int):
        """# REFACTOR: Delegation to shared HotcueManager (was ~15 lines of duplicated try/except + CuePoint creation)."""
        if not self.current_track or not getattr(self.current_track, 'id', None):
            return
        self._hotcue_mgr.set_track_id(self.current_track.id)
        self._hotcue_mgr.save_to_db(index, time_ms)

    def _delete_hotcue_from_db(self, index: int):
        """# REFACTOR: Delegation to shared HotcueManager."""
        if not self.current_track or not getattr(self.current_track, 'id', None):
            return
        self._hotcue_mgr.set_track_id(self.current_track.id)
        self._hotcue_mgr.delete_from_db(index)

    def _load_hotcues_from_track(self, track_id: int):
        """# REFACTOR: Data load via HotcueManager; only pad refresh kept locally."""
        loaded = self._hotcue_mgr.load_from_db(track_id)
        self._sync_hotcues_alias()

        for p in self.hotcue_pads:
            p._has_cue = False
            p.set_cue_time(None)
            p._update_style()

        for idx, t_ms in loaded.items():
            if idx < len(self.hotcue_pads):
                p = self.hotcue_pads[idx]
                p._has_cue = True
                p.set_cue_time(t_ms)
                p._update_style()

    # ---------------- Track loading (public API used by DJPlayerWindow) ----------------

    def load_track(self, track: Track) -> None:
        """Load a Track into the single player view (deck "A" in engine).

        # REFACTOR: Signature + docstring improved. Hotcue loading now via manager.
        """
        # Enrich id if possible (for hotcue persistence)
        if track and not getattr(track, 'id', None):
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(track.path)
                if dbt and getattr(dbt, 'id', None):
                    track = dbt
            except Exception as exc:
                logger.debug(f"SinglePlayerView: DB lookup for hotcue track id failed: {exc}")

        self.current_track = track
        title = f"{track.artist or ''} - {track.title or ''}".strip(" -") or Path(track.path).name
        self.title_label.setText(title[:60])

        bpm = getattr(track, 'bpm', None)
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{bpm:.1f} BPM")
            self.waveform.set_bpm(bpm)
        else:
            self.bpm_label.setText("— BPM")
            self.waveform.set_bpm(None)

        # Reset state
        self.waveform.clear()
        self._main_cue_ms = 0
        self.cue_btn.setToolTip("CUE: jump to main cue (double-click waveform to set)")
        # REFACTOR: Clear via manager
        self._hotcue_mgr.clear_all()
        self._sync_hotcues_alias()
        for p in self.hotcue_pads:
            p._has_cue = False
            p.set_cue_time(None)
            p._update_style()

        if self.playback_engine:
            try:
                ok = self.playback_engine.load_deck("A", track.path)
            except Exception as e:
                logger.exception(f"SinglePlayerView: Exception loading {track.path}")
                ok = False

            if ok:
                try:
                    st = self.playback_engine.get_deck_state("A")
                    dur = st.duration_ms if st else 0
                    self.waveform.set_duration(dur)
                    self._load_waveform_async(track.path, dur)
                    if getattr(track, 'id', None):
                        self._load_hotcues_from_track(track.id)
                    self.play_btn.setText("▶  ODTWÓRZ")
                    self.time_label.setText(f"0:00 / {self._format_time(dur)}")
                except Exception as e:
                    logger.exception("SinglePlayerView: Post-load error")
                    self.time_label.setText("0:00 / 0:00")
            else:
                last_err = ""
                try:
                    if self.playback_engine:
                        last_err = self.playback_engine.deck("A").get_last_error() or ""
                except Exception as exc:
                    logger.debug(f"SinglePlayerView: get_last_error failed after load fail: {exc}")
                self.time_label.setText("0:00 / 0:00")
                err_msg = "✗ Błąd ładowania" + (f" ({last_err})" if last_err else "")
                logger.warning(f"SinglePlayerView: Nie udało się załadować pliku. {last_err}")
                # Surface the *real* backend error to the user (was only in log before)
                self._update_status(err_msg)
        else:
            self.time_label.setText("0:00 / 0:00")

    def _update_status(self, text: str):
        """Minimal status for single view – shows in title area temporarily."""
        if hasattr(self, 'title_label'):
            self._last_title = getattr(self, '_last_title', self.title_label.text())
            self.title_label.setText(text)
            QtCore.QTimer.singleShot(2200, lambda: self.title_label.setText(getattr(self, '_last_title', '')) if hasattr(self, 'title_label') else None)

    def _load_waveform_async(self, audio_path: str, duration_ms: int):
        """Safe async waveform using QRunnable + token (see DeckWidget for rationale)."""
        if not audio_path:
            return
        token = str(audio_path)
        self.waveform.set_expected_waveform_token(token)
        runnable = WaveformRunnable(audio_path, duration_ms, self.waveform, token)
        QtCore.QThreadPool.globalInstance().start(runnable)

    def _format_time(self, ms: int) -> str:
        """Local time formatter (mm:ss) for CUE / time label.

        # REFACTOR: Now delegates to shared module-level format_track_time
        # (extracted to address duplication between DeckWidget and SinglePlayerView).
        # Preserves original behavior exactly.
        """
        return format_track_time(ms)

    def _update_playhead(self):
        if not self.playback_engine:
            return
        try:
            state = self.playback_engine.get_deck_state("A")
            if not state:
                return
            self.waveform.set_playhead(state.position_ms)

            # Update play button from real state
            is_play = False
            try:
                is_play = bool(self.playback_engine.deck("A").is_playing())
            except Exception:
                is_play = getattr(state, "is_playing", False)
            self.play_btn.setText("❚❚  PAUZA" if is_play else "▶  ODTWÓRZ")

            # Time label
            pos = state.position_ms
            dur = state.duration_ms or 0
            self.time_label.setText(f"{self._format_time(pos)} / {self._format_time(dur)}")
        except Exception:
            pass

    # ---------------- Drag & drop + file dialog ----------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-lumbago-track-paths") or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        paths = []
        if mime.hasFormat("application/x-lumbago-track-paths"):
            data = mime.data("application/x-lumbago-track-paths").data().decode()
            paths = [p for p in data.split(",") if p]
        elif mime.hasUrls():
            for u in mime.urls():
                if u.isLocalFile():
                    paths.append(u.toLocalFile())
        if paths:
            self._load_path(paths[0])
            event.acceptProposedAction()

    def _load_file_dialog(self):
        """Open file dialog and load into single view (deck A)."""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj utwór do odtwarzacza",
            "", "Audio (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All (*)"
        )
        if path:
            self._load_path(path)

    def _load_path(self, path: str):
        try:
            from pathlib import Path as P
            name = P(path).stem
            t = Track(path=path, title=name)
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(path)
                if dbt and dbt.id:
                    t = dbt
            except Exception:
                pass
            self.load_track(t)
        except Exception:
            pass


class DJPlayerWindow(QtWidgets.QMainWindow):
    """Główne niezależne okno DJ Playera."""

    # Signals for tight integration with main library views (now playing indicators, sync)
    deck_track_loaded = QtCore.pyqtSignal(str, object)   # deck ("A"/"B"), Track
    deck_track_unloaded = QtCore.pyqtSignal(str)         # deck
    all_stopped = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lumbago DJ Player")
        self.setMinimumSize(620, 520)
        self.resize(680, 580)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # ========== MODE SELECTOR BAR (always visible) ==========
        # "Odtwarzacz" = clean single-deck view   |   "Konsola DJ" = full pro dual-deck console
        mode_bar = QtWidgets.QHBoxLayout()
        mode_bar.setContentsMargins(0, 0, 0, 4)
        mode_bar.setSpacing(2)

        self.mode_btn_single = QtWidgets.QPushButton("Odtwarzacz")
        self.mode_btn_console = QtWidgets.QPushButton("Konsola DJ")
        for btn in (self.mode_btn_single, self.mode_btn_console):
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setFixedWidth(118)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a2233;
                    border: 1px solid #2f3a52;
                    border-radius: 5px;
                    font-weight: 700;
                    font-size: 12px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS["accent"]};
                }}
                QPushButton:checked {{
                    background-color: {COLORS["accent"]};
                    color: {COLORS["bg"]};
                    border-color: {COLORS["accent"]};
                    font-weight: 800;
                }}
            """)

        self.mode_btn_group = QtWidgets.QButtonGroup(self)
        self.mode_btn_group.addButton(self.mode_btn_single, 0)
        self.mode_btn_group.addButton(self.mode_btn_console, 1)
        self.mode_btn_group.idClicked.connect(self._switch_player_mode)

        # Default to full console (preserves existing rich experience)
        self.mode_btn_console.setChecked(True)
        self._current_mode = "console"   # "console" or "single"

        mode_bar.addStretch(1)
        mode_bar.addWidget(self.mode_btn_single)
        mode_bar.addWidget(self.mode_btn_console)
        mode_bar.addStretch(1)
        main_layout.addLayout(mode_bar)

        # Track widgets that belong to the dual console for show/hide during mode switch
        self._console_widgets: list[QtWidgets.QWidget] = []

        # Układ kompaktowy (deck A nad deck B)
        try:
            # Tworzymy wspólny silnik playbacku (VLC lub fallback)
            self.playback_engine = PlaybackEngine()

            # === NOWA ARCHITEKTURA (sole implementation) ===
            # Używamy helperów z tasku integracyjnego — czysty, powtarzalny wiring
            # Nowa architektura zawsze (import succeeded)
            try:
                created_dual = self._create_dual_console_ui(main_layout)
                self.dual_console = created_dual
                if created_dual is None:
                    raise RuntimeError("dual console creation returned None")
                # === NOWA ARCHITEKTURA AKTYWNA (primary path) ===
                logger.info("NEW ARCHITECTURE ACTIVE: DeckController + FocusedDeckView/ConsoleDeckView/DualConsoleWidget (pełny wiring drag&drop, skróty, mikser)")
                logger.info("Nowa architektura - sole impl (stary DeckWidget/SinglePlayerView usunięty)")
            except Exception as e:
                logger.exception("Nowa architektura zawiodła przy tworzeniu UI - nie ma fallbacku")
                raise  # re-raise to be caught by outer except and show error dialog

            # Recent history per deck (for quick reloads, task requirement)
            self._recent_a: list[Track] = []
            self._recent_b: list[Track] = []
            self._MAX_RECENT = 8

            # === SMOKE TEST READY (po final cleanup) ===
            # Uruchom:
            #   $env:LUMBAGO_SAFE_MODE=1; $env:LUMBAGO_SMOKE_SECONDS=3; python main.py
            # Oczekuj w logach: "NEW ARCHITECTURE ACTIVE" (nowa architektura primary).
            # Pełny manual checklist: crew/AGENT3_UI_Designer_Rekordbox_Redo.md (hotcues, waveform, drag&drop, tryby, mixer, skróty, DB persystencja).
            # Testy: pytest tests/test_dj_hotcue_manager.py  (musi przejść po przeniesieniu)
            # Po starcie w trybie console: DualConsoleWidget z dwoma ConsoleDeckView + DeckCtrl + MixerStrip (opcjonalny).

        except Exception as exc:
            logger.exception("Błąd podczas tworzenia decków w DJPlayerWindow")
            # Zawsze pokazuj okno z czytelnym błędem + możliwość zaznaczenia tekstu
            error_text = QtWidgets.QPlainTextEdit()
            error_text.setPlainText(
                "Wystąpił błąd podczas inicjalizacji DJ Playera.\n\n"
                f"Szczegóły:\n{exc}\n\n"
                "Jeśli błąd dotyczy 'QShortcut' lub podobnych rzeczy — to jest błąd w kodzie aplikacji (nie problem z VLC).\n\n"
                "Spróbuj zrestartować aplikację. Jeśli problem będzie się powtarzał, skopiuj dokładny tekst błędu i wyślij."
            )
            error_text.setReadOnly(True)
            error_text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
            main_layout.addWidget(error_text)

            # Przycisk kopiowania
            copy_btn = QtWidgets.QPushButton("Kopiuj błąd do schowka")
            copy_btn.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(error_text.toPlainText()))
            main_layout.addWidget(copy_btn)
            if hasattr(self, "_console_widgets"):
                self._console_widgets.extend([error_text, copy_btn])

            self.deck_a = None
            self.deck_b = None
            # Nie return — pozwalamy na otwarcie okna z komunikatem błędu

        # === GÓRNY MIXER STRIP (Master + HP Cue + PFL) ===
        # W nowej architekturze DualConsoleWidget ma własny mikser (cross/master/cue) — pomijamy stary
        # Używamy MixerStrip gdzie możliwe jako alternatywa/globalny pasek (task integracji)
        _use_new = getattr(self, "_use_new_dj_views", True)
        if self.deck_a and self.deck_b and not _use_new:
            self._build_mixer_strip(main_layout)
        elif _use_new and MixerStrip is not None:
            # Opcjonalny globalny MixerStrip na górze (dla PFL, master — cross jest w Dual)
            try:
                self.global_mixer = MixerStrip(self)
                # Podłącz sygnały do engine (gdzie wspierane)
                self.global_mixer.master_changed.connect(self._on_master_changed)
                self.global_mixer.hp_changed.connect(self._on_hp_changed)
                self.global_mixer.crossfader_changed.connect(self._on_global_crossfader)
                self.global_mixer.pfl_changed.connect(self._on_pfl_changed)
                main_layout.addWidget(self.global_mixer)
                if hasattr(self, "_console_widgets"):
                    self._console_widgets.append(self.global_mixer)
                QtCore.QTimer.singleShot(0, self._apply_initial_mixer_values)
            except Exception:
                logger.debug("MixerStrip nie podłączony (fallback do Dual wewnętrznego)")
                self.global_mixer = None

        # Fallback banner (clear but non-annoying) when QtMultimedia is active
        self._maybe_show_fallback_banner(main_layout)

        # Crossfader — bigger, clearer...
        # W nowej architekturze POMIJAMY (DualConsoleWidget ma własny crossfader + master/cue podłączony bezpośrednio do engine)
        _use_new = getattr(self, "_use_new_dj_views", True)
        if not _use_new:
            cross_frame = QtWidgets.QFrame()
            cross_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS["panel"]};
                    border: 1px solid {COLORS["panel_border"]};
                    border-radius: 6px;
                    padding: 4px 8px;
                }}
            """)
            cross = QtWidgets.QHBoxLayout(cross_frame)
            cross.setContentsMargins(8, 4, 8, 4)
            cross.setSpacing(6)

            a_lbl = QtWidgets.QLabel("A")
            a_lbl.setStyleSheet(f"color: {COLORS['accent']}; font-size: 14px; font-weight: 900; min-width: 18px;")
            cross.addWidget(a_lbl)

            self.crossfader = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.crossfader.setRange(0, 100)
            self.crossfader.setValue(50)
            self.crossfader.setMinimumHeight(26)
            self.crossfader.setToolTip("Crossfader — drag for A/B mix. Center = both decks audible")
            cross.addWidget(self.crossfader, 1)

            b_lbl = QtWidgets.QLabel("B")
            b_lbl.setStyleSheet(f"color: {COLORS['accent']}; font-size: 14px; font-weight: 900; min-width: 18px;")
            cross.addWidget(b_lbl)

            main_layout.addWidget(cross_frame)
            self._console_widgets.append(cross_frame)

            # Podłączamy crossfader + volume slidery do wspólnej logiki miksowania (stara architektura)
            if self.crossfader:
                self.crossfader.valueChanged.connect(self._update_crossfader_volumes)
            if self.deck_a and hasattr(self.deck_a, 'volume_slider') and self.deck_a.volume_slider:
                self.deck_a.volume_slider.valueChanged.connect(self._update_crossfader_volumes)
            if self.deck_b and hasattr(self.deck_b, 'volume_slider') and self.deck_b.volume_slider:
                self.deck_b.volume_slider.valueChanged.connect(self._update_crossfader_volumes)

        # Pasek przełączników widoczności (zawsze na dole)
        toggle_bar = QtWidgets.QHBoxLayout()
        toggle_bar.addWidget(QtWidgets.QLabel("Pokaż / Ukryj:"))

        self.btn_hotcues = QtWidgets.QPushButton("Hotcues")
        self.btn_loops = QtWidgets.QPushButton("Loops")
        self.btn_beatgrid = QtWidgets.QPushButton("Beatgrid ✓")   # domyślnie włączony
        self.btn_energy = QtWidgets.QPushButton("Energy")
        self.btn_eq = QtWidgets.QPushButton("EQ ✓")               # domyślnie włączony

        for btn in (self.btn_hotcues, self.btn_loops, self.btn_beatgrid, self.btn_energy, self.btn_eq):
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedHeight(24)
            toggle_bar.addWidget(btn)

        toggle_bar.addStretch(1)

        # Przełączanie układu
        self.btn_layout = QtWidgets.QPushButton("Układ: Kompaktowy")
        self.btn_layout.setCheckable(True)
        self.btn_layout.clicked.connect(self._toggle_layout)
        toggle_bar.addWidget(self.btn_layout)

        self._current_layout = "compact"  # compact lub wide

        toggle_container = QtWidgets.QWidget()
        toggle_container.setLayout(toggle_bar)
        main_layout.addWidget(toggle_container)
        self._console_widgets.append(toggle_container)

        # Połączenia przełączników
        self.btn_hotcues.toggled.connect(lambda v: self._toggle_section("hotcues", v))
        self.btn_loops.toggled.connect(lambda v: self._toggle_section("loops", v))
        self.btn_beatgrid.toggled.connect(self._toggle_beatgrid)
        # EQ already always visible + per-deck controls

        self._apply_base_style()

        # Status bar
        self.setStatusBar(QtWidgets.QStatusBar())

        # Inicjalne ustawienie głośności – TYLKO stara architektura (nowa ma własny mikser w DualConsole)
        _use_new = getattr(self, "_use_new_dj_views", True)
        if not _use_new:
            QtCore.QTimer.singleShot(0, self._update_crossfader_volumes)

        # Pokazujemy czytelny status backendu na deckach (VLC / Qt / Brak) — defensywnie
        if hasattr(self, '_update_deck_backend_status'):
            QtCore.QTimer.singleShot(50, self._update_deck_backend_status)
        if hasattr(self, '_update_backend_info_label'):
            QtCore.QTimer.singleShot(80, self._update_backend_info_label)

        # ========== CREATE SINGLE PLAYER VIEW (inserted right after mode bar for clean toggle) ==========
        # W nowej architekturze używamy helpera _create_focused_single_ui (FocusedDeckView + ctrl)
        # Stary SinglePlayerView tylko w fallbacku. Alias single_player_view zawsze ustawiony.
        try:
            _use_new = getattr(self, "_use_new_dj_views", True)
            if _use_new:
                # Helper już mógł stworzyć single_container — użyj go lub utwórz
                if not hasattr(self, "single_container") or self.single_container is None:
                    focused = self._create_focused_single_ui(main_layout)
                    if focused:
                        self.single_player_view = focused
                else:
                    # single_container już istnieje z dual creation — NIE wstawiaj ponownie (już w layout)
                    self.single_player_view = getattr(self, "single_container", None)
                    # Upewnij się że nie jest widoczny na starcie (domyślnie console)
                    if self.single_player_view:
                        self.single_player_view.setVisible(False)
                if self.single_player_view:
                    self.single_player_view.setVisible(False)
            else:
                self.single_player_view = SinglePlayerView(self.playback_engine, self)
                main_layout.insertWidget(1, self.single_player_view)
                self.single_player_view.setVisible(False)

            if not hasattr(self, "_console_widgets"):
                self._console_widgets = []
            # single_player_view to widok alternatywny (nie console)
        except Exception as e:
            logger.warning(f"Failed to create SinglePlayerView / Focused: {e}")
            self.single_player_view = None

        # Akceptujemy dropy na całym oknie (fallback)
        self.setAcceptDrops(True)

        # Podstawowe skróty klawiszowe (extended to 8 for advanced hotcue mode)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Space), self, self._global_play_pause)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self, lambda: self._quick_load_hotcue(0))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self, lambda: self._quick_load_hotcue(1))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self, lambda: self._quick_load_hotcue(2))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+4"), self, lambda: self._quick_load_hotcue(3))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+5"), self, lambda: self._quick_load_hotcue(4))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+6"), self, lambda: self._quick_load_hotcue(5))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+7"), self, lambda: self._quick_load_hotcue(6))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+8"), self, lambda: self._quick_load_hotcue(7))

    def _toggle_section(self, section: str, visible: bool):
        # Nowa architektura: ConsoleDeckView / Focused nie mają set_visible_section (na razie pełny widok)
        # Zachowujemy dla kompatybilności ze starym UI — defensywnie
        if False:  # old architecture removed (sole new DJ impl)
            if self.deck_a and hasattr(self.deck_a, "set_visible_section"):
                self.deck_a.set_visible_section(section, visible)
            if self.deck_b and hasattr(self.deck_b, "set_visible_section"):
                self.deck_b.set_visible_section(section, visible)

    def _toggle_beatgrid(self, visible: bool):
        # Wsparcie dla obu architektur
        if True:  # new architecture sole impl (old removed)
            # W dual: waveformy są wewnątrz ConsoleDeckView — ustaw przez dual jeśli ma API
            if hasattr(self, "dual_console") and self.dual_console:
                for deck_id in ("A", "B"):
                    v = self.dual_console.get_deck_view(deck_id) if hasattr(self.dual_console, "get_deck_view") else None
                    if v and hasattr(v, "waveform") and hasattr(v.waveform, "set_beatgrid_visible"):
                        try: v.waveform.set_beatgrid_visible(visible)
                        except Exception: pass
            if hasattr(self, "single_container") and self.single_container:
                if hasattr(self.single_container, "waveform") and hasattr(self.single_container.waveform, "set_beatgrid_visible"):
                    try: self.single_container.waveform.set_beatgrid_visible(visible)
                    except Exception: pass
        else:
            if self.deck_a and hasattr(self.deck_a, "waveform"):
                self.deck_a.waveform.set_beatgrid_visible(visible)
            if self.deck_b and hasattr(self.deck_b, "waveform"):
                self.deck_b.waveform.set_beatgrid_visible(visible)
        # Single view alias
        spv = getattr(self, "single_player_view", None)
        if spv and hasattr(spv, "waveform") and hasattr(spv.waveform, "set_beatgrid_visible"):
            try: spv.waveform.set_beatgrid_visible(visible)
            except Exception: pass
        if hasattr(self, "btn_beatgrid"):
            self.btn_beatgrid.setText("Beatgrid ✓" if visible else "Beatgrid")

    def _build_mixer_strip(self, main_layout: QtWidgets.QVBoxLayout):
        """Górny pasek miksera — Master Volume + Headphone Cue (PFL) + podstawowe kontrolki globalne.
        To jedna z kluczowych rzeczy, których brakowało w poprzedniej wersji (propozycja wdrożona)."""
        mixer = QtWidgets.QHBoxLayout()
        mixer.setContentsMargins(4, 2, 4, 2)
        mixer.setSpacing(8)

        # MASTER
        mixer.addWidget(QtWidgets.QLabel("MASTER"))
        self.master_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(85)
        self.master_slider.setFixedWidth(120)
        self.master_slider.setToolTip("Głośność główna (Master)")
        mixer.addWidget(self.master_slider)
        self.master_value = QtWidgets.QLabel("85")
        self.master_value.setFixedWidth(28)
        mixer.addWidget(self.master_value)
        self.master_slider.valueChanged.connect(self._on_master_changed)

        mixer.addSpacing(12)

        # HEADPHONE CUE (PFL)
        mixer.addWidget(QtWidgets.QLabel("HP CUE"))
        self.hp_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hp_slider.setRange(0, 100)
        self.hp_slider.setValue(70)
        self.hp_slider.setFixedWidth(100)
        self.hp_slider.setToolTip("Głośność słuchawek (Headphone Cue)")
        mixer.addWidget(self.hp_slider)
        self.hp_value = QtWidgets.QLabel("70")
        self.hp_value.setFixedWidth(24)
        mixer.addWidget(self.hp_value)
        self.hp_slider.valueChanged.connect(self._on_hp_changed)

        mixer.addSpacing(8)

        # PFL toggles
        self.pfl_a = QtWidgets.QPushButton("PFL A")
        self.pfl_b = QtWidgets.QPushButton("PFL B")
        self.pfl_a.setCheckable(True)
        self.pfl_b.setCheckable(True)
        self.pfl_a.setFixedWidth(52)
        self.pfl_b.setFixedWidth(52)
        self.pfl_a.setToolTip("Podświetl / przygotuj Deck A do cue w słuchawkach")
        self.pfl_b.setToolTip("Podświetl / przygotuj Deck B do cue w słuchawkach")
        mixer.addWidget(self.pfl_a)
        mixer.addWidget(self.pfl_b)
        self.pfl_a.toggled.connect(lambda v: self._on_pfl_changed("A", v))
        self.pfl_b.toggled.connect(lambda v: self._on_pfl_changed("B", v))

        mixer.addSpacing(12)

        # SYNC (stub + wizualny)
        self.sync_btn = QtWidgets.QPushButton("SYNC")
        self.sync_btn.setFixedWidth(52)
        self.sync_btn.setToolTip("Zsynchronizuj BPM i fazę (na razie podstawowa wersja)")
        self.sync_btn.clicked.connect(self._do_sync)
        mixer.addWidget(self.sync_btn)

        mixer.addSpacing(8)

        # Load buttons (pro standalone usability)
        load_a = QtWidgets.QPushButton("Load A…")
        load_b = QtWidgets.QPushButton("Load B…")
        load_a.setFixedWidth(64)
        load_b.setFixedWidth(64)
        load_a.setStyleSheet("font-size: 10px;")
        load_b.setStyleSheet("font-size: 10px;")
        load_a.clicked.connect(lambda: self._load_file_dialog("A"))
        load_b.clicked.connect(lambda: self._load_file_dialog("B"))
        mixer.addWidget(load_a)
        mixer.addWidget(load_b)

        mixer.addSpacing(8)

        # Global deck controls (tight main<->player integration)
        stop_all_btn = QtWidgets.QPushButton("■ STOP ALL")
        stop_all_btn.setFixedWidth(78)
        stop_all_btn.setStyleSheet("font-size: 10px; font-weight: 700; color: #ff6b6b;")
        stop_all_btn.setToolTip("Stop playback on both decks immediately")
        stop_all_btn.clicked.connect(self.stop_all_decks)
        mixer.addWidget(stop_all_btn)

        unload_all_btn = QtWidgets.QPushButton("Unload All")
        unload_all_btn.setFixedWidth(78)
        unload_all_btn.setStyleSheet("font-size: 10px;")
        unload_all_btn.setToolTip("Unload tracks from both decks (keeps player open)")
        unload_all_btn.clicked.connect(self.unload_all)
        mixer.addWidget(unload_all_btn)

        mixer.addSpacing(6)

        # Recent history per-deck (clickable reloads, 5-8 tracks)
        self.recent_menu_a = QtWidgets.QMenu(self)
        self.recent_menu_b = QtWidgets.QMenu(self)
        self.recent_btn_a = QtWidgets.QToolButton()
        self.recent_btn_a.setText("Recent A ▾")
        self.recent_btn_a.setMenu(self.recent_menu_a)
        self.recent_btn_a.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.recent_btn_a.setFixedHeight(22)
        self.recent_btn_a.setStyleSheet("font-size: 9px; padding: 0 6px;")
        self.recent_btn_a.setToolTip("Ostatnio załadowane na Deck A (kliknij aby przeładować)")
        mixer.addWidget(self.recent_btn_a)

        self.recent_btn_b = QtWidgets.QToolButton()
        self.recent_btn_b.setText("Recent B ▾")
        self.recent_btn_b.setMenu(self.recent_menu_b)
        self.recent_btn_b.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.recent_btn_b.setFixedHeight(22)
        self.recent_btn_b.setStyleSheet("font-size: 9px; padding: 0 6px;")
        self.recent_btn_b.setToolTip("Ostatnio załadowane na Deck B (kliknij aby przeładować)")
        mixer.addWidget(self.recent_btn_b)

        # Populate menus dynamically
        self.recent_menu_a.aboutToShow.connect(lambda: self._populate_recent_menu("A", self.recent_menu_a))
        self.recent_menu_b.aboutToShow.connect(lambda: self._populate_recent_menu("B", self.recent_menu_b))

        mixer.addStretch(1)

        # Backend info (krótko)
        self.backend_info_label = QtWidgets.QLabel("")
        self.backend_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        mixer.addWidget(self.backend_info_label)

        mixer_container = QtWidgets.QWidget()
        mixer_container.setLayout(mixer)
        main_layout.addWidget(mixer_container)
        if hasattr(self, "_console_widgets"):
            self._console_widgets.append(mixer_container)

        # Inicjalne wartości
        QtCore.QTimer.singleShot(0, self._apply_initial_mixer_values)

    def _update_crossfader_volumes(self):
        """
        Crossfader steruje miksem A/B (stara ścieżka).
        W nowej architekturze (DualConsole) crossfader jest podłączony bezpośrednio w widoku — ta metoda jest no-op.
        """
        if True:  # new architecture sole impl (old removed)
            return  # DualConsole + DeckController + engine obsługują to wewnętrznie
        if not self.playback_engine or not hasattr(self, "crossfader") or not self.crossfader:
            return

        cross_value = (self.crossfader.value() / 50.0) - 1.0   # 0..100 → -1.0 .. +1.0
        self.playback_engine.set_crossfader(cross_value)

        # Volume slidery decków = trim/gain (niezależny od crossfadera) — tylko stara architektura
        try:
            if self.deck_a and hasattr(self.deck_a, "volume_slider") and self.deck_a.volume_slider:
                trim_a = self.deck_a.volume_slider.value() / 100.0
                self.playback_engine.set_deck_trim("A", trim_a)
            if self.deck_b and hasattr(self.deck_b, "volume_slider") and self.deck_b.volume_slider:
                trim_b = self.deck_b.volume_slider.value() / 100.0
                self.playback_engine.set_deck_trim("B", trim_b)
        except Exception:
            pass

    def _toggle_layout(self):
        """Przełącza między układem kompaktowym (pionowym) a szerokim (poziomym)."""
        if getattr(self, "_current_mode", "console") == "single":
            # Layout toggle is only meaningful in full dual console mode
            return
        main_layout = self.centralWidget().layout()

        # Usuwamy obecne decki + crossfader frame/slider
        for i in reversed(range(main_layout.count())):
            item = main_layout.itemAt(i)
            if item:
                w = item.widget()
                if w and w in (self.deck_a, self.deck_b):
                    main_layout.removeWidget(w)
                    w.setParent(None)
                # Also remove our crossfader wrapper frame if present
                if w and hasattr(self, "crossfader") and w != self.crossfader:
                    try:
                        if self.crossfader and w.findChild(QtWidgets.QSlider) is self.crossfader:
                            main_layout.removeWidget(w)
                            w.setParent(None)
                    except Exception:
                        pass

        if self._current_layout == "compact":
            decks_layout = QtWidgets.QHBoxLayout()
            decks_layout.addWidget(self.deck_a)
            decks_layout.addWidget(self.deck_b)
            main_layout.insertLayout(0, decks_layout)

            cross = QtWidgets.QHBoxLayout()
            cross.addWidget(QtWidgets.QLabel("A"))
            cross.addWidget(self.crossfader, 1)
            cross.addWidget(QtWidgets.QLabel("B"))
            main_layout.insertLayout(1, cross)

            self._current_layout = "wide"
            self.btn_layout.setText("Układ: Szeroki")
        else:
            main_layout.insertWidget(0, self.deck_a)
            main_layout.insertWidget(1, self.deck_b)

            cross = QtWidgets.QHBoxLayout()
            cross.addWidget(QtWidgets.QLabel("A"))
            cross.addWidget(self.crossfader, 1)
            cross.addWidget(QtWidgets.QLabel("B"))
            main_layout.insertLayout(2, cross)

            self._current_layout = "compact"
            self.btn_layout.setText("Układ: Kompaktowy")

        if False:  # old architecture removed (sole new DJ impl)
            QtCore.QTimer.singleShot(10, self._update_crossfader_volumes)

    # ------------------------------------------------------------------
    # HELPERY DLA NOWEJ ARCHITEKTURY (integracja wiring)
    # Tworzenie kontrolerów + widoków w stylu "dumb view + smart controller"
    # Zachowujemy pełne zachowanie, polski w komentarzach.
    # ------------------------------------------------------------------

    def _create_deck_controllers(self):
        """Helper #1: Tworzy parę DeckController (A/B) podłączoną do PlaybackEngine.
        # Używamy wyłącznie w nowej architekturze. Zwraca (ctrl_a, ctrl_b) lub (None, None).
        """
        if False or DeckController is None or not hasattr(self, "playback_engine"):  # old arch removed
            return None, None
        try:
            ctrl_a = DeckController("A", self.playback_engine)
            ctrl_b = DeckController("B", self.playback_engine)
            logger.debug("Nowa architektura: DeckController A/B utworzone")
            return ctrl_a, ctrl_b
        except Exception as exc:
            logger.exception(f"Błąd tworzenia DeckController: {exc}")
            return None, None

    def _create_dual_console_ui(self, main_layout: QtWidgets.QVBoxLayout):
        """Helper #2: Buduje DualConsoleWidget (dwa ConsoleDeckView + własny mikser z crossfader/master/cue).
        Podłączamy do layoutu, zapisujemy referencje. Zwraca dual lub None.
        """
        if False or DualConsoleWidget is None:  # old arch removed
            return None
        try:
            ctrl_a, ctrl_b = self._create_deck_controllers()
            if not ctrl_a or not ctrl_b:
                return None
            self._deck_ctrl_a = ctrl_a
            self._deck_ctrl_b = ctrl_b

            dual = DualConsoleWidget(ctrl_a, ctrl_b, self.playback_engine, self)
            main_layout.addWidget(dual)
            self._console_widgets.extend([dual])

            # Kompatybilność dla reszty kodu (deck_a/b wskazują na widoki ConsoleDeckView)
            self.deck_a = dual.get_deck_view("A") if hasattr(dual, "get_deck_view") else None
            self.deck_b = dual.get_deck_view("B") if hasattr(dual, "get_deck_view") else None

            # Przygotuj też single_container (Focused) — ukryty na start
            if FocusedDeckView is not None:
                self.single_container = FocusedDeckView(ctrl_a, self)
                self.single_container.setVisible(False)
                main_layout.addWidget(self.single_container)
            else:
                self.single_container = None

            logger.info("NEW ARCHITECTURE ACTIVE: DualConsoleWidget + 2x ConsoleDeckView + DeckController A/B + FocusedDeckView przygotowany (ukryty)")
            logger.debug("Nowa architektura: DualConsoleWidget + FocusedDeckView gotowe")
            return dual
        except Exception as exc:
            logger.exception(f"Błąd _create_dual_console_ui: {exc}")
            return None

    def _create_focused_single_ui(self, main_layout: QtWidgets.QVBoxLayout):
        """Helper #3: Tworzy/wymienia FocusedDeckView jako single view (tryb 'Odtwarzacz').
        Używany też fallbackowo w single_player_view.
        """
        if False or FocusedDeckView is None:  # old arch removed
            return None
        try:
            # Jeśli nie ma jeszcze kontrolera A — stwórz (dla pure single)
            if not hasattr(self, "_deck_ctrl_a") or self._deck_ctrl_a is None:
                ctrl_a, _ = self._create_deck_controllers()
                self._deck_ctrl_a = ctrl_a
                self._deck_ctrl_b = None  # w pure single B nie jest potrzebne

            if self._deck_ctrl_a is None:
                return None

            focused = FocusedDeckView(self._deck_ctrl_a, self)
            main_layout.insertWidget(1, focused)  # zaraz po mode bar
            focused.setVisible(False)
            self.single_container = focused
            # Alias dla kompatybilności ze starym kodem (load_track_to_deck itp.)
            self.single_player_view = focused
            logger.info("NEW ARCHITECTURE ACTIVE: FocusedDeckView (tryb single) + DeckController")
            logger.debug("Nowa architektura: FocusedDeckView (single) utworzony")
            return focused
        except Exception as exc:
            logger.exception(f"Błąd _create_focused_single_ui: {exc}")
            return None

    # ------------------------------------------------------------------
    # Player mode switching (Odtwarzacz vs Konsola DJ)
    # ------------------------------------------------------------------

    def _switch_player_mode(self, mode_id: int):
        """Switch between clean single-deck view and full dual console.
        Zaadaptowane dla nowej architektury (Focused + DualConsole + DeckController).
        Zachowuje pełne zachowanie dla fallbacku starego kodu.
        """
        is_single = (mode_id == 0)
        self._current_mode = "single" if is_single else "console"

        # Update button checked states (in case called programmatically)
        if hasattr(self, "mode_btn_single") and hasattr(self, "mode_btn_console"):
            self.mode_btn_single.setChecked(is_single)
            self.mode_btn_console.setChecked(not is_single)

        spv = getattr(self, "single_player_view", None)
        if spv:
            spv.setVisible(is_single)
            # Propagate current beatgrid visibility preference to single view on switch
            if hasattr(self, "btn_beatgrid") and hasattr(spv, "waveform"):
                try:
                    spv.waveform.set_beatgrid_visible(self.btn_beatgrid.isChecked())
                except Exception:
                    pass

        # Nowa architektura - przełączanie kontenerów (DualConsole vs FocusedDeckView)
        if True:  # new architecture sole impl (old removed)
            if hasattr(self, "single_container") and self.single_container:
                self.single_container.setVisible(is_single)
            if hasattr(self, "dual_console") and self.dual_console:
                self.dual_console.setVisible(not is_single)
            # W nowej architekturze deck_a/b to widoki z Dual (ukryte razem z kontenerem)
            # więc nie dotykamy ich bezpośrednio tutaj (kontener zarządza)

        # Aggressively hide/show console content (działa dla obu architektur)
        for w in getattr(self, "_console_widgets", []):
            if w:
                try:
                    w.setVisible(not is_single)
                except Exception:
                    pass

        # Extra safety dla starych elementów (cross_frame itp — tylko gdy istnieją)
        if hasattr(self, "cross_frame") and self.cross_frame:
            try: self.cross_frame.setVisible(not is_single)
            except Exception: pass

        # Sync tylko gdy mamy stary single_player_view + stary deck_a (fallback path)
        # W nowej architekturze sync jest prostszy (oba widoki subskrybują tego samego DeckController)
        use_old_sync = False and spv and hasattr(self, "deck_a") and self.deck_a  # old arch removed, always new sync
        if use_old_sync:
            try:
                self._sync_deck_a_state_between_views(is_single)
            except Exception as exc:
                logger.warning(f"Mode switch sync failed (non-fatal): {exc}")
        elif True and is_single:  # new arch sole
            # W trybie single z nową architekturą — upewnij się że Focused ma aktualny playhead
            try:
                if self.playback_engine and hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
                    state = self.playback_engine.get_deck_state("A")
                    if state and hasattr(self.single_container, "waveform"):
                        self.single_container.waveform.set_playhead(state.position_ms)
            except Exception:
                pass

    def _sync_deck_a_state_between_views(self, going_to_single: bool) -> None:
        """
        Robust bidirectional sync of Deck A <-> SinglePlayerView (same engine deck "A").
        Zaadaptowane: w nowej architekturze (DeckController) sync jest zbędny (oba widoki słuchają sygnałów tego samego kontrolera).
        Metoda zachowana dla pełnej kompatybilności fallbacku.
        """
        # W nowej architekturze — nic do roboty (wspólny DeckController + sygnały Qt)
        if True:  # new architecture sole impl (old removed)
            return

        spv = getattr(self, "single_player_view", None)
        da = getattr(self, "deck_a", None)
        if not spv or not da:
            return

        try:
            if going_to_single:
                # Console (dual) → Single view
                if not da.current_track:
                    return
                same_track = (spv.current_track is da.current_track) or \
                             (getattr(spv.current_track, 'path', None) == getattr(da.current_track, 'path', None))

                if not same_track:
                    spv.load_track(da.current_track)
                    return

                # Lightweight sync of mutable DJ state
                # REFACTOR: Prefer HotcueManager when present on either side (reduces raw dict coupling)
                src_hotcues = da._hotcue_mgr.hotcues if hasattr(da, "_hotcue_mgr") else da._hotcues
                if hasattr(spv, "_hotcue_mgr"):
                    spv._hotcue_mgr.clear_all()
                    for k, v in src_hotcues.items():
                        if 0 <= k < 4:
                            spv._hotcue_mgr.set(k, v)
                    if hasattr(spv, "_sync_hotcues_alias"):
                        spv._sync_hotcues_alias()
                else:
                    spv._hotcues = {k: v for k, v in src_hotcues.items() if 0 <= k < 4}
                # keep higher indices in deck_a only (they survive in DB)
                spv._main_cue_ms = getattr(da, '_main_cue_ms', 0) or 0

                # Copy a few pro states if present
                if hasattr(da, '_quantize_enabled'):
                    # Single has no quantize toggle exposed, but we can store it
                    spv._quantize_enabled = getattr(da, '_quantize_enabled', True)

                # Refresh pads (single only has 4)
                for i in range(4):
                    if hasattr(spv, '_update_hotcue_pad'):
                        spv._update_hotcue_pad(i)

                # Update waveform main cue / loop if single supports it (defensive)
                if hasattr(spv, 'waveform'):
                    if getattr(da, '_loop_in_ms', None) and getattr(da, '_loop_out_ms', None):
                        spv.waveform.set_loop(da._loop_in_ms, da._loop_out_ms)
                    else:
                        spv.waveform.clear_loop()

                    # Pull live playhead from engine so waveform doesn't jump on mode switch
                    try:
                        st = self.playback_engine.get_deck_state("A") if self.playback_engine else None
                        if st:
                            spv.waveform.set_playhead(st.position_ms)
                    except Exception as exc:
                        logger.debug(f"Sync playhead console→single failed: {exc}")

                logger.debug("DJ sync: console→single (lightweight hotcue/main-cue copy)")

                # Guarantee waveform peaks + beatgrid appear after lightweight mode switch (same track)
                try:
                    if hasattr(spv, "_load_waveform_async") and getattr(da, "current_track", None):
                        dur = 0
                        if self.playback_engine:
                            st = self.playback_engine.get_deck_state("A")
                            if st and st.duration_ms:
                                dur = st.duration_ms
                        if dur <= 0:
                            dur = 180000
                        spv._load_waveform_async(da.current_track.path, dur)
                        bpm = getattr(da, "_original_bpm", None)
                        if bpm:
                            spv.waveform.set_bpm(bpm)
                except Exception:
                    pass

            else:
                # Single → Console (dual)
                if not spv.current_track:
                    return
                same_track = (da.current_track is spv.current_track) or \
                             (getattr(da.current_track, 'path', None) == getattr(spv.current_track, 'path', None))

                if not same_track:
                    da.load_track(spv.current_track)
                    return

                # Copy state back (Deck A supports full 0-7)
                # REFACTOR: Use manager when available on source/target for consistency
                src_hotcues = spv._hotcue_mgr.hotcues if hasattr(spv, "_hotcue_mgr") else getattr(spv, "_hotcues", {})
                if hasattr(da, "_hotcue_mgr"):
                    da._hotcue_mgr.clear_all()
                    for k, v in src_hotcues.items():
                        da._hotcue_mgr.set(k, v)
                    if hasattr(da, "_sync_hotcues_alias"):
                        da._sync_hotcues_alias()
                else:
                    da._hotcues = dict(src_hotcues)
                da._main_cue_ms = getattr(spv, '_main_cue_ms', 0) or 0

                if hasattr(spv, '_quantize_enabled') and hasattr(da, '_quantize_enabled'):
                    da._quantize_enabled = spv._quantize_enabled

                # Refresh all visible pads on deck A (4 or 8 depending on current mode)
                if hasattr(da, '_rebuild_hotcue_pads'):
                    # safest: ask deck to refresh its current pad set
                    for i in range(min(8, len(getattr(da, 'hotcue_pads', [])))):
                        if hasattr(da, '_update_hotcue_pad'):
                            da._update_hotcue_pad(i)
                else:
                    for i in range(4):
                        if hasattr(da, '_update_hotcue_pad'):
                            da._update_hotcue_pad(i)

                # Loop (single view doesn't expose loop UI, so we only push if deck already had it)
                # Nothing to pull from single for loop here.

                # Pull live playhead from engine
                try:
                    if hasattr(da, 'waveform') and self.playback_engine:
                        st = self.playback_engine.get_deck_state("A")
                        if st:
                            da.waveform.set_playhead(st.position_ms)
                except Exception as exc:
                    logger.debug(f"Sync playhead single→console failed: {exc}")

                logger.debug("DJ sync: single→console (lightweight hotcue/main-cue copy)")

                # Guarantee waveform on deck A after switch back from single
                try:
                    if hasattr(da, "_load_waveform_async") and getattr(spv, "current_track", None):
                        dur = 0
                        if self.playback_engine:
                            st = self.playback_engine.get_deck_state("A")
                            if st and st.duration_ms:
                                dur = st.duration_ms
                        if dur <= 0:
                            dur = 180000
                        da._load_waveform_async(spv.current_track.path, dur)
                        bpm = getattr(spv, "_original_bpm", None) or getattr(spv, "current_track", None) and getattr(spv.current_track, "bpm", None)
                        if bpm:
                            da.waveform.set_bpm(bpm)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"_sync_deck_a_state_between_views failed: {e}")
            # Last resort – do not crash the mode switch

    def _apply_base_style(self):
        """Rich pro dark booth stylesheet — high contrast, larger controls, readable everywhere."""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {COLORS["bg"]};
                color: {COLORS["text"]};
                font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
                font-size: 13px;
            }}
            QLabel {{
                color: {COLORS["text"]};
            }}
            QPushButton {{
                background-color: #1a2233;
                border: 1px solid #2f3a52;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {COLORS["accent"]};
                background-color: #232d42;
            }}
            QPushButton:pressed {{
                background-color: #0f1623;
            }}
            QPushButton:checked {{
                background-color: {COLORS["accent"]};
                color: {COLORS["bg"]};
                border-color: {COLORS["accent"]};
                font-weight: 700;
            }}
            QComboBox {{
                background-color: #1a2233;
                border: 1px solid #2f3a52;
                border-radius: 4px;
                padding: 2px 6px;
                min-height: 20px;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: #1f2a40;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS["accent"]};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid #0a0e17;
            }}
            QSlider::groove:vertical {{
                width: 6px;
                background: #1f2a40;
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {COLORS["accent"]};
                height: 16px;
                width: 16px;
                margin: 0 -5px;
                border-radius: 8px;
                border: 2px solid #0a0e17;
            }}
            /* Crossfader extra weight */
            QSlider#crossfader, QSlider[objectName="crossfader"] {{
                min-height: 28px;
            }}
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-lumbago-track-paths") or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        paths = []

        if mime.hasFormat("application/x-lumbago-track-paths"):
            data = mime.data("application/x-lumbago-track-paths").data().decode()
            paths = [p for p in data.split(",") if p]
        elif mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())

        if paths:
            # Domyślnie ładujemy do Deck A
            self._load_dropped_track("A", paths[0])
            event.acceptProposedAction()

    def closeEvent(self, event):
        """Zwalniamy zasoby audio przy zamknięciu okna."""
        try:
            if hasattr(self, "playback_engine") and self.playback_engine:
                self.playback_engine.release_all()
        except Exception:
            pass
        if event is not None:
            event.accept()

    def load_track_to_deck(self, deck: str, track: Track):
        """Ładuje track do wybranego decku.
        Zaadaptowane pod nową architekturę: w przypadku Focused/ConsoleDeckView delegujemy do DeckController.load_track
        (widoki są "dumb" i nie mają metody load_track).
        Zachowane pełne zachowanie + recent + emit sygnału.
        """
        d = deck.upper()
        is_single_mode = getattr(self, '_current_mode', 'console') == 'single'

        # NOWA ARCHITEKTURA: używamy kontrolerów (jedno źródło prawdy)
        if True:  # new architecture sole impl (old removed)
            ctrl = self._deck_ctrl_a if d == "A" else self._deck_ctrl_b
            target_view = self.deck_a if d == "A" else self.deck_b
            if ctrl:
                try:
                    prev = getattr(ctrl, 'current_track', None)
                    ctrl.load_track(track)
                    self._push_recent(d, prev)
                except Exception as e:
                    logger.exception(f"load_track_to_deck (nowa arch, {d}) failed")
            # W trybie single zawsze synchronizuj Focused (używa tego samego ctrl_a)
            if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
                # FocusedDeckView nie ma load_track — controller już zaktualizował stan i wyemitował sygnały
                # Wystarczy lekkie odświeżenie referencji
                try:
                    if hasattr(self.single_player_view, "current_track"):
                        self.single_player_view.current_track = track
                except Exception:
                    pass
            if not is_single_mode and False:  # old arch removed
                QtCore.QTimer.singleShot(50, self._update_crossfader_volumes)
            try:
                self.deck_track_loaded.emit(d, track)
            except Exception as exc:
                logger.debug(f"deck_track_loaded emit failed: {exc}")
            return

        # === STARA ARCHITEKTURA (fallback) ===
        # Only touch physical dual decks when in console mode
        if not is_single_mode:
            if d == "A" and self.deck_a:
                try:
                    prev = getattr(self.deck_a, 'current_track', None)
                    self.deck_a.load_track(track)
                    self._push_recent("A", prev)
                except Exception as e:
                    logger.exception("load_track_to_deck A failed")
            elif d == "B" and self.deck_b:
                try:
                    prev = getattr(self.deck_b, 'current_track', None)
                    self.deck_b.load_track(track)
                    self._push_recent("B", prev)
                except Exception as e:
                    logger.exception("load_track_to_deck B failed")
        else:
            # In single mode we drive everything through single_player_view (which also drives engine deck A).
            if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    self.single_player_view.load_track(track)
                    if self.deck_a:
                        self.deck_a.current_track = track
                except Exception as e:
                    logger.warning(f"load_track_to_deck (single): {e}")
                return

        # Console mode or loading to B: keep SinglePlayerView in sync when loading to A
        if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
            try:
                self.single_player_view.load_track(track)
            except Exception as e:
                logger.warning(f"Failed to sync to single_player_view: {e}")

        if not is_single_mode and False:  # old arch removed
            QtCore.QTimer.singleShot(50, self._update_crossfader_volumes)

        try:
            self.deck_track_loaded.emit(d, track)
        except Exception as exc:
            logger.debug(f"deck_track_loaded emit failed (no listeners?): {exc}")

    def unload_deck(self, deck: str):
        d = deck.upper()
        # NOWA ARCHITEKTURA — delegacja do kontrolera (widoki nie mają unload_track)
        if True:  # new architecture sole impl (old removed)
            ctrl = self._deck_ctrl_a if d == "A" else self._deck_ctrl_b
            if ctrl:
                try:
                    ctrl.unload_track()
                except Exception:
                    pass
            self.deck_track_unloaded.emit(d)
            # Wyczyść alias single jeśli A
            if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    spv = self.single_player_view
                    if hasattr(spv, "title_label"): spv.title_label.setText("Brak utworu — upuść plik lub załaduj z biblioteki")
                    if hasattr(spv, "bpm_label"): spv.bpm_label.setText("— BPM")
                    if hasattr(spv, "waveform") and hasattr(spv.waveform, "clear"): spv.waveform.clear()
                    if hasattr(spv, "time_label"): spv.time_label.setText("0:00 / 0:00")
                    if hasattr(spv, "current_track"): spv.current_track = None
                    if hasattr(spv, "hotcue_grid") and hasattr(spv.hotcue_grid, "clear_all"):
                        spv.hotcue_grid.clear_all()
                except Exception:
                    pass
            return

        # STARA ARCHITEKTURA
        if d == "A" and self.deck_a:
            self.deck_a.unload_track()
            self.deck_track_unloaded.emit("A")
            if hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    self.single_player_view.title_label.setText("Brak utworu — upuść plik lub załaduj z biblioteki")
                    self.single_player_view.bpm_label.setText("— BPM")
                    self.single_player_view.waveform.clear()
                    self.single_player_view.time_label.setText("0:00 / 0:00")
                    self.single_player_view.play_btn.setText("▶  ODTWÓRZ")
                    self.single_player_view.current_track = None
                    if hasattr(self.single_player_view, "_hotcue_mgr"):
                        self.single_player_view._hotcue_mgr.clear_all()
                        if hasattr(self.single_player_view, "_sync_hotcues_alias"):
                            self.single_player_view._sync_hotcues_alias()
                    else:
                        self.single_player_view._hotcues.clear()
                    for p in self.single_player_view.hotcue_pads:
                        p._has_cue = False
                        p.set_cue_time(None)
                        p._update_style()
                except Exception:
                    pass
        elif self.deck_b:
            self.deck_b.unload_track()
            self.deck_track_unloaded.emit("B")

    def stop_all_decks(self):
        """Global stop for both decks + clear play states."""
        try:
            if self.playback_engine:
                self.playback_engine.stop_deck("A")
                self.playback_engine.stop_deck("B")
            if self.deck_a:
                self.deck_a.play_btn.setText("▶")
            if self.deck_b:
                self.deck_b.play_btn.setText("▶")
            if hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    self.single_player_view.play_btn.setText("▶  ODTWÓRZ")
                    self.single_player_view.waveform.set_playhead(0)
                except Exception:
                    pass
            self.all_stopped.emit()
            logger.info("DJ Player: Stop all decks")
        except Exception as e:
            logger.warning(f"stop_all_decks error: {e}")

    def unload_all(self):
        self.unload_deck("A")
        self.unload_deck("B")

    def _push_recent(self, deck: str, track: Optional[Track]):
        if not track or not getattr(track, 'path', None):
            return
        recents = self._recent_a if deck.upper() == "A" else self._recent_b
        # Avoid consecutive duplicates or current (path based)
        if recents and recents[0].path == track.path:
            return
        # Also avoid if it's the other deck's current? no, per deck ok
        recents.insert(0, track)
        # Trim + dedup by path keeping most recent
        seen = set()
        deduped = []
        for t in recents:
            if t.path not in seen:
                seen.add(t.path)
                deduped.append(t)
            if len(deduped) >= self._MAX_RECENT:
                break
        if deck.upper() == "A":
            self._recent_a = deduped
        else:
            self._recent_b = deduped

    def _populate_recent_menu(self, deck: str, menu: QtWidgets.QMenu):
        menu.clear()
        recents = self._recent_a if deck.upper() == "A" else self._recent_b
        if not recents:
            act = menu.addAction("(brak historii)")
            act.setEnabled(False)
            return
        for t in recents[:self._MAX_RECENT]:
            title = f"{t.artist or ''} - {t.title or ''}".strip(" -") or Path(t.path).stem
            display = (title[:38] + "…") if len(title) > 40 else title
            act = menu.addAction(display)
            # Capture track by value
            act.triggered.connect(lambda checked=False, tr=t, d=deck: self.load_track_to_deck(d, tr))

    def _load_dropped_track(self, deck: str, path: str):
        """Ładuje track upuszczony przez drag & drop (używa ścieżki)."""
        try:
            from pathlib import Path as PathLib
            name = PathLib(path).stem
            track = Track(path=path, title=name)
            # Enrich from DB if this file is in the library (to get id for hotcues)
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(path)
                if dbt and dbt.id:
                    track = dbt
            except Exception as exc:
                logger.debug(f"_load_dropped_track: DB lookup failed: {exc}")
            self.load_track_to_deck(deck, track)
        except Exception as e:
            logger.warning(f"Błąd ładowania upuszczonego tracka: {e}")

    def _global_play_pause(self):
        """Spacja = Play/Pause na Deck A (domyślny aktywny deck).
        Wspiera zarówno nową architekturę (DeckController) jak i stary DeckWidget.
        """
        # Nowa architektura — priorytet na kontroler
        if True and hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:  # new arch sole
            try:
                self._deck_ctrl_a.toggle_play()
                return
            except Exception:
                pass
        # Fallback stary
        if self.deck_a and hasattr(self.deck_a, "_toggle_play"):
            self.deck_a._toggle_play()

    def _quick_load_hotcue(self, index: int):
        """Ctrl+1..8 = jump to hotcue on Deck A.
        Pełne wsparcie 8 hotcue'ów. W nowej architekturze delegujemy do DeckController.jump_hotcue.
        """
        # Nowa architektura
        if True and hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:  # new arch sole
            try:
                self._deck_ctrl_a.jump_hotcue(index)
                return
            except Exception:
                pass
        # Fallback stary
        if self.deck_a and hasattr(self.deck_a, "_jump_to_hotcue"):
            self.deck_a._jump_to_hotcue(index)

    # ------------------------------------------------------------------
    # Mixer strip handlers (Master, HP Cue, PFL, Sync)
    # ------------------------------------------------------------------

    def _apply_initial_mixer_values(self):
        if not self.playback_engine:
            return
        # W nowej architekturze master_slider może nie istnieć (Dual ma własny) — defensywnie
        try:
            if hasattr(self, "master_slider") and self.master_slider:
                self.playback_engine.set_master_volume(self.master_slider.value() / 100.0)
            else:
                self.playback_engine.set_master_volume(0.85)
        except Exception:
            pass
        self._update_backend_info_label()

    def _on_master_changed(self, value: int):
        # Obsługa zarówno starego paska jak i global_mixer (MixerStrip)
        if hasattr(self, "master_value") and self.master_value:
            self.master_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try: self.global_mixer.set_master(value)
            except Exception: pass
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(value / 100.0)
            except Exception:
                pass

    def _on_hp_changed(self, value: int):
        if hasattr(self, "hp_value") and self.hp_value:
            self.hp_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try: self.global_mixer.set_hp(value)
            except Exception: pass
        # Na razie tylko UI — prawdziwy oddzielny output HP wymaga więcej

    def _on_pfl_changed(self, deck: str, checked: bool):
        # Wsparcie dla starego + MixerStrip
        style = "background-color: #3dd9c3; color: #0f1623; font-weight: bold;" if checked else ""
        btn = None
        if hasattr(self, "pfl_a") and deck == "A": btn = self.pfl_a
        elif hasattr(self, "pfl_b") and deck == "B": btn = self.pfl_b
        if btn:
            btn.setStyleSheet(style)
        # W nowej architekturze PFL może też iść do ConsoleDeckView (status)
        if True:  # new architecture sole impl (old removed)
            try:
                if deck == "A" and hasattr(self, "deck_a") and self.deck_a and hasattr(self.deck_a, "pfl_btn"):
                    self.deck_a.pfl_btn.setChecked(checked)
                elif deck == "B" and hasattr(self, "deck_b") and self.deck_b and hasattr(self.deck_b, "pfl_btn"):
                    self.deck_b.pfl_btn.setChecked(checked)
            except Exception:
                pass
        logger.debug(f"PFL {deck}: {'ON' if checked else 'OFF'}")

    def _on_global_crossfader(self, value: int):
        """Obsługa crossfadera z MixerStrip (gdy używany jako globalny)."""
        if self.playback_engine:
            try:
                pos = (value / 50.0) - 1.0
                self.playback_engine.set_crossfader(pos)
            except Exception:
                pass

    def _do_sync(self):
        """Global mixer SYNC (legacy path) — delegates basic tempo match.
        Prefer per-deck SYNC buttons for full tempo+phase+keylock+quantize experience.
        """
        if not self.playback_engine or not (self.deck_a and self.deck_b):
            return
        try:
            # Simple: make B follow A's current effective rate (non-BPM aware for brevity)
            state_a = self.playback_engine.get_deck_state("A")
            if state_a:
                self.playback_engine.set_deck_rate("B", state_a.rate)
                if hasattr(self.deck_b, 'pitch_slider'):
                    self.deck_b.pitch_slider.setValue(int(round((state_a.rate - 1.0) * 100)))
                self.sync_btn.setStyleSheet("background-color: #5cc8ff; color: black; font-weight: 700;")
                QtCore.QTimer.singleShot(900, lambda: self.sync_btn.setStyleSheet("") if hasattr(self, 'sync_btn') else None)
                logger.info("Global SYNC: Deck B rate matched to A (use deck buttons for pro sync)")
        except Exception as e:
            logger.warning(f"Global sync failed: {e}")

    def _update_backend_info_label(self):
        if not hasattr(self, "backend_info_label") or not self.playback_engine:
            return
        try:
            d = self.playback_engine.get_diagnostics()
            a = d.get("deck_a", {})
            b = d.get("deck_b", {})
            txt = f"{a.get('backend','?')} / {b.get('backend','?')}"
            self.backend_info_label.setText(txt)
        except Exception:
            pass

    def _dismiss_fallback_banner(self, banner):
        """Session-persistent dismiss for the fallback warning."""
        self._fallback_dismissed_this_session = True
        if banner:
            banner.setVisible(False)

    def _load_file_dialog(self, deck: str):
        """Open file dialog to load a track directly into a deck (standalone pro use)."""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Load track to Deck {deck}",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*)"
        )
        if path:
            self._load_dropped_track(deck, path)

    def _maybe_show_fallback_banner(self, main_layout: QtWidgets.QVBoxLayout):
        """Prominent warning when the professional DJ Player is running on degraded QtMultimedia fallback."""
        if getattr(self, "_fallback_dismissed_this_session", False):
            return
        if not self.playback_engine:
            return
        try:
            d = self.playback_engine.get_diagnostics()
            using_qt = False
            for key in ("deck_a", "deck_b"):
                if d.get(key, {}).get("backend") == "qtmultimedia":
                    using_qt = True
                    break
            if not using_qt:
                return

            banner = QtWidgets.QFrame()
            banner.setStyleSheet(f"""
                QFrame {{
                    background-color: #3a2f1f;
                    border: 1px solid #854d0e;
                    border-radius: 4px;
                    margin: 2px 0;
                }}
                QLabel {{
                    color: {COLORS['warning']};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 10px;
                }}
            """)
            bl = QtWidgets.QHBoxLayout(banner)
            bl.setContentsMargins(6, 2, 6, 2)
            bl.setSpacing(6)

            lbl = QtWidgets.QLabel(
                "⚠ FALLBACK MODE: QtMultimedia (no real EQ, keylock, or low-jitter loops). Install VLC from videolan.org/vlc for full professional DJ features."
            )
            lbl.setWordWrap(False)
            bl.addWidget(lbl, 1)

            close_btn = QtWidgets.QPushButton("×")
            close_btn.setFixedSize(18, 18)
            close_btn.setStyleSheet("font-size: 13px; font-weight: bold; color: #facc15; border: none; background: transparent;")
            close_btn.clicked.connect(lambda: self._dismiss_fallback_banner(banner))
            bl.addWidget(close_btn)

            main_layout.addWidget(banner)
            self._fallback_banner = banner  # keep reference for session dismiss
            if hasattr(self, "_console_widgets"):
                self._console_widgets.append(banner)
        except Exception:
            pass
