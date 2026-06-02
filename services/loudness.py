from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


def analyze_loudness(path: Path) -> float | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    args = [
        ffmpeg,
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        "loudnorm=print_format=json",
        "-f",
        "null",
        "-",
    ]
    _, stderr = _run_ffmpeg(args, timeout=90)
    payload = _extract_json(stderr or "")
    if not payload:
        return None
    value = payload.get("input_i")
    return _to_float(value)


def normalize_loudness(
    path: Path,
    output_path: Path,
    target_lufs: float = -14.0,
    true_peak: float = -1.5,
    lra: float = 11.0,
) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}",
        str(output_path),
    ]
    code, _ = _run_ffmpeg(args, timeout=300)
    return code == 0


def _run_ffmpeg(args: list[str], timeout: int = 120) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            check=False,
            timeout=timeout
        )
        return result.returncode, result.stderr or ""
    except subprocess.TimeoutExpired:
        return 1, "ffmpeg timeout"
    except Exception as e:
        return 1, str(e)


def _extract_json(text: str) -> dict | None:
    matches = list(re.finditer(r"\{.*?\}", text, re.DOTALL))
    if not matches:
        return None
    last = matches[-1].group(0)
    try:
        return json.loads(last)
    except Exception:
        return None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
