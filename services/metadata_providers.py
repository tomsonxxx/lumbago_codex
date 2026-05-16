from __future__ import annotations

import requests

from core.config import default_musicbrainz_user_agent, normalize_musicbrainz_user_agent


class MusicBrainzProvider:
    def __init__(self, app_name: str | None = None):
        self.app_name = (
            normalize_musicbrainz_user_agent(app_name)
            if app_name
            else default_musicbrainz_user_agent()
        )

    def _headers(self) -> dict:
        return {"User-Agent": self.app_name}

    def search_recording(self, query: str, limit: int = 10) -> dict | None:
        url = "https://musicbrainz.org/ws/2/recording/"
        params = {"query": query, "fmt": "json", "limit": max(1, limit)}
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def search(self, query: str, limit: int = 5) -> list[dict]:
        result = self.search_recording(query, limit=limit)
        if not result:
            return []
        recordings = result.get("recordings", [])
        return recordings[:limit]

    def get_recording(self, mbid: str) -> dict | None:
        """Full recording lookup by MBID — returns ISRC, releases, labels."""
        url = f"https://musicbrainz.org/ws/2/recording/{mbid}"
        params = {"inc": "artist-credits+releases+isrcs+label-info", "fmt": "json"}
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=10)
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
        self._limiter.wait()
        return super().search(query, limit)

    def get_recording(self, mbid: str) -> dict | None:
        self._limiter.wait()
        return super().get_recording(mbid)


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


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _best_mbid_from_acoustid(payload: dict) -> str | None:
    """Return the best MusicBrainz recording ID from an AcoustID lookup response."""
    results = payload.get("results", [])
    if not results:
        return None
    best = max(results, key=lambda r: float(r.get("score", 0)))
    if float(best.get("score", 0)) < 0.75:
        return None
    recordings = best.get("recordings", [])
    if not recordings:
        return None
    return recordings[0].get("id")


def _parse_mb_recording(recording: dict) -> dict:
    """Convert a MusicBrainz recording dict to a flat metadata dict."""
    meta: dict = {}

    if title := recording.get("title"):
        meta["title"] = title

    # Artist (join all credits)
    credits = recording.get("artist-credit", [])
    artist_str = _join_artist_credits(credits)
    if artist_str:
        meta["artist"] = artist_str

    # ISRC (first one)
    isrcs = recording.get("isrcs", [])
    if isrcs:
        meta["isrc"] = isrcs[0]

    # From releases: pick earliest by date
    releases = recording.get("releases", [])
    if releases:
        sorted_releases = sorted(releases, key=lambda r: r.get("date") or "9999")
        earliest = sorted_releases[0]

        if album := earliest.get("title"):
            meta["album"] = album

        date_str = earliest.get("date", "")
        if date_str and len(date_str) >= 4:
            year = date_str[:4]
            if year.isdigit() and 1900 <= int(year) <= 2100:
                meta["year"] = year

        # Track number from first medium
        for medium in earliest.get("media", []):
            tracks = medium.get("tracks", [])
            if tracks:
                tn = tracks[0].get("number") or str(tracks[0].get("position", ""))
                if tn:
                    meta["tracknumber"] = str(tn)
                break

        # Publisher (label)
        for li in earliest.get("label-info", []):
            if isinstance(li, dict) and li.get("label"):
                label_name = li["label"].get("name", "")
                if label_name:
                    meta["publisher"] = label_name
                    break

        # Album artist from release
        release_credits = earliest.get("artist-credit", [])
        albumartist_str = _join_artist_credits(release_credits)
        if albumartist_str:
            meta["albumartist"] = albumartist_str

        disambiguation_parts = [
            str(recording.get("disambiguation") or "").strip(),
            str(earliest.get("disambiguation") or "").strip(),
        ]
        comment = " / ".join(part for part in dict.fromkeys(disambiguation_parts) if part)
        if comment:
            meta["comment"] = comment

    return meta


def _join_artist_credits(credits: list) -> str:
    parts: list[str] = []
    for ac in credits:
        if isinstance(ac, str):
            parts.append(ac)
        elif isinstance(ac, dict):
            name = ac.get("name") or ac.get("artist", {}).get("name", "")
            joinphrase = ac.get("joinphrase", "")
            if name:
                parts.append(name + joinphrase)
    return "".join(parts).strip()
