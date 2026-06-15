from __future__ import annotations

import os
import struct
import sys
import tempfile
import wave

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.models import Track
from services.playback.engine import PlaybackEngine
from ui.dj.deck_controller import DeckController
from ui.dj.views.console_deck_view import ConsoleDeckView
from ui.dj.views.dual_console_widget import DualConsoleWidget
from ui.dj.views.focused_deck_view import FocusedDeckView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def _make_wav() -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(struct.pack("<h", 0) * 44100)
    return path


def test_deck_controller_cue_api(qapp):
    engine = PlaybackEngine()
    ctrl = DeckController("A", engine)
    cues: list[int] = []
    ctrl.cue_changed.connect(cues.append)

    path = _make_wav()
    try:
        track = Track(path=path, title="Deck CUE", duration=1)
        ctrl.load_track(track)
        assert cues == [0]

        ctrl.set_cue_at_ms(2200)
        assert ctrl._main_cue_ms == 2200
        assert cues[-1] == 2200

        ctrl.clear_cue()
        assert ctrl._main_cue_ms == 0
        assert cues[-1] == 0

        ctrl.set_cue_at_ms(900)
        ctrl.jump_to_cue()
        state = engine.get_deck_state("A")
        assert state is not None
        assert abs(state.position_ms - 900) < 500
    finally:
        os.remove(path)


def test_focused_and_console_views_headless(qapp):
    engine = PlaybackEngine()
    ctrl_a = DeckController("A", engine)
    ctrl_b = DeckController("B", engine)

    focused = FocusedDeckView(ctrl_a)
    console = ConsoleDeckView(ctrl_b, deck_label="B")
    dual = DualConsoleWidget(ctrl_a, ctrl_b, engine)

    assert focused.controller is ctrl_a
    assert console.controller is ctrl_b
    assert dual.deck_a_view is not None
    assert dual.deck_b_view is not None
    assert hasattr(focused.transport, "_controller")
    assert focused.transport._controller is ctrl_a
    assert console.transport._controller is ctrl_b

    focused.show()
    console.show()
    dual.show()
    qapp.processEvents()

    assert focused.waveform is not None
    assert console.waveform is not None


def test_deck_metrics_modes_differ(qapp):
    from ui.dj.styles import BoothMetrics

    focused = BoothMetrics(mode="deck_focused")
    console = BoothMetrics(mode="deck_console")
    mixer = BoothMetrics(mode="dual_mixer")
    assert focused.wave_min_height() > console.wave_min_height()
    assert focused.font_px("bpm") > console.font_px("bpm")
    assert mixer.crossfader_height() >= 30
    assert mixer.mixer_slider_width() > 100


def test_booth_icons_transport(qapp):
    from ui.dj.styles import BOOTH_ICONS, booth_transport_text

    assert "play" in BOOTH_ICONS
    assert "▶" in booth_transport_text("play")
    assert "PAUZA" in booth_transport_text("play", playing=True)