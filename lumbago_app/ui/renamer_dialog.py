from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.models import Track
from lumbago_app.core.renamer import apply_rename_plan, build_rename_plan, undo_last_rename
from lumbago_app.data.repository import update_track_paths_bulk


class RenamerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renamer")
        self.setMinimumSize(860, 520)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._plan = []
        self._build_ui()

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

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Wzorzec:"))
        self.pattern = QtWidgets.QLineEdit("{artist} - {title}")
        self.pattern.setToolTip("UĹĽyj pĂłl: {artist} {title} {album} {genre} {bpm} {key} {index}")
        row.addWidget(self.pattern, 1)
        self.preview_btn = QtWidgets.QPushButton("PodglÄ…d")
        self.preview_btn.clicked.connect(self._preview)
        row.addWidget(self.preview_btn)
        layout.addLayout(row)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Stara nazwa", "Nowa nazwa", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        actions = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Zastosuj")
        self.apply_btn.setToolTip("ZmieĹ„ nazwy plikĂłw wedĹ‚ug planu")
        self.apply_btn.clicked.connect(self._apply)
        self.undo_btn = QtWidgets.QPushButton("Cofnij ostatniÄ… zmianÄ™")
        self.undo_btn.setToolTip("PrzywrĂłÄ‡ poprzednie nazwy z ostatniego uĹĽycia")
        self.undo_btn.clicked.connect(self._undo)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        actions.addStretch(1)
        actions.addWidget(self.apply_btn)
        actions.addWidget(self.undo_btn)
        actions.addWidget(self.close_btn)
        layout.addLayout(actions)

    def _preview(self):
        self._plan = build_rename_plan(self._tracks, self.pattern.text().strip())
        self.table.setRowCount(0)
        for item in self._plan:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.old_path)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.new_path)))
            status = "OK" if not item.conflict else f"Konflikt: {item.reason}"
            status_item = QtWidgets.QTableWidgetItem(status)
            if item.conflict:
                status_item.setForeground(QtCore.Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)

    def _apply(self):
        if not self._plan:
            self._preview()
        history = apply_rename_plan(self._plan)
        update_track_paths_bulk(history)
        self.accept()

    def _undo(self):
        history = undo_last_rename()
        flipped = [{"old": item["new"], "new": item["old"]} for item in history]
        update_track_paths_bulk(flipped)
        self.accept()




