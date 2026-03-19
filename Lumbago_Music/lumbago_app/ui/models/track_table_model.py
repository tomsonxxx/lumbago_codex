"""
Lumbago Music AI — Model tabeli utworów (QAbstractTableModel)
==============================================================
"""

import logging
from typing import Any

from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, pyqtSignal
)
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)

# Kolumny tabeli
COLUMNS = [
    ("artist",      "Artysta",    200),
    ("title",       "Tytuł",      220),
    ("album",       "Album",      160),
    ("genre",       "Gatunek",    110),
    ("bpm",         "BPM",        60),
    ("key_camelot", "Tonacja",    65),
    ("duration",    "Czas",       60),
    ("year",        "Rok",        50),
    ("rating",      "Ocena",      55),
    ("energy_level","Energia",    60),
]


class TrackTableModel(QAbstractTableModel):
    """
    Model tabeli dla QTableView — wyświetla TrackOrm z bazy.
    Obsługuje sortowanie przez QSortFilterProxyModel.
    """

    tracks_loaded = pyqtSignal(int)  # emituje liczbę załadowanych rekordów

    def __init__(self) -> None:
        super().__init__()
        self._tracks: list[Any] = []

    def reload(self, search_params: dict | None = None) -> None:
        """Przeładowuje dane z bazy."""
        self.beginResetModel()
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.repository import TrackRepository

            with session_scope() as session:
                repo = TrackRepository(session)
                if search_params:
                    self._tracks = list(repo.search(**search_params))
                else:
                    self._tracks = list(repo.get_all(limit=5000))
            logger.debug("TrackTableModel: załadowano %d rekordów", len(self._tracks))
            self.tracks_loaded.emit(len(self._tracks))
        except Exception as exc:
            logger.warning("Błąd ładowania danych do tabeli: %s", exc)
            self._tracks = []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._tracks):
            return None

        track = self._tracks[index.row()]
        col_field, _, _ = COLUMNS[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            value = getattr(track, col_field, None)
            if value is None:
                return ""
            if col_field == "bpm":
                return f"{value:.1f}" if value else ""
            if col_field == "duration":
                from lumbago_app.core.utils import format_duration
                return format_duration(float(value))
            if col_field == "rating":
                return "★" * int(value) if value else ""
            return str(value)

        if role == Qt.ItemDataRole.UserRole:
            return track.id

        if role == Qt.ItemDataRole.ForegroundRole:
            if col_field == "key_camelot":
                return QColor("#00f5ff") if track.key_camelot else QColor("#404050")
            if col_field == "bpm":
                return QColor("#c0c060")
            return None

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and section < len(COLUMNS):
            return COLUMNS[section][1]
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sortuje dane po kolumnie."""
        if column >= len(COLUMNS):
            return
        field, _, _ = COLUMNS[column]
        reverse = order == Qt.SortOrder.DescendingOrder
        self.beginResetModel()
        self._tracks.sort(
            key=lambda t: (getattr(t, field) is None, getattr(t, field) or ""),
            reverse=reverse,
        )
        self.endResetModel()
