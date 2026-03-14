from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets


class AnimatedButton(QtWidgets.QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._base_color = QtGui.QColor("#101522")
        self._hover_color = QtGui.QColor("#1b2a3d")
        self._anim = QtCore.QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.valueChanged.connect(self._on_anim_value)

    def enterEvent(self, event):
        self._start_anim(self._base_color, self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._start_anim(self._hover_color, self._base_color)
        super().leaveEvent(event)

    def _start_anim(self, start: QtGui.QColor, end: QtGui.QColor):
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def _on_anim_value(self, value):
        color: QtGui.QColor = value
        self.setStyleSheet(
            f"background-color: {color.name()}; border-radius: 14px; padding: 8px 12px;"
        )
