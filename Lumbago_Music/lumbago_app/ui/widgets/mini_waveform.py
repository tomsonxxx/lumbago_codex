"""Lumbago Music AI — Mini waveform dla panelu playera."""

import logging
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class MiniWaveform(QWidget):
    """Uproszczona waveform do wyświetlania w panelu playera."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(50)
        self._peaks: list[float] = []
        self._position: float = 0.0

    def set_peaks(self, peaks: list[float]) -> None:
        self._peaks = peaks
        self.update()

    def set_position(self, pos: float) -> None:
        self._position = max(0.0, min(1.0, pos))
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        mid = h // 2

        painter.fillRect(0, 0, w, h, QColor("#080808"))

        if not self._peaks:
            painter.setPen(QPen(QColor("#1e1e2e"), 1))
            painter.drawLine(0, mid, w, mid)
            return

        playhead_x = int(w * self._position)
        step = max(1, w / len(self._peaks))

        for i, peak in enumerate(self._peaks):
            x = int(i * step)
            peak_h = max(1, int(peak * mid * 0.9))
            color = QColor("#00f5ff") if x <= playhead_x else QColor("#006070")
            painter.setPen(QPen(color, max(1, int(step))))
            painter.drawLine(x, mid - peak_h, x, mid + peak_h)

        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(playhead_x, 0, playhead_x, h)
