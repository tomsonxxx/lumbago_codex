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
# ------------------------------------------------------------------
from ui.dj.hotcue_manager import HotcueManager, format_track_time

# (HotcueManager + persystencja wyłącznie w ui/dj/hotcue_manager.py)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# REFACTOR (Opcja A cleanup): format_track_time + HotcueManager w osobnym module.
# Sole new architecture: ui/dj/ (DeckController + FocusedDeckView/ConsoleDeckView/DualConsoleWidget).
# WaveformWidget remains here (imported lazily by views) + uses BOOTH_COLORS.
# ------------------------------------------------------------------

# Note: extract_peaks (and its internal _generate_fallback) now lives in core/waveform.py
# for reuse by library detail panel (eliminates ffmpeg dependency for small previews).
# Thin wrapper for WaveformWidget (now used by new views in ui/dj).
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


# Pro DJ booth high-contrast dark theme – teraz alias do centralnej palety BOOTH_COLORS (Rekordbox polish)
# Zachowany dla kompatybilności z WaveformWidget (który jest w tym pliku).
# Używaj ui.dj.styles.BOOTH_COLORS w nowych widokach!
from ui.dj.styles import BOOTH_COLORS
# No legacy aliases left. New booth styles in ui/dj/styles.py.
COLORS = {
    **BOOTH_COLORS,
    "text": BOOTH_COLORS.get("text_primary", "#f0f4f8"),
    "panel": BOOTH_COLORS.get("surface", "#12171f"),
    "panel_border": BOOTH_COLORS.get("border", "#2a3442"),
    "section_label": BOOTH_COLORS.get("text_muted", "#6b7688"),
    "hotcue_active": "#ffffff",
    "accent_green": BOOTH_COLORS.get("play", "#22c55e"),
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

        # Waveform (classic + gain feel + energy tint for Rekordbox-style colored waveform by intensity)
        energy_tint = QtGui.QColor(COLORS.get("accent_orange", "#ff8a00"))  # high energy sections (from booth palette)
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

            # Energy coloring overlay (pro polish: intense parts get orange tint)
            if amp > 0.65:
                energy_pen = QtGui.QPen(energy_tint, 1)
                energy_pen.setAlphaF(0.3 + (amp - 0.65) * 1.0)
                painter.setPen(energy_pen)
                painter.drawLine(px, mid - int(ph * 0.65), px, mid - rh)
                painter.drawLine(px, mid + rh, px, mid + int(ph * 0.65))

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


# (stary HotcuePad usunięty – wyłącznie w ui/dj/views/hotcue_pad.py z 8 kolorami z BOOTH)

# === OLD DECKWIDGET + SINGLEPLAYERVIEW REMOVED (Opcja A complete: sole impl via ui/dj/* + DeckController + DualConsoleWidget) ===

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
                logger.info("Nowa architektura sole (redesign complete)")
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
        # W sole new arch: DualConsoleWidget ma własny mikser (cross/master/cue) wewnątrz.
        # Opcjonalny globalny MixerStrip na górze (dla PFL, master — cross jest w Dual) dla stand-alone wygody.
        if MixerStrip is not None:
            try:
                self.global_mixer = MixerStrip(self)
                self.global_mixer.master_changed.connect(self._on_master_changed)
                self.global_mixer.hp_changed.connect(self._on_hp_changed)
                self.global_mixer.crossfader_changed.connect(self._on_global_crossfader)
                self.global_mixer.pfl_changed.connect(self._on_pfl_changed)
                main_layout.addWidget(self.global_mixer)
                if hasattr(self, "_console_widgets"):
                    self._console_widgets.append(self.global_mixer)
                QtCore.QTimer.singleShot(0, self._apply_initial_mixer_values)
            except Exception:
                logger.debug("MixerStrip nie podłączony (DualConsole ma własny)")
                self.global_mixer = None

        # === KOMPAKTOWY PASEK NARZĘDZI (Recent + Load + STOP ALL + backend) dla stand-alone pro use ===
        # Zachowane po usunięciu starego _build_mixer_strip w Opcja A. Działa dla obu trybów.
        try:
            tools = QtWidgets.QHBoxLayout()
            tools.setContentsMargins(4, 2, 4, 2)
            tools.setSpacing(6)

            # Recent
            self.recent_menu_a = QtWidgets.QMenu(self)
            self.recent_menu_b = QtWidgets.QMenu(self)
            self.recent_btn_a = QtWidgets.QToolButton()
            self.recent_btn_a.setText("Recent A ▾")
            self.recent_btn_a.setMenu(self.recent_menu_a)
            self.recent_btn_a.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            self.recent_btn_a.setFixedHeight(22)
            self.recent_btn_a.setStyleSheet("font-size: 9px; padding: 0 6px;")
            tools.addWidget(self.recent_btn_a)

            self.recent_btn_b = QtWidgets.QToolButton()
            self.recent_btn_b.setText("Recent B ▾")
            self.recent_btn_b.setMenu(self.recent_menu_b)
            self.recent_btn_b.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            self.recent_btn_b.setFixedHeight(22)
            self.recent_btn_b.setStyleSheet("font-size: 9px; padding: 0 6px;")
            tools.addWidget(self.recent_btn_b)

            self.recent_menu_a.aboutToShow.connect(lambda: self._populate_recent_menu("A", self.recent_menu_a))
            self.recent_menu_b.aboutToShow.connect(lambda: self._populate_recent_menu("B", self.recent_menu_b))

            tools.addSpacing(8)

            # Load dialogs
            load_a = QtWidgets.QPushButton("Load A…")
            load_b = QtWidgets.QPushButton("Load B…")
            load_a.setFixedWidth(64)
            load_b.setFixedWidth(64)
            load_a.setStyleSheet("font-size: 9px;")
            load_b.setStyleSheet("font-size: 9px;")
            load_a.clicked.connect(lambda: self._load_file_dialog("A"))
            load_b.clicked.connect(lambda: self._load_file_dialog("B"))
            tools.addWidget(load_a)
            tools.addWidget(load_b)

            tools.addSpacing(8)

            # Global controls
            stop_all_btn = QtWidgets.QPushButton("■ STOP ALL")
            stop_all_btn.setFixedWidth(72)
            stop_all_btn.setStyleSheet("font-size: 9px; font-weight: 700; color: #ff6b6b;")
            stop_all_btn.clicked.connect(self.stop_all_decks)
            tools.addWidget(stop_all_btn)

            unload_all_btn = QtWidgets.QPushButton("Unload All")
            unload_all_btn.setFixedWidth(68)
            unload_all_btn.setStyleSheet("font-size: 9px;")
            unload_all_btn.clicked.connect(self.unload_all)
            tools.addWidget(unload_all_btn)

            tools.addStretch(1)

            # Backend info
            self.backend_info_label = QtWidgets.QLabel("")
            self.backend_info_label.setStyleSheet(f"color: {COLORS.get('text_muted', '#6b7688')}; font-size: 9px;")
            tools.addWidget(self.backend_info_label)

            tools_w = QtWidgets.QWidget()
            tools_w.setLayout(tools)
            main_layout.addWidget(tools_w)
            if hasattr(self, "_console_widgets"):
                self._console_widgets.append(tools_w)
            QtCore.QTimer.singleShot(120, self._update_backend_info_label)
        except Exception:
            logger.debug("Tools bar (recent/load/stop) nie utworzony")

        # Fallback banner (clear but non-annoying) when QtMultimedia is active
        self._maybe_show_fallback_banner(main_layout)

        # UWAGA: W sole new architecture (DualConsoleWidget + ConsoleDeckView) crossfader jest wewnętrzny w widoku dual.
        # Stary crossfader block (poza Dual) usunięty w Opcja A cleanup.

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

        # Pokazujemy czytelny status backendu na deckach (VLC / Qt / Brak) — defensywnie
        if hasattr(self, '_update_backend_info_label'):
            QtCore.QTimer.singleShot(80, self._update_backend_info_label)

        # ========== CREATE FOCUSED SINGLE VIEW (sole new arch) ==========
        try:
            # Helper już mógł stworzyć single_container — użyj go lub utwórz (z _create_dual_console_ui)
            if not hasattr(self, "single_container") or self.single_container is None:
                focused = self._create_focused_single_ui(main_layout)
                if focused:
                    self.single_player_view = focused
            else:
                # single_container już istnieje z dual creation — NIE wstawiaj ponownie (już w layout)
                self.single_player_view = getattr(self, "single_container", None)
                if self.single_player_view:
                    self.single_player_view.setVisible(False)
            if self.single_player_view:
                self.single_player_view.setVisible(False)
            if not hasattr(self, "_console_widgets"):
                self._console_widgets = []
        except Exception as e:
            logger.warning(f"Failed to create focused single view: {e}")
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
        # Dodatkowe pro shortcuts (Rekordbox feel)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self._toggle_quantize_a)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self._do_sync_a_b)  # quick sync A to B

    def _toggle_section(self, section: str, visible: bool):
        # Nowa architektura sole impl: views manage their own sections internally (no-op here for compat)
        pass

    def _toggle_beatgrid(self, visible: bool):
        # Sole new architecture: waveformy wewnątrz ConsoleDeckView / FocusedDeckView
        for deck_id in ("A", "B"):
            try:
                if hasattr(self, "dual_console") and self.dual_console:
                    v = self.dual_console.get_deck_view(deck_id) if hasattr(self.dual_console, "get_deck_view") else None
                    if v and hasattr(v, "waveform") and hasattr(v.waveform, "set_beatgrid_visible"):
                        v.waveform.set_beatgrid_visible(visible)
            except Exception:
                pass
        try:
            if hasattr(self, "single_container") and self.single_container:
                if hasattr(self.single_container, "waveform") and hasattr(self.single_container.waveform, "set_beatgrid_visible"):
                    self.single_container.waveform.set_beatgrid_visible(visible)
        except Exception:
            pass
        # Single view alias (FocusedDeckView)
        spv = getattr(self, "single_player_view", None)
        if spv and hasattr(spv, "waveform") and hasattr(spv.waveform, "set_beatgrid_visible"):
            try:
                spv.waveform.set_beatgrid_visible(visible)
            except Exception:
                pass
        if hasattr(self, "btn_beatgrid"):
            self.btn_beatgrid.setText("Beatgrid ✓" if visible else "Beatgrid")

    # _build_mixer_strip i _update_crossfader_volumes usunięte w Opcja A (sole new architecture).
    # Funkcjonalność recent/load/stopall zachowana w kompaktowym pasku narzędzi (dodany poniżej po global_mixer).
    # Crossfader/master/cue/PFL obsługiwane wewnątrz DualConsoleWidget + MixerStrip.

    def _toggle_layout(self):
        """W sole new architecture (DualConsoleWidget) układy side-by-side są wewnątrz Dual (QSplitter).
        Ten toggle jest no-op dla nowego redesignu (Rekordbox-style). Przycisk zachowany dla kompatybilności UI."""
        # W trybie single lub dual: splitter wewnątrz DualConsoleWidget lub Focused zarządza rozmiarem.
        # Nie reparentujemy już decków bezpośrednio (były w starej architekturze).
        if hasattr(self, "btn_layout"):
            self.btn_layout.setText("Układ: Side-by-side (nowy)")
        logger.debug("_toggle_layout: no-op under sole new DJ architecture (use splitter in DualConsoleWidget)")

    # ------------------------------------------------------------------
    # HELPERY DLA NOWEJ ARCHITEKTURY (integracja wiring)
    # Tworzenie kontrolerów + widoków w stylu "dumb view + smart controller"
    # Zachowujemy pełne zachowanie, polski w komentarzach.
    # ------------------------------------------------------------------

    def _create_deck_controllers(self):
        """Tworzy parę DeckController (A/B) podłączoną do PlaybackEngine. Sole new architecture."""
        if DeckController is None or not hasattr(self, "playback_engine"):
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
        """Buduje DualConsoleWidget jako sole impl nowej architektury."""
        try:
            ctrl_a, ctrl_b = self._create_deck_controllers()
            if not ctrl_a or not ctrl_b:
                return None
            self._deck_ctrl_a = ctrl_a
            self._deck_ctrl_b = ctrl_b

            dual = DualConsoleWidget(ctrl_a, ctrl_b, self.playback_engine, self)
            main_layout.addWidget(dual)
            self._console_widgets.extend([dual])

            self.deck_a = dual.get_deck_view("A") if hasattr(dual, "get_deck_view") else None
            self.deck_b = dual.get_deck_view("B") if hasattr(dual, "get_deck_view") else None

            if FocusedDeckView is not None:
                self.single_container = FocusedDeckView(ctrl_a, self)
                self.single_container.setVisible(False)
                main_layout.addWidget(self.single_container)
            else:
                self.single_container = None

            logger.info("NEW ARCHITECTURE ACTIVE: DualConsoleWidget + 2x ConsoleDeckView + DeckController A/B + FocusedDeckView")
            return dual
        except Exception as exc:
            logger.exception(f"Błąd _create_dual_console_ui: {exc}")
            return None

    def _create_focused_single_ui(self, main_layout: QtWidgets.QVBoxLayout):
        """Tworzy FocusedDeckView jako sole single view (tryb 'Odtwarzacz')."""
        try:
            if not hasattr(self, "_deck_ctrl_a") or self._deck_ctrl_a is None:
                ctrl_a, _ = self._create_deck_controllers()
                self._deck_ctrl_a = ctrl_a
                self._deck_ctrl_b = None

            if self._deck_ctrl_a is None:
                return None

            focused = FocusedDeckView(self._deck_ctrl_a, self)
            main_layout.insertWidget(1, focused)
            focused.setVisible(False)
            self.single_container = focused
            self.single_player_view = focused
            logger.info("NEW ARCHITECTURE ACTIVE: FocusedDeckView (tryb single) + DeckController")
            return focused
        except Exception as exc:
            logger.exception(f"Błąd _create_focused_single_ui: {exc}")
            return None

    # ------------------------------------------------------------------
    # Player mode switching (Odtwarzacz vs Konsola DJ)
    # ------------------------------------------------------------------

    def _switch_player_mode(self, mode_id: int):
        """Switch between clean single-deck view and full dual console.
        Sole new architecture (Focused + DualConsole + DeckController).
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

        # Sole new: przełączanie kontenerów (DualConsole vs FocusedDeckView)
        if hasattr(self, "single_container") and self.single_container:
            self.single_container.setVisible(is_single)
        if hasattr(self, "dual_console") and self.dual_console:
            self.dual_console.setVisible(not is_single)
        # deck_a/b to widoki z Dual (ukryte razem z kontenerem)

        # Aggressively hide/show console content (działa dla obu architektur)
        for w in getattr(self, "_console_widgets", []):
            if w:
                try:
                    w.setVisible(not is_single)
                except Exception:
                    pass

        # (cross_frame z starej arch usunięty w Opcja A; dual ma własny cross)

        # Sync w nowej architekturze (sole): obsługiwany przez sygnały DeckController + widoki (zero duplikacji).
        if is_single:
            try:
                if self.playback_engine and hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
                    state = self.playback_engine.get_deck_state("A")
                    if state and hasattr(self.single_container, "waveform"):
                        self.single_container.waveform.set_playhead(state.position_ms)
            except Exception:
                pass

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
        """Ładuje track do wybranego decku (sole new arch: DeckController + views).
        Deleguje do DeckController.load_track (widoki są dumb). Zachowane recent + emit.
        """
        d = deck.upper()
        is_single_mode = getattr(self, '_current_mode', 'console') == 'single'

        ctrl = self._deck_ctrl_a if d == "A" else self._deck_ctrl_b
        if ctrl:
            try:
                prev = getattr(ctrl, 'current_track', None)
                ctrl.load_track(track)
                self._push_recent(d, prev)
            except Exception as e:
                logger.exception(f"load_track_to_deck (nowa arch, {d}) failed")
        # W trybie single synchronizuj Focused (używa tego samego ctrl_a)
        if d == "A" and hasattr(self, "single_player_view") and self.single_player_view:
            try:
                if hasattr(self.single_player_view, "current_track"):
                    self.single_player_view.current_track = track
            except Exception:
                pass
        try:
            self.deck_track_loaded.emit(d, track)
        except Exception as exc:
            logger.debug(f"deck_track_loaded emit failed: {exc}")

    def unload_deck(self, deck: str):
        d = deck.upper()
        # Sole new: delegacja do kontrolera (widoki nie mają unload_track)
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

    def stop_all_decks(self):
        """Global stop for both decks + clear play states (sole new arch)."""
        try:
            if self.playback_engine:
                self.playback_engine.stop_deck("A")
                self.playback_engine.stop_deck("B")
            # Let signals from controllers/views update transport buttons (ConsoleDeckView/Focused use .transport.set_playing)
            # Direct play_btn access removed (old DeckWidget style); use transport if present for immediate feedback.
            for deck_view in (getattr(self, 'deck_a', None), getattr(self, 'deck_b', None)):
                if deck_view:
                    try:
                        if hasattr(deck_view, 'transport') and hasattr(deck_view.transport, 'set_playing'):
                            deck_view.transport.set_playing(False)
                        elif hasattr(deck_view, 'play_btn'):
                            deck_view.play_btn.setText("▶")
                    except Exception:
                        pass
            if hasattr(self, "single_player_view") and self.single_player_view:
                try:
                    spv = self.single_player_view
                    if hasattr(spv, 'transport') and hasattr(spv.transport, 'set_playing'):
                        spv.transport.set_playing(False)
                    elif hasattr(spv, 'play_btn'):
                        spv.play_btn.setText("▶  ODTWÓRZ")
                    if hasattr(spv, "waveform") and hasattr(spv.waveform, "set_playhead"):
                        spv.waveform.set_playhead(0)
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
        """Spacja = Play/Pause na Deck A (domyślny aktywny deck). Sole new (DeckController)."""
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            try:
                self._deck_ctrl_a.toggle_play()
                return
            except Exception:
                pass

    def _quick_load_hotcue(self, index: int):
        """Ctrl+1..8 = jump to hotcue on Deck A. Sole new arch."""
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            try:
                self._deck_ctrl_a.jump_hotcue(index)
                return
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Mixer strip handlers (Master, HP Cue, PFL, Sync)
    # ------------------------------------------------------------------

    def _apply_initial_mixer_values(self):
        if not self.playback_engine:
            return
        # master_slider może być w global_mixer lub wewnątrz Dual (defensywnie)
        try:
            if hasattr(self, "master_slider") and self.master_slider:
                self.playback_engine.set_master_volume(self.master_slider.value() / 100.0)
            else:
                self.playback_engine.set_master_volume(0.85)
        except Exception:
            pass
        self._update_backend_info_label()

    def _on_master_changed(self, value: int):
        # Obsługa global_mixer (MixerStrip) + ew. stary master_value (jeśli obecny)
        if hasattr(self, "master_value") and self.master_value:
            self.master_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try:
                self.global_mixer.set_master(value)
            except Exception:
                pass
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(value / 100.0)
            except Exception:
                pass

    def _on_hp_changed(self, value: int):
        if hasattr(self, "hp_value") and self.hp_value:
            self.hp_value.setText(str(value))
        if hasattr(self, "global_mixer") and self.global_mixer:
            try:
                self.global_mixer.set_hp(value)
            except Exception:
                pass
        # Na razie tylko UI — prawdziwy oddzielny output HP (w silniku) wymaga więcej

    def _on_pfl_changed(self, deck: str, checked: bool):
        # Obsługa global_mixer (MixerStrip) + delegacja do deck views jeśli mają pfl_btn (dla statusu)
        style = "background-color: #3dd9c3; color: #0f1623; font-weight: bold;" if checked else ""
        btn = None
        if hasattr(self, "pfl_a") and deck == "A": btn = self.pfl_a
        elif hasattr(self, "pfl_b") and deck == "B": btn = self.pfl_b
        if btn:
            btn.setStyleSheet(style)
        # New arch: deck views (Console/Focused) mogą mieć wewnętrzny PFL toggle podłączony do controller/engine
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
        Prefer per-deck SYNC buttons (in ConsoleDeckView) for full pro experience (DeckController.do_sync).
        """
        if not self.playback_engine or not (getattr(self, 'deck_a', None) and getattr(self, 'deck_b', None)):
            return
        try:
            state_a = self.playback_engine.get_deck_state("A")
            if state_a:
                self.playback_engine.set_deck_rate("B", state_a.rate)
                # New arch: PitchControl inside views listens to controller; avoid direct slider poke
                # Visual feedback only on the global sync_btn if present (rare now)
                if hasattr(self, 'sync_btn') and self.sync_btn:
                    self.sync_btn.setStyleSheet("background-color: #5cc8ff; color: black; font-weight: 700;")
                    QtCore.QTimer.singleShot(900, lambda: self.sync_btn.setStyleSheet("") if hasattr(self, 'sync_btn') else None)
                logger.info("Global SYNC: Deck B rate matched to A (use deck SYNC for phase+key+quantize)")
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

    # ------------------------------------------------------------------
    # Dodatkowe skróty klawiszowe (UI polish – integracja z pro workflow)
    # ------------------------------------------------------------------
    def _toggle_quantize_a(self):
        if hasattr(self, "_deck_ctrl_a") and self._deck_ctrl_a:
            self._deck_ctrl_a.toggle_quantize()

    def _do_sync_a_b(self):
        if hasattr(self, "_deck_ctrl_a") and hasattr(self, "_deck_ctrl_b") and self._deck_ctrl_a and self._deck_ctrl_b:
            self._deck_ctrl_a.do_sync(self._deck_ctrl_b)
            self._deck_ctrl_a.status_changed.emit("SYNC A->B (Ctrl+S)")
