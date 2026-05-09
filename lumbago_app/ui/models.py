from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.models import Track


class TrackTableModel(QtCore.QAbstractTableModel):
    headers = [
        "Tytuł",
        "Artysta",
        "Album",
        "Artysta albumu",
        "Rok",
        "Gatunek",
        "Kompozytor",
        "BPM",
        "Tonacja",
        "Nastrój",
        "Energia",
        "Komentarz",
        "Tekst",
        "ISRC",
        "Wydawca",
        "Grupa",
        "Prawa autorskie",
        "Remikser",
        "Głośność (LUFS)",
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

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        track = self._tracks[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return [
                track.title or "",
                track.artist or "",
                track.album or "",
                track.albumartist or "",
                track.year or "",
                track.genre or "",
                track.composer or "",
                _format_float(track.bpm, 1),
                track.key or "",
                track.mood or "",
                _format_float(track.energy, 2),
                track.comment or "",
                track.lyrics or "",
                track.isrc or "",
                track.publisher or "",
                track.grouping or "",
                track.copyright or "",
                track.remixer or "",
                _format_float(track.loudness_lufs, 1),
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
            ][index.column()]
        if role == QtCore.Qt.ItemDataRole.DecorationRole and index.column() == 0:
            if track.artwork_path:
                path = Path(track.artwork_path)
                if path.exists():
                    pixmap = QtGui.QPixmap(str(path))
                    if not pixmap.isNull():
                        return QtGui.QIcon(pixmap.scaled(96, 96, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return track
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
        painter.restore()

    def sizeHint(self, option, index: QtCore.QModelIndex) -> QtCore.QSize:
        return QtCore.QSize(140, 160)
