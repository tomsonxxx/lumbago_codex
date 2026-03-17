from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import zipfile

from lumbago_app.core.config import app_data_dir, settings_path


def perform_backup(max_backups: int = 10) -> None:
    data_dir = app_data_dir()
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = data_dir / "lumbago.db"
    settings_file = settings_path()
    archive_path = backups_dir / f"backup_{timestamp}.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if db_path.exists():
            zf.write(db_path, db_path.name)
        if settings_file.exists():
            zf.write(settings_file, settings_file.name)
    _trim_backups(backups_dir, max_backups)


def perform_pre_operation_backup() -> None:
    perform_backup(max_backups=20)


def restore_backup(archive_path: Path) -> None:
    """Przywraca bazę i ustawienia z archiwum ZIP. Wymaga restartu aplikacji."""
    data_dir = app_data_dir()
    with zipfile.ZipFile(archive_path, "r") as zf:
        for name in zf.namelist():
            dest = data_dir / name
            with zf.open(name) as src, dest.open("wb") as dst:
                dst.write(src.read())


def perform_scheduled_backup(interval_days: int = 7, max_backups: int = 10) -> bool:
    """Wykonuje backup tylko jeśli od ostatniego minęło co najmniej interval_days dni.

    Returns True jeśli backup został wykonany, False jeśli pominięto.
    """
    data_dir = app_data_dir()
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(backups_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        last_mtime = datetime.fromtimestamp(files[0].stat().st_mtime)
        if datetime.now() - last_mtime < timedelta(days=interval_days):
            return False
    perform_backup(max_backups=max_backups)
    return True


def list_backups() -> list[Path]:
    """Zwraca listę plików backup posortowanych od najnowszego."""
    backups_dir = app_data_dir() / "backups"
    if not backups_dir.exists():
        return []
    return sorted(backups_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)


def _trim_backups(backups_dir: Path, max_backups: int) -> None:
    if max_backups <= 0:
        return
    files = sorted(backups_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[max_backups:]:
        try:
            path.unlink()
        except Exception:
            continue
