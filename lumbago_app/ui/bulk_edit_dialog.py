from __future__ import annotations

from PyQt6 import QtWidgets

from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_tracks


class BulkEditDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edycja zbiorcza tagów")
        self.setMinimumWidth(520)
        self._tracks = tracks
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.title_check = QtWidgets.QCheckBox("Tytuł")
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
