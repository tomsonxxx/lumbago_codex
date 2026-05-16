from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path
import json

import requests

log = logging.getLogger(__name__)

# Semafory ograniczające równoległe zapytania do zewnętrznych źródeł.
# Dzięki nim wiele plików może być w różnych fazach pipeline jednocześnie
# (jeden czeka na AcoustID, drugi na fpcalc, trzeci na MusicBrainz).
_FPCALC_SEM = threading.Semaphore(2)   # maks. 2 równoległe procesy fpcalc
_ACOUSTID_SEM = threading.Semaphore(1)  # maks. 1 równoległe zapytanie AcoustID


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
        for command in commands:
            try:
                with _FPCALC_SEM:
                    proc = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=12,
                    )
                payload = json.loads(proc.stdout)
                duration = int(payload["duration"])
                fingerprint = str(payload["fingerprint"])
                result = (duration, fingerprint)
                self._fingerprint_cache[cache_key] = result
                return result
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                log.warning("fpcalc timeout: %s", audio_path)
                return None
            except Exception as exc:
                log.debug("fpcalc error for %s: %s", audio_path, exc)
                continue
        log.debug("fpcalc not available (tried %d commands)", len(commands))
        return None

    def recognize(self, audio_path: Path) -> dict | None:
        if not self.api_key:
            return None
        fp = self.fingerprint(audio_path)
        if not fp:
            return None
        duration, fingerprint = fp

        # Cache lookup — jeśli ten fingerprint był już wyszukiwany, użyj wynik z SQLite.
        _CACHE_TTL = 30 * 24 * 3600
        cache_key = f"acoustid_fp:{fingerprint[:64]}"
        try:
            from data.repository import get_metadata_cache, set_metadata_cache
            cached = get_metadata_cache(cache_key, max_age_seconds=_CACHE_TTL)
            if cached:
                return cached
        except Exception:
            set_metadata_cache = None  # type: ignore[assignment]

        url = "https://api.acoustid.org/v2/lookup"
        try:
            for meta in ("recordings+releasegroups+compress", "recordings+releasegroups"):
                params = {
                    "client": self.api_key,
                    "duration": duration,
                    "fingerprint": fingerprint,
                    "meta": meta,
                }
                with _ACOUSTID_SEM:
                    resp = requests.get(url, params=params, timeout=7)
                resp.raise_for_status()
                payload = resp.json()
                results = payload.get("results", []) if isinstance(payload, dict) else []
                if results:
                    try:
                        set_metadata_cache(cache_key, payload, source="acoustid")
                    except Exception:
                        pass
                    return payload
            return None
        except requests.exceptions.Timeout:
            log.warning("AcoustID timeout for %s", audio_path)
            return None
        except Exception as exc:
            log.warning("AcoustID error for %s: %s", audio_path, exc)
            return None
