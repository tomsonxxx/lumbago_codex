from __future__ import annotations

from pathlib import Path
from PyQt6 import QtCore, QtGui, QtWidgets


class _DialogFadeFilter(QtCore.QObject):
    def __init__(self, dialog: QtWidgets.QDialog, anim: QtCore.QPropertyAnimation):
        super().__init__(dialog)
        self._dialog = dialog
        self._anim = anim

    def eventFilter(self, obj, event):
        if obj is self._dialog and event.type() == QtCore.QEvent.Type.Show:
            self._dialog.setWindowOpacity(0.0)
            self._anim.stop()
            self._anim.start()
        return super().eventFilter(obj, event)


def apply_dialog_fade(dialog: QtWidgets.QDialog, duration_ms: int = 180) -> None:
    dialog.setSizeGripEnabled(True)
    dialog.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, True)
    anim = QtCore.QPropertyAnimation(dialog, b"windowOpacity", dialog)
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

    filt = _DialogFadeFilter(dialog, anim)
    dialog.installEventFilter(filt)

    # Zachowaj referencje, by nie zostały zebrane przez GC.
    dialog._fade_anim = anim  # type: ignore[attr-defined]
    dialog._fade_filter = filt  # type: ignore[attr-defined]


def apply_window_fade(widget: QtWidgets.QWidget, duration_ms: int = 220) -> None:
    anim = QtCore.QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

    filt = _DialogFadeFilter(widget, anim)
    widget.installEventFilter(filt)

    widget._fade_anim = anim  # type: ignore[attr-defined]
    widget._fade_filter = filt  # type: ignore[attr-defined]


class AnimatedButton(QtWidgets.QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._base_color = QtGui.QColor("#141a2a")
        self._hover_color = QtGui.QColor("#1f2a3d")
        self._anim = QtCore.QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.valueChanged.connect(self._on_anim_value)
        self._pulse_anim: QtCore.QPropertyAnimation | None = None

    def enterEvent(self, event):
        if self.objectName() not in {"PrimaryAction", "AutoTagApi", "AutoTagSearch", "DangerAction"}:
            self._start_anim(self._base_color, self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.objectName() not in {"PrimaryAction", "AutoTagApi", "AutoTagSearch", "DangerAction"}:
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
            "color: #e8f3ff; "
            f"background-color: {color.name()}; "
            "border: 1px solid #2b3a55; "
            "border-radius: 12px; "
            "padding: 8px 12px;"
        )

    def enable_pulse(self, intensity: int = 18) -> None:
        if self._pulse_anim is not None:
            return
        effect = QtWidgets.QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(6)
        effect.setOffset(0, 0)
        effect.setColor(QtGui.QColor("#63f2ff"))
        self.setGraphicsEffect(effect)

        anim = QtCore.QPropertyAnimation(effect, b"blurRadius", self)
        anim.setStartValue(6)
        anim.setEndValue(max(10, intensity))
        anim.setDuration(1400)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
        anim.setLoopCount(-1)
        anim.setDirection(QtCore.QAbstractAnimation.Direction.Forward)
        anim.start()
        self._pulse_anim = anim


def dialog_icon_pixmap(size: int = 18) -> QtGui.QPixmap:
    icon_path = Path(__file__).resolve().parent / "assets" / "icons" / "dialog.svg"
    pix = QtGui.QPixmap(str(icon_path))
    if pix.isNull():
        return QtGui.QPixmap()
    return pix.scaled(
        size,
        size,
        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation,
    )
