from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from ui.dj.deck_layout import build_centered_transport, dynamic_wave_min_height
from ui.dj.styles import BoothMetrics, booth_transport_text


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_dynamic_wave_min_grows_with_panel(qapp):
    normal = BoothMetrics(mode="normal")
    small = dynamic_wave_min_height(normal, 400)
    large = dynamic_wave_min_height(normal, 900)
    assert large >= small
    assert large >= normal.wave_min_height()


def test_dynamic_wave_compact_clamped(qapp):
    compact = BoothMetrics(compact=True)
    h = dynamic_wave_min_height(compact, 2000, compact=True)
    assert h <= compact.px(120)


def test_deck_console_ratio(qapp):
    console = BoothMetrics(mode="deck_console")
    h = dynamic_wave_min_height(console, 600)
    assert h >= console.wave_min_height()


def test_build_centered_transport_order(qapp):
    m = BoothMetrics(mode="deck_focused")
    t = build_centered_transport(m)
    assert t.cue_btn is not None
    assert t.play_btn is not None
    assert t.stop_btn is not None
    assert "CUE" in t.cue_btn.text()


def test_compact_transport_labels(qapp):
    assert booth_transport_text("play", compact=True) == "▶"
    assert booth_transport_text("play", playing=True, compact=True) == "❚❚"