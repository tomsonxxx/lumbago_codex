"""
ui/dj/compact_pilot_window.py

Osobne okno pilota kompaktowego (Winamp mini / weDJ) — zawsze widoczne, niezależne od głównego DJ window.
Per SZPIEG_DJ_Player_Redesign_2026 compact pilot spec.
"""

from __future__ import annotations

import logging

from PyQt6 import QtCore, QtWidgets

from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.styles import BOOTH_SIZES
from ui.dj.views.odtwarzacz_view import OdtwarzaczView

logger = logging.getLogger(__name__)


class CompactPilotWindow(QtWidgets.QMainWindow):
    """Mini odtwarzacz: waveform + VOL + transport + spin. StaysOnTop opcjonalnie."""

    closed_by_user = QtCore.pyqtSignal()

    def __init__(
        self,
        controller: SimpleDeckController,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle("Odtwarzacz — pilot kompaktowy")
        cmin = BOOTH_SIZES.get("compact_window_min", (420, 300))
        self.setMinimumSize(*cmin)
        self.resize(440, 320)

        flags = (
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._view = OdtwarzaczView(controller, self)
        self._view.set_compact_mode(True)
        layout.addWidget(self._view, 1)

    def show_pilot(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        try:
            self._view.set_compact_mode(True)
            self._view._update_compact_play_state(getattr(self._view, "_is_playing", False))
            # Faza1 highDPI force refresh (per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish + Analyzer: pilot extreme + rapid toggle). Must document identical.
            self._view.updateGeometry()
            self._view.update()
            if hasattr(self._view, "waveform"):
                self._view.waveform.update()
        except Exception as exc:
            logger.debug("compact pilot resync: %s", exc)

    def closeEvent(self, event) -> None:
        self.closed_by_user.emit()
        super().closeEvent(event)


__all__ = ["CompactPilotWindow"]