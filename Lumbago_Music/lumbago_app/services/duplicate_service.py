"""
Lumbago Music AI — Serwis wykrywania duplikatów
================================================
Wykrywa duplikaty po hashu, fingerprinte, lub rozmytym tytule+artyście.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Grupa zduplikowanych utworów."""
    method: str          # "hash", "fingerprint", "fuzzy"
    track_ids: list[int]
    similarity: float    # 0.0 - 1.0


class DuplicateService:
    """
    Wykrywa duplikaty w bibliotece muzycznej.

    Metody:
    - hash: identyczne pliki (SHA256)
    - fingerprint: ten sam utwór (AcoustID)
    - fuzzy: podobny artysta+tytuł (rapidfuzz)
    """

    def find_all(self, threshold: float = 0.9) -> list[DuplicateGroup]:
        """
        Szuka wszystkich duplikatów w bibliotece.

        Args:
            threshold: Próg podobieństwa dla fuzzy matching (0-1).

        Returns:
            Lista grup duplikatów.
        """
        raise NotImplementedError(
            "DuplicateService.find_all() — do implementacji w FAZIE 2.\n"
            "Plan: 1) hash match przez GROUP BY file_hash,\n"
            "2) acoustid match przez fingerprint_id,\n"
            "3) fuzzy match przez rapidfuzz.process.extract()."
        )

    def find_by_hash(self) -> list[DuplicateGroup]:
        """Szuka duplikatów z identycznym hashem pliku."""
        raise NotImplementedError

    def find_by_fuzzy(self, threshold: float = 0.9) -> list[DuplicateGroup]:
        """Szuka duplikatów przez rozmyte dopasowanie tytułu+artysty."""
        raise NotImplementedError

    def resolve(
        self,
        group: DuplicateGroup,
        keep_id: int,
        action: str = "trash",
    ) -> None:
        """
        Rozwiązuje grupę duplikatów.

        Args:
            group: Grupa duplikatów.
            keep_id: ID utworu do zachowania.
            action: Co zrobić z resztą: "trash" | "delete" | "mark_only".
        """
        raise NotImplementedError(
            "DuplicateService.resolve() — do implementacji w FAZIE 2."
        )
