from __future__ import annotations

from core.waveform import classify_band_from_ratios, extract_spectral_bands


def test_classify_band_kick_bass():
    assert classify_band_from_ratios(0.7, 0.2, 0.1) == 0


def test_classify_band_percussion():
    assert classify_band_from_ratios(0.2, 0.65, 0.15) == 1


def test_classify_band_vocal_mid():
    assert classify_band_from_ratios(0.2, 0.25, 0.55) == 2


def test_classify_band_breakdown():
    assert classify_band_from_ratios(0.1, 0.1, 0.1) == 3


def test_extract_spectral_bands_fallback_length():
    bands = extract_spectral_bands("/nonexistent/track.mp3", num_points=120)
    assert len(bands) == 120
    assert all(0 <= b <= 3 for b in bands)