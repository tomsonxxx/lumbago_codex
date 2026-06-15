"""
ui/dj/views/eq_strip.py

EQStrip – 3 pasmowe EQ (LOW / MID / HI) — pionowe suwaki (BoothMetrics).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import BoothMetrics, get_slider_stylesheet, get_section_label_stylesheet

if TYPE_CHECKING:
    from ui.dj.deck_controller import DeckController


class EQStrip(QtWidgets.QWidget):
    """Pionowy 3-pasmowy EQ."""

    eq_changed = QtCore.pyqtSignal(float, float, float)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._controller: DeckController | None = None
        self._metrics = BoothMetrics(mode="deck_console")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self.low_slider = self._create_band("LOW")
        self.mid_slider = self._create_band("MID")
        self.high_slider = self._create_band("HI")

        layout.addWidget(self.low_slider)
        for slider, name in [
            (self.low_slider, "LOW"),
            (self.mid_slider, "MID"),
            (self.high_slider, "HI"),
        ]:
            slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            slider.customContextMenuRequested.connect(
                lambda pos, n=name, s=slider: self._show_eq_menu(pos, n, s)
            )
        layout.addWidget(self.mid_slider)
        layout.addWidget(self.high_slider)

        self.reset_to_flat()
        self.apply_metrics(self._metrics)

    def bind_controller(self, controller: DeckController) -> None:
        self._controller = controller

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        self._metrics = metrics
        h = metrics.eq_slider_height()
        ss = metrics.section_label_stylesheet()
        for band in (self.low_slider, self.mid_slider, self.high_slider):
            band.slider.setFixedHeight(h)  # type: ignore[attr-defined]
            band.band_label.setStyleSheet(ss)  # type: ignore[attr-defined]

    def _create_band(self, name: str) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(container)
        v.setSpacing(4)
        v.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(name)
        label.setStyleSheet(get_section_label_stylesheet())
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setStyleSheet(get_slider_stylesheet("vertical"))
        slider.valueChanged.connect(lambda _v: self._emit_current())

        v.addWidget(label)
        v.addWidget(slider, 1)
        v.addStretch()

        container.slider = slider  # type: ignore[attr-defined]
        container.band_label = label  # type: ignore[attr-defined]
        return container

    def _band_value(self, band_widget: QtWidgets.QWidget) -> float:
        return band_widget.slider.value() / 100.0  # type: ignore[attr-defined]

    def _set_band_value(self, band_widget: QtWidgets.QWidget, val: int) -> None:
        band_widget.slider.blockSignals(True)  # type: ignore[attr-defined]
        band_widget.slider.setValue(val)  # type: ignore[attr-defined]
        band_widget.slider.blockSignals(False)  # type: ignore[attr-defined]

    def _emit_current(self) -> None:
        low = self._band_value(self.low_slider)
        mid = self._band_value(self.mid_slider)
        high = self._band_value(self.high_slider)
        self.eq_changed.emit(low, mid, high)

    def reset_to_flat(self) -> None:
        for band in (self.low_slider, self.mid_slider, self.high_slider):
            self._set_band_value(band, 50)
        self.eq_changed.emit(0.5, 0.5, 0.5)

    def _apply_eq_values(self, low: float, mid: float, high: float) -> None:
        self._set_band_value(self.low_slider, int(low * 100))
        self._set_band_value(self.mid_slider, int(mid * 100))
        self._set_band_value(self.high_slider, int(high * 100))
        self.eq_changed.emit(low, mid, high)
        if self._controller:
            self._controller.set_eq(low, mid, high)

    def _show_eq_menu(self, pos, band_name: str, slider):
        menu = QtWidgets.QMenu(self)
        act_reset = menu.addAction(f"Reset {band_name}")
        act_kill = menu.addAction(f"{band_name} Kill (0%)")
        act_boost = menu.addAction(f"{band_name} Boost (100%)")
        menu.addSeparator()
        act_all = menu.addAction("Reset ALL EQ")
        chosen = menu.exec(slider.mapToGlobal(pos))
        if not chosen:
            return
        low = self._band_value(self.low_slider)
        mid = self._band_value(self.mid_slider)
        high = self._band_value(self.high_slider)
        if chosen == act_all:
            self.reset_to_flat()
            if self._controller:
                self._controller.set_eq(0.5, 0.5, 0.5)
            return
        target = {"LOW": low, "MID": mid, "HI": high}
        if chosen == act_reset:
            target[band_name] = 0.5
        elif chosen == act_kill:
            target[band_name] = 0.0
        elif chosen == act_boost:
            target[band_name] = 1.0
        else:
            return
        self._apply_eq_values(target["LOW"], target["MID"], target["HI"])

    def set_eq(self, low: float, mid: float, high: float) -> None:
        self._set_band_value(self.low_slider, int(low * 100))
        self._set_band_value(self.mid_slider, int(mid * 100))
        self._set_band_value(self.high_slider, int(high * 100))