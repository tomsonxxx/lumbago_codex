"""Lumbago Music AI — Panel filtrów wyszukiwania."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt

logger = logging.getLogger(__name__)


class FilterPanel(QWidget):
    """Panel filtrów: wyszukiwanie tekstowe, gatunek, BPM, tonacja."""

    filter_changed = pyqtSignal(dict)  # emituje słownik filtrów

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumHeight(100)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Wiersz 1: szukaj
        row1 = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Szukaj (artysta, tytuł, album...)")
        self._search.textChanged.connect(self._emit_filter)
        row1.addWidget(self._search)
        layout.addLayout(row1)

        # Wiersz 2: gatunek, BPM range, tonacja
        row2 = QHBoxLayout()
        row2.setSpacing(4)

        self._genre = QComboBox()
        self._genre.addItem("Wszystkie gatunki")
        self._genre.setMinimumWidth(120)
        self._genre.currentIndexChanged.connect(self._emit_filter)

        self._key = QComboBox()
        self._key.addItem("Wszystkie tonacje")
        self._key.addItems([
            "1A", "2A", "3A", "4A", "5A", "6A",
            "7A", "8A", "9A", "10A", "11A", "12A",
            "1B", "2B", "3B", "4B", "5B", "6B",
            "7B", "8B", "9B", "10B", "11B", "12B",
        ])
        self._key.currentIndexChanged.connect(self._emit_filter)

        row2.addWidget(QLabel("Gatunek:"))
        row2.addWidget(self._genre)
        row2.addWidget(QLabel("Tonacja:"))
        row2.addWidget(self._key)
        row2.addStretch()
        layout.addLayout(row2)

    def _emit_filter(self) -> None:
        """Emituje aktualny stan filtrów."""
        genre = self._genre.currentText()
        key = self._key.currentText()
        self.filter_changed.emit({
            "query": self._search.text(),
            "genre": genre if genre != "Wszystkie gatunki" else "",
            "key_camelot": key if key != "Wszystkie tonacje" else "",
        })

    def populate_genres(self, genres: list[str]) -> None:
        """Wypełnia listę gatunków."""
        self._genre.clear()
        self._genre.addItem("Wszystkie gatunki")
        self._genre.addItems(sorted(genres))
