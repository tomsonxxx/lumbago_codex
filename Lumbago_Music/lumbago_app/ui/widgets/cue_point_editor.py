"""Lumbago Music AI — Widget edytora cue points."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QColorDialog,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


class CuePointEditor(QWidget):
    """
    Widget do zarządzania 8 cue points.
    Każdy cue ma: numer, pozycję, etykietę, kolor.
    """

    cue_updated = pyqtSignal(int, float, str, str)  # (index, position, label, color)
    cue_deleted = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cues: list[dict] = []
        self._current_position: float = 0.0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("CUE POINTS")
        header.setStyleSheet(
            "color: #00f5ff; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        layout.addWidget(header)

        self._rows: list[QWidget] = []
        for i in range(8):
            row = self._build_cue_row(i)
            layout.addWidget(row)
            self._rows.append(row)

    def _build_cue_row(self, index: int) -> QWidget:
        """Buduje wiersz dla jednego cue point."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        COLORS = ["#ff4444", "#44ff44", "#4444ff", "#ffff44",
                  "#ff44ff", "#44ffff", "#ff8800", "#8800ff"]

        btn_set = QPushButton(f"H{index+1}")
        btn_set.setFixedWidth(30)
        btn_set.setFixedHeight(22)
        btn_set.setStyleSheet(
            f"background: {COLORS[index]}33; border: 1px solid {COLORS[index]}88; "
            f"color: {COLORS[index]}; border-radius: 3px; font-size: 10px;"
        )
        btn_set.setToolTip(f"Ustaw Hot Cue {index+1} w aktualnej pozycji")
        btn_set.clicked.connect(lambda _, i=index: self._on_set_cue(i))

        pos_label = QLabel("--:--")
        pos_label.setFixedWidth(45)
        pos_label.setStyleSheet("color: #808090; font-size: 10px;")

        name_edit = QLineEdit()
        name_edit.setPlaceholderText(f"Cue {index+1}")
        name_edit.setMaxLength(20)
        name_edit.setStyleSheet("font-size: 10px; padding: 1px 4px;")

        btn_del = QPushButton("×")
        btn_del.setFixedWidth(18)
        btn_del.setFixedHeight(18)
        btn_del.setStyleSheet(
            "color: #606070; border: none;"
            "QPushButton:hover { color: #ff4444; }"
        )
        btn_del.clicked.connect(lambda _, i=index: self.cue_deleted.emit(i))

        row_layout.addWidget(btn_set)
        row_layout.addWidget(pos_label)
        row_layout.addWidget(name_edit, stretch=1)
        row_layout.addWidget(btn_del)

        # Przechowaj referencje
        row._pos_label = pos_label  # type: ignore[attr-defined]
        row._name_edit = name_edit  # type: ignore[attr-defined]
        row._index = index  # type: ignore[attr-defined]

        return row

    def _on_set_cue(self, index: int) -> None:
        """Ustawia cue w aktualnej pozycji odtwarzania."""
        from lumbago_app.core.utils import format_duration
        row = self._rows[index]
        row._pos_label.setText(format_duration(self._current_position))  # type: ignore[attr-defined]
        self.cue_updated.emit(
            index,
            self._current_position,
            row._name_edit.text() or f"Cue {index+1}",  # type: ignore[attr-defined]
            "#ffffff",
        )

    def set_playback_position(self, position_seconds: float) -> None:
        """Aktualizuje aktualną pozycję odtwarzania."""
        self._current_position = position_seconds
