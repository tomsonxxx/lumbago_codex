from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

from core.config import app_data_dir, settings_path


def perform_backup(max_backups: int = 10) -> None:
    data_dir = app_data_dir()
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = data_dir / "lumbago.db"
    settings_file = settings_path()
    if db_path.exists():
        _copy_file(db_path, backups_dir / f"lumbago_{timestamp}.db")
    if settings_file.exists():
        _copy_file(settings_file, backups_dir / f"settings_{timestamp}.json")
    _trim_backups(backups_dir, max_backups)


def _copy_file(src: Path, dst: Path) -> None:
    try:
        shutil.copy2(src, dst)
    except Exception:
        return


def _trim_backups(backups_dir: Path, max_backups: int) -> None:
    if max_backups <= 0:
        return
    files = sorted(backups_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[max_backups:]:
        try:
            path.unlink()
        except Exception:
            continue
