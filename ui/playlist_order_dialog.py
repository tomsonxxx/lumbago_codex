from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from core.models import Track
# Playlist intel Faza2: sort helpers from audio_features (harmonic Camelot, energy)
from services.audio_features import sort_tracks_for_harmonic_mixing, sort_tracks_by_energy


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
        up_btn.setToolTip("EFEKT: ręczne przesunięcie zaznaczonego w górę listy (kolejność playlisty).")
        up_btn.clicked.connect(self._move_up)
        down_btn = QtWidgets.QPushButton("Dół")
        down_btn.setToolTip("EFEKT: ręczne przesunięcie zaznaczonego w dół listy (kolejność playlisty).")
        down_btn.clicked.connect(self._move_down)
        controls.addWidget(up_btn)
        controls.addWidget(down_btn)

        # Faza2 auto sort intel buttons + EFFECT
        sort_harm = QtWidgets.QPushButton("Sortuj harmonicznie (Camelot)")
        sort_harm.setToolTip("EFEKT: auto-sort wg zgodności harmoniczej Camelot (z helpers audio_features). Płynne przejścia miksów. Zastosuj + Zapisz.")
        sort_harm.clicked.connect(self._sort_harmonic)
        sort_en = QtWidgets.QPushButton("Sortuj po energii (desc)")
        sort_en.setToolTip("EFEKT: auto-sort wg energii (malejąco) dla budowania flow setu. Używa sort_tracks_by_energy.")
        sort_en.clicked.connect(self._sort_energy)
        controls.addWidget(sort_harm)
        controls.addWidget(sort_en)
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

    def _sort_harmonic(self):
        # rebuild from current list order (in case manual tweaks)
        current = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            # find orig track
            t = next((tr for tr in self._tracks if getattr(tr, 'path', None) == path), None)
            if t: current.append(t)
        sorted_t = sort_tracks_for_harmonic_mixing(current)
        self._rebuild_list(sorted_t)

    def _sort_energy(self):
        current = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            t = next((tr for tr in self._tracks if getattr(tr, 'path', None) == path), None)
            if t: current.append(t)
        sorted_t = sort_tracks_by_energy(current, ascending=False)
        self._rebuild_list(sorted_t)

    def _rebuild_list(self, tracks: list[Track]):
        self.list_widget.clear()
        for track in tracks:
            item = QtWidgets.QListWidgetItem(f"{track.artist or ''} - {track.title or ''}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, track.path)
            self.list_widget.addItem(item)

    def ordered_paths(self) -> list[str]:
        paths: list[str] = []
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths




