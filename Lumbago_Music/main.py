"""
Lumbago Music AI — Entry Point
================================
Punkt wejścia aplikacji. Inicjalizuje środowisko, konfigurację
i uruchamia główne okno PyQt6.
"""

import sys
import os
import logging
from pathlib import Path


def _bootstrap_env() -> None:
    """Wczytuje .env przed importem jakichkolwiek modułów aplikacji."""
    try:
        from decouple import Config, RepositoryEnv
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            # decouple wczyta .env automatycznie przy pierwszym imporcie
            pass
    except ImportError:
        pass  # decouple opcjonalne na etapie bootstrapu


def _apply_cli_flags() -> None:
    """Przetwarza flagi CLI przekazane przez launcher.py lub bezpośrednio."""
    if "--safe-mode" in sys.argv:
        os.environ["LUMBAGO_SAFE_MODE"] = "1"
    if "--disable-multimedia" in sys.argv:
        os.environ["LUMBAGO_DISABLE_MULTIMEDIA"] = "1"
    if "--verbose" in sys.argv:
        os.environ["LUMBAGO_VERBOSE"] = "1"
    if "--reset-db" in sys.argv:
        os.environ["LUMBAGO_RESET_DB"] = "1"


def main() -> int:
    """
    Główna funkcja uruchamiająca aplikację.

    Returns:
        Kod wyjścia (0 = sukces).
    """
    _bootstrap_env()
    _apply_cli_flags()

    # Import po bootstrapie środowiska
    from lumbago_app.core.logging_setup import configure_logging
    configure_logging()

    logger = logging.getLogger(__name__)
    logger.info("Uruchamianie Lumbago Music AI v1.0.0")

    # Inicjalizacja bazy danych
    try:
        from lumbago_app.data.database import init_database
        init_database()
        logger.info("Baza danych zainicjalizowana")
    except Exception as exc:
        logger.critical("Nie można zainicjalizować bazy danych: %s", exc, exc_info=True)
        if os.environ.get("LUMBAGO_SAFE_MODE") != "1":
            return 1

    # Uruchomienie UI
    try:
        from lumbago_app.ui.app import run_app
        return run_app(sys.argv)
    except Exception as exc:
        logger.critical("Krytyczny błąd aplikacji: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
