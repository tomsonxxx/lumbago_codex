from __future__ import annotations

import json

from PyQt6 import QtWidgets, QtGui
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from lumbago_app.core.models import Playlist


class PlaylistEditorDialog(QtWidgets.QDialog):
    def __init__(self, playlist: Playlist | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Playlista")
        self.setMinimumSize(520, 360)
        apply_dialog_fade(self)
        self._playlist = playlist
        self._build_ui()
        if playlist:
            self._load(playlist)

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
        self.name_input = QtWidgets.QLineEdit()
        self.desc_input = QtWidgets.QLineEdit()
        self.smart_check = QtWidgets.QCheckBox("Playlista smart (reguły)")
        self.search_input = QtWidgets.QLineEdit()
        self.genre_input = QtWidgets.QLineEdit()
        self.key_input = QtWidgets.QLineEdit()
        self.bpm_min = QtWidgets.QDoubleSpinBox()
        self.bpm_min.setRange(0, 300)
        self.bpm_max = QtWidgets.QDoubleSpinBox()
        self.bpm_max.setRange(0, 300)

        form.addRow("Nazwa", self.name_input)
        form.addRow("Opis", self.desc_input)
        form.addRow("", self.smart_check)
        form.addRow("Wyszukiwanie", self.search_input)
        form.addRow("Gatunek", self.genre_input)
        form.addRow("Tonacja", self.key_input)
        form.addRow("BPM min", self.bpm_min)
        form.addRow("BPM max", self.bpm_max)
        layout.addLayout(form)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(save_btn)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

    def _load(self, playlist: Playlist):
        self.name_input.setText(playlist.name)
        self.desc_input.setText(playlist.description or "")
        self.smart_check.setChecked(bool(playlist.is_smart))
        if playlist.rules:
            try:
                rules = json.loads(playlist.rules)
            except Exception:
                rules = {}
            self.search_input.setText(rules.get("search", ""))
            self.genre_input.setText(rules.get("genre", ""))
            self.key_input.setText(rules.get("key", ""))
            self.bpm_min.setValue(rules.get("bpm_min", 0) or 0)
            self.bpm_max.setValue(rules.get("bpm_max", 0) or 0)

    def get_payload(self) -> dict:
        rules = None
        if self.smart_check.isChecked():
            rules = {
                "search": self.search_input.text().strip(),
                "genre": self.genre_input.text().strip(),
                "key": self.key_input.text().strip(),
                "bpm_min": self.bpm_min.value() or None,
                "bpm_max": self.bpm_max.value() or None,
            }
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip() or None,
            "is_smart": self.smart_check.isChecked(),
            "rules": json.dumps(rules, ensure_ascii=False) if rules else None,
        }




