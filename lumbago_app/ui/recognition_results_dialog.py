from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_track


@dataclass
class RecognitionResult:
    track: Track
    original_title: str | None
    original_artist: str | None
    original_album: str | None
    original_year: str | None
    original_genre: str | None
    original_artwork: str | None
    success: bool


class RecognitionResultsDialog(QtWidgets.QDialog):
    def __init__(self, results: list[RecognitionResult], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wyniki rozpoznawania metadanych")
        self.setMinimumSize(900, 500)
        apply_dialog_fade(self)
        self._results = results
        self._accepted: set[int] = set()
        self._build_ui()
        self._populate()

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

        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Plik", "Stary tytuł", "Nowy tytuł", "Stary artysta", "Nowy artysta", "Album", "Rok", "Akcja"]
        )
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setObjectName("DialogHint")
        layout.addWidget(self.status_label)

        actions = QtWidgets.QHBoxLayout()
        accept_all_btn = QtWidgets.QPushButton("Akceptuj wszystkie")
        accept_all_btn.clicked.connect(self._accept_all)
        reject_all_btn = QtWidgets.QPushButton("Odrzuć wszystkie")
        reject_all_btn.clicked.connect(self._reject_all)
        apply_btn = QtWidgets.QPushButton("Zastosuj zaznaczone")
        apply_btn.setToolTip("Zapisz do bazy tylko zaakceptowane wyniki")
        apply_btn.clicked.connect(self._apply_accepted)
        close_btn = QtWidgets.QPushButton("Zamknij bez zapisu")
        close_btn.clicked.connect(self.reject)
        actions.addWidget(accept_all_btn)
        actions.addWidget(reject_all_btn)
        actions.addStretch(1)
        actions.addWidget(apply_btn)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

    def _populate(self):
        self.table.setRowCount(0)
        success_count = sum(1 for r in self._results if r.success)
        self.status_label.setText(
            f"Rozpoznano: {success_count} / {len(self._results)} — zaakceptuj lub odrzuć wyniki przed zapisem."
        )
        for idx, result in enumerate(self._results):
            row = self.table.rowCount()
            self.table.insertRow(row)
            from pathlib import Path
            filename = Path(result.track.path).name
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(filename))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(result.original_title or ""))
            new_title = result.track.title or ""
            new_title_item = QtWidgets.QTableWidgetItem(new_title)
            if result.success and new_title != (result.original_title or ""):
                new_title_item.setForeground(QtCore.Qt.GlobalColor.green)
            self.table.setItem(row, 2, new_title_item)
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(result.original_artist or ""))
            new_artist = result.track.artist or ""
            new_artist_item = QtWidgets.QTableWidgetItem(new_artist)
            if result.success and new_artist != (result.original_artist or ""):
                new_artist_item.setForeground(QtCore.Qt.GlobalColor.green)
            self.table.setItem(row, 4, new_artist_item)
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(result.track.album or ""))
            self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(result.track.year or ""))

            if result.success:
                btn_widget = QtWidgets.QWidget()
                btn_row = QtWidgets.QHBoxLayout(btn_widget)
                btn_row.setContentsMargins(2, 2, 2, 2)
                accept_btn = QtWidgets.QPushButton("Akceptuj")
                accept_btn.setCheckable(True)
                accept_btn.setChecked(True)
                self._accepted.add(idx)
                accept_btn.setStyleSheet("QPushButton:checked { background: #1a4a1a; color: #66ff66; }")
                accept_btn.clicked.connect(lambda checked, i=idx, b=accept_btn: self._toggle(i, b))
                btn_row.addWidget(accept_btn)
                self.table.setCellWidget(row, 7, btn_widget)
            else:
                skip_item = QtWidgets.QTableWidgetItem("Nie rozpoznano")
                skip_item.setForeground(QtCore.Qt.GlobalColor.darkGray)
                self.table.setItem(row, 7, skip_item)

    def _toggle(self, idx: int, btn: QtWidgets.QPushButton):
        if btn.isChecked():
            self._accepted.add(idx)
            btn.setText("Akceptuj")
        else:
            self._accepted.discard(idx)
            btn.setText("Odrzuć")

    def _accept_all(self):
        for idx, result in enumerate(self._results):
            if result.success:
                self._accepted.add(idx)
        self._refresh_buttons(checked=True)

    def _reject_all(self):
        self._accepted.clear()
        self._refresh_buttons(checked=False)

    def _refresh_buttons(self, checked: bool):
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 7)
            if widget:
                btn = widget.findChild(QtWidgets.QPushButton)
                if btn:
                    btn.setChecked(checked)
                    btn.setText("Akceptuj" if checked else "Odrzuć")

    def _apply_accepted(self):
        saved = 0
        for idx in self._accepted:
            result = self._results[idx]
            try:
                update_track(result.track)
                saved += 1
            except Exception:
                continue
        self.status_label.setText(f"Zapisano {saved} wyników.")
        self.accept()
