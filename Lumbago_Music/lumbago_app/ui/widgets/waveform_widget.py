"""
Lumbago Music AI — Widget wizualizacji waveform (pełny)
========================================================
Renderuje peaks waveform z pozycją odtwarzania i markerami cue.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class WaveformWidget(QWidget):
    """
    Widget do wyświetlania waveform audio.

    Funkcje:
    - Renderowanie peaks (lewa/prawa strona)
    - Pozycja odtwarzania (pionowa linia)
    - Markery cue points (kolorowe pionowe linie)
    - Kliknięcie = seek do pozycji
    """

    position_clicked = pyqtSignal(float)  # 0.0 - 1.0 pozycja

    COLOR_BG = QColor("#0a0a0c")
    COLOR_WAVE = QColor("#00c8d8")
    COLOR_WAVE_PLAYED = QColor("#00f5ff")
    COLOR_PLAYHEAD = QColor("#ffffff")
    COLOR_CUE = [
        QColor("#ff4444"), QColor("#44ff44"), QColor("#4444ff"),
        QColor("#ffff44"), QColor("#ff44ff"), QColor("#44ffff"),
        QColor("#ff8800"), QColor("#8800ff"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(80)
        self._peaks: list[float] = []
        self._position: float = 0.0      # 0.0 - 1.0
        self._cue_positions: list[tuple[float, int]] = []  # (pos 0-1, index)

    def set_peaks(self, peaks: list[float]) -> None:
        """Ustawia dane peaks i odświeża."""
        self._peaks = peaks
        self.update()

    def set_position(self, pos: float) -> None:
        """Aktualizuje pozycję odtwarzania (0.0-1.0)."""
        self._position = max(0.0, min(1.0, pos))
        self.update()

    def set_cue_points(self, cues: list[tuple[float, int]]) -> None:
        """Ustawia pozycje cue points. cues = [(pos_ratio, index), ...]"""
        self._cue_positions = cues
        self.update()

    def paintEvent(self, event: object) -> None:
        """Renderuje waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        h = self.height()
        mid = h // 2

        # Tło
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        if not self._peaks:
            # Placeholder
            painter.setPen(QPen(QColor("#1e1e2e"), 1))
            painter.drawLine(0, mid, w, mid)
            return

        # Peaks
        playhead_x = int(w * self._position)
        step = w / len(self._peaks)

        for i, peak in enumerate(self._peaks):
            x = int(i * step)
            peak_h = max(1, int(peak * mid * 0.95))
            color = self.COLOR_WAVE_PLAYED if x <= playhead_x else self.COLOR_WAVE
            painter.setPen(QPen(color, max(1, int(step))))
            painter.drawLine(x, mid - peak_h, x, mid + peak_h)

        # Playhead
        painter.setPen(QPen(self.COLOR_PLAYHEAD, 2))
        painter.drawLine(playhead_x, 0, playhead_x, h)

        # Cue points
        for pos, idx in self._cue_positions:
            cx = int(w * pos)
            color = self.COLOR_CUE[idx % len(self.COLOR_CUE)]
            painter.setPen(QPen(color, 1))
            painter.drawLine(cx, 0, cx, h)
            # Trójkąt markera
            painter.setBrush(color)
            path = QPainterPath()
            path.moveTo(QPointF(cx - 4, 0))
            path.lineTo(QPointF(cx + 4, 0))
            path.lineTo(QPointF(cx, 10))
            path.closeSubpath()
            painter.fillPath(path, color)

    def mousePressEvent(self, event: object) -> None:
        """Emit seek position przy kliknięciu."""
        pos = event.pos().x() / self.width()  # type: ignore[union-attr]
        self.position_clicked.emit(max(0.0, min(1.0, pos)))
