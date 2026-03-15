from __future__ import annotations

from PyQt6 import QtWidgets, QtGui

from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_tracks
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class BulkEditDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edycja zbiorcza tagĂłw")
        self.setMinimumWidth(520)
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

        form = QtWidgets.QFormLayout()

        self.title_check = QtWidgets.QCheckBox("TytuĹ‚")
        self.artist_check = QtWidgets.QCheckBox("Artysta")
        self.album_check = QtWidgets.QCheckBox("Album")
        self.genre_check = QtWidgets.QCheckBox("Gatunek")
        self.bpm_check = QtWidgets.QCheckBox("BPM")
        self.key_check = QtWidgets.QCheckBox("Tonacja")

        self.title_input = QtWidgets.QLineEdit()
        self.artist_input = QtWidgets.QLineEdit()
        self.album_input = QtWidgets.QLineEdit()
        self.genre_input = QtWidgets.QLineEdit()
        self.bpm_input = QtWidgets.QLineEdit()
        self.key_input = QtWidgets.QLineEdit()

        form.addRow(self.title_check, self.title_input)
        form.addRow(self.artist_check, self.artist_input)
        form.addRow(self.album_check, self.album_input)
        form.addRow(self.genre_check, self.genre_input)
        form.addRow(self.bpm_check, self.bpm_input)
        form.addRow(self.key_check, self.key_input)

        layout.addLayout(form)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        apply_btn = QtWidgets.QPushButton("Zastosuj")
        apply_btn.clicked.connect(self._apply)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(apply_btn)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

    def _apply(self):
        for track in self._tracks:
            if self.title_check.isChecked():
                track.title = self.title_input.text().strip()
            if self.artist_check.isChecked():
                track.artist = self.artist_input.text().strip()
            if self.album_check.isChecked():
                track.album = self.album_input.text().strip()
            if self.genre_check.isChecked():
                track.genre = self.genre_input.text().strip()
            if self.key_check.isChecked():
                track.key = self.key_input.text().strip()
            if self.bpm_check.isChecked():
                try:
                    track.bpm = float(self.bpm_input.text()) if self.bpm_input.text().strip() else None
                except ValueError:
                    track.bpm = None
        update_tracks(self._tracks)
        self.accept()




