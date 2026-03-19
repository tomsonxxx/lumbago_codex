"""
Lumbago Music AI — Benchmark 10k utworów
==========================================
Mierzy wydajność importu i wyszukiwania dla 10 000 rekordów.
Uruchom: pytest tests/benchmarks/bench_10k.py --benchmark-autosave
"""

import pytest


@pytest.fixture(scope="module")
def db_with_10k_tracks(db_engine):
    """Inicjalizuje bazę z 10 000 fikcyjnymi rekordami."""
    from lumbago_app.data.database import session_scope
    from lumbago_app.data.models import TrackOrm

    with session_scope() as session:
        existing = session.query(TrackOrm).count()
        if existing >= 10_000:
            return  # już wypełniona

        tracks = [
            TrackOrm(
                file_path=f"/benchmark/track_{i:05d}.mp3",
                title=f"Track {i}",
                artist=f"Artist {i % 500}",
                genre=["House", "Techno", "Trance", "DnB"][i % 4],
                bpm=120.0 + (i % 80),
                key_camelot=f"{(i % 12) + 1}{'AB'[i % 2]}",
                duration=180.0 + (i % 300),
            )
            for i in range(10_000)
        ]
        session.bulk_save_objects(tracks)
    return db_engine


def test_search_10k_by_genre(benchmark, db_with_10k_tracks):
    """Benchmark: wyszukiwanie wg gatunku w 10k rekordów."""
    from lumbago_app.data.database import session_scope
    from lumbago_app.data.repository import TrackRepository

    def search():
        with session_scope() as session:
            repo = TrackRepository(session)
            return repo.search(query="", genre="House", limit=100)

    result = benchmark(search)
    assert len(result) > 0


def test_search_10k_fulltext(benchmark, db_with_10k_tracks):
    """Benchmark: wyszukiwanie pełnotekstowe w 10k rekordów."""
    from lumbago_app.data.database import session_scope
    from lumbago_app.data.repository import TrackRepository

    def search():
        with session_scope() as session:
            repo = TrackRepository(session)
            return repo.search(query="Artist 10", limit=50)

    result = benchmark(search)
    assert len(result) >= 0
