from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.config import cache_dir


def analysis_cache_path(audio_path: Path) -> Path:
    key = _safe_key(audio_path)
    return cache_dir() / f"{key}_analysis.json"


def load_analysis_cache(audio_path: Path) -> dict | None:
    path = analysis_cache_path(audio_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_analysis_cache(audio_path: Path, payload: dict) -> None:
    path = analysis_cache_path(audio_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return


def _safe_key(audio_path: Path) -> str:
    digest = hashlib.sha1(str(audio_path).encode("utf-8", errors="ignore")).hexdigest()
    return digest[:16]
