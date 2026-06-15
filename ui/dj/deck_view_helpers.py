from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from ui.dj.deck_controller import DeckController
from ui.dj.deck_layout import apply_waveform_resize
from ui.dj.booth_svg_icons import apply_transport_button_content
from ui.dj.styles import BoothMetrics
from ui.dj.views.transport_bar import TransportBar


def screen_info(widget: QtWidgets.QWidget) -> tuple[float, int]:
    dpi, screen_w = 96.0, 1920
    try:
        app = QtWidgets.QApplication.instance()
        if app:
            scr = widget.screen() if widget.isVisible() and widget.screen() else app.primaryScreen()
            if scr:
                dpi = float(scr.logicalDotsPerInch())
                screen_w = int(scr.geometry().width())
    except Exception:
        pass
    return dpi, screen_w


def metrics_for_odt(widget: QtWidgets.QWidget, *, compact: bool = False) -> BoothMetrics:
    dpi, screen_w = screen_info(widget)
    return BoothMetrics.from_environment(
        compact=compact,
        logical_dpi=dpi,
        widget_width=max(widget.width(), 320),
        screen_width=screen_w,
    )


def metrics_for_deck(widget: QtWidgets.QWidget, *, console: bool = False) -> BoothMetrics:
    dpi, screen_w = screen_info(widget)
    mode = "deck_console" if console else "deck_focused"
    return BoothMetrics.from_environment(
        mode=mode,
        logical_dpi=dpi,
        widget_width=max(widget.width(), 280),
        screen_width=screen_w,
    )


def metrics_for_mixer(widget: QtWidgets.QWidget) -> BoothMetrics:
    dpi, screen_w = screen_info(widget)
    return BoothMetrics.from_environment(
        mode="dual_mixer",
        logical_dpi=dpi,
        widget_width=max(widget.width(), 640),
        screen_width=screen_w,
    )


def apply_main_layout_margins(layout: QtWidgets.QLayout, metrics: BoothMetrics) -> None:
    layout.setContentsMargins(*metrics.layout_margins())
    layout.setSpacing(metrics.layout_spacing())


def wire_cue_transport(
    transport: TransportBar,
    controller: DeckController,
    view: QtWidgets.QWidget,
) -> None:
    """CDJ CUE: trzymaj=podgląd, zwolnij=stop na CUE, Shift+trzymaj=ustaw CUE."""
    view._skip_cue_release = False  # type: ignore[attr-defined]

    def on_pressed() -> None:
        mods = QtWidgets.QApplication.keyboardModifiers()
        if mods & QtCore.Qt.KeyboardModifier.ShiftModifier:
            view._skip_cue_release = True  # type: ignore[attr-defined]
            controller.set_cue_at_playhead()
            return
        view._skip_cue_release = False  # type: ignore[attr-defined]
        controller.cue_pressed()

    def on_released() -> None:
        if getattr(view, "_skip_cue_release", False):
            view._skip_cue_release = False  # type: ignore[attr-defined]
            return
        controller.cue_released()

    transport.cue_pressed.connect(on_pressed)
    transport.cue_released.connect(on_released)
    transport.bind_controller(controller)


def waveform_set_hotcue_free(controller: DeckController, time_ms: int) -> None:
    """Shift+klik waveform: ustaw hotcue na pierwszym wolnym slocie (lub nadpisz 0)."""
    if not controller.current_track:
        return
    snapped = controller.snap_to_beat(time_ms)
    for idx in range(8):
        if controller.get_hotcue(idx) is None:
            controller.set_hotcue(idx, snapped)
            return
    controller.set_hotcue(0, snapped)


def waveform_set_main_cue(controller: DeckController, time_ms: int) -> None:
    snapped = controller.snap_to_beat(time_ms)
    controller.set_cue_at_ms(snapped)
    controller.seek(snapped)


def transport_labels_from_metrics(transport: TransportBar, *, playing: bool) -> None:
    """Ujednolicone ikony + etykiety transportu (SVG + BOOTH_ICONS)."""
    apply_transport_button_content(
        transport._metrics,
        transport.cue_btn,
        transport.play_btn,
        transport.stop_btn,
        playing=playing,
    )


def refresh_waveform_on_resize(
    view: QtWidgets.QWidget,
    waveform: QtWidgets.QWidget,
    metrics: BoothMetrics,
    *,
    compact: bool = False,
) -> None:
    """Wspólny resize waveform — używany we wszystkich deck views."""
    if waveform is not None:
        apply_waveform_resize(waveform, metrics, view.height(), compact=compact)