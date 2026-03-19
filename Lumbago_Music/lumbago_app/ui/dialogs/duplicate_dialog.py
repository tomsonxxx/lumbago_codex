"""Lumbago Music AI — Dialog wykrywania duplikatów."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTreeWidget, QTreeWidgetItem, QProgressBar,
)

logger = logging.getLogger(__name__)


class DuplicateDialog(QDialog):
    """Dialog do znajdowania i rozwiązywania duplikatów."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("⊕ Wykrywanie duplikatów")
        self.resize(700, 500)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        info = QLabel(
            "Skanuje bibliotekę w poszukiwaniu identycznych plików (hash), "
            "tych samych nagrań (fingerprint) i podobnych tytułów."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #909090; font-size: 11px;")
        layout.addWidget(info)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Artysta — Tytuł", "Ścieżka", "Metoda", "Podobieństwo"])
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree, stretch=1)

        self._status = QLabel("Kliknij 'Szukaj' aby rozpocząć skanowanie.")
        layout.addWidget(self._status)

        btn_layout = QHBoxLayout()
        btn_scan = QPushButton("🔍 Szukaj duplikatów")
        btn_scan.setProperty("accent", True)
        btn_scan.clicked.connect(self._on_scan)
        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_scan)
        layout.addLayout(btn_layout)

    def _on_scan(self) -> None:
        """Uruchamia skanowanie duplikatów."""
        self._status.setText("Skanowanie duplikatów — do implementacji w FAZIE 2")
        logger.info("DuplicateDialog: skanowanie — FAZA 2")
