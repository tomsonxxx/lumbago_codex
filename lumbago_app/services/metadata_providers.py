from __future__ import annotations

import time

import requests


def _get_with_retry(url: str, params: dict, headers: dict, timeout: int, retries: int = 2) -> requests.Response:
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
    raise last_exc  # type: ignore[misc]


class MusicBrainzProvider:
    def __init__(self, app_name: str | None):
        self.app_name = app_name or "LumbagoMusicAI"

    def search_recording(self, query: str) -> dict | None:
        url = "https://musicbrainz.org/ws/2/recording/"
        params = {"query": query, "fmt": "json"}
        headers = {"User-Agent": self.app_name}
        try:
            resp = _get_with_retry(url, params=params, headers=headers, timeout=20)
            return resp.json()
        except Exception:
            return None


class DiscogsProvider:
    def __init__(self, token: str | None):
        self.token = token

    def search_release(self, query: str) -> dict | None:
        if not self.token:
            return None
        url = "https://api.discogs.com/database/search"
        params = {"q": query, "type": "release", "token": self.token}
        try:
            resp = _get_with_retry(url, params=params, headers={}, timeout=20)
            return resp.json()
        except Exception:
            return None
