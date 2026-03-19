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

    def search(self, query: str, limit: int = 5) -> list[dict]:
        result = self.search_recording(query)
        if not result:
            return []
        recordings = result.get("recordings", [])
        return recordings[:limit]


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

    def search(self, query: str, limit: int = 5) -> list[dict]:
        result = self.search_release(query)
        if not result:
            return []
        results = result.get("results", [])
        return results[:limit]


import threading as _threading
import time as _time

class RateLimiter:
    def __init__(self, calls_per_second: float):
        self._interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
        self._last_call: float = 0.0
        self._lock = _threading.Lock()

    def wait(self):
        if self._interval == 0: return
        with self._lock:
            elapsed = _time.monotonic() - self._last_call
            if elapsed < self._interval:
                _time.sleep(self._interval - elapsed)
            self._last_call = _time.monotonic()


class RateLimitedMusicBrainzProvider(MusicBrainzProvider):
    _limiter = RateLimiter(calls_per_second=1.0)
    def search(self, query: str, limit: int = 5) -> list[dict]:
        self._limiter.wait(); return super().search(query, limit)


class RateLimitedDiscogsProvider(DiscogsProvider):
    _limiter = RateLimiter(calls_per_second=1.0)
    def search(self, query: str, limit: int = 5) -> list[dict]:
        self._limiter.wait(); return super().search(query, limit)


class FallbackMetadataChain:
    def __init__(self, acoustid_provider=None, mb_provider=None, discogs_provider=None):
        self._acoustid = acoustid_provider
        self._mb = mb_provider or RateLimitedMusicBrainzProvider()
        self._discogs = discogs_provider or RateLimitedDiscogsProvider()
        self.stats = {"acoustid_hits":0,"mb_hits":0,"discogs_hits":0,"misses":0}

    def enrich(self, track) -> dict | None:
        import logging; log = logging.getLogger(__name__)
        if self._acoustid and getattr(track,'fingerprint',None):
            try:
                r = self._acoustid.lookup(track.fingerprint, int(track.duration or 0))
                if r: self.stats["acoustid_hits"] += 1; return r
            except Exception as e: log.warning("AcoustID: %s", e)
        query = " ".join(filter(None,[getattr(track,'artist',''),getattr(track,'title','')])).strip()
        if query:
            try:
                r = self._mb.search(query, limit=1)
                if r: self.stats["mb_hits"] += 1; return r[0]
            except Exception as e: log.warning("MB: %s", e)
            try:
                r = self._discogs.search(query, limit=1)
                if r: self.stats["discogs_hits"] += 1; return r[0]
            except Exception as e: log.warning("Discogs: %s", e)
        self.stats["misses"] += 1; return None

    def get_stats_summary(self) -> str:
        s = self.stats
        return f"AcoustID:{s['acoustid_hits']} | MB:{s['mb_hits']} | Discogs:{s['discogs_hits']} | Puste:{s['misses']}"
