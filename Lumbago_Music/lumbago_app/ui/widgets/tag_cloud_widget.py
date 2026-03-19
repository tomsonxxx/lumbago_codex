"""Lumbago Music AI — Widget chmury tagów."""

import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame

logger = logging.getLogger(__name__)


class TagCloud(QWidget):
    """Wyświetla tagi jako klikalne pigułki."""

    tag_removed = pyqtSignal(str)
    tag_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tags: list[str] = []
        self._editable: bool = True
        self._build_ui()

    def _build_ui(self) -> None:
        from PyQt6.QtWidgets import QVBoxLayout, QScrollArea
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._container = QWidget()
        self._container_layout = self._FlowLayout(self._container)
        scroll = QScrollArea()
        scroll.setWidget(self._container)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

    def set_tags(self, tags: list[str], editable: bool = True) -> None:
        """Ustawia listę tagów."""
        self._tags = tags
        self._editable = editable
        self._rebuild()

    def _rebuild(self) -> None:
        """Odbudowuje widgety tagów."""
        # Usuń stare widgety
        while self._container_layout.count():
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tag in self._tags:
            pill = self._TagPill(tag, removable=self._editable)
            pill.remove_clicked.connect(self._on_remove)
            pill.tag_clicked.connect(self.tag_clicked)
            self._container_layout.addWidget(pill)

    def _on_remove(self, tag: str) -> None:
        if tag in self._tags:
            self._tags.remove(tag)
            self._rebuild()
            self.tag_removed.emit(tag)

    class _FlowLayout(QHBoxLayout):
        """Uproszczony layout poziomy z zawijaniem — placeholder."""
        pass

    class _TagPill(QWidget):
        """Pigułka z tagiem."""
        remove_clicked = pyqtSignal(str)
        tag_clicked = pyqtSignal(str)

        def __init__(self, tag: str, removable: bool = True) -> None:
            super().__init__()
            layout = QHBoxLayout(self)
            layout.setContentsMargins(6, 2, 4, 2)
            layout.setSpacing(2)

            lbl = QLabel(tag)
            lbl.setStyleSheet("color: #00f5ff; font-size: 11px;")
            layout.addWidget(lbl)

            if removable:
                btn = QPushButton("×")
                btn.setFixedSize(14, 14)
                btn.setStyleSheet(
                    "QPushButton { color: #606070; border: none; font-size: 12px; }"
                    "QPushButton:hover { color: #ff4444; }"
                )
                btn.clicked.connect(lambda: self.remove_clicked.emit(tag))
                layout.addWidget(btn)

            self.setStyleSheet(
                "background: #00f5ff18; border: 1px solid #00f5ff44; "
                "border-radius: 10px;"
            )
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        def mousePressEvent(self, event: object) -> None:
            lbl = self.findChild(QLabel)
            if lbl:
                self.tag_clicked.emit(lbl.text())
