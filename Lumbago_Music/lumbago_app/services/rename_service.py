"""
Lumbago Music AI — Serwis masowego przemianowania plików
=========================================================
Zmienia nazwy plików wg szablonu Jinja2.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Domyślny szablon nazwy pliku
DEFAULT_TEMPLATE = "{{ artist }} - {{ title }}{{ ext }}"


class RenameService:
    """
    Masowo przemianowuje pliki audio wg szablonu Jinja2.

    Dostępne zmienne szablonu:
    - artist, title, album, year, track_number, genre, bpm, key, ext
    """

    def preview(
        self,
        track_ids: list[int],
        template: str = DEFAULT_TEMPLATE,
    ) -> list[dict[str, str]]:
        """
        Podgląd zmian nazw bez fizycznego przemianowania.

        Returns:
            Lista {"old": str, "new": str} dla każdego ID.
        """
        raise NotImplementedError(
            "RenameService.preview() — do implementacji w FAZIE 3.\n"
            "Plan: 1) pobierz TrackOrm dla track_ids,\n"
            "2) renderuj Jinja2(template, **track_fields),\n"
            "3) zwróć listę par old/new."
        )

    def execute(
        self,
        track_ids: list[int],
        template: str = DEFAULT_TEMPLATE,
        dry_run: bool = False,
    ) -> dict[int, Optional[str]]:
        """
        Wykonuje przemianowanie plików.

        Args:
            track_ids: ID utworów do przemianowania.
            template: Szablon Jinja2 nazwy pliku.
            dry_run: Jeśli True, tylko symuluj (nie zmieniaj).

        Returns:
            Słownik track_id -> nowa ścieżka (None = błąd).
        """
        raise NotImplementedError(
            "RenameService.execute() — do implementacji w FAZIE 3."
        )
