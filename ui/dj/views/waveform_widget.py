from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Optional
import logging

from ui.dj.styles import BOOTH_COLORS

logger = logging.getLogger(__name__)


class WaveformWidget(QtWidgets.QWidget):
    """
    Waveforma DJ w stylu Rekordbox 7: symetryczna RGB(W), beatgrid, playhead, marker CUE.
    """

    seek_requested = QtCore.pyqtSignal(int)
    cue_set_requested = QtCore.pyqtSignal(int)
    double_clicked = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setMouseTracking(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip(
            "Waveform RGB (Rekordbox 7): czerwień=bas, zieleń=środek, błękit=góra. "
            "Klik=seek • Double-klik=ustaw CUE • Pomarańczowa linia=punkt CUE"
        )

        self._peaks: list[float] = []
        self._bands_low: list[float] = []
        self._bands_mid: list[float] = []
        self._bands_high: list[float] = []
        self._duration_ms: int = 0
        self._playhead_ms: int = 0
        self._cue_ms: int = 0
        self._show_beatgrid: bool = True
        self._bpm: float | None = None
        self._loading: bool = False
        self._current_token: Optional[str] = None

        self._loop_start_ms: int = -1
        self._loop_end_ms: int = -1

        c = BOOTH_COLORS
        self._col_bg = QtGui.QColor(c["wave_bg"])
        self._col_center = QtGui.QColor(c.get("wave_center", "#0e1218"))
        self._col_low = QtGui.QColor(c.get("wave_low", "#ff3b3b"))
        self._col_mid = QtGui.QColor(c.get("wave_mid", "#3dcc3d"))
        self._col_high = QtGui.QColor(c.get("wave_high", "#3d8bff"))
        self._col_white = QtGui.QColor(c.get("wave_white", "#f0f2f8"))
        self._col_cue = QtGui.QColor(c.get("wave_cue", "#ff9500"))
        self._col_playhead = QtGui.QColor(c["playhead"])
        self._col_beat = QtGui.QColor(255, 255, 255, 38)
        self._col_bar = QtGui.QColor(255, 255, 255, 88)
        self._col_beatgrid = QtGui.QColor(255, 255, 255, 28)

    @QtCore.pyqtSlot(list, int, str)
    def load_waveform(
        self,
        peaks: list[float] | None,
        duration_ms: int,
        token: str = "",
        rgb_bands: dict[str, list[float]] | None = None,
    ):
        if token and self._current_token is not None and token != self._current_token:
            return
        self._peaks = peaks or []
        if rgb_bands:
            self._bands_low = list(rgb_bands.get("low") or self._peaks)
            self._bands_mid = list(rgb_bands.get("mid") or self._peaks)
            self._bands_high = list(rgb_bands.get("high") or self._peaks)
            if rgb_bands.get("peak"):
                self._peaks = list(rgb_bands["peak"])
        else:
            self._bands_low = list(self._peaks)
            self._bands_mid = list(self._peaks)
            self._bands_high = list(self._peaks)
        self._duration_ms = max(0, duration_ms)
        self._playhead_ms = 0
        self._loading = False
        self.update()

    def set_expected_waveform_token(self, token: Optional[str]) -> None:
        self._current_token = token

    def set_playhead(self, time_ms: int):
        if time_ms != self._playhead_ms:
            self._playhead_ms = max(0, min(time_ms, self._duration_ms))
            self.update()

    def set_main_cue_ms(self, cue_ms: int) -> None:
        cue_ms = max(0, int(cue_ms))
        if cue_ms != self._cue_ms:
            self._cue_ms = cue_ms
            self.update()

    def set_beatgrid_visible(self, visible: bool):
        if self._show_beatgrid != visible:
            self._show_beatgrid = visible
            self.update()

    def set_bpm(self, bpm: float | None):
        if bpm and bpm > 20:
            self._bpm = float(bpm)
        else:
            self._bpm = None
        if self._show_beatgrid:
            self.update()

    def set_duration(self, duration_ms: int):
        self._duration_ms = max(0, duration_ms)
        self.update()

    def clear(self):
        self._peaks = []
        self._bands_low = []
        self._bands_mid = []
        self._bands_high = []
        self._duration_ms = 0
        self._playhead_ms = 0
        self._cue_ms = 0
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

    def _sample_at(self, data: list[float], px: int, width: int) -> float:
        if not data:
            return 0.0
        n = len(data)
        idx = int(px / max(1, width) * n)
        if idx >= n:
            idx = n - 1
        return max(0.0, min(1.0, data[idx]))

    def _rgb_for_sample(self, lo: float, mid: float, hi: float, peak: float) -> QtGui.QColor:
        """Mieszanka addytywna RB7: każde pasmo wnosi swój kolor, szczyty → biel."""
        if peak < 0.02:
            return QtGui.QColor(self._col_center)

        brightness = 0.42 + (peak ** 0.82) * 1.05
        r = min(255, int((lo * self._col_low.red() + mid * self._col_mid.red() * 0.35
                          + hi * self._col_high.red() * 0.2) * brightness))
        g = min(255, int((lo * self._col_low.green() * 0.25 + mid * self._col_mid.green()
                          + hi * self._col_high.green() * 0.3) * brightness))
        b = min(255, int((lo * self._col_low.blue() * 0.15 + mid * self._col_mid.blue() * 0.2
                          + hi * self._col_high.blue()) * brightness))

        if peak > 0.58:
            mix = min(1.0, (peak - 0.58) * 2.2)
            w = self._col_white
            r = int(r * (1 - mix) + w.red() * mix)
            g = int(g * (1 - mix) + w.green() * mix)
            b = int(b * (1 - mix) + w.blue() * mix)

        alpha = 200 + int(min(55, peak * 70))
        return QtGui.QColor(r, g, b, alpha)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        mid_y = h // 2

        painter.fillRect(0, 0, w, h, self._col_bg)

        has_data = bool(self._peaks) and self._duration_ms > 0
        if has_data:
            max_h = int(mid_y * 0.90)
            bar_w = 2 if w > 520 else 1
            step = bar_w

            for px in range(0, w, step):
                lo = self._sample_at(self._bands_low, px, w)
                md = self._sample_at(self._bands_mid, px, w)
                hi = self._sample_at(self._bands_high, px, w)
                pk = self._sample_at(self._peaks, px, w)
                bar_h = max(1, int(pk * max_h))
                color = self._rgb_for_sample(lo, md, hi, pk)
                painter.fillRect(px, mid_y - bar_h, bar_w, bar_h, color)
                painter.fillRect(px, mid_y + 1, bar_w, bar_h, color)

            # Cienka linia środka (szczelina RB między połówkami)
            painter.setPen(QtGui.QPen(self._col_center, 1))
            painter.drawLine(0, mid_y, w, mid_y)

            if self._loop_start_ms >= 0 and self._loop_end_ms > self._loop_start_ms:
                x1 = int(self._loop_start_ms / self._duration_ms * w)
                x2 = int(self._loop_end_ms / self._duration_ms * w)
                painter.fillRect(x1, 0, max(1, x2 - x1), h, QtGui.QColor(61, 140, 255, 32))

            if self._show_beatgrid:
                self._draw_musical_beatgrid(painter, w, h)

            self._draw_cue_marker(painter, w, h)
        else:
            painter.setPen(QtGui.QPen(self._col_center, 1))
            painter.drawLine(0, mid_y, w, mid_y)

        self._draw_playhead(painter, w, h)
        painter.end()

    def _draw_cue_marker(self, painter: QtGui.QPainter, w: int, h: int) -> None:
        if self._duration_ms <= 0 or self._cue_ms <= 0:
            return
        px = int(self._cue_ms / self._duration_ms * w)
        if px <= 0 or px >= w:
            return
        glow = QtGui.QColor(self._col_cue)
        glow.setAlpha(48)
        painter.fillRect(max(0, px - 1), 0, 3, h, glow)
        painter.setPen(QtGui.QPen(self._col_cue, 2))
        painter.drawLine(px, 0, px, h)
        painter.setBrush(self._col_cue)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        tri = QtGui.QPolygonF(
            [
                QtCore.QPointF(px - 5, h - 1),
                QtCore.QPointF(px + 5, h - 1),
                QtCore.QPointF(px, h - 8),
            ]
        )
        painter.drawPolygon(tri)

    def _draw_musical_beatgrid(self, painter, w, h):
        if self._bpm and self._bpm > 20:
            beat_ms = 60000.0 / self._bpm
            duration = self._duration_ms
            if duration <= 0:
                return

            painter.setPen(QtGui.QPen(self._col_beat, 1, QtCore.Qt.PenStyle.DotLine))
            i = 1
            while True:
                t = i * beat_ms
                if t >= duration:
                    break
                px = int((t / duration) * w)
                if 0 < px < w:
                    painter.drawLine(px, 6, px, h - 6)
                i += 1

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
            painter.setPen(QtGui.QPen(self._col_beatgrid, 1, QtCore.Qt.PenStyle.DashLine))
            for i in range(1, 16):
                px = int(w * (i / 16))
                painter.drawLine(px, 0, px, h)

    def _draw_playhead(self, painter, w, h):
        if self._duration_ms <= 0:
            return
        px = max(0, min(int(self._playhead_ms / self._duration_ms * w), w - 1))

        c = BOOTH_COLORS
        glow_col = QtGui.QColor(c.get("playhead_glow", "#7ec8ff"))
        for offset, alpha in ((2, 20), (1, 45)):
            glow = QtGui.QColor(glow_col)
            glow.setAlpha(alpha)
            painter.setPen(QtGui.QPen(glow, 1 + offset))
            painter.drawLine(px, 0, px, h)

        painter.setPen(QtGui.QPen(self._col_playhead, 2))
        painter.drawLine(px, 0, px, h)

        arrow_size = 5
        painter.setBrush(self._col_playhead)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        path = QtGui.QPainterPath()
        path.moveTo(px - arrow_size, 0)
        path.lineTo(px + arrow_size, 0)
        path.lineTo(px, arrow_size + 1)
        path.closeSubpath()
        painter.drawPath(path)

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
        if self._duration_ms <= 0:
            return
        t = int(event.position().x() / self.width() * self._duration_ms)
        t = max(0, min(t, self._duration_ms))
        self.double_clicked.emit(t)
        self.seek_requested.emit(t)

    def mouseMoveEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def time_at_x(self, x: int) -> int:
        if self._duration_ms <= 0 or self.width() <= 0:
            return 0
        t = int(x / self.width() * self._duration_ms)
        return max(0, min(t, self._duration_ms))