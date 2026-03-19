"""
Lumbago Music AI — Cache odpowiedzi LLM
=========================================
Unika ponownego wysyłania tych samych metadanych do AI.
Klucz cache = hash JSON metadanych + nazwa providera.
"""

import datetime
import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Domyślny czas wygaśnięcia cache: 30 dni
DEFAULT_TTL_DAYS = 30


class LLMCache:
    """
    Cache odpowiedzi LLM przechowywany w bazie danych (MetadataCacheOrm).

    Klucz cache = SHA256(provider + JSON(tracks_meta_sorted)).
    """

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def _make_key(self, tracks_meta: list[dict[str, Any]]) -> str:
        """Generuje unikalny klucz cache dla zestawu metadanych."""
        payload = json.dumps(
            {"provider": self.provider_name, "tracks": tracks_meta},
            sort_keys=True, ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def get(self, tracks_meta: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """
        Sprawdza cache dla podanych metadanych.

        Returns:
            Słownik wyników lub None jeśli brak / wygasło.
        """
        key = self._make_key(tracks_meta)
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.repository import MetadataCacheRepository

            with session_scope() as session:
                repo = MetadataCacheRepository(session)
                cached = repo.get_fresh(f"llm:{key}")
                if cached:
                    logger.debug("Cache HIT dla LLM key=%s", key[:8])
                    return json.loads(cached.data_json)
        except Exception as exc:
            logger.debug("Błąd odczytu cache LLM: %s", exc)
        return None

    def set(
        self,
        tracks_meta: list[dict[str, Any]],
        result: dict[str, Any],
        ttl_days: int = DEFAULT_TTL_DAYS,
    ) -> None:
        """
        Zapisuje wyniki do cache.

        Args:
            tracks_meta: Oryginalne metadane (klucz).
            result: Wyniki tagowania.
            ttl_days: Czas wygaśnięcia w dniach.
        """
        key = self._make_key(tracks_meta)
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.models import MetadataCacheOrm
            from lumbago_app.data.repository import MetadataCacheRepository

            expires = datetime.datetime.utcnow() + datetime.timedelta(days=ttl_days)
            row = MetadataCacheOrm(
                cache_key=f"llm:{key}",
                source=f"llm_{self.provider_name}",
                data_json=json.dumps(result, ensure_ascii=False),
                expires_at=expires,
            )
            with session_scope() as session:
                repo = MetadataCacheRepository(session)
                repo.set(row)
            logger.debug("Cache SET dla LLM key=%s (wygasa %s)", key[:8], expires.date())
        except Exception as exc:
            logger.warning("Błąd zapisu cache LLM: %s", exc)
