from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.styles import BOOTH_COLORS, BoothMetrics, BOOTH_TOKENS, BOOTH_RESOLUTION_PROFILES
from services.playback.engine import PlaybackEngine


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_booth_metrics_normal_vs_compact():
    normal = BoothMetrics(compact=False)
    compact = BoothMetrics(compact=True)
    assert normal.font_px("title") > compact.font_px("title")
    assert normal.size("transport_play")[0] > compact.size("transport_play")[0]
    assert normal.wave_min_height() > compact.wave_min_height()
    nh, nv, _, _ = normal.layout_margins()
    ch, cv, _, _ = compact.layout_margins()
    assert nh > ch
    assert nv > cv


def test_booth_metrics_from_environment_dpi_and_resolution():
    base = BoothMetrics.from_environment(compact=False, logical_dpi=96.0, screen_width=1920)
    hdpi = BoothMetrics.from_environment(compact=False, logical_dpi=120.0, screen_width=1920)
    qhd = BoothMetrics.from_environment(compact=False, logical_dpi=96.0, screen_width=2560)
    assert hdpi.scale_factor > base.scale_factor
    assert qhd.scale_factor > base.scale_factor
    assert qhd.font_px("title") >= base.font_px("title")


def test_rekordbox7_wave_colors_defined():
    assert BOOTH_COLORS["wave_low"].lower() == "#ff3b3b"
    assert BOOTH_COLORS["wave_mid"].lower() == "#3dcc3d"
    assert BOOTH_COLORS["wave_high"].lower() == "#3d8bff"
    assert BOOTH_COLORS["wave_bg"].lower() == "#030408"
    assert float(BOOTH_RESOLUTION_PROFILES["1440p"]["scale_boost"]) > 1.0


def test_booth_tokens_cover_roles():
    for mode in ("normal", "compact"):
        tokens = BOOTH_TOKENS[mode]
        for key in ("title_font", "transport_play", "wave_min_h"):
            assert key in tokens


def test_simple_deck_cue_set_and_jump(qapp):
    engine = PlaybackEngine()
    ctrl = SimpleDeckController("A", engine)
    cues: list[int] = []
    ctrl.cue_changed.connect(cues.append)

    from core.models import Track
    import tempfile
    import wave
    import struct

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(struct.pack("<h", 0) * 44100)

    try:
        track = Track(path=path, title="Cue Test", duration=1)
        ctrl.load_track(track)
        assert cues == [0]

        ctrl.set_cue_at_ms(1500)
        assert ctrl._main_cue_ms == 1500
        assert cues[-1] == 1500

        ctrl.jump_to_cue()
        state = engine.get_deck_state("A")
        assert state is not None
        assert abs(state.position_ms - 1500) < 500
    finally:
        os.remove(path)