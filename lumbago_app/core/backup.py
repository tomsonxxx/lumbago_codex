from __future__ import annotations

from datetime import datetime
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


def _trim_backups(backups_dir: Path, max_backups: int) -> None:
    if max_backups <= 0:
        return
    files = sorted(backups_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[max_backups:]:
        try:
            path.unlink()
        except Exception:
            continue
