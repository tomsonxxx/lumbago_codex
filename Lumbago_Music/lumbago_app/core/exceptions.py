"""
Lumbago Music AI — Hierarchia wyjątków
=========================================
Wszystkie własne wyjątki aplikacji w jednym miejscu.
"""


class LumbagoError(Exception):
    """Bazowy wyjątek Lumbago Music."""


# ------------------------------------------------------------------ #
# Baza danych
# ------------------------------------------------------------------ #

class DatabaseError(LumbagoError):
    """Ogólny błąd bazy danych."""


class MigrationError(DatabaseError):
    """Błąd migracji Alembic."""


class DuplicateTrackError(DatabaseError):
    """Utwór już istnieje w bazie (duplikat ścieżki)."""


# ------------------------------------------------------------------ #
# Import / Pliki
# ------------------------------------------------------------------ #

class ImportError(LumbagoError):
    """Błąd importu pliku/katalogu."""


class UnsupportedFormatError(ImportError):
    """Nieobsługiwany format pliku audio."""

    def __init__(self, path: str, extension: str) -> None:
        super().__init__(
            f"Nieobsługiwany format '{extension}' dla pliku: {path}"
        )
        self.path = path
        self.extension = extension


class FileReadError(ImportError):
    """Nie można odczytać pliku (brak dostępu, uszkodzony)."""


# ------------------------------------------------------------------ #
# Analiza audio
# ------------------------------------------------------------------ #

class AudioAnalysisError(LumbagoError):
    """Błąd podczas analizy audio (librosa, pyloudnorm)."""


class FingerprintError(LumbagoError):
    """Błąd generowania lub wyszukiwania fingerprinta."""


class WaveformError(AudioAnalysisError):
    """Błąd generowania formy fali."""


# ------------------------------------------------------------------ #
# AI / LLM
# ------------------------------------------------------------------ #

class AIError(LumbagoError):
    """Ogólny błąd usługi AI."""


class NoProviderAvailableError(AIError):
    """Brak skonfigurowanego i dostępnego providera AI."""


class LLMResponseError(AIError):
    """Nieprawidłowa lub niekompletna odpowiedź od LLM."""


class RateLimitError(AIError):
    """Przekroczono limit zapytań do API."""

    def __init__(self, provider: str, retry_after: float | None = None) -> None:
        msg = f"Rate limit dla '{provider}'"
        if retry_after:
            msg += f" — spróbuj ponownie za {retry_after:.1f}s"
        super().__init__(msg)
        self.provider = provider
        self.retry_after = retry_after


# ------------------------------------------------------------------ #
# Integracje zewnętrzne
# ------------------------------------------------------------------ #

class IntegrationError(LumbagoError):
    """Błąd zewnętrznej integracji (MusicBrainz, Discogs itp.)."""


class AcoustidError(IntegrationError):
    """Błąd usługi AcoustID."""


class MusicBrainzError(IntegrationError):
    """Błąd usługi MusicBrainz."""


class DiscogsError(IntegrationError):
    """Błąd usługi Discogs."""


class SpotifyError(IntegrationError):
    """Błąd usługi Spotify."""


class LastFmError(IntegrationError):
    """Błąd usługi Last.fm."""


# ------------------------------------------------------------------ #
# UI / Workery
# ------------------------------------------------------------------ #

class WorkerCancelledError(LumbagoError):
    """Operacja w tle została anulowana przez użytkownika."""


class ConfigurationError(LumbagoError):
    """Błąd konfiguracji aplikacji (brakujące klucze, nieprawidłowe wartości)."""
