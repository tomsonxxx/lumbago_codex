"""
ui/dj/views/hotcue_grid.py

HotcuePadGrid – zawsze 2×4 grid (8 padów).

Czysty widget prezentacyjny.
- Tworzy 8 instancji HotcuePad
- Przekazuje sygnały dalej (można podłączyć do kontrolera)
- Rozmiar padów z centralnego BOOTH_SIZES
- Zero logiki hotcue – tylko układ

Używany zarówno w FocusedDeckView jak i ConsoleDeckView.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.views.hotcue_pad import HotcuePad
from ui.dj.styles import BOOTH_SIZES, BoothMetrics


class HotcuePadGrid(QtWidgets.QWidget):
    """
    Profesjonalny 2×4 grid hotcue'ów (zawsze 8 padów).

    Sygnały są przekazywane z padów:
    - pad_activated(index)
    - pad_set_requested(index)
    """

    pad_activated = QtCore.pyqtSignal(int)
    pad_set_requested = QtCore.pyqtSignal(int)
    pad_delete_requested = QtCore.pyqtSignal(int)
    pad_rename_requested = QtCore.pyqtSignal(int)
    pad_color_change_requested = QtCore.pyqtSignal(int, str)

    def __init__(
        self,
        pad_size: tuple[int, int] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)
        self.pads: list[HotcuePad] = []

        # Zawsze dokładnie 8 padów (2 rzędy × 4 kolumny)
        num_cues = 8
        size = pad_size or BOOTH_SIZES.get("hotcue_pad", (82, 62))

        grid = QtWidgets.QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        for i in range(num_cues):
            pad = HotcuePad(i)
            pad.setFixedSize(*size)
            self.pads.append(pad)

            # Przekazywanie sygnałów
            pad.activated.connect(self._on_pad_activated)
            pad.set_requested.connect(self._on_pad_set_requested)
            pad.delete_requested.connect(self._on_pad_delete_requested)
            pad.rename_requested.connect(self._on_pad_rename_requested)
            pad.color_change_requested.connect(self._on_pad_color_change_requested)

            row, col = divmod(i, 4)
            grid.addWidget(pad, row, col)

    def _on_pad_activated(self, index: int) -> None:
        self.pad_activated.emit(index)

    def _on_pad_set_requested(self, index: int) -> None:
        self.pad_set_requested.emit(index)

    def get_pad(self, index: int) -> HotcuePad | None:
        """Zwraca pad po indeksie (0-7)."""
        if 0 <= index < len(self.pads):
            return self.pads[index]
        return None

    def clear_all(self) -> None:
        """Czyści wizualnie wszystkie pady (używane przy unload)."""
        for pad in self.pads:
            pad.clear_cue()

    def apply_metrics(self, metrics: BoothMetrics) -> None:
        w, h = metrics.hotcue_pad_size()
        for pad in self.pads:
            pad.setFixedSize(w, h)
            pad._apply_style()

    def _on_pad_delete_requested(self, index: int) -> None:
        self.pad_delete_requested.emit(index)

    def _on_pad_rename_requested(self, index: int) -> None:
        self.pad_rename_requested.emit(index)

    def _on_pad_color_change_requested(self, index: int, color: str) -> None:
        self.pad_color_change_requested.emit(index, color)
