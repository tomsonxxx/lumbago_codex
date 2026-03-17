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
        "Rok",
        "Gatunek",
        "BPM",
        "Tonacja",
        "Nastrój",
        "Energia",
        "Głośność (LUFS)",
        "Czas",
        "Format",
        "Bitrate",
        "Sample rate",
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
        "Status",
    ]

    def __init__(self, tracks: list[Track] | None = None):
        super().__init__()
        self._tracks = tracks or []
        self._now_playing: str | None = None

    def set_now_playing(self, path: str | None) -> None:
        self._now_playing = path
        self.layoutChanged.emit()

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
                track.year or "",
                track.genre or "",
                _format_float(track.bpm, 1),
                track.key or "",
                track.mood or "",
                _format_float(track.energy, 2),
                _format_float(track.loudness_lufs, 1),
                _format_duration(track.duration),
                track.format or "",
                _format_int(track.bitrate),
                _format_int(track.sample_rate),
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
        if role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Now Playing ma najwyższy priorytet
            if self._now_playing and track.path == self._now_playing:
                return QtGui.QColor(0, 80, 60)       # ciemnozielony — odtwarzany
            energy = track.energy
            if energy is not None:
                if energy >= 0.7:
                    return QtGui.QColor(50, 18, 8)   # ciepły czerwono-pomarańczowy — wysoka energia
                elif energy >= 0.5:
                    return QtGui.QColor(18, 35, 18)  # zielonkawy — średnia energia
                elif energy <= 0.3:
                    return QtGui.QColor(8, 18, 40)   # niebieski — niska energia
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


class StarRatingDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate rysujący gwiazdki 0-5 w kolumnie Ocena i pozwalający na edycję kliknięciem."""

    _STAR_FULL = "★"
    _STAR_EMPTY = "☆"
    MAX = 5

    def paint(self, painter: QtGui.QPainter, option, index: QtCore.QModelIndex):
        painter.save()
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        try:
            rating = int(index.data(QtCore.Qt.ItemDataRole.DisplayRole) or 0)
        except (ValueError, TypeError):
            rating = 0
        stars = self._STAR_FULL * rating + self._STAR_EMPTY * (self.MAX - rating)
        color = QtGui.QColor("#ffd700") if rating > 0 else QtGui.QColor("#555")
        painter.setPen(color)
        painter.drawText(option.rect, QtCore.Qt.AlignmentFlag.AlignCenter, stars)
        painter.restore()

    def sizeHint(self, option, index: QtCore.QModelIndex) -> QtCore.QSize:
        return QtCore.QSize(90, option.rect.height() or 24)

    def editorEvent(self, event, model, option, index: QtCore.QModelIndex) -> bool:
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            x = event.pos().x() - option.rect.x()
            star_w = option.rect.width() / self.MAX
            clicked_star = min(self.MAX, max(1, int(x / star_w) + 1))
            try:
                current = int(model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) or 0)
            except (ValueError, TypeError):
                current = 0
            # Kliknięcie tej samej gwiazdki co bieżąca ocena zeruje ją
            new_rating = 0 if clicked_star == current else clicked_star
            # Pobierz track i zaktualizuj przez source model
            track = model.data(index, QtCore.Qt.ItemDataRole.UserRole)
            if track is not None:
                from lumbago_app.data.repository import update_track
                track.rating = new_rating
                update_track(track)
                src = model.sourceModel() if hasattr(model, "sourceModel") else model
                src_idx = model.mapToSource(index) if hasattr(model, "mapToSource") else index
                src.dataChanged.emit(src_idx, src_idx, [QtCore.Qt.ItemDataRole.DisplayRole])
            return True
        return False


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

        text_rect = QtCore.QRect(rect.x() + 8, rect.y() + 106, rect.width() - 16, rect.height() - 110)
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
