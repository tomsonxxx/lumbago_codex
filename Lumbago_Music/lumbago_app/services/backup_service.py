"""
Lumbago Music AI — Serwis kopii zapasowych
============================================
Tworzy i zarządza kopiami zapasowymi bazy danych.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BackupService:
    """Zarządza kopiami zapasowymi bazy danych SQLite."""

    def __init__(self) -> None:
        from lumbago_app.core.config import get_settings
        settings = get_settings()
        self._backup_dir = Path(settings.BACKUP_DIR) if settings.BACKUP_DIR else None
        self._max_count = settings.BACKUP_MAX_COUNT

    def create_backup(self, label: str = "") -> Optional[Path]:
        """
        Tworzy kopię zapasową bazy danych.

        Args:
            label: Opcjonalna etykieta (np. "przed_migracją").

        Returns:
            Ścieżka do pliku backup lub None przy błędzie.
        """
        raise NotImplementedError(
            "BackupService.create_backup() — do implementacji w FAZIE 2.\n"
            "Plan: 1) SQLite VACUUM INTO '<backup>.db', 2) kompresja gzip,\n"
            "3) zapisz w backup_dir, 4) usuń stare jeśli > max_count."
        )

    def list_backups(self) -> list[Path]:
        """Zwraca listę dostępnych backupów (posortowane od najnowszego)."""
        if not self._backup_dir or not self._backup_dir.exists():
            return []
        backups = sorted(
            self._backup_dir.glob("lumbago_backup_*.db*"),
            reverse=True,
        )
        return backups

    def restore(self, backup_path: Path) -> bool:
        """
        Przywraca bazę z kopii zapasowej.

        Args:
            backup_path: Ścieżka do pliku backup.

        Returns:
            True jeśli sukces.
        """
        raise NotImplementedError(
            "BackupService.restore() — do implementacji w FAZIE 2."
        )
