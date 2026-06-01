"""
ui/dj/views/eq_strip.py

EQStrip – 3 pasmowe EQ (LOW / MID / HI) – pionowe suwaki.

Prosta wersja szkieletowa (faza 1).
Gotowa do podłączenia z DeckController.set_eq(low, mid, high).

Używa wyłącznie stylów z styles.py.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.styles import BOOTH_SIZES, get_slider_stylesheet, get_section_label_stylesheet


class EQStrip(QtWidgets.QWidget):
    """
    Pionowy 3-pasmowy EQ.

    Sygnał:
    - eq_changed(low: float, mid: float, high: float) – wartości 0.0-1.0
    """

    eq_changed = QtCore.pyqtSignal(float, float, float)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self.low_slider = self._create_band("LOW")
        self.mid_slider = self._create_band("MID")
        self.high_slider = self._create_band("HI")

        layout.addWidget(self.low_slider)

        # PPM na każdym paśmie (Krok 5/6)
        for slider, name in [(self.low_slider, "LOW"), (self.mid_slider, "MID"), (self.high_slider, "HI")]:
            slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            slider.customContextMenuRequested.connect(lambda pos, n=name, s=slider: self._show_eq_menu(pos, n, s))
        layout.addWidget(self.mid_slider)
        layout.addWidget(self.high_slider)

        # Domyślnie flat (0.5)
        self.reset_to_flat()

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
        eq_h = BOOTH_SIZES.get("eq_slider_height", 100)
        slider.setFixedHeight(eq_h)

        # Przekazujemy sygnał z wartościami znormalizowanymi
        def on_change(val: int):
            self._emit_current()

        slider.valueChanged.connect(on_change)

        v.addWidget(label)
        v.addWidget(slider, 1)
        v.addStretch()

        # Zapamiętujemy slider w kontenerze (łatwy dostęp)
        container.slider = slider  # type: ignore[attr-defined]
        return container

    def _emit_current(self) -> None:
        low = self.low_slider.slider.value() / 100.0   # type: ignore
        mid = self.mid_slider.slider.value() / 100.0   # type: ignore
        high = self.high_slider.slider.value() / 100.0 # type: ignore
        self.eq_changed.emit(low, mid, high)

    def reset_to_flat(self) -> None:
        for band in (self.low_slider, self.mid_slider, self.high_slider):
            band.slider.blockSignals(True)  # type: ignore
            band.slider.setValue(50)        # type: ignore
            band.slider.blockSignals(False) # type: ignore
        self.eq_changed.emit(0.5, 0.5, 0.5)

    def _show_eq_menu(self, pos, band_name: str, slider):
        menu = QtWidgets.QMenu(self)
        menu.addAction(f"Reset {band_name}")
        menu.addAction(f"{band_name} Kill (0%)")
        menu.addAction(f"{band_name} Boost (100%)")
        menu.addSeparator()
        menu.addAction("Reset ALL EQ")
        menu.exec(slider.mapToGlobal(pos))

    def set_eq(self, low: float, mid: float, high: float) -> None:
        self.low_slider.slider.blockSignals(True)   # type: ignore
        self.low_slider.slider.setValue(int(low * 100))  # type: ignore
        self.low_slider.slider.blockSignals(False)  # type: ignore

        self.mid_slider.slider.blockSignals(True)   # type: ignore
        self.mid_slider.slider.setValue(int(mid * 100))  # type: ignore
        self.mid_slider.slider.blockSignals(False)  # type: ignore

        self.high_slider.slider.blockSignals(True)  # type: ignore
        self.high_slider.slider.setValue(int(high * 100)) # type: ignore
        self.high_slider.slider.blockSignals(False) # type: ignore
