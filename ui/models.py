from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets

from core.models import Track


class TrackTableModel(QtCore.QAbstractTableModel):
    headers = [
        "Tytuł",
        "Artysta",
        "Album",
        "Rok",
        "Gatunek",
        "BPM",
        "Tonacja",
        "Nastrój",
        "Energia",
        "Komentarz",
        "Tekst",
        "Remikser",
        "Czas",
        "Format",
        "Rozmiar",
        "Odtworzenia",
        "Ocena",
        "Cue In",
        "Cue Out",
        "Fingerprint",
        "Hash pliku",
        "Data dodania",
        "Data modyfikacji",
        "Okładka",
        "Waveform",
        "Ścieżka",
        "Tagi",
    ]

    def __init__(self, tracks: list[Track] | None = None):
        super().__init__()
        self._tracks = tracks or []
        self._now_playing: dict[str, str | None] = {"A": None, "B": None}  # deck -> path

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        track = self._tracks[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row_data = [
                track.title or "",
                track.artist or "",
                track.album or "",
                track.year or "",
                track.genre or "",
                _format_float(track.bpm, 1),
                track.key or "",
                track.mood or "",
                _format_float(track.energy, 2),
                track.comment or "",
                track.lyrics or "",
                track.remixer or "",
                _format_duration(track.duration),
                track.format or "",
                _format_size(track.file_size),
                _format_int(track.play_count),
                _format_int(track.rating),
                _format_ms(track.cue_in_ms),
                _format_ms(track.cue_out_ms),
                track.fingerprint or "",
                track.file_hash or "",
                _format_date(track.date_added),
                _format_date(track.date_modified),
                track.artwork_path or "",
                track.waveform_path or "",
                track.path,
                _format_tags(track.tags),
            ]
            if index.column() == 0:
                p = getattr(track, 'path', None)
                prefix = ""
                if p:
                    if self._now_playing.get("A") == p:
                        prefix += "▶A "
                    if self._now_playing.get("B") == p:
                        prefix += "▶B "
                return prefix + str(row_data[0])
            return row_data[index.column()]
        if role == QtCore.Qt.ItemDataRole.DecorationRole and index.column() == 0:
            if track.artwork_path:
                path = Path(track.artwork_path)
                if path.exists():
                    pixmap = QtGui.QPixmap(str(path))
                    if not pixmap.isNull():
                        return QtGui.QIcon(pixmap.scaled(96, 96, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return track
        if role == QtCore.Qt.ItemDataRole.BackgroundRole:
            p = getattr(track, 'path', None)
            if p:
                playing_a = self._now_playing.get("A") == p
                playing_b = self._now_playing.get("B") == p
                if playing_a and playing_b:
                    return QtGui.QColor("#2a1f3a")  # both decks (subtle purple)
                if playing_a:
                    return QtGui.QColor("#162a40")  # Deck A highlight (cool blue)
                if playing_b:
                    return QtGui.QColor("#1a3328")  # Deck B highlight (green tint)
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.headers[section]
        return str(section + 1)

    def update_tracks(self, tracks: list[Track]) -> None:
        self.beginResetModel()
        self._tracks = tracks
        self.endResetModel()

    def track_at(self, row: int) -> Track | None:
        if 0 <= row < len(self._tracks):
            return self._tracks[row]
        return None

    def set_now_playing(self, deck_a_path: str | None, deck_b_path: str | None) -> None:
        """Update which tracks are loaded in DJ Player decks for visual indicators."""
        self._now_playing = {"A": deck_a_path, "B": deck_b_path}
        if self._tracks:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self._tracks) - 1, len(self.headers) - 1)
            self.dataChanged.emit(top_left, bottom_right, [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.BackgroundRole])

    def mimeData(self, indexes):
        """Obsługa drag & drop - przekazujemy ścieżki plików."""
        from PyQt6.QtCore import QMimeData, QByteArray
        mime = QMimeData()
        paths = []
        for index in indexes:
            if index.column() == 0:  # tylko pierwsza kolumna, żeby nie duplikować
                track = self.track_at(index.row())
                if track:
                    paths.append(track.path)
        if paths:
            mime.setData("application/x-lumbago-track-paths", QByteArray(",".join(paths).encode()))
            # Dodatkowo standardowe URI dla kompatybilności
            urls = [f"file://{p}" for p in paths]
            mime.setUrls([QtCore.QUrl(u) for u in urls])
        return mime


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def _format_float(value: float | None, digits: int) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _format_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(int(value))


def _format_ms(value: int | None) -> str:
    if value is None:
        return ""
    seconds = int(value) // 1000
    return _format_duration(seconds)


def _format_size(value: int | None) -> str:
    if value is None:
        return ""
    size = float(value)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def _format_date(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")


def _format_tags(tags: list) -> str:
    if not tags:
        return ""
    return ", ".join(tag.value for tag in tags if tag.value)


class TrackGridDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, placeholder: QtGui.QPixmap):
        super().__init__()
        self.placeholder = placeholder
        self._now_playing: dict[str, str | None] = {"A": None, "B": None}

    def set_now_playing(self, deck_a_path: str | None, deck_b_path: str | None) -> None:
        self._now_playing = {"A": deck_a_path, "B": deck_b_path}

    def paint(self, painter: QtGui.QPainter, option, index: QtCore.QModelIndex):
        painter.save()
        rect = option.rect
        track: Track | None = index.data(QtCore.Qt.ItemDataRole.UserRole)
        title = track.title if track else ""
        artist = track.artist if track else ""

        icon = index.data(QtCore.Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QtGui.QIcon):
            pixmap = icon.pixmap(96, 96)
        else:
            pixmap = self.placeholder

        image_rect = QtCore.QRect(rect.x() + 8, rect.y() + 6, 96, 96)
        painter.drawPixmap(image_rect, pixmap)

        waveform_rect = QtCore.QRect(rect.x() + 8, rect.y() + 104, 96, 8)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#1f2a3d"))
        painter.drawRoundedRect(waveform_rect, 3, 3)
        painter.setBrush(QtGui.QColor("#39ff14"))
        if track and track.path:
            seed = abs(hash(track.path)) % 100
        else:
            seed = 42
        bars = 12
        bar_w = max(2, waveform_rect.width() // bars)
        for i in range(bars):
            height = (seed + i * 7) % 8 + 2
            x = waveform_rect.x() + i * bar_w + 1
            y = waveform_rect.y() + (waveform_rect.height() - height)
            painter.drawRect(x, y, bar_w - 2, height)

        text_rect = QtCore.QRect(rect.x() + 8, rect.y() + 108, rect.width() - 16, rect.height() - 112)
        painter.setPen(QtGui.QColor("#e8f8ff"))
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.TextFlag.TextWordWrap, title or "")

        painter.setPen(QtGui.QColor("#9aa6b2"))
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.TextFlag.TextWordWrap, artist or "")

        # Now playing badges for DJ Player integration (▶A / ▶B)
        p = getattr(track, 'path', None) if track else None
        if p:
            playing_a = self._now_playing.get("A") == p
            playing_b = self._now_playing.get("B") == p
            if playing_a or playing_b:
                badge = "▶ "
                if playing_a:
                    badge += "A"
                if playing_b:
                    badge += ("+" if playing_a else "") + "B"
                badge_rect = QtCore.QRect(rect.x() + rect.width() - 52, rect.y() + 6, 46, 16)
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QColor("#ff2d55" if (playing_a and not playing_b) else "#22c55e" if (playing_b and not playing_a) else "#a855f7"))
                painter.drawRoundedRect(badge_rect, 3, 3)
                painter.setPen(QtGui.QColor("#ffffff"))
                f2 = painter.font()
                f2.setPointSize(7)
                f2.setBold(True)
                painter.setFont(f2)
                painter.drawText(badge_rect, QtCore.Qt.AlignmentFlag.AlignCenter, badge)

        painter.restore()

    def sizeHint(self, option, index: QtCore.QModelIndex) -> QtCore.QSize:
        return QtCore.QSize(140, 160)
