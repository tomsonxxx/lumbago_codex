"""Lumbago Music AI — Dialog generatora setlisty AI."""

import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

logger = logging.getLogger(__name__)


class SetlistDialog(QDialog):
    """Dialog do generowania AI setlisty."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Setlist Generator")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Generator setlisty AI — do implementacji w FAZIE 3.\n\n"
            "Funkcje:\n"
            "- Wybór kandydatów (gatunek, BPM, energia)\n"
            "- Krzywa energii (build/peak/outro)\n"
            "- Walidacja harmoniczna (Camelot)\n"
            "- Eksport do pliku/playlisty"
        ))
        btn = QPushButton("Zamknij")
        btn.clicked.connect(self.reject)
        layout.addWidget(btn)
