from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

from ui.dj.deck_layout import (
    apply_action_buttons,
    apply_pro_buttons,
    apply_section_label,
    apply_status_label,
)
from ui.dj.styles import (
    BoothMetrics,
    action_button_stylesheet,
    deck_channel_badge_stylesheet,
    get_mixer_panel_stylesheet,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_metrics_scaled_stylesheets(qapp):
    focused = BoothMetrics(mode="deck_focused")
    compact = BoothMetrics(compact=True)
    assert focused.font_px("bpm") >= compact.font_px("bpm")
    assert "font-size" in focused.section_label_stylesheet()
    assert "font-size" in focused.value_label_stylesheet()
    assert "font-weight: 600" in focused.status_stylesheet()


def test_mixer_and_channel_badges(qapp):
    m = BoothMetrics(mode="dual_mixer")
    assert "MixerPanel" in get_mixer_panel_stylesheet()
    assert "00e0ff" in deck_channel_badge_stylesheet(m)


def test_action_and_pro_button_helpers(qapp):
    m = BoothMetrics(mode="deck_console")
    mem = QPushButton("S")
    loop = QPushButton("LOOP")
    loop.setCheckable(True)
    loop.setChecked(True)
    sync = QPushButton("SYNC")
    sync.setCheckable(True)
    apply_action_buttons(
        m,
        [
            (mem, "mem", False),
            (loop, "loop", True),
        ],
    )
    apply_pro_buttons(m, [(sync, True)])
    assert "border" in mem.styleSheet()
    assert action_button_stylesheet(m, active=True, role="loop")


def test_apply_label_helpers(qapp):
    m = BoothMetrics(mode="deck_focused")
    status = QLabel("ready")
    section = QLabel("EQ")
    apply_status_label(status, m)
    apply_section_label(section, m)
    assert "font-size" in status.styleSheet()
    assert "letter-spacing" in section.styleSheet()