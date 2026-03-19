"""Lumbago Music AI — Dialog masowego przemianowania."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
)

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE = "{{ artist }} - {{ title }}{{ ext }}"


class RenameDialog(QDialog):
    """Dialog masowego przemianowania plików wg szablonu Jinja2."""

    def __init__(self, track_ids: list[int], parent=None) -> None:
        super().__init__(parent)
        self._track_ids = track_ids
        self.setWindowTitle("Masowe przemianowanie plików")
        self.resize(700, 500)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._template = QLineEdit(DEFAULT_TEMPLATE)
        self._template.setToolTip(
            "Zmienne: {{ artist }}, {{ title }}, {{ album }}, {{ year }}, "
            "{{ track_number }}, {{ genre }}, {{ bpm }}, {{ key }}, {{ ext }}"
        )
        form.addRow("Szablon nazwy:", self._template)
        layout.addLayout(form)

        self._preview_table = QTableWidget()
        self._preview_table.setColumnCount(2)
        self._preview_table.setHorizontalHeaderLabels(["Stara nazwa", "Nowa nazwa"])
        self._preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._preview_table)

        btn_layout = QHBoxLayout()
        btn_preview = QPushButton("Podgląd")
        btn_preview.clicked.connect(self._on_preview)
        btn_apply = QPushButton("✓ Zastosuj")
        btn_apply.setProperty("accent", True)
        btn_apply.clicked.connect(self._on_apply)
        btn_close = QPushButton("Anuluj")
        btn_close.clicked.connect(self.reject)

        btn_layout.addWidget(btn_preview)
        btn_layout.addWidget(btn_apply)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _on_preview(self) -> None:
        logger.info("Rename preview — do implementacji w FAZIE 3")

    def _on_apply(self) -> None:
        logger.info("Rename apply — do implementacji w FAZIE 3")
        self.accept()
