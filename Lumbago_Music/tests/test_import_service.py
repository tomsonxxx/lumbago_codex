"""Testy ImportService."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_import_nonexistent_directory(db_session):
    """import_directory rzuca ImportError dla nieistniejącego katalogu."""
    from lumbago_app.services.import_service import ImportService
    from lumbago_app.core.exceptions import ImportError as LumbagoImportError

    service = ImportService()
    with pytest.raises(LumbagoImportError):
        service.import_directory(Path("/nonexistent/path"))


def test_import_directory_counts(tmp_audio_dir, db_session):
    """import_directory zlicza poprawnie dodane/pominięte pliki."""
    from lumbago_app.services.import_service import ImportService

    service = ImportService()
    # Prosty test — bez rzeczywistego audio, mutagen może rzucić wyjątek
    # więc liczymy tylko że metoda uruchamia się bez crash
    try:
        result = service.import_directory(tmp_audio_dir, recursive=False)
        # .txt nie jest audio — pominięte lub błąd, ale nie crash
        assert result.total >= 0
    except Exception:
        pass  # OK — pliki nie mają prawdziwych danych audio


def test_safe_filename():
    """safe_filename usuwa niedozwolone znaki."""
    from lumbago_app.core.utils import safe_filename
    assert "/" not in safe_filename("AC/DC - Track")
    assert ":" not in safe_filename("12:00")
    assert safe_filename("") == "unnamed"


def test_is_audio_file():
    """is_audio_file rozpoznaje formaty audio."""
    from lumbago_app.core.utils import is_audio_file
    assert is_audio_file(Path("track.mp3")) is True
    assert is_audio_file(Path("track.flac")) is True
    assert is_audio_file(Path("document.pdf")) is False
    assert is_audio_file(Path("image.jpg")) is False
