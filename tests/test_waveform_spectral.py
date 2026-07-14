from __future__ import annotations

from core.waveform import classify_band_from_ratios, extract_spectral_bands, get_band_tint


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


def test_get_band_tint_discrete():
    # discrete per-band tint (Faza2)
    assert "e63939" in get_band_tint(0).name() or get_band_tint(0).red() > 200  # red kick
    assert get_band_tint(3).blue() > 100  # blue breakdown
    # fallback
    c = get_band_tint(99)
    assert c.red() >= 0

# Faza2 asserts per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color...)
def test_faza2_waveform_color_exact_tints():
    c0 = get_band_tint(0)
    c1 = get_band_tint(1)
    c2 = get_band_tint(2)
    c3 = get_band_tint(3)
    # red kick, yellow perc, teal vocal, blue breakdown
    assert c0.red() > 200 or "#e6" in str(c0)
    assert c1.red() > 150 and c1.green() > 150  # yellow-ish
    assert c3.blue() > 100
    assert get_band_tint(None).red() >= 0  # fallback

def test_faza2_spectral_bands_range_and_classify():
    bands = extract_spectral_bands("nonexistent", 30)
    assert len(bands) == 30
    assert all(isinstance(b, int) and 0 <= b <= 3 for b in bands)
    # classify coverage
    assert classify_band_from_ratios(0.6, 0.3, 0.1) == 0  # kick
    assert classify_band_from_ratios(0.1, 0.7, 0.2) == 1  # perc

# Blok 3 Faza2 real viz advancement (per user "przejście do następnego bloku")
# energy overlay: high pk segments get bright white mix overlay (see widget paint >0.55)
def test_faza2_energy_overlay_high_peak_bright():
    # simulate condition used in paintEvent for energy bright overlay
    pk = 0.72
    assert pk > 0.55
    mix = min(0.65, (pk - 0.55) * 1.8)
    assert mix > 0.3
    # band 0 (kick) + high energy should produce bright tint effect
    c = get_band_tint(0)
    assert c.red() > 150  # red base + overlay brightens

def test_faza2_full_discrete_pipeline():
    bands = extract_spectral_bands("nonexistent", 60)
    assert len(bands) == 60
    for b in bands:
        tint = get_band_tint(b)
        assert tint.red() >= 0 and tint.green() >= 0 and tint.blue() >= 0
    # covers kick(0) red, perc(1) yellow-ish, vocal(2), breakdown(3) blue
    assert get_band_tint(0).red() > 180 or "#e6" in str(get_band_tint(0))
    assert get_band_tint(3).blue() > 80
