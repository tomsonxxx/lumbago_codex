from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.models import Track


class PlaylistOrderDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kolejność w playliście")
        self.setMinimumSize(520, 420)
        apply_dialog_fade(self)
        self._tracks = tracks
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

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        for track in self._tracks:
            item = QtWidgets.QListWidgetItem(f"{track.artist or ''} - {track.title or ''}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, track.path)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)

        controls = QtWidgets.QHBoxLayout()
        up_btn = QtWidgets.QPushButton("Góra")
        up_btn.clicked.connect(self._move_up)
        down_btn = QtWidgets.QPushButton("Dół")
        down_btn.clicked.connect(self._move_down)
        controls.addWidget(up_btn)
        controls.addWidget(down_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(save_btn)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row <= 0:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row - 1, item)
        self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= self.list_widget.count() - 1:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row + 1, item)
        self.list_widget.setCurrentRow(row + 1)

    def ordered_paths(self) -> list[str]:
        paths: list[str] = []
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths




