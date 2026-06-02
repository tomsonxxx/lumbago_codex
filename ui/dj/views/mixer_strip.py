"""
MixerStrip — globalny mikser (Master + HP Cue + Crossfader + PFL).

Część redesignu w stylu Rekordbox (duży, czytelny crossfader, wyraźne A/B).
Używany zarówno w trybie Dual Console, jak i jako osobny pasek.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import (
    BOOTH_COLORS,
    get_button_stylesheet,
    get_slider_stylesheet,
)


class MixerStrip(QtWidgets.QFrame):
    """Pasek miksera górnego (master, cue, crossfader, PFL)."""

    master_changed = QtCore.pyqtSignal(int)
    hp_changed = QtCore.pyqtSignal(int)
    crossfader_changed = QtCore.pyqtSignal(int)
    pfl_changed = QtCore.pyqtSignal(str, bool)  # deck, enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        c = BOOTH_COLORS

        # MASTER
        layout.addWidget(QtWidgets.QLabel("MASTER"))
        self.master_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(85)
        self.master_slider.setFixedWidth(140)
        self.master_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.master_value = QtWidgets.QLabel("85")
        self.master_value.setFixedWidth(28)
        self.master_slider.valueChanged.connect(self._on_master_changed)
        layout.addWidget(self.master_slider)
        layout.addWidget(self.master_value)

        # Krok 6: menu PPM dla master
        self.master_slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.master_slider.customContextMenuRequested.connect(self._show_master_menu)

        layout.addSpacing(16)

        # HP CUE
        layout.addWidget(QtWidgets.QLabel("HP CUE"))
        self.hp_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hp_slider.setRange(0, 100)
        self.hp_slider.setValue(70)
        self.hp_slider.setFixedWidth(110)
        self.hp_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.hp_value = QtWidgets.QLabel("70")
        self.hp_value.setFixedWidth(24)
        self.hp_slider.valueChanged.connect(self._on_hp_changed)
        layout.addWidget(self.hp_slider)
        layout.addWidget(self.hp_value)

        # Krok 6: menu PPM dla HP Cue
        self.hp_slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.hp_slider.customContextMenuRequested.connect(self._show_hp_menu)

        layout.addSpacing(16)

        # PFL
        self.pfl_a = QtWidgets.QPushButton("PFL A")
        self.pfl_b = QtWidgets.QPushButton("PFL B")
        self.pfl_a.setCheckable(True)
        self.pfl_b.setCheckable(True)
        self.pfl_a.setFixedSize(56, 30)
        self.pfl_b.setFixedSize(56, 30)
        self.pfl_a.setStyleSheet(get_button_stylesheet("toggle"))
        self.pfl_b.setStyleSheet(get_button_stylesheet("toggle"))
        self.pfl_a.toggled.connect(lambda v: self.pfl_changed.emit("A", v))
        self.pfl_b.toggled.connect(lambda v: self.pfl_changed.emit("B", v))
        layout.addWidget(self.pfl_a)
        layout.addWidget(self.pfl_b)

        # Krok 6: menu PPM dla PFL buttons
        self.pfl_a.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.pfl_b.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.pfl_a.customContextMenuRequested.connect(lambda p: self._show_pfl_menu(p, "A"))
        self.pfl_b.customContextMenuRequested.connect(lambda p: self._show_pfl_menu(p, "B"))

        layout.addStretch(1)

        # CROSSFADER (duży, wyraźny)
        cross_box = QtWidgets.QHBoxLayout()
        cross_box.setSpacing(6)
        a_lbl = QtWidgets.QLabel("A")
        a_lbl.setStyleSheet(f"color: {c['accent']}; font-weight: 900; font-size: 14px;")
        cross_box.addWidget(a_lbl)

        self.crossfader = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.crossfader.setRange(0, 100)
        self.crossfader.setValue(50)
        self.crossfader.setMinimumHeight(32)
        self.crossfader.setStyleSheet(get_slider_stylesheet("horizontal"))
        cross_box.addWidget(self.crossfader, 1)

        # Krok 6: menu PPM dla crossfader
        self.crossfader.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.crossfader.customContextMenuRequested.connect(self._show_crossfader_menu)

        b_lbl = QtWidgets.QLabel("B")
        b_lbl.setStyleSheet(f"color: {c['accent']}; font-weight: 900; font-size: 14px;")
        cross_box.addWidget(b_lbl)

        self.crossfader.valueChanged.connect(self.crossfader_changed.emit)

        layout.addLayout(cross_box)

    def _on_master_changed(self, v: int):
        self.master_value.setText(str(v))
        self.master_changed.emit(v)

    def _on_hp_changed(self, v: int):
        self.hp_value.setText(str(v))
        self.hp_changed.emit(v)

    def set_master(self, value: int):
        self.master_slider.blockSignals(True)
        self.master_slider.setValue(value)
        self.master_slider.blockSignals(False)
        self.master_value.setText(str(value))

    def set_hp(self, value: int):
        self.hp_slider.blockSignals(True)
        self.hp_slider.setValue(value)
        self.hp_slider.blockSignals(False)
        self.hp_value.setText(str(value))

    def set_crossfader(self, value: int):
        self.crossfader.blockSignals(True)
        self.crossfader.setValue(value)
        self.crossfader.blockSignals(False)

    def _show_master_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Reset do 85")
        menu.addAction("Ustaw 100")
        menu.addAction("Ustaw 50")
        menu.addAction("Mute Master")
        menu.exec(self.master_slider.mapToGlobal(pos))

    def _show_hp_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Reset do 70")
        menu.addAction("Ustaw 100")
        menu.addAction("Mute Cue")
        menu.exec(self.hp_slider.mapToGlobal(pos))

    def _show_pfl_menu(self, pos, deck: str):
        menu = QtWidgets.QMenu(self)
        menu.addAction(f"Toggle PFL {deck}")
        menu.addAction(f"Reset PFL {deck}")
        menu.exec((self.pfl_a if deck == "A" else self.pfl_b).mapToGlobal(pos))

    def _show_crossfader_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Wyśrodkuj (50)")
        menu.addAction("Pełne A (0)")
        menu.addAction("Pełne B (100)")
        menu.addSeparator()
        menu.addAction("Reset curve")
        menu.exec(self.crossfader.mapToGlobal(pos))
