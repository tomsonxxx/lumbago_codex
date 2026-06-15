from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QPushButton

from ui.dj.booth_svg_icons import (
    apply_transport_button_content,
    booth_transport_icon,
    svg_available,
)
from ui.dj.deck_layout import build_centered_transport
from ui.dj.styles import BoothMetrics, booth_transport_label


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_svg_available_in_pyqt6(qapp):
    assert svg_available() is True


def test_booth_transport_icon_non_empty(qapp):
    metrics = BoothMetrics(mode="normal")
    for role in ("play", "cue", "stop"):
        icon = booth_transport_icon(metrics, role)
        assert icon is not None
        assert not icon.isNull()
    pause = booth_transport_icon(metrics, "play", playing=True)
    assert pause is not None
    assert not pause.isNull()


def test_apply_transport_normal_has_labels(qapp):
    metrics = BoothMetrics(mode="deck_focused")
    cue = QPushButton()
    play = QPushButton()
    stop = QPushButton()
    apply_transport_button_content(metrics, cue, play, stop, playing=False, compact=False)
    if svg_available():
        assert play.text() == booth_transport_label("play")
        assert cue.text() == "CUE"
        assert stop.text() == "STOP"
        assert not play.icon().isNull()
    else:
        assert "ODTWÓRZ" in play.text() or "▶" in play.text()


def test_apply_transport_compact_icon_only(qapp):
    metrics = BoothMetrics(compact=True)
    t = build_centered_transport(metrics)
    apply_transport_button_content(
        metrics,
        t.cue_btn,
        t.play_btn,
        t.stop_btn,
        playing=True,
        compact=True,
    )
    if svg_available():
        assert t.play_btn.text() == ""
        assert not t.play_btn.icon().isNull()
        assert not t.cue_btn.icon().isNull()
        assert not t.stop_btn.icon().isNull()