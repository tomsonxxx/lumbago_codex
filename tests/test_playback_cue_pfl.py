from __future__ import annotations

import pytest

from services.playback.engine import PlaybackEngine, _NoopAudioBackend


def test_cue_volume_stored_and_applied():
    engine = PlaybackEngine(backend_factory=_NoopAudioBackend)
    try:
        engine.set_cue_volume(0.55)
        assert abs(engine.get_cue_volume() - 0.55) < 0.001
        diag = engine.get_diagnostics()
        assert diag["cue_volume"] == pytest.approx(0.55)
    finally:
        engine.release_all()


def test_pfl_routes_deck_to_cue_path():
    engine = PlaybackEngine(backend_factory=_NoopAudioBackend)
    try:
        engine.set_master_volume(1.0)
        engine.set_crossfader(0.0)
        engine.set_deck_trim("A", 1.0)
        engine.set_deck_trim("B", 1.0)
        engine.set_cue_volume(0.8)

        base_a = engine.get_deck_volume("A")
        base_b = engine.get_deck_volume("B")
        assert base_a > 0.5 and base_b > 0.5

        engine.set_deck_pfl("A", True)
        assert engine.get_deck_pfl("A") is True
        assert engine.is_any_pfl_active() is True

        pfl_a = engine.get_deck_volume("A")
        pfl_b = engine.get_deck_volume("B")
        assert abs(pfl_a - 0.8) < 0.05
        assert pfl_b < base_b * 0.5

        engine.set_deck_pfl("A", False)
        assert engine.is_any_pfl_active() is False
    finally:
        engine.release_all()


def test_cue_volume_clamped():
    engine = PlaybackEngine(backend_factory=_NoopAudioBackend)
    try:
        engine.set_cue_volume(2.5)
        assert engine.get_cue_volume() == 1.0
        engine.set_cue_volume(-1.0)
        assert engine.get_cue_volume() == 0.0
    finally:
        engine.release_all()