"""
Lumbago Music AI — Funkcje pomocnicze
========================================
Ogólne utility używane w całej aplikacji.
"""

import hashlib
import logging
import os
import re
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ------------------------------------------------------------------ #
# Operacje na plikach
# ------------------------------------------------------------------ #

def compute_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """
    Oblicza hash pliku blok po bloku (bezpieczne dla dużych plików).

    Args:
        path: Ścieżka do pliku.
        algorithm: Algorytm haszujący ('sha256', 'md5').

    Returns:
        Hex-string hasha.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    Sanityzuje nazwę pliku — usuwa znaki niedozwolone w Windows/Linux.

    Args:
        name: Oryginalna nazwa.
        max_length: Maksymalna długość.

    Returns:
        Bezpieczna nazwa pliku.
    """
    # Usuń znaki niedozwolone
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Usuń wiodące/kończące spacje i kropki
    name = name.strip(". ")
    # Ogranicz długość
    name = name[:max_length]
    return name or "unnamed"


def format_file_size(size_bytes: int) -> str:
    """Formatuje rozmiar pliku do czytelnej postaci (KB/MB/GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """
    Formatuje czas trwania: mm:ss lub h:mm:ss.

    Args:
        seconds: Czas w sekundach.

    Returns:
        Sformatowany string.
    """
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ------------------------------------------------------------------ #
# Dekoratory
# ------------------------------------------------------------------ #

def retry(
    times: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Dekorator ponawiający wykonanie funkcji przy błędzie.

    Args:
        times: Liczba prób.
        delay: Opóźnienie między próbami (sekundy).
        exceptions: Typy wyjątków do przechwycenia.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "Próba %d/%d dla %s nie powiodła się: %s",
                        attempt, times, func.__name__, exc,
                    )
                    if attempt < times:
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator


def timed(func: F) -> F:
    """Dekorator mierzący czas wykonania funkcji i logujący go na DEBUG."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug("%s zajął %.3f s", func.__name__, elapsed)
        return result
    return wrapper  # type: ignore[return-value]


# ------------------------------------------------------------------ #
# BPM / Klucz muzyczny
# ------------------------------------------------------------------ #

def normalize_bpm(bpm: float, min_bpm: int = 60, max_bpm: int = 220) -> float:
    """
    Normalizuje BPM do zakresu przez podwajanie/dzielenie.

    Args:
        bpm: Wartość BPM do znormalizowania.
        min_bpm: Minimalne BPM.
        max_bpm: Maksymalne BPM.

    Returns:
        Znormalizowane BPM.
    """
    while bpm < min_bpm:
        bpm *= 2
    while bpm > max_bpm:
        bpm /= 2
    return round(bpm, 2)


def key_to_camelot(key: str) -> str | None:
    """
    Konwertuje klucz muzyczny na notację Camelot.

    Args:
        key: Klucz w formacie 'C major', 'A minor' itp.

    Returns:
        Notacja Camelot (np. '8B') lub None jeśli nieznany.
    """
    from lumbago_app.core.constants import CAMELOT_WHEEL
    return CAMELOT_WHEEL.get(key)


def camelot_distance(a: str, b: str) -> int:
    """
    Oblicza odległość harmoniczną między dwoma kodami Camelot.

    Args:
        a: Kod Camelot (np. '8B').
        b: Kod Camelot (np. '9B').

    Returns:
        Odległość (0 = identyczne, 1 = sąsiad, wyższe = dalej).
    """
    if a == b:
        return 0
    from lumbago_app.core.constants import CAMELOT_COMPATIBLE
    neighbours = CAMELOT_COMPATIBLE.get(a, [])
    if b in neighbours:
        return 1
    return 2  # uproszczenie — pełna implementacja w beatgrid_service


# ------------------------------------------------------------------ #
# Walidacja
# ------------------------------------------------------------------ #

def is_audio_file(path: Path) -> bool:
    """Sprawdza czy plik ma obsługiwany format audio."""
    from lumbago_app.core.constants import SUPPORTED_FORMATS
    return path.suffix.lower() in SUPPORTED_FORMATS


def ensure_dir(path: Path) -> Path:
    """Tworzy katalog jeśli nie istnieje. Zwraca ścieżkę."""
    path.mkdir(parents=True, exist_ok=True)
    return path
