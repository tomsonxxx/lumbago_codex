"""
ui/dj/views/pitch_control.py

PitchControl – suwak pitch + wartość procentowa + KEYLOCK (BoothMetrics).

Reused for minimal single Odtwarzacz pitch stub (Faza1 item3) in odtwarzacz_view.py:
- signals connected directly (no full DeckController bind needed for MVP single)
- compact hide handled in caller
- EFFECT tooltip set by odt: "EFEKT: zmienia tempo/pitch utworu (FILE load, STREAM playback)"
per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub, pitch_control + odt_view wiring + simple_controller, stub minimal slider KEYLOCK, compact aware)... must document identical.
No changes to dual/full paths. Minimal for single.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import (
    BoothMetrics,
    booth_toggle_text,
    get_slider_stylesheet,
    get_section_label_stylesheet,
    get_value_label_stylesheet,
    pro_button_stylesheet,
)

if TYPE_CHECKING:
    from ui.dj.deck_controller import DeckController


class PitchControl(QtWidgets.QWidget):
    """Kontrolka pitch (slider + label + keylock)."""

    pitch_changed = QtCore.pyqtSignal(int)
    keylock_toggled = QtCore.pyqtSignal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._controller: DeckController | None = None
        self._metrics = BoothMetrics(mode="deck_focused")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("PITCH")
        label.setStyleSheet(get_section_label_stylesheet())
        self._header_label = label
        self.value_label = QtWidgets.QLabel("0.0%")
        self.value_label.setStyleSheet(get_value_label_stylesheet())
        header.addWidget(label)
        header.addStretch()
        header.addWidget(self.value_label)
        layout.addLayout(header)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(-50, 50)
        self.slider.setValue(0)
        self.slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        self.keylock_btn = QtWidgets.QPushButton("KEY")
        self.keylock_btn.setCheckable(True)
        self.keylock_btn.clicked.connect(lambda checked: self.keylock_toggled.emit(checked))
        layout.addWidget(self.keylock_btn, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.slider.customContextMenuRequested.connect(self._show_pitch_menu)
        self.keylock_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.keylock_btn.customContextMenuRequested.connect(self._show_keylock_menu)

        self.apply_metrics(self._metrics)

    def bind_controller(self, controller: DeckController) -> None:
        self._controller = controller

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        self.slider.setFixedWidth(metrics.pitch_slider_width())
        w, h = metrics.pro_button_size()
        self.keylock_btn.setFixedSize(w, h)
        self.keylock_btn.setStyleSheet(pro_button_stylesheet(metrics, active=self.keylock_btn.isChecked()))
        self._header_label.setStyleSheet(metrics.section_label_stylesheet())
        self.value_label.setStyleSheet(metrics.value_label_stylesheet())

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
        self.keylock_btn.setStyleSheet(
            pro_button_stylesheet(self._metrics, active=enabled)
        )

    def _apply_pitch_preset(self, percent: int) -> None:
        self.set_pitch(percent)
        self.pitch_changed.emit(percent)
        if self._controller is not None:
            self._controller.set_pitch(float(percent))

    def _show_pitch_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_reset = menu.addAction("Reset (0%)")
        act_p6 = menu.addAction("Ustaw +6%")
        act_m6 = menu.addAction("Ustaw -6%")
        act_p12 = menu.addAction("Ustaw +12%")
        act_m12 = menu.addAction("Ustaw -12%")
        chosen = menu.exec(self.slider.mapToGlobal(pos))
        if not chosen:
            return
        if chosen == act_reset:
            self._apply_pitch_preset(0)
        elif chosen == act_p6:
            self._apply_pitch_preset(6)
        elif chosen == act_m6:
            self._apply_pitch_preset(-6)
        elif chosen == act_p12:
            self._apply_pitch_preset(12)
        elif chosen == act_m12:
            self._apply_pitch_preset(-12)

    def _show_keylock_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_on = menu.addAction("Włącz KEY")
        act_off = menu.addAction("Wyłącz KEY")
        act_toggle = menu.addAction("Przełącz")
        chosen = menu.exec(self.keylock_btn.mapToGlobal(pos))
        if not chosen:
            return
        if chosen == act_on:
            self.keylock_btn.setChecked(True)
            self.keylock_toggled.emit(True)
            if self._controller:
                self._controller.set_keylock(True)
        elif chosen == act_off:
            self.keylock_btn.setChecked(False)
            self.keylock_toggled.emit(False)
            if self._controller:
                self._controller.set_keylock(False)
        elif chosen == act_toggle:
            checked = not self.keylock_btn.isChecked()
            self.keylock_btn.setChecked(checked)
            self.keylock_toggled.emit(checked)
            if self._controller:
                self._controller.set_keylock(checked)