"""
ui/dj/views/dual_console_widget.py

DualConsoleWidget – dwa decki side-by-side + kompaktowy pasek miksera weDJ.

Per SZPIEG_DJ_Player_Redesign_2026.md:
- Decki bez wbudowanego transportu (transport na MixerCompactBar)
- Crossfader max ~240px — nie dominuje nad przyciskami
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from services.playback import PlaybackEngine
from ui.dj.deck_controller import DeckController
from ui.dj.views.console_deck_view import ConsoleDeckView
from ui.dj.views.mixer_compact_bar import MixerCompactBar
from ui.dj.deck_view_helpers import apply_main_layout_margins, metrics_for_mixer
from ui.dj.styles import BoothMetrics, get_deck_panel_stylesheet


class DualConsoleWidget(QtWidgets.QWidget):
    """Konsola DJ: splitter A|B + MixerCompactBar (weDJ layout)."""

    def __init__(
        self,
        controller_a: DeckController,
        controller_b: DeckController,
        playback_engine: PlaybackEngine | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller_a = controller_a
        self.controller_b = controller_b
        self.playback_engine = playback_engine

        self.setStyleSheet(get_deck_panel_stylesheet())
        self._metrics = BoothMetrics(mode="dual_mixer")
        self._last_metrics_scale: float = 1.0

        self._setup_ui()
        self._wire_decks()
        self._refresh_metrics(force_apply=True)

        QtCore.QTimer.singleShot(0, self._apply_initial_mixer)

    def _setup_ui(self) -> None:
        main = QtWidgets.QVBoxLayout(self)
        self._main_layout = main
        main.setSpacing(self._metrics.px(6))

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)

        self.deck_a_view = ConsoleDeckView(self.controller_a, deck_label="A", embed_transport=False)
        self.deck_b_view = ConsoleDeckView(self.controller_b, deck_label="B", embed_transport=False)

        splitter.addWidget(self.deck_a_view)
        splitter.addWidget(self.deck_b_view)
        splitter.setSizes([480, 480])

        main.addWidget(splitter, 1)

        self.mixer_bar = MixerCompactBar(
            self.controller_a,
            self.controller_b,
            self.playback_engine,
        )
        main.addWidget(self.mixer_bar, 0)

    def _wire_decks(self) -> None:
        self.deck_a_view.set_partner_controller(self.controller_b)
        self.deck_b_view.set_partner_controller(self.controller_a)

    def _apply_initial_mixer(self) -> None:
        if hasattr(self, "mixer_bar"):
            self.mixer_bar.apply_initial_values()

    def _refresh_metrics(self, force_apply: bool = False) -> None:
        new_m = metrics_for_mixer(self)
        old = self._last_metrics_scale
        self._metrics = new_m
        self._last_metrics_scale = new_m.scale_factor
        if force_apply or abs(new_m.scale_factor - old) > 0.04:
            self._apply_metrics()

    def _apply_metrics(self) -> None:
        m = self._metrics
        if hasattr(self, "_main_layout"):
            apply_main_layout_margins(self._main_layout, m)
        if hasattr(self, "mixer_bar"):
            self.mixer_bar.apply_metrics(m)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_metrics(force_apply=False)

    def get_deck_view(self, deck_id: str) -> ConsoleDeckView | None:
        if deck_id.upper() == "A":
            return self.deck_a_view
        if deck_id.upper() == "B":
            return self.deck_b_view
        return None

    def refresh_mixer(self) -> None:
        QtCore.QTimer.singleShot(10, self._apply_initial_mixer)


__all__ = ["DualConsoleWidget"]