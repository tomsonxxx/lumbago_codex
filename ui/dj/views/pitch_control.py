"""
ui/dj/views/pitch_control.py

PitchControl – suwak pitch + wartość procentowa + KEYLOCK.

Prosta wersja szkieletowa (faza 1).
Używa helperów styles + BOOTH_SIZES.
Sygnały do podłączenia z DeckController.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import (
    BOOTH_SIZES,
    get_slider_stylesheet,
    get_section_label_stylesheet,
    get_value_label_stylesheet,
)


class PitchControl(QtWidgets.QWidget):
    """
    Kontrolka pitch (poziomy slider + label + keylock).

    Sygnały:
    - pitch_changed(percent: int)
    - keylock_toggled(enabled: bool)
    """

    pitch_changed = QtCore.pyqtSignal(int)
    keylock_toggled = QtCore.pyqtSignal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        # Nagłówek
        header = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("PITCH")
        label.setStyleSheet(get_section_label_stylesheet())
        self.value_label = QtWidgets.QLabel("0.0%")
        self.value_label.setStyleSheet(get_value_label_stylesheet())
        header.addWidget(label)
        header.addStretch()
        header.addWidget(self.value_label)
        layout.addLayout(header)

        # Slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(-50, 50)
        self.slider.setValue(0)
        self.slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        width = BOOTH_SIZES.get("pitch_slider_width", 180)
        self.slider.setFixedWidth(width)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        # Keylock toggle (prosty przycisk)
        self.keylock_btn = QtWidgets.QPushButton("KEY")
        self.keylock_btn.setCheckable(True)
        self.keylock_btn.setFixedSize(52, 32)
        self.keylock_btn.clicked.connect(
            lambda checked: self.keylock_toggled.emit(checked)
        )
        layout.addWidget(self.keylock_btn, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        # PPM menu na sliderze i KEY (Krok 5)
        self.slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.slider.customContextMenuRequested.connect(self._show_pitch_menu)
        self.keylock_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.keylock_btn.customContextMenuRequested.connect(self._show_keylock_menu)

    def _on_value_changed(self, value: int) -> None:
        self.value_label.setText(f"{value}%")
        self.pitch_changed.emit(value)

    def set_pitch(self, percent: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(percent)
        self.slider.blockSignals(False)
        self.value_label.setText(f"{percent}%")

    def set_keylock(self, enabled: bool) -> None:
        self.keylock_btn.setChecked(enabled)

    def _show_pitch_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Reset (0%)")
        menu.addAction("Ustaw +6%")
        menu.addAction("Ustaw -6%")
        menu.addAction("Ustaw +12%")
        menu.addAction("Ustaw -12%")
        menu.exec(self.slider.mapToGlobal(pos))

    def _show_keylock_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Włącz KEY")
        menu.addAction("Wyłącz KEY")
        menu.addSeparator()
        menu.addAction("Przełącz")
        menu.exec(self.keylock_btn.mapToGlobal(pos))
