from lumbago_app.core.models import Track
from lumbago_app.services.metadata_enricher import _validate_candidate


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
