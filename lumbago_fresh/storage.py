from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import Track


APP_DIR_NAME = "LumbagoFresh"
LIBRARY_FILE = "library.json"
SETTINGS_FILE = "settings.json"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    target = Path(base) / APP_DIR_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_library() -> list[Track]:
    path = app_data_dir() / LIBRARY_FILE
    rows = _read_json(path, default=[])
    tracks: list[Track] = []
    for row in rows:
        if isinstance(row, dict) and row.get("path"):
            tracks.append(Track.from_dict(row))
    return tracks


def save_library(tracks: list[Track]) -> None:
    path = app_data_dir() / LIBRARY_FILE
    _write_json(path, [t.to_dict() for t in tracks])


def load_settings() -> dict[str, Any]:
    path = app_data_dir() / SETTINGS_FILE
    defaults: dict[str, Any] = {
        "watch_folder": "",
        "watch_enabled": False,
        "watch_interval_sec": 6,
        "auto_tag_on_import": True,
    }
    loaded = _read_json(path, default={})
    if not isinstance(loaded, dict):
        loaded = {}
    defaults.update(loaded)
    return defaults


def save_settings(settings: dict[str, Any]) -> None:
    path = app_data_dir() / SETTINGS_FILE
    _write_json(path, settings)

