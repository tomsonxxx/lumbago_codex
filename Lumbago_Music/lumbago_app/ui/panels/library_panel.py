"""
Lumbago Music AI — Panel biblioteki (tabela utworów)
=====================================================
Główna tabela wszystkich utworów z sortowaniem i filtrem.
"""

import logging

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QAbstractItemView

logger = logging.getLogger(__name__)


class LibraryPanel(QWidget):
    """Panel z tabelą wszystkich utworów biblioteki."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._table = QTableView()
        self._table.setObjectName("libraryTable")
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._table.setSortingEnabled(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self._table)
        self._load_model()

    def _load_model(self) -> None:
        """Ładuje model danych do tabeli."""
        try:
            from lumbago_app.ui.models.track_table_model import TrackTableModel
            self._model = TrackTableModel()
            self._proxy = QSortFilterProxyModel()
            self._proxy.setSourceModel(self._model)
            self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._table.setModel(self._proxy)
            self._model.reload()
        except Exception as exc:
            logger.warning("Błąd ładowania modelu tabeli: %s", exc)

    def set_filter(self, text: str) -> None:
        """Ustawia filtr tekstowy na proxy modelu."""
        if hasattr(self, "_proxy"):
            self._proxy.setFilterFixedString(text)

    def _on_context_menu(self, pos: object) -> None:
        """Wyświetla menu kontekstowe dla zaznaczonego wiersza."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu(self)

        act_tag = menu.addAction("✦ Taguj przez AI")
        act_analyze = menu.addAction("⚙ Analizuj audio")
        menu.addSeparator()
        act_edit = menu.addAction("✎ Edytuj metadane")
        act_delete = menu.addAction("✕ Usuń z biblioteki")

        action = menu.exec(self._table.mapToGlobal(pos))  # type: ignore[arg-type]
        logger.debug("Context menu: %s", action.text() if action else "brak")
