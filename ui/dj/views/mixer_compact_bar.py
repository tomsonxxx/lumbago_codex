"""
ui/dj/views/mixer_compact_bar.py

Kompaktowy pasek miksera w stylu Pioneer weDJ — jeden rząd:
Deck A transport | crossfader (max ~240px) | Deck B transport | MASTER | CUE HP

Per SZPIEG_DJ_Player_Redesign_2026.md binding.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from services.playback import PlaybackEngine
from ui.dj.deck_controller import DeckController
from ui.dj.deck_layout import apply_transport_button_metrics
from ui.dj.styles import (
    BoothMetrics,
    booth_toggle_text,
    deck_channel_badge_stylesheet,
    get_mixer_panel_stylesheet,
    get_slider_stylesheet,
)


class _MiniTransport(QtWidgets.QWidget):
    """CUE | PLAY | STOP — kompaktowy klaster per deck."""

    play_clicked = QtCore.pyqtSignal()
    stop_clicked = QtCore.pyqtSignal()
    cue_pressed = QtCore.pyqtSignal()
    cue_released = QtCore.pyqtSignal()

    def __init__(self, deck_label: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._metrics = BoothMetrics(mode="dual_mixer")
        self._playing = False
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(self._metrics.px(6))

        badge = QtWidgets.QLabel(booth_toggle_text(f"deck_{deck_label.lower()}"))
        badge.setStyleSheet(deck_channel_badge_stylesheet(self._metrics))
        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.play_btn = QtWidgets.QPushButton("▶")
        self.stop_btn = QtWidgets.QPushButton("■")

        for btn in (self.cue_btn, self.play_btn, self.stop_btn):
            btn.setFixedHeight(self._metrics.px(32))

        row.addWidget(badge, 0)
        row.addWidget(self.cue_btn, 0)
        row.addWidget(self.play_btn, 0)
        row.addWidget(self.stop_btn, 0)

        self.play_btn.clicked.connect(self.play_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.cue_btn.pressed.connect(self.cue_pressed.emit)
        self.cue_btn.released.connect(self.cue_released.emit)

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        apply_transport_button_metrics(
            metrics, self.cue_btn, self.play_btn, self.stop_btn, playing=self._playing, compact=True
        )

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        apply_transport_button_metrics(
            self._metrics,
            self.cue_btn,
            self.play_btn,
            self.stop_btn,
            playing=self._playing,
            compact=True,
        )


class MixerCompactBar(QtWidgets.QFrame):
    """
    Pasek miksera weDJ: transport A | XF | transport B | master | cue.
    Crossfader ma sztywny max width — nie pożera panelu.
    """

    def __init__(
        self,
        controller_a: DeckController,
        controller_b: DeckController,
        playback_engine: PlaybackEngine | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("MixerPanel")
        self.setStyleSheet(get_mixer_panel_stylesheet())
        self.controller_a = controller_a
        self.controller_b = controller_b
        self.playback_engine = playback_engine
        self._metrics = BoothMetrics(mode="dual_mixer")
        self._setup_ui()
        self._wire()

    def _setup_ui(self) -> None:
        m = self._metrics
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(m.px(10), m.px(6), m.px(10), m.px(6))
        root.setSpacing(m.px(12))

        self.transport_a = _MiniTransport("a")
        root.addWidget(self.transport_a, 0)

        xf_box = QtWidgets.QVBoxLayout()
        xf_box.setSpacing(2)
        xf_lbl = QtWidgets.QLabel("XF")
        xf_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        xf_lbl.setStyleSheet(m.section_label_stylesheet())
        self.crossfader = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.crossfader.setRange(0, 100)
        self.crossfader.setValue(50)
        self.crossfader.setFixedWidth(m.crossfader_max_width())
        self.crossfader.setFixedHeight(m.crossfader_height())
        self.crossfader.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.crossfader.setToolTip("Crossfader A ↔ B")
        xf_box.addWidget(xf_lbl)
        xf_box.addWidget(self.crossfader)
        root.addLayout(xf_box, 0)

        self.transport_b = _MiniTransport("b")
        root.addWidget(self.transport_b, 0)

        root.addSpacing(m.px(16))

        master_box = self._vol_column("MASTER", default=85)
        self.master_slider = master_box["slider"]
        self.master_val = master_box["label"]
        root.addLayout(master_box["layout"], 0)

        cue_box = self._vol_column("CUE", default=70)
        self.cue_slider = cue_box["slider"]
        self.cue_val = cue_box["label"]
        root.addLayout(cue_box["layout"], 0)

        root.addStretch(1)

        self.apply_metrics(m)

    def _vol_column(self, title: str, *, default: int) -> dict:
        m = self._metrics
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(2)
        lbl = QtWidgets.QLabel(title)
        lbl.setStyleSheet(m.section_label_stylesheet())
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(default)
        slider.setFixedWidth(m.mixer_slider_width(cue=title == "CUE"))
        slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        val = QtWidgets.QLabel(str(default))
        val.setStyleSheet(m.value_label_stylesheet())
        val.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        col.addWidget(lbl)
        col.addWidget(slider)
        col.addWidget(val)
        return {"layout": col, "slider": slider, "label": val}

    def _wire(self) -> None:
        ta, tb = self.transport_a, self.transport_b
        ca, cb = self.controller_a, self.controller_b

        ta.play_clicked.connect(ca.toggle_play)
        ta.stop_clicked.connect(ca.stop)
        self._wire_cue(ta, ca)

        tb.play_clicked.connect(cb.toggle_play)
        tb.stop_clicked.connect(cb.stop)
        self._wire_cue(tb, cb)

        ca.play_state_changed.connect(ta.set_playing)
        cb.play_state_changed.connect(tb.set_playing)

        self.crossfader.valueChanged.connect(self._on_crossfader)
        self.master_slider.valueChanged.connect(self._on_master)
        self.cue_slider.valueChanged.connect(self._on_cue)

    def _wire_cue(self, transport: _MiniTransport, controller: DeckController) -> None:
        class _Host(QtWidgets.QWidget):
            pass

        host = _Host()
        host._skip_cue_release = False  # type: ignore[attr-defined]

        def on_pressed() -> None:
            mods = QtWidgets.QApplication.keyboardModifiers()
            if mods & QtCore.Qt.KeyboardModifier.ShiftModifier:
                host._skip_cue_release = True  # type: ignore[attr-defined]
                controller.set_cue_at_playhead()
                return
            host._skip_cue_release = False  # type: ignore[attr-defined]
            controller.cue_pressed()

        def on_released() -> None:
            if getattr(host, "_skip_cue_release", False):
                host._skip_cue_release = False  # type: ignore[attr-defined]
                return
            controller.cue_released()

        transport.cue_pressed.connect(on_pressed)
        transport.cue_released.connect(on_released)

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        self.crossfader.setFixedWidth(metrics.crossfader_max_width())
        self.crossfader.setFixedHeight(metrics.crossfader_height())
        self.master_slider.setFixedWidth(metrics.mixer_slider_width())
        self.cue_slider.setFixedWidth(metrics.mixer_slider_width(cue=True))
        self.transport_a.apply_metrics(metrics)
        self.transport_b.apply_metrics(metrics)

    def _on_crossfader(self, value: int) -> None:
        if not self.playback_engine:
            return
        pos = (value / 50.0) - 1.0
        try:
            self.playback_engine.set_crossfader(pos)
        except Exception:
            pass

    def _on_master(self, value: int) -> None:
        self.master_val.setText(str(value))
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(value / 100.0)
            except Exception:
                pass

    def _on_cue(self, value: int) -> None:
        self.cue_val.setText(str(value))
        if self.playback_engine:
            try:
                self.playback_engine.set_cue_volume(value / 100.0)
            except Exception:
                pass

    def apply_initial_values(self) -> None:
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(0.85)
                self.playback_engine.set_crossfader(0.0)
                self.playback_engine.set_cue_volume(0.70)
            except Exception:
                pass
        self.master_val.setText("85")
        self.cue_val.setText("70")


__all__ = ["MixerCompactBar"]