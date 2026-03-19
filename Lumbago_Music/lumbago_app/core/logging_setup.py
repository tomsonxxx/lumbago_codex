"""
Lumbago Music AI — Konfiguracja logowania
==========================================
Inicjalizuje logging z obsługą pliku rotacyjnego i konsoli.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


def configure_logging(log_dir: Path | None = None) -> None:
    """
    Konfiguruje globalny system logowania.

    Args:
        log_dir: Katalog na pliki logów. Domyślnie logs/ obok main.py.
    """
    verbose: bool = os.environ.get("LUMBAGO_VERBOSE") == "1"
    level = logging.DEBUG if verbose else logging.INFO

    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "lumbago.log"

    # Format wiadomości
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # Handler: plik rotacyjny (max 5MB × 3 kopie)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler: konsola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)-8s %(name)s: %(message)s")
    )

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Wycisz hałaśliwe biblioteki zewnętrzne
    for noisy in ("urllib3", "httpx", "httpcore", "hpack", "h2"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logowanie skonfigurowane: poziom=%s, plik=%s",
        logging.getLevelName(level),
        log_file,
    )
