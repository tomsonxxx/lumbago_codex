"""Lumbago Music AI — Widget oceny gwiazdkowej (1-5)."""

import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class RatingWidget(QWidget):
    """Widget oceny 1-5 gwiazdek z klikalnymi gwiazdkami."""

    rating_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(90, 24)
        self._rating: int = 0
        self._hover: int = 0

    @property
    def rating(self) -> int:
        return self._rating

    @rating.setter
    def rating(self, value: int) -> None:
        self._rating = max(0, min(5, value))
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        font = QFont()
        font.setPixelSize(16)
        painter.setFont(font)

        active = self._hover or self._rating

        for i in range(5):
            x = i * 18 + 2
            if i < active:
                painter.setPen(QColor("#f0c040"))
            else:
                painter.setPen(QColor("#303040"))
            painter.drawText(x, 18, "★")

    def mousePressEvent(self, event: object) -> None:
        star = event.pos().x() // 18  # type: ignore[union-attr]
        new_rating = star + 1
        self._rating = 0 if self._rating == new_rating else new_rating
        self.rating_changed.emit(self._rating)
        self.update()

    def mouseMoveEvent(self, event: object) -> None:
        self._hover = event.pos().x() // 18 + 1  # type: ignore[union-attr]
        self.update()

    def leaveEvent(self, event: object) -> None:
        self._hover = 0
        self.update()
