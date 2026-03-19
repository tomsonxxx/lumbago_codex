"""Fuzzy deduplication serwis - rapidfuzz 85% threshold."""
from __future__ import annotations
import hashlib, logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lumbago_app.core.models import Track

logger = logging.getLogger(__name__)
SIMILARITY_THRESHOLD = 85.0
DURATION_TOLERANCE_S = 3.0
HASH_CHUNK_SIZE = 256 * 1024


@dataclass
class DuplicateGroup:
    tracks: list = field(default_factory=list)
    similarity: float = 100.0
    match_method: str = "exact"


class FuzzyDedupService:
    SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD

    def dedup_hash_256kb(self, path: Path) -> str:
        try:
            size = path.stat().st_size
            with path.open("rb") as f:
                chunk = f.read(HASH_CHUNK_SIZE)
            return hashlib.sha256(chunk + str(size).encode()).hexdigest()
        except OSError as exc:
            logger.warning("Hash error %s: %s", path, exc)
            return ""

    def find_exact_duplicates(self, tracks: list) -> list[DuplicateGroup]:
        from collections import defaultdict
        hmap: dict[str, list] = defaultdict(list)
        for t in tracks:
            p = Path(t.path)
            if p.exists():
                h = self.dedup_hash_256kb(p)
                if h:
                    hmap[h].append(t)
        return [DuplicateGroup(tracks=g, similarity=100.0, match_method="hash_exact")
                for g in hmap.values() if len(g) > 1]

    def find_fuzzy_duplicates(self, tracks: list) -> list[DuplicateGroup]:
        try:
            from rapidfuzz import fuzz
        except ImportError:
            logger.error("rapidfuzz nie zainstalowana")
            return []
        pairs = []
        n = len(tracks)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = tracks[i], tracks[j]
                if abs((a.duration or 0) - (b.duration or 0)) > DURATION_TOLERANCE_S:
                    continue
                ta = (a.title or Path(a.path).stem).lower()
                tb = (b.title or Path(b.path).stem).lower()
                score = fuzz.token_sort_ratio(ta, tb)
                if score >= self.SIMILARITY_THRESHOLD:
                    pairs.append((a, b, float(score)))
        return self._pairs_to_groups(pairs, tracks)

    def _pairs_to_groups(self, pairs, all_tracks) -> list[DuplicateGroup]:
        from collections import defaultdict
        adj: dict[str, set[str]] = defaultdict(set)
        sim_map: dict[tuple, float] = {}
        for a, b, score in pairs:
            adj[a.path].add(b.path); adj[b.path].add(a.path)
            k = (min(a.path, b.path), max(a.path, b.path))
            sim_map[k] = score
        tmap = {t.path: t for t in all_tracks}
        visited: set[str] = set()
        groups = []
        for path in adj:
            if path in visited:
                continue
            cluster, queue, min_sim = [], [path], 100.0
            while queue:
                cur = queue.pop()
                if cur in visited: continue
                visited.add(cur)
                if cur in tmap: cluster.append(tmap[cur])
                for nb in adj[cur]:
                    if nb not in visited:
                        queue.append(nb)
                        k = (min(cur, nb), max(cur, nb))
                        min_sim = min(min_sim, sim_map.get(k, 100.0))
            if len(cluster) > 1:
                groups.append(DuplicateGroup(tracks=cluster, similarity=min_sim, match_method="fuzzy_tags"))
        return groups

    def compute_health_stats(self, tracks: list) -> dict:
        total = len(tracks)
        if total == 0:
            return {"total": 0, "fields": {}, "overall_score": 0}
        def pct(c): return round(c / total * 100, 1)
        has_bpm = sum(1 for t in tracks if t.bpm and t.bpm > 0)
        has_key = sum(1 for t in tracks if t.key and t.key.strip())
        has_genre = sum(1 for t in tracks if t.genre and t.genre.strip())
        has_artwork = sum(1 for t in tracks if t.artwork_path and Path(t.artwork_path).exists())
        has_mood = sum(1 for t in tracks if t.mood and t.mood.strip())
        has_energy = sum(1 for t in tracks if t.energy is not None)
        has_year = sum(1 for t in tracks if t.year and str(t.year).strip())
        has_rating = sum(1 for t in tracks if t.rating and t.rating > 0)
        fields = {
            "bpm": {"count": has_bpm, "pct": pct(has_bpm), "missing": total - has_bpm},
            "key": {"count": has_key, "pct": pct(has_key), "missing": total - has_key},
            "genre": {"count": has_genre, "pct": pct(has_genre), "missing": total - has_genre},
            "artwork": {"count": has_artwork, "pct": pct(has_artwork), "missing": total - has_artwork},
            "mood": {"count": has_mood, "pct": pct(has_mood), "missing": total - has_mood},
            "energy": {"count": has_energy, "pct": pct(has_energy), "missing": total - has_energy},
            "year": {"count": has_year, "pct": pct(has_year), "missing": total - has_year},
            "rating": {"count": has_rating, "pct": pct(has_rating), "missing": total - has_rating},
        }
        score = round((has_bpm+has_key+has_genre+has_artwork+has_mood+has_energy)/(total*6)*100, 1)
        return {"total": total, "fields": fields, "overall_score": score}
