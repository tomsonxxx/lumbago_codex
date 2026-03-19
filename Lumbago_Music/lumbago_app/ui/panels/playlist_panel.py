"""Lumbago Music AI — Panel playlist (drzewo)."""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QLabel
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class PlaylistPanel(QWidget):
    """Panel drzewa playlist z folderami."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("PLAYLISTY")
        header.setStyleSheet(
            "color: #606070; font-size: 10px; font-weight: bold; "
            "padding: 6px 8px; letter-spacing: 1px;"
        )
        layout.addWidget(header)

        self._tree = QTreeView()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self._tree, stretch=1)

        self._load_model()

    def _load_model(self) -> None:
        """Ładuje model drzewa playlist."""
        try:
            from lumbago_app.ui.models.playlist_tree_model import PlaylistTreeModel
            self._model = PlaylistTreeModel()
            self._tree.setModel(self._model)
        except Exception as exc:
            logger.warning("Błąd ładowania modelu playlist: %s", exc)
