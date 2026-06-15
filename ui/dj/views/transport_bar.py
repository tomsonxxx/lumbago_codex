"""
ui/dj/views/transport_bar.py

TransportBar – duże przyciski PLAY / CUE / STOP (BoothMetrics + CDJ CUE hold).
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from typing import TYPE_CHECKING

from ui.dj.deck_layout import apply_transport_button_metrics
from ui.dj.styles import (
    BoothMetrics,
    booth_transport_text,
    get_transport_button_stylesheet,
    get_time_label_stylesheet,
)

if TYPE_CHECKING:
    from ui.dj.deck_controller import DeckController


class TransportBar(QtWidgets.QWidget):
    """
    Pasek transportu (duże przyciski booth).

    Sygnały:
    - play_clicked()
    - cue_pressed() / cue_released() — CDJ podgląd CUE
    - stop_clicked()
    """

    play_clicked = QtCore.pyqtSignal()
    cue_pressed = QtCore.pyqtSignal()
    cue_released = QtCore.pyqtSignal()
    stop_clicked = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._metrics = BoothMetrics(mode="deck_focused")
        self._playing = False
        self._controller: DeckController | None = None

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(self._metrics.transport_gap())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        self.play_btn = QtWidgets.QPushButton(booth_transport_text("play"))
        self.cue_btn = QtWidgets.QPushButton(booth_transport_text("cue"))
        self.stop_btn = QtWidgets.QPushButton(booth_transport_text("stop"))

        self.play_btn.clicked.connect(self.play_clicked)
        self.cue_btn.pressed.connect(self.cue_pressed)
        self.cue_btn.released.connect(self.cue_released)
        self.stop_btn.clicked.connect(self.stop_clicked)

        layout.addWidget(self.cue_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch(1)

        self._setup_context_menus()

        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_label.hide()

        self.apply_metrics(self._metrics)

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        apply_transport_button_metrics(
            metrics,
            self.cue_btn,
            self.play_btn,
            self.stop_btn,
            playing=self._playing,
        )
        if self.time_label.isHidden():
            self.time_label.setStyleSheet(metrics.time_stylesheet())
        layout = self.layout()
        if layout is not None:
            layout.setSpacing(metrics.transport_gap())

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        apply_transport_button_metrics(
            self._metrics,
            self.cue_btn,
            self.play_btn,
            self.stop_btn,
            playing=self._playing,
        )

    def set_time_text(self, text: str) -> None:
        self.time_label.setText(text)

    def bind_controller(self, controller: DeckController) -> None:
        """Podłącz menu PPM play/cue/stop do DeckController."""
        self._controller = controller

    def _setup_context_menus(self) -> None:
        self.play_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.play_btn.customContextMenuRequested.connect(self._show_play_menu)
        self.cue_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.cue_btn.customContextMenuRequested.connect(self._show_cue_menu)
        self.stop_btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.stop_btn.customContextMenuRequested.connect(self._show_stop_menu)

    def _show_play_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_cue = menu.addAction("Odtwórz od CUE")
        act_start = menu.addAction("Odtwórz od początku")
        act_here = menu.addAction("Odtwórz od aktualnej pozycji")
        chosen = menu.exec(self.play_btn.mapToGlobal(pos))
        ctrl = self._controller
        if not chosen or ctrl is None:
            return
        if chosen == act_cue:
            ctrl.play_from_cue()
        elif chosen == act_start:
            ctrl.play_from_start()
        elif chosen == act_here:
            ctrl.play()

    def _show_cue_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_set = menu.addAction("Ustaw CUE w aktualnej pozycji")
        act_jump = menu.addAction("Skocz do CUE")
        act_clear = menu.addAction("Wyczyść CUE")
        chosen = menu.exec(self.cue_btn.mapToGlobal(pos))
        ctrl = self._controller
        if not chosen or ctrl is None:
            return
        if chosen == act_set:
            ctrl.set_cue_at_playhead()
        elif chosen == act_jump:
            ctrl.jump_to_cue()
        elif chosen == act_clear:
            ctrl.clear_cue()

    def _show_stop_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_cue = menu.addAction("Stop + powrót do CUE")
        act_zero = menu.addAction("Stop + powrót do 0")
        act_hold = menu.addAction("Tylko Stop")
        chosen = menu.exec(self.stop_btn.mapToGlobal(pos))
        ctrl = self._controller
        if not chosen or ctrl is None:
            return
        if chosen == act_cue:
            ctrl.stop()
        elif chosen == act_zero:
            ctrl.stop_at_zero()
        elif chosen == act_hold:
            ctrl.stop_hold_position()