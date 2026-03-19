"""
Lumbago Music AI — Serwis obserwatora katalogów (watchdog)
==========================================================
Monitoruje katalogi muzyczne i automatycznie importuje nowe pliki.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Callback: (file_path) -> None
FileAddedCallback = Callable[[Path], None]


class LibraryWatcher:
    """
    Monitoruje katalogi przez watchdog i wywołuje import przy nowych plikach.

    Wymaga: watchdog >= 4.0
    """

    def __init__(self, callback: FileAddedCallback) -> None:
        """
        Args:
            callback: Funkcja wywoływana przy nowym pliku audio.
        """
        self._callback = callback
        self._observer: Optional[object] = None
        self._watched_dirs: list[Path] = []

    def start(self, directories: list[Path]) -> None:
        """
        Startuje obserwację katalogów.

        Args:
            directories: Lista katalogów do monitorowania.
        """
        raise NotImplementedError(
            "LibraryWatcher.start() — do implementacji w FAZIE 2.\n"
            "Plan: 1) watchdog.observers.Observer(),\n"
            "2) FileSystemEventHandler na zdarzenia CREATE,\n"
            "3) filtruj is_audio_file(), wywołaj callback."
        )

    def stop(self) -> None:
        """Zatrzymuje obserwację."""
        if self._observer is not None:
            try:
                self._observer.stop()  # type: ignore[union-attr]
                self._observer.join()  # type: ignore[union-attr]
                logger.info("LibraryWatcher zatrzymany")
            except Exception as exc:
                logger.warning("Błąd zatrzymania watchera: %s", exc)
            finally:
                self._observer = None

    @property
    def is_running(self) -> bool:
        """Sprawdza czy obserwacja jest aktywna."""
        if self._observer is None:
            return False
        return getattr(self._observer, "is_alive", lambda: False)()
