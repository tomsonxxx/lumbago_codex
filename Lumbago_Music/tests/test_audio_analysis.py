"""Testy AudioAnalyzer (unit, bez prawdziwego audio)."""

import pytest
from lumbago_app.core.utils import normalize_bpm, format_duration, key_to_camelot


def test_normalize_bpm_doubling():
    """normalize_bpm podwaja zbyt wolne BPM."""
    assert normalize_bpm(64.0) == 128.0


def test_normalize_bpm_halving():
    """normalize_bpm dzieli zbyt szybkie BPM."""
    assert normalize_bpm(256.0) == 128.0


def test_normalize_bpm_in_range():
    """normalize_bpm zwraca wartość bez zmian jeśli w zakresie."""
    assert normalize_bpm(128.0) == 128.0


def test_format_duration_seconds():
    """format_duration formatuje < 1h jako mm:ss."""
    assert format_duration(90) == "1:30"
    assert format_duration(3600) == "1:00:00"


def test_key_to_camelot_known():
    """key_to_camelot zwraca poprawne kody Camelot."""
    assert key_to_camelot("C major") == "8B"
    assert key_to_camelot("A minor") == "8A"
    assert key_to_camelot("F# minor") == "11A"


def test_key_to_camelot_unknown():
    """key_to_camelot zwraca None dla nieznanej tonacji."""
    assert key_to_camelot("X major") is None


def test_audio_analyzer_imports():
    """AudioAnalyzer importuje się poprawnie."""
    from lumbago_app.services.audio_analysis import AudioAnalyzer, AudioAnalysisResult
    analyzer = AudioAnalyzer()
    assert analyzer is not None
