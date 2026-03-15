from __future__ import annotations

from PyQt6 import QtWidgets, QtGui
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.data.repository import list_change_log


class ChangeHistoryDialog(QtWidgets.QDialog):
    def __init__(self, track_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historia zmian tagĂłw")
        self.setMinimumSize(720, 420)
        apply_dialog_fade(self)
        self._track_path = track_path
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(10)
        layout.addWidget(card)
        layout = card_layout

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pole", "Stare", "Nowe", "ĹąrĂłdĹ‚o", "Data"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        close_btn = QtWidgets.QPushButton("Zamknij")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _load(self):
        rows = list_change_log(self._track_path)
        self.table.setRowCount(0)
        for entry in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry["field"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry["old"]))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(entry["new"]))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(entry["source"]))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(entry["changed_at"]))




