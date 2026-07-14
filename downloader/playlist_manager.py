from __future__ import annotations

"""
Playlist manager + checkpoint + helpers dla dużych playlist (700+).

- Deduplikacja po video_id
- Lazy entry iterator
- Checkpoint JSON (zapis pobranych ID)
- Filename sanitize (Windows-safe)
- Estymacja (prosta)

Per prompt spec.
Per SZPIEG research + ... 2026-06-27 + "dalej" (est dialog+disk ...) + CHECKLIST... must document identical.
"""

from pathlib import Path
import json
import re
from typing import Any, Iterator

_ILLEGAL_FS_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str, max_len: int = 180) -> str:
    name = _ILLEGAL_FS_CHARS.sub("_", name).strip()
    # Windows reserved
    for bad in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT1"):
        if name.upper().startswith(bad):
            name = "_" + name
            break
    if len(name) > max_len:
        name = name[:max_len-10] + "..." + name[-7:]
    return name or "track"


def checkpoint_path(output_dir: Path, url: str) -> Path:
    # Prosty hash url do nazwy pliku checkpointu
    safe = re.sub(r"[^a-zA-Z0-9]", "_", url)[:64]
    return output_dir / f".lumbago_dl_checkpoint_{safe}.json"


def load_checkpoint(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("downloaded_ids", []))
    except Exception:
        return set()


def save_checkpoint(path: Path, downloaded_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = {"downloaded_ids": sorted(downloaded_ids)}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass  # non-fatal


def iter_playlist_entries(info: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """
    Lazy iterator po wpisach playlisty lub pojedynczym.
    Nie ładuje wszystkiego jeśli nie trzeba.
    """
    if not info:
        return
    entries = info.get("entries")
    if entries:
        for e in entries:
            if e:
                yield e
    else:
        # single video / track
        yield info


def estimate_playlist_size(entries_sample: list[dict[str, Any]], total_count: int) -> dict[str, Any]:
    """
    Prosta estymacja rozmiaru/czasu na podstawie pierwszych N entry (bez pełnego download).
    Używane przed startem dla dużych playlist (700+).
    Zwraca dict z approx_duration_sec, approx_size_mb, warning.
    """
    if not entries_sample or total_count <= 0:
        return {"approx_duration_sec": 0, "approx_size_mb": 0, "warning": "Brak danych do estymacji"}

    sample_count = len(entries_sample)
    total_dur = sum(e.get("duration") or 0 for e in entries_sample)
    avg_dur = total_dur / sample_count if sample_count else 180  # fallback ~3min

    # Bardzo przybliżone: assume ~10MB per minute for high quality audio
    avg_size_mb = (avg_dur / 60.0) * 10.0
    total_size_mb = avg_size_mb * total_count
    total_dur_sec = avg_dur * total_count

    warning = ""
    if total_size_mb > 5000:  # >5GB rough
        warning = f"OSTRZEŻENIE: Szacowany rozmiar ~{int(total_size_mb/1000)} GB. Duże playlisty WAV mogą zająć dużo miejsca!"

    return {
        "approx_duration_sec": int(total_dur_sec),
        "approx_size_mb": int(total_size_mb),
        "warning": warning,
        "sample_used": sample_count,
    }
