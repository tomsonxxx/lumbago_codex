from core.models import Track
from services.metadata_enricher import (
    _validate_candidate,
    _is_compilation_album,
    _is_valid_year,
)


def test_validate_candidate_strict_exact_match():
    track = Track(path="x", title="Daft Punk", artist="Daft Punk")
    assert _validate_candidate(track, "Daft Punk", "Daft Punk", policy="strict") is True


def test_validate_candidate_strict_rejects_mismatch():
    track = Track(path="x", title="One More Time", artist="Daft Punk")
    assert _validate_candidate(track, "Around The World", "Daft Punk", policy="strict") is False


def test_validate_candidate_balanced_allows_close_match():
    track = Track(path="x", title="Around The World", artist="Daft Punk")
    assert _validate_candidate(track, "Around World", "Daft Punk", policy="balanced") is True


def test_validate_candidate_lenient_allows_looser_match():
    track = Track(path="x", title="Around The World", artist="Daft Punk")
    assert _validate_candidate(track, "Around", "Daft", policy="lenient") is True


def test_validate_candidate_aggressive_allows_noisy_local_metadata():
    track = Track(path="x", title="Sandstorm (Official Video) [HD]", artist="Darude - Topic")
    assert _validate_candidate(track, "Sandstorm", "Darude", policy="aggressive") is True


def test_compilation_album_detection():
    assert _is_compilation_album("Greatest Hits") is True


def test_valid_year_range():
    assert _is_valid_year(1999) is True
    assert _is_valid_year(1800) is False
