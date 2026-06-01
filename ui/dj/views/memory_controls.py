"""
MemoryControls — przyciski S (Save) / R (Recall) stanu decku.

Część redesignu. Proste, wyraźne, z tooltipami.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import get_button_stylesheet


class MemoryControls(QtWidgets.QWidget):
    save_requested = QtCore.pyqtSignal()
    recall_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.btn_save = QtWidgets.QPushButton("S")
        self.btn_save.setFixedSize(36, 28)
        self.btn_save.setToolTip("Zapisz aktualny stan decku (Memory Save)")
        self.btn_save.setStyleSheet(get_button_stylesheet("default"))
        self.btn_save.clicked.connect(self.save_requested.emit)

        self.btn_recall = QtWidgets.QPushButton("R")
        self.btn_recall.setFixedSize(36, 28)
        self.btn_recall.setToolTip("Przywołaj zapisany stan decku (Memory Recall)")
        self.btn_recall.setStyleSheet(get_button_stylesheet("default"))
        self.btn_recall.clicked.connect(self.recall_requested.emit)

        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_recall)
