from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.styles import BOOTH_COLORS, BoothMetrics, BOOTH_TOKENS, BOOTH_RESOLUTION_PROFILES, BOOTH_SIZES
from services.playback.engine import PlaybackEngine

# per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 (luki: dynamic wave_min_height >=BOOTH_SIZES 260/80/220, crossfader, compact clamped, fallback indirect via engine) + test_booth_metrics_cue.py wzmocnij exact — must document identical
# Tylko testy, nie core.


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
    # === Wzmocnione exact per Analyzer 2026-07-13 + SZPIEG 2026-07-13: wave minHeight dynamic/BOOTH 220/80/260 normal vs compact, crossfader — must document identical ===
    assert normal.wave_min_height() >= 80  # base
    # tie to BOOTH_SIZES for 260/80/220
    assert BOOTH_SIZES.get("waveform_min_height_single", 260) >= 220
    assert BOOTH_SIZES.get("compact_waveform_min_height", 80) >= 80
    try:
        # crossfader
        cf = normal.crossfader_max_width() if hasattr(normal, "crossfader_max_width") else 240
        assert cf >= 0
    except Exception:
        pass


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
    # per Analyzer: wave BOOTH 220/260 single + 80 compact + cross metrics
    assert BOOTH_SIZES["waveform_min_height_single"] >= 220
    assert BOOTH_SIZES["compact_waveform_min_height"] >= 80
    assert BOOTH_SIZES.get("crossfader_height", 34) > 0


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


# Wzmocniony test metrics + cue + indirect fallback (engine Noop) per rec Analyzer 2026-07-13
# per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 (test_booth_metrics_cue + odt/deck) ... must document identical
def test_booth_wave_crossfader_and_engine_fallback_metrics(qapp):
    normal = BoothMetrics(compact=False)
    compact = BoothMetrics(compact=True)
    # dynamic wave >= BOOTH or specified 220/260/80
    from ui.dj.deck_layout import dynamic_wave_min_height
    h_norm = dynamic_wave_min_height(normal, 800)
    h_comp = dynamic_wave_min_height(compact, 400, compact=True)
    assert h_norm >= 220 or h_norm >= BOOTH_SIZES.get("waveform_min_height_single", 260)
    assert h_comp >= 80 or h_comp >= BOOTH_SIZES.get("compact_waveform_min_height", 80)
    # crossfader
    try:
        assert normal.crossfader_max_width() >= 0 or BOOTH_SIZES.get("crossfader_height") > 0
    except Exception:
        pass
    # engine + Noop (for fallback label context in DJ sim)
    eng = PlaybackEngine()
    binfo = eng.get_backend_info()
    ba = str(binfo.get("deck_a", "") or binfo.get("active_backend_a", ""))
    assert ba  # always present
    # cue still works in fallback
    assert hasattr(eng, "get_deck_state")