from __future__ import annotations

from PyQt6 import QtCore, QtWidgets, QtGui
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.audio import write_tags
from lumbago_app.data.repository import list_change_log, update_track
from lumbago_app.core.models import Track
from pathlib import Path


class ChangeHistoryDialog(QtWidgets.QDialog):
    def __init__(self, track_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historia zmian tagów")
        self.setMinimumSize(720, 420)
        apply_dialog_fade(self)
        self._track_path = track_path
        self._all_rows: list[dict[str, str]] = []
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

        filter_row = QtWidgets.QHBoxLayout()
        filter_row.addWidget(QtWidgets.QLabel("Źródło:"))
        self.source_filter = QtWidgets.QComboBox()
        self.source_filter.addItem("Wszystkie", "")
        self.source_filter.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(self.source_filter)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pole", "Stare", "Nowe", "Źródło", "Data"])
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)
        layout.addWidget(self.table, 1)

        btn_row = QtWidgets.QHBoxLayout()
        restore_btn = QtWidgets.QPushButton("Przywróć tę wartość")
        restore_btn.setToolTip("Przywróć starą wartość zaznaczonego wiersza")
        restore_btn.clicked.connect(self._restore_selected)
        close_btn = QtWidgets.QPushButton("Zamknij")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load(self):
        self._all_rows = list_change_log(self._track_path)
        sources = sorted({r["source"] for r in self._all_rows if r["source"]})
        self.source_filter.blockSignals(True)
        for s in sources:
            label = _format_source(s)
            self.source_filter.addItem(label, s)
        self.source_filter.blockSignals(False)
        self._apply_filter()

    def _apply_filter(self):
        selected_source = self.source_filter.currentData()
        rows = self._all_rows if not selected_source else [r for r in self._all_rows if r["source"] == selected_source]
        self.table.setRowCount(0)
        for entry in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry["field"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry["old"]))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(entry["new"]))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(_format_source(entry["source"])))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(entry["changed_at"]))

    def _restore_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.information(self, "Przywróć", "Zaznacz wiersz do przywrócenia.")
            return
        field_item = self.table.item(row, 0)
        old_item = self.table.item(row, 1)
        if not field_item or not old_item:
            return
        field = field_item.text()
        old_value = old_item.text()
        confirm = QtWidgets.QMessageBox.question(
            self, "Przywróć", f"Przywrócić pole '{field}' do wartości: '{old_value}'?"
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            write_tags(Path(self._track_path), {field: old_value})
        except Exception:
            pass
        QtWidgets.QMessageBox.information(self, "Przywróć", "Wartość została przywrócona.")

    def _show_column_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        show_all = menu.addAction("Pokaż wszystkie")
        hide_all = menu.addAction("Ukryj wszystkie")
        menu.addSeparator()
        actions = []
        for col in range(self.table.columnCount()):
            name = self.table.horizontalHeaderItem(col).text()
            action = QtWidgets.QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(col))
            actions.append((action, col))
            menu.addAction(action)
        chosen = menu.exec(self.table.horizontalHeader().mapToGlobal(pos))
        if chosen == show_all:
            for _, col in actions:
                self.table.setColumnHidden(col, False)
            return
        if chosen == hide_all:
            for _, col in actions:
                self.table.setColumnHidden(col, True)
            return
        for action, col in actions:
            if chosen == action:
                self.table.setColumnHidden(col, not action.isChecked())
                break


def _format_source(source: str) -> str:
    if not source:
        return ""
    if source.startswith("ai:"):
        return f"AI ({source[3:]})"
    return source.replace("_", " ").title()
