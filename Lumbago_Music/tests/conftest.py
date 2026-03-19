"""
Lumbago Music AI — Konfiguracja pytest
========================================
Fixtures współdzielone między testami.
"""

import os
import pytest
from pathlib import Path
from typing import Generator

# Ustaw testową bazę przed importem modułów
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LUMBAGO_VERBOSE"] = "0"


@pytest.fixture(scope="session")
def db_engine():
    """Inicjalizuje bazę w pamięci dla testów."""
    from lumbago_app.data.database import init_database, get_engine
    init_database()
    yield get_engine()


@pytest.fixture
def db_session(db_engine):
    """Zwraca sesję SQLAlchemy z rollbackiem po teście."""
    from lumbago_app.data.database import get_session
    session = get_session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_track_data() -> dict:
    """Przykładowe dane do tworzenia TrackOrm."""
    return {
        "file_path": "/test/artist - title.mp3",
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "genre": "House",
        "bpm": 128.0,
        "key_camelot": "8B",
        "duration": 360.0,
        "year": 2024,
        "rating": 4,
    }


@pytest.fixture
def tmp_audio_dir(tmp_path: Path) -> Path:
    """Tworzy tymczasowy katalog z przykładowymi 'plikami audio'."""
    for name in ["track1.mp3", "track2.flac", "not_audio.txt"]:
        (tmp_path / name).write_bytes(b"\x00" * 1024)
    return tmp_path
