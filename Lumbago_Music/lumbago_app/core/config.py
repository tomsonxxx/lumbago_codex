"""
Lumbago Music AI — Konfiguracja aplikacji
==========================================
Centralne miejsce wszystkich ustawień. Używa python-decouple
do wczytywania wartości z .env lub zmiennych środowiskowych.
"""

import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional

from decouple import config, Csv

logger = logging.getLogger(__name__)


class Settings:
    """
    Konfiguracja aplikacji wczytywana z .env / env vars.

    Priorytet: env var > .env > wartość domyślna.
    """

    # ------------------------------------------------------------------ #
    # Tryby diagnostyczne
    # ------------------------------------------------------------------ #
    SAFE_MODE: bool = config("LUMBAGO_SAFE_MODE", default=False, cast=bool)
    DISABLE_MULTIMEDIA: bool = config("LUMBAGO_DISABLE_MULTIMEDIA", default=False, cast=bool)
    VERBOSE: bool = config("LUMBAGO_VERBOSE", default=False, cast=bool)
    RESET_DB: bool = config("LUMBAGO_RESET_DB", default=False, cast=bool)

    # ------------------------------------------------------------------ #
    # Baza danych
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = config(
        "DATABASE_URL", default="sqlite:///lumbago.db"
    )

    # ------------------------------------------------------------------ #
    # AI — klucze API
    # ------------------------------------------------------------------ #
    OPENAI_API_KEY: Optional[str] = config("OPENAI_API_KEY", default=None)
    OPENAI_MODEL: str = config("OPENAI_MODEL", default="gpt-4o-mini")

    ANTHROPIC_API_KEY: Optional[str] = config("ANTHROPIC_API_KEY", default=None)
    ANTHROPIC_MODEL: str = config("ANTHROPIC_MODEL", default="claude-3-haiku-20240307")

    GROK_API_KEY: Optional[str] = config("GROK_API_KEY", default=None)
    GROK_MODEL: str = config("GROK_MODEL", default="grok-beta")

    DEEPSEEK_API_KEY: Optional[str] = config("DEEPSEEK_API_KEY", default=None)
    DEEPSEEK_MODEL: str = config("DEEPSEEK_MODEL", default="deepseek-chat")

    GEMINI_API_KEY: Optional[str] = config("GEMINI_API_KEY", default=None)
    GEMINI_MODEL: str = config("GEMINI_MODEL", default="gemini-1.5-flash")

    # ------------------------------------------------------------------ #
    # Acoustid / fingerprinting
    # ------------------------------------------------------------------ #
    ACOUSTID_API_KEY: Optional[str] = config("ACOUSTID_API_KEY", default=None)

    # ------------------------------------------------------------------ #
    # MusicBrainz
    # ------------------------------------------------------------------ #
    MUSICBRAINZ_APP: str = config(
        "MUSICBRAINZ_APP", default="LumbagoMusic/1.0"
    )
    MUSICBRAINZ_RATE_LIMIT: float = config(
        "MUSICBRAINZ_RATE_LIMIT", default=1.0, cast=float
    )

    # ------------------------------------------------------------------ #
    # Discogs
    # ------------------------------------------------------------------ #
    DISCOGS_USER_TOKEN: Optional[str] = config("DISCOGS_USER_TOKEN", default=None)
    DISCOGS_CONSUMER_KEY: Optional[str] = config("DISCOGS_CONSUMER_KEY", default=None)
    DISCOGS_CONSUMER_SECRET: Optional[str] = config("DISCOGS_CONSUMER_SECRET", default=None)

    # ------------------------------------------------------------------ #
    # Last.fm
    # ------------------------------------------------------------------ #
    LASTFM_API_KEY: Optional[str] = config("LASTFM_API_KEY", default=None)
    LASTFM_API_SECRET: Optional[str] = config("LASTFM_API_SECRET", default=None)
    LASTFM_USERNAME: Optional[str] = config("LASTFM_USERNAME", default=None)
    LASTFM_PASSWORD_HASH: Optional[str] = config("LASTFM_PASSWORD_HASH", default=None)

    # ------------------------------------------------------------------ #
    # Spotify
    # ------------------------------------------------------------------ #
    SPOTIFY_CLIENT_ID: Optional[str] = config("SPOTIFY_CLIENT_ID", default=None)
    SPOTIFY_CLIENT_SECRET: Optional[str] = config("SPOTIFY_CLIENT_SECRET", default=None)
    SPOTIFY_REDIRECT_URI: str = config(
        "SPOTIFY_REDIRECT_URI", default="http://localhost:8888/callback"
    )

    # ------------------------------------------------------------------ #
    # Analiza audio
    # ------------------------------------------------------------------ #
    LIBROSA_CACHE_DIR: Path = Path(
        config("LIBROSA_CACHE_DIR", default=".cache/librosa")
    )
    WAVEFORM_RESOLUTION: int = config("WAVEFORM_RESOLUTION", default=1000, cast=int)
    LUFS_TARGET: float = config("LUFS_TARGET", default=-14.0, cast=float)
    BPM_MIN: int = config("BPM_MIN", default=60, cast=int)
    BPM_MAX: int = config("BPM_MAX", default=220, cast=int)

    # ------------------------------------------------------------------ #
    # Import
    # ------------------------------------------------------------------ #
    WATCH_DIRECTORIES: list[str] = config(
        "WATCH_DIRECTORIES", default="", cast=Csv()
    )
    IMPORT_BATCH_SIZE: int = config("IMPORT_BATCH_SIZE", default=50, cast=int)
    IMPORT_THREADS: int = config("IMPORT_THREADS", default=4, cast=int)

    # ------------------------------------------------------------------ #
    # Backup
    # ------------------------------------------------------------------ #
    BACKUP_DIR: Optional[str] = config("BACKUP_DIR", default=None)
    BACKUP_MAX_COUNT: int = config("BACKUP_MAX_COUNT", default=10, cast=int)

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    DEFAULT_THEME: str = config("DEFAULT_THEME", default="cyber_neon")
    LANGUAGE: str = config("LANGUAGE", default="pl")

    # ------------------------------------------------------------------ #
    # Ścieżki systemowe
    # ------------------------------------------------------------------ #
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    BUNDLED_DIR: Path = BASE_DIR / "bundled"
    FFMPEG_PATH: Path = BUNDLED_DIR / "ffmpeg" / "ffmpeg.exe"
    FPCALC_PATH: Path = BUNDLED_DIR / "fpcalc" / "fpcalc.exe"

    def available_ai_providers(self) -> list[str]:
        """Zwraca listę dostępnych providerów AI (mają skonfigurowany klucz)."""
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if self.GROK_API_KEY:
            providers.append("grok")
        if self.DEEPSEEK_API_KEY:
            providers.append("deepseek")
        if self.GEMINI_API_KEY:
            providers.append("gemini")
        return providers

    def log_summary(self) -> None:
        """Loguje podsumowanie konfiguracji (bez sekretów)."""
        logger.info(
            "Konfiguracja: safe=%s, multimedia=%s, verbose=%s, theme=%s, "
            "ai_providers=%s",
            self.SAFE_MODE,
            self.DISABLE_MULTIMEDIA,
            self.VERBOSE,
            self.DEFAULT_THEME,
            self.available_ai_providers(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Zwraca singleton Settings (cached)."""
    settings = Settings()
    settings.log_summary()
    return settings
