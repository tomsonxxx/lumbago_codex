from __future__ import annotations

import subprocess
from pathlib import Path

import requests


class AcoustIdRecognizer:
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def fingerprint(self, audio_path: Path) -> tuple[int, str] | None:
        try:
            proc = subprocess.run(
                ["fpcalc", "-json", str(audio_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            import json

            payload = json.loads(proc.stdout)
            return int(payload["duration"]), payload["fingerprint"]
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
        params = {
            "client": self.api_key,
            "duration": duration,
            "fingerprint": fingerprint,
            "meta": "recordings+releasegroups+compress",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

