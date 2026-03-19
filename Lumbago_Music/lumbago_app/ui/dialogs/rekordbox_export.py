"""Lumbago Music AI — Dialog eksportu Rekordbox XML."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog,
)

logger = logging.getLogger(__name__)


class RekordboxExportDialog(QDialog):
    """Dialog eksportu biblioteki do formatu XML Rekordbox."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Eksport Rekordbox XML")
        self.resize(450, 280)
        layout = QVBoxLayout(self)

        info = QLabel(
            "Eksportuje bibliotekę do formatu XML kompatybilnego z Rekordbox.\n\n"
            "Eksportowane dane:\n"
            "- Metadane (artysta, tytuł, album, BPM, tonacja)\n"
            "- Hot cue points\n"
            "- Beatgrid\n"
            "- Playlisty\n\n"
            "Implementacja: FAZA 3"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Eksportuj XML...")
        btn_export.setProperty("accent", True)
        btn_export.clicked.connect(self._on_export)
        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj XML", "lumbago_library.xml", "XML (*.xml)"
        )
        if path:
            logger.info("Rekordbox eksport do %s — FAZA 3", path)
