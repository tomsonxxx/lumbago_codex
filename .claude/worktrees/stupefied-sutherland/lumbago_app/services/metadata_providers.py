from __future__ import annotations

import requests


class MusicBrainzProvider:
    def __init__(self, app_name: str | None):
        self.app_name = app_name or "LumbagoMusicAI"

    def search_recording(self, query: str) -> dict | None:
        url = "https://musicbrainz.org/ws/2/recording/"
        params = {"query": query, "fmt": "json"}
        headers = {"User-Agent": self.app_name}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
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
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

