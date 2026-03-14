from __future__ import annotations

from PyQt6 import QtWidgets

from lumbago_app.data.repository import list_change_log


class ChangeHistoryDialog(QtWidgets.QDialog):
    def __init__(self, track_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historia zmian tagów")
        self.setMinimumSize(720, 420)
        self._track_path = track_path
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pole", "Stare", "Nowe", "Źródło", "Data"])
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
