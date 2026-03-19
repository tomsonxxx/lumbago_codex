"""Lumbago Music AI — Dialog kopii zapasowych."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox,
)

logger = logging.getLogger(__name__)


class BackupDialog(QDialog):
    """Dialog zarządzania kopiami zapasowymi bazy."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kopie zapasowe")
        self.resize(500, 350)
        self._build_ui()
        self._load_backups()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Dostępne kopie zapasowe:"))

        self._list = QListWidget()
        layout.addWidget(self._list, stretch=1)

        btn_layout = QHBoxLayout()
        btn_create = QPushButton("+ Utwórz backup")
        btn_create.clicked.connect(self._on_create)
        btn_restore = QPushButton("↩ Przywróć")
        btn_restore.clicked.connect(self._on_restore)
        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.reject)

        btn_layout.addWidget(btn_create)
        btn_layout.addWidget(btn_restore)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _load_backups(self) -> None:
        try:
            from lumbago_app.services.backup_service import BackupService
            service = BackupService()
            backups = service.list_backups()
            self._list.clear()
            for b in backups:
                self._list.addItem(b.name)
            if not backups:
                self._list.addItem("(brak kopii zapasowych)")
        except Exception as exc:
            logger.warning("Błąd ładowania backupów: %s", exc)

    def _on_create(self) -> None:
        QMessageBox.information(
            self, "Backup",
            "Tworzenie backupu — do implementacji w FAZIE 2"
        )

    def _on_restore(self) -> None:
        QMessageBox.information(
            self, "Przywróć",
            "Przywracanie backupu — do implementacji w FAZIE 2"
        )
