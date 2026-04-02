from __future__ import annotations

import subprocess
from pathlib import Path
import json

import requests


class AcoustIdRecognizer:
    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self._fingerprint_cache: dict[tuple[str, float], tuple[int, str]] = {}

    def fingerprint(self, audio_path: Path) -> tuple[int, str] | None:
        try:
            cache_key = (str(audio_path), audio_path.stat().st_mtime)
        except Exception:
            cache_key = (str(audio_path), 0.0)
        if cache_key in self._fingerprint_cache:
            return self._fingerprint_cache[cache_key]

        commands = [
            ["fpcalc", "-json", "-length", "120", str(audio_path)],
            [str(Path(__file__).resolve().parents[2] / "tools" / "fpcalc.exe"), "-json", "-length", "120", str(audio_path)],
        ]
        try:
            for command in commands:
                proc = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                payload = json.loads(proc.stdout)
                duration = int(payload["duration"])
                fingerprint = str(payload["fingerprint"])
                result = (duration, fingerprint)
                self._fingerprint_cache[cache_key] = result
                return result
            return None
        except Exception:
            return None

    def recognize(self, audio_path: Path) -> dict | None:
        if not self.api_key:
            return None
        fp = self.fingerprint(audio_path)
        if not fp:
            return None
        duration, fingerprint = fp
        url = "https://api.acoustid.org/v2/lookup"
        try:
            for meta in ("recordings+releasegroups+compress", "recordings+releasegroups"):
                params = {
                    "client": self.api_key,
                    "duration": duration,
                    "fingerprint": fingerprint,
                    "meta": meta,
                }
                resp = requests.get(url, params=params, timeout=12)
                resp.raise_for_status()
                payload = resp.json()
                results = payload.get("results", []) if isinstance(payload, dict) else []
                if results:
                    return payload
            return None
        except Exception:
            return None
