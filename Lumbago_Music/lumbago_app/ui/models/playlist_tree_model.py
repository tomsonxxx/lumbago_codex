"""
Lumbago Music AI — Model drzewa playlist (QAbstractItemModel)
=============================================================
"""

import logging
from typing import Any

from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex,
)

logger = logging.getLogger(__name__)


class PlaylistTreeModel(QAbstractItemModel):
    """
    Model drzewa playlist dla QTreeView.
    Obsługuje hierarchię folderów i playlist.
    """

    def __init__(self) -> None:
        super().__init__()
        self._roots: list[Any] = []
        self._reload()

    def _reload(self) -> None:
        """Przeładowuje drzewo z bazy."""
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.repository import PlaylistRepository
            with session_scope() as session:
                repo = PlaylistRepository(session)
                self._roots = list(repo.get_roots())
        except Exception as exc:
            logger.warning("Błąd ładowania playlist: %s", exc)
            self._roots = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self._roots)
        node = parent.internalPointer()
        return len(getattr(node, "children", []))

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            count = len(getattr(node, "tracks", []))
            return f"{node.name} ({count})" if count else node.name
        if role == Qt.ItemDataRole.DecorationRole:
            return None  # ikony w FAZIE 2
        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            if row < len(self._roots):
                return self.createIndex(row, column, self._roots[row])
            return QModelIndex()
        parent_node = parent.internalPointer()
        children = getattr(parent_node, "children", [])
        if row < len(children):
            return self.createIndex(row, column, children[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:  # type: ignore[override]
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        parent_node = getattr(node, "parent", None)
        if parent_node is None:
            return QModelIndex()
        # Znajdź pozycję parenta w jego rodzicu
        grandparent = getattr(parent_node, "parent", None)
        if grandparent is None:
            siblings = self._roots
        else:
            siblings = list(getattr(grandparent, "children", []))
        try:
            row = siblings.index(parent_node)
            return self.createIndex(row, 0, parent_node)
        except ValueError:
            return QModelIndex()
