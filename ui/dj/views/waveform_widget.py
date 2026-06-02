from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets
from pathlib import Path
from typing import Optional
import logging

from ui.dj.styles import BOOTH_COLORS

logger = logging.getLogger(__name__)


class WaveformWidget(QtWidgets.QWidget):
    """
    Professional DJ waveform with:
    - Real peaks (from core.waveform via controller runnable)
    - BPM-aware musical beatgrid (bars + beats when BPM known)
    - High-visibility playhead with multi-layer glow
    - Loop region highlight
    - Seek (click) + Shift+click cue request + Double-click (set main CUE + seek)
    - time_at_x(x) helper for precise context menus / external use

    Extracted from ui/dj_player_window.py into clean reusable module (ui/dj/views/).
    All original paint, beatgrid, interaction, token-stale protection, clear, set_*
    functionality preserved exactly.

    Used by OdtwarzaczView (MVP single) + Focused/Console (dual).
    Colors: ui/dj/styles.BOOTH_COLORS.
    """
    seek_requested = QtCore.pyqtSignal(int)
    cue_set_requested = QtCore.pyqtSignal(int)   # Shift + click
    double_clicked = QtCore.pyqtSignal(int)      # Double-click: pro "set main cue + preview jump"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(162)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip(
            "Waveform: Click=seek • Shift+Click=set hotcue • "
            "Double-click=set main CUE")

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

        # Colors (pro booth) — now from central palette
        c = BOOTH_COLORS
        self._col_bg = QtGui.QColor(c["wave_bg"])
        self._col_peak = QtGui.QColor(c["wave_peak"])
        self._col_rms = QtGui.QColor(c["wave_rms"])
        self._col_playhead = QtGui.QColor(c["playhead"])
        self._col_beat = QtGui.QColor(255, 255, 255, 70)       # regular beat
        self._col_bar = QtGui.QColor(255, 255, 255, 140)       # every 4th (bar)
        self._col_beatgrid = QtGui.QColor(255, 255, 255, 55)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @QtCore.pyqtSlot(list, int, str)
    def load_waveform(self, peaks: list[float] | None, duration_ms: int, token: str = ""):
        """Load real waveform peaks (thread-safe via QThreadPool).
        Ignores stale token deliveries (prevents showing waveform for unloaded track).
        """
        if token and self._current_token is not None and token != self._current_token:
            return
        self._peaks = peaks or []
        self._duration_ms = max(0, duration_ms)
        self._playhead_ms = 0
        self._loading = False
        self.update()

    def set_expected_waveform_token(self, token: Optional[str]) -> None:
        """Called by view before async waveform load.
        Later load_waveform must match token or dropped (stale guard).
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

        # Waveform + energy tint (Rekordbox-style by intensity)
        c = BOOTH_COLORS
        energy_tint = QtGui.QColor(c.get("accent_orange", "#ff8a00"))
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

            # Energy overlay (intense parts get orange tint)
            if amp > 0.65:
                energy_pen = QtGui.QPen(energy_tint, 1)
                energy_pen.setAlphaF(0.3 + (amp - 0.65) * 1.0)
                painter.setPen(energy_pen)
                painter.drawLine(px, mid - int(ph * 0.65), px, mid - rh)
                painter.drawLine(px, mid + rh, px, mid + int(ph * 0.65))

        # Loop region (more visible)
        if (self._loop_start_ms >= 0 and
                self._loop_end_ms > self._loop_start_ms and
                self._duration_ms > 0):
            x1 = int(self._loop_start_ms / self._duration_ms * w)
            x2 = int(self._loop_end_ms / self._duration_ms * w)
            painter.fillRect(x1, 0, max(1, x2 - x1), h,
                             QtGui.QColor(96, 165, 250, 48))

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
        c = BOOTH_COLORS
        for offset, alpha in ((3, 18), (2, 35), (1, 70)):
            glow = QtGui.QColor(c["playhead_glow"])
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
        """Double-click = set main cue + seek (pro preview).
        Respects quantize if parent provides via consumer.
        """
        if self._duration_ms <= 0:
            return
        t = int(event.position().x() / self.width() * self._duration_ms)
        t = max(0, min(t, self._duration_ms))
        self.double_clicked.emit(t)
        # immediate seek for responsiveness
        self.seek_requested.emit(t)

    def mouseMoveEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def time_at_x(self, x: int) -> int:
        """Zwraca czas w ms dla pozycji x na waveformie."""
        if self._duration_ms <= 0 or self.width() <= 0:
            return 0
        t = int(x / self.width() * self._duration_ms)
        return max(0, min(t, self._duration_ms))
