"""
ui/dj/deck_layout.py

Wspólne buildery layoutu decków (per SZPIEG Build Spec 2026-06-15).
Używane przez OdtwarzaczView, FocusedDeckView, ConsoleDeckView — jeden system, różna gęstość.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6 import QtCore, QtWidgets

from ui.dj.booth_svg_icons import apply_transport_button_content
from ui.dj.styles import (
    BoothMetrics,
    action_button_stylesheet,
    booth_transport_text,
    pro_button_stylesheet,
)


# Udział wysokości panelu dla waveformu (po odjęciu overhead)
WAVE_HEIGHT_RATIO: dict[str, float] = {
    "normal": 0.36,
    "compact": 0.28,
    "deck_focused": 0.36,
    "deck_console": 0.28,
}

# Szacowany overhead (header + time + transport + status) w px @ scale 1.0
WAVE_OVERHEAD_BASE: dict[str, int] = {
    "normal": 130,
    "compact": 90,
    "deck_focused": 280,
    "deck_console": 220,
}


@dataclass
class DeckHeaderParts:
    layout: QtWidgets.QHBoxLayout
    title_label: QtWidgets.QLabel
    bpm_label: QtWidgets.QLabel


def build_deck_header(
    metrics: BoothMetrics,
    *,
    empty_title: str,
    header_spacing: int | None = None,
    extra_right: QtWidgets.QWidget | None = None,
) -> DeckHeaderParts:
    """Nagłówek: tytuł (stretch) + opcjonalny widget + BPM."""
    header = QtWidgets.QHBoxLayout()
    header.setSpacing(header_spacing if header_spacing is not None else metrics.px(16))

    title = QtWidgets.QLabel(empty_title)
    title.setStyleSheet(metrics.title_stylesheet())
    title.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
    )
    title.setWordWrap(False)
    title.setAlignment(
        QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
    )

    bpm = QtWidgets.QLabel("— BPM")
    bpm.setStyleSheet(metrics.bpm_stylesheet())
    bpm.setAlignment(
        QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
    )
    bpm.setMinimumWidth(metrics.bpm_min_width())

    header.addWidget(title, 1)
    if extra_right is not None:
        header.addWidget(extra_right, 0)
    header.addWidget(bpm, 0)
    return DeckHeaderParts(layout=header, title_label=title, bpm_label=bpm)


def build_time_label(metrics: BoothMetrics) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel("0:00 / 0:00")
    lbl.setStyleSheet(metrics.time_stylesheet())
    lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    return lbl


def configure_waveform_widget(waveform: QtWidgets.QWidget, metrics: BoothMetrics) -> None:
    waveform.setMinimumHeight(metrics.wave_min_height())
    waveform.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
    )


def dynamic_wave_min_height(
    metrics: BoothMetrics,
    panel_height: int,
    *,
    compact: bool = False,
) -> int:
    """
    Dynamiczna min. wysokość waveformu z dostępnej przestrzeni panelu.
    Reguła SZPIEG: max(token_min, ratio * avail_h), clamp per tryb.
    """
    mode_key = "compact" if compact else metrics.mode
    ratio = WAVE_HEIGHT_RATIO.get(mode_key, WAVE_HEIGHT_RATIO.get(metrics.mode, 0.32))
    overhead_base = WAVE_OVERHEAD_BASE.get(mode_key, WAVE_OVERHEAD_BASE.get(metrics.mode, 130))
    base_min = metrics.wave_min_height()
    overhead = metrics.px(overhead_base)
    avail_h = max(metrics.px(48), panel_height - overhead)
    target = max(base_min, int(avail_h * ratio))
    if compact or metrics.compact:
        return min(metrics.px(120), max(metrics.px(40), target))
    if metrics.mode == "deck_console":
        return min(metrics.px(220), target)
    if metrics.mode == "deck_focused":
        return min(metrics.px(320), target)
    return min(metrics.px(280), target)


def apply_waveform_resize(
    waveform: QtWidgets.QWidget,
    metrics: BoothMetrics,
    panel_height: int,
    *,
    compact: bool = False,
) -> None:
    target = dynamic_wave_min_height(metrics, panel_height, compact=compact)
    if waveform.minimumHeight() != target:
        waveform.setMinimumHeight(target)


@dataclass
class TransportButtonSet:
    layout: QtWidgets.QHBoxLayout
    cue_btn: QtWidgets.QPushButton
    play_btn: QtWidgets.QPushButton
    stop_btn: QtWidgets.QPushButton


def build_centered_transport(metrics: BoothMetrics) -> TransportButtonSet:
    """CDJ kolejność: CUE | PLAY | STOP — wycentrowany klaster."""
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(metrics.transport_gap())
    row.addStretch(1)

    cue_btn = QtWidgets.QPushButton(booth_transport_text("cue"))
    play_btn = QtWidgets.QPushButton(booth_transport_text("play"))
    stop_btn = QtWidgets.QPushButton(booth_transport_text("stop"))

    row.addWidget(cue_btn)
    row.addWidget(play_btn)
    row.addWidget(stop_btn)
    row.addStretch(1)

    apply_transport_button_metrics(metrics, cue_btn, play_btn, stop_btn)
    return TransportButtonSet(layout=row, cue_btn=cue_btn, play_btn=play_btn, stop_btn=stop_btn)


def apply_transport_button_metrics(
    metrics: BoothMetrics,
    cue_btn: QtWidgets.QPushButton,
    play_btn: QtWidgets.QPushButton,
    stop_btn: QtWidgets.QPushButton,
    *,
    playing: bool = False,
    compact: bool = False,
) -> None:
    min_h = metrics.min_transport_height()

    def _sz(role: str) -> tuple[int, int]:
        w, h = metrics.size(role)
        return w, max(h, min_h)

    cue_btn.setFixedSize(*_sz("transport_cue"))
    play_btn.setFixedSize(*_sz("transport_play"))
    stop_btn.setFixedSize(*_sz("transport_stop"))
    cue_btn.setStyleSheet(metrics.transport_stylesheet("cue"))
    play_btn.setStyleSheet(metrics.transport_stylesheet("play"))
    stop_btn.setStyleSheet(metrics.transport_stylesheet("stop"))
    apply_transport_button_content(
        metrics,
        cue_btn,
        play_btn,
        stop_btn,
        playing=playing,
        compact=compact or metrics.compact,
    )
def apply_status_label(label: QtWidgets.QLabel, metrics: BoothMetrics) -> None:
    label.setStyleSheet(metrics.status_stylesheet())


def apply_section_label(label: QtWidgets.QLabel, metrics: BoothMetrics) -> None:
    label.setStyleSheet(metrics.section_label_stylesheet())


def apply_pro_buttons(
    metrics: BoothMetrics,
    buttons: list[tuple[QtWidgets.QPushButton, bool]],
) -> None:
    """Skaluj rząd przycisków pro (SYNC/PFL/Q/KEY) — active = stan wyróżniony."""
    w, h = metrics.pro_button_size()
    for btn, active in buttons:
        btn.setFixedSize(w, h)
        btn.setStyleSheet(pro_button_stylesheet(metrics, active=active))


def apply_action_buttons(
    metrics: BoothMetrics,
    spec: list[tuple[QtWidgets.QPushButton, str, bool]],
) -> None:
    """MEM / LOOP / IN / OUT — role + active."""
    for btn, role, active in spec:
        btn.setStyleSheet(action_button_stylesheet(metrics, active=active, role=role))


def apply_header_metrics(parts: DeckHeaderParts, metrics: BoothMetrics) -> None:
    parts.title_label.setStyleSheet(metrics.title_stylesheet())
    parts.bpm_label.setStyleSheet(metrics.bpm_stylesheet())
    parts.bpm_label.setMinimumWidth(metrics.bpm_min_width())


def deck_badge_stylesheet(metrics: BoothMetrics) -> str:
    fs = metrics.font_px("title")
    return (
        f"color: #00e0ff; font-size: {fs}px; font-weight: 900; letter-spacing: 2px; "
        f"min-width: {metrics.px(28)}px; background-color: #0f141c; "
        "border: 1px solid #3a4556; border-radius: 4px; padding: 2px 6px;"
    )


def build_deck_badge(label: str, metrics: BoothMetrics) -> QtWidgets.QLabel:
    badge = QtWidgets.QLabel(label)
    badge.setStyleSheet(deck_badge_stylesheet(metrics))
    badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    return badge