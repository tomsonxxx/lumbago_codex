from __future__ import annotations

from typing import Dict, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from pathlib import Path

from core.audio import read_tags, write_tags
from core.audio import extract_metadata
from data.repository import update_track
from core.models import Track


class TagCompareDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Porównanie tagów")
        self.setMinimumSize(780, 460)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._index = 0
        self._build_ui()
        self._load_track()

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

        self.title_label = QtWidgets.QLabel("")
        layout.addWidget(self.title_label)

        header = QtWidgets.QHBoxLayout()
        self.cover_label = QtWidgets.QLabel()
        self.cover_label.setFixedSize(120, 120)
        self.cover_label.setScaledContents(True)
        header.addWidget(self.cover_label)

        self.old_tags_view = QtWidgets.QTextEdit()
        self.old_tags_view.setReadOnly(True)
        self.old_tags_view.setPlaceholderText("Stare tagi")
        self.new_tags_view = QtWidgets.QTextEdit()
        self.new_tags_view.setReadOnly(True)
        self.new_tags_view.setPlaceholderText("Nowe tagi")
        header.addWidget(self.old_tags_view, 1)
        header.addWidget(self.new_tags_view, 1)
        layout.addLayout(header)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tag", "Stare", "Nowe", "Użyj starego"])
        header_table = self.table.horizontalHeader()
        header_table.setStretchLastSection(True)
        header_table.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header_table.setSectionsMovable(True)
        header_table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header_table.customContextMenuRequested.connect(self._show_column_menu)
        layout.addWidget(self.table, 1)

        nav = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("Poprzedni")
        self.prev_btn.clicked.connect(self._prev)
        self.prev_btn.setToolTip("Wróć do poprzedniego utworu")
        self.next_btn = QtWidgets.QPushButton("Następny")
        self.next_btn.clicked.connect(self._next)
        self.next_btn.setToolTip("Przejdź do następnego utworu")
        self.apply_current_btn = QtWidgets.QPushButton("Zapisz dla tego utworu")
        self.apply_current_btn.clicked.connect(self._apply_current)
        self.apply_current_btn.setToolTip("Zapisz tagi tylko dla bieżącego utworu")
        self.apply_all_btn = QtWidgets.QPushButton("Zapisz wszystkie")
        self.apply_all_btn.clicked.connect(self._apply_all)
        self.apply_all_btn.setToolTip("Zapisz tagi dla wszystkich utworów z listy")
        self.apply_diff_btn = QtWidgets.QPushButton("Zastosuj tylko różnice")
        self.apply_diff_btn.clicked.connect(self._apply_diff_current)
        self.apply_diff_btn.setToolTip("Zapisz tylko zmienione tagi")
        self.cancel_btn = QtWidgets.QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.next_btn)
        nav.addStretch(1)
        nav.addWidget(self.apply_current_btn)
        nav.addWidget(self.apply_all_btn)
        nav.addWidget(self.apply_diff_btn)
        nav.addWidget(self.cancel_btn)
        layout.addLayout(nav)

    def _load_track(self):
        if not self._tracks:
            return
        track = self._tracks[self._index]
        self.title_label.setText(f"{track.title or 'Nieznany'} — {track.artist or ''}")
        old_tags = read_tags_from_track(track)
        new_tags = getattr(track, "_pending_new_tags", None) or build_new_tags_from_track(track)
        for key in POPULAR_TAGS:
            if not new_tags.get(key):
                if key in old_tags:
                    new_tags[key] = old_tags[key]
                else:
                    new_tags.setdefault(key, "")
        tags = order_tags(old_tags, new_tags)
        self.table.setRowCount(0)
        for tag in tags:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(tag))
            old_item = QtWidgets.QTableWidgetItem(old_tags.get(tag, ""))
            old_item.setFlags(old_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, old_item)
            new_item = QtWidgets.QTableWidgetItem(new_tags.get(tag, ""))
            new_item.setFlags(new_item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, new_item)
            btn = QtWidgets.QPushButton("Użyj")
            btn.clicked.connect(lambda _, r=row: self._copy_new(r))
            self.table.setCellWidget(row, 3, btn)
        self.prev_btn.setEnabled(self._index > 0)
        self.next_btn.setEnabled(self._index < len(self._tracks) - 1)
        self._update_preview(old_tags, new_tags)
        self._update_cover(track)

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
            self._hide_all_but_anchor([col for _, col in actions])
            return
        for action, col in actions:
            if chosen == action:
                if action.isChecked():
                    self.table.setColumnHidden(col, False)
                else:
                    visible = sum(1 for _, c in actions if not self.table.isColumnHidden(c))
                    if visible > 1:
                        self.table.setColumnHidden(col, True)
                    else:
                        action.setChecked(True)
                break

    def _hide_all_but_anchor(self, columns: list[int]) -> None:
        if not columns:
            return
        anchor = columns[0]
        for col in columns:
            self.table.setColumnHidden(col, col != anchor)

    def _copy_new(self, row: int):
        old_item = self.table.item(row, 1)
        if old_item:
            new_item = self.table.item(row, 2)
            if new_item:
                new_item.setText(old_item.text())

    def _collect_new_tags(self) -> Dict[str, str]:
        tags: Dict[str, str] = {}
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            val_item = self.table.item(row, 2)
            if key_item and val_item:
                tags[key_item.text()] = val_item.text()
        return tags

    def _prev(self):
        self._apply_current()
        if self._index > 0:
            self._index -= 1
            self._load_track()

    def _next(self):
        self._apply_current()
        if self._index < len(self._tracks) - 1:
            self._index += 1
            self._load_track()

    def edited_tags(self) -> Dict[str, str]:
        return self._collect_new_tags()

    def _apply_current(self):
        track = self._tracks[self._index]
        tags = self._collect_new_tags()
        try:
            write_tags(Path(track.path), tags)
            refreshed = extract_metadata(Path(track.path))
            track.title = refreshed.title
            track.artist = refreshed.artist
            track.album = refreshed.album
            track.genre = refreshed.genre
            update_track(track)
        except Exception:
            pass
        self._save_current_edits()

    def _apply_diff_current(self):
        track = self._tracks[self._index]
        old_tags = read_tags_from_track(track)
        new_tags = self._collect_new_tags()
        diff = diff_tags(old_tags, new_tags)
        try:
            write_tags(Path(track.path), diff)
            refreshed = extract_metadata(Path(track.path))
            track.title = refreshed.title
            track.artist = refreshed.artist
            track.album = refreshed.album
            track.genre = refreshed.genre
            update_track(track)
        except Exception:
            pass
        self._save_current_edits()

    def _apply_all(self):
        self._save_current_edits()
        for track in self._tracks:
            tags = getattr(track, "_pending_new_tags", None)
            if not tags:
                continue
            try:
                write_tags(Path(track.path), tags)
                refreshed = extract_metadata(Path(track.path))
                track.title = refreshed.title
                track.artist = refreshed.artist
                track.album = refreshed.album
                track.genre = refreshed.genre
                update_track(track)
            except Exception:
                continue
        self.accept()

    def _save_current_edits(self):
        track = self._tracks[self._index]
        tags = self._collect_new_tags()
        track._pending_new_tags = tags  # type: ignore[attr-defined]

    def _update_preview(self, old_tags: Dict[str, str], new_tags: Dict[str, str]):
        self.old_tags_view.setPlainText(format_tags(old_tags))
        self.new_tags_view.setPlainText(format_tags(new_tags))

    def _update_cover(self, track: Track):
        if track.artwork_path and Path(track.artwork_path).exists():
            pixmap = QtGui.QPixmap(track.artwork_path)
        else:
            pixmap = QtGui.QPixmap(120, 120)
            pixmap.fill(QtGui.QColor("#1a1f2e"))
        self.cover_label.setPixmap(pixmap)


def read_tags_from_track(track: Track) -> Dict[str, str]:
    return read_tags(Path(track.path))


def build_new_tags_from_track(track: Track) -> Dict[str, str]:
    tags = {}
    if track.title:
        tags["title"] = track.title
    if track.artist:
        tags["artist"] = track.artist
    if track.album:
        tags["album"] = track.album
    if track.genre:
        tags["genre"] = track.genre
    if track.bpm:
        tags["bpm"] = str(track.bpm)
    if track.key:
        tags["key"] = track.key
    if track.rating:
        tags["rating"] = str(track.rating)
    if track.mood:
        tags["mood"] = track.mood
    return tags


def diff_tags(old: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    diff: Dict[str, str] = {}
    keys = set(old.keys()) | set(new.keys())
    for key in keys:
        old_val = old.get(key, "")
        new_val = new.get(key, "")
        if old_val != new_val:
            diff[key] = new_val
    return diff


def format_tags(tags: Dict[str, str]) -> str:
    lines = [f"{k}: {v}" for k in order_tags(tags, tags) for v in [tags.get(k, "")]]
    return "\n".join(lines)


POPULAR_TAGS = [
    "title",
    "bpm",
    "key",
    "artist",
    "album",
    "genre",
    "date",
    "composer",
    "comment",
    "lyrics",
    "publisher",
    "albumartist",
    "tracknumber",
    "discnumber",
    "rating",
    "isrc",
    "grouping",
    "copyright",
    "remixer",
    "mood",
]


def order_tags(old: Dict[str, str], new: Dict[str, str]) -> list[str]:
    keys = list(dict.fromkeys(POPULAR_TAGS))
    for key in sorted(set(old.keys()) | set(new.keys())):
        if key not in keys:
            keys.append(key)
    return keys




