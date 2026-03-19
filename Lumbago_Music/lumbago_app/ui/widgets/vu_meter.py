"""Lumbago Music AI — Widget VU metr."""

import logging
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class VUMeter(QWidget):
    """VU metr w stylu DJ (zielony-żółty-czerwony)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(16)
        self.setMinimumHeight(100)
        self._level: float = 0.0    # 0.0 - 1.0

    def set_level(self, level: float) -> None:
        """Ustawia poziom sygnału (0.0-1.0)."""
        self._level = max(0.0, min(1.0, level))
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        level_h = int(h * self._level)

        # Tło
        painter.fillRect(0, 0, w, h, QColor("#0a0a0c"))

        if level_h <= 0:
            return

        # Gradient zielony → żółty → czerwony
        grad = QLinearGradient(0, h, 0, 0)
        grad.setColorAt(0.0, QColor("#00cc44"))
        grad.setColorAt(0.7, QColor("#cccc00"))
        grad.setColorAt(1.0, QColor("#cc2200"))

        painter.fillRect(1, h - level_h, w - 2, level_h, grad)

        # Segment lines
        painter.setPen(QColor("#050505"))
        seg_count = 20
        for i in range(1, seg_count):
            y = int(h * i / seg_count)
            painter.drawLine(0, y, w, y)
