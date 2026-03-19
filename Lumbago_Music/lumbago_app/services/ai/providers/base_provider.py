"""
Lumbago Music AI — Bazowy provider LLM (ABC)
=============================================
Każdy provider AI musi dziedziczyć po BaseProvider
i zaimplementować metodę tag_tracks().
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Typ wejściowy: lista słowników z metadanymi utworu
TrackMeta = dict[str, Any]

# Typ wyjściowy: słownik track_id -> dict z tagami
TagResult = dict[str | int, dict[str, Any]]


class BaseProvider(ABC):
    """
    Abstrakcyjna klasa bazowa dla providerów AI.

    Każdy provider implementuje:
    - tag_tracks(): wysyła metadane utworów, zwraca tagi
    - is_available(): sprawdza czy klucz API jest skonfigurowany
    """

    #: Nazwa providera (np. "openai", "anthropic")
    provider_name: str = ""

    def __init__(self, api_key: str, model: str) -> None:
        """
        Args:
            api_key: Klucz API do serwisu.
            model: Identyfikator modelu LLM.
        """
        self.api_key = api_key
        self.model = model
        self._logger = logging.getLogger(
            f"{__name__}.{self.provider_name or type(self).__name__}"
        )

    @abstractmethod
    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Wysyła metadane utworów do LLM i zwraca zaproponowane tagi.

        Args:
            tracks_meta: Lista słowników z polami:
                - id: int — identyfikator utworu w bazie
                - title: str
                - artist: str
                - album: str | None
                - genre: str | None
                - bpm: float | None
                - key: str | None
                - duration: float | None

        Returns:
            Słownik: track_id -> {
                "genre": str,
                "mood": list[str],
                "style": str,
                "energy_level": int,
                "tags": list[str],
                "confidence": float,
            }

        Raises:
            AIError: Przy błędzie komunikacji z API.
            RateLimitError: Przy przekroczeniu limitu zapytań.
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Sprawdza czy provider jest dostępny (klucz API skonfigurowany, sieć OK).

        Returns:
            True jeśli provider gotowy do użycia.
        """
        raise NotImplementedError

    def _build_system_prompt(self) -> str:
        """Zwraca systemowy prompt dla AI taggera."""
        return (
            "Jesteś ekspertem muzycznym specjalizującym się w klasyfikacji muzyki elektronicznej "
            "i DJ sets. Twoim zadaniem jest analiza metadanych utworów i przypisanie im:\n"
            "- gatunku muzycznego (genre)\n"
            "- nastrojów (mood): lista 1-4 przymiotników\n"
            "- stylu (style): opis w 2-5 słowach\n"
            "- poziomu energii (energy_level): liczba 1-10\n"
            "- tagów (tags): lista 3-8 słów kluczowych\n\n"
            "Odpowiadaj WYŁĄCZNIE w formacie JSON. Nie dodawaj wyjaśnień poza JSON.\n"
            "Format: {\"results\": [{\"id\": <track_id>, \"genre\": \"...\", "
            "\"mood\": [...], \"style\": \"...\", \"energy_level\": N, "
            "\"tags\": [...], \"confidence\": 0.0-1.0}]}"
        )

    def _build_user_prompt(self, tracks_meta: list[TrackMeta]) -> str:
        """Buduje prompt użytkownika z metadanymi utworów."""
        lines = ["Przeanalizuj poniższe utwory i przypisz tagi:\n"]
        for t in tracks_meta:
            parts = [f"ID={t.get('id', '?')}"]
            if t.get("artist"):
                parts.append(f"Artysta: {t['artist']}")
            if t.get("title"):
                parts.append(f"Tytuł: {t['title']}")
            if t.get("album"):
                parts.append(f"Album: {t['album']}")
            if t.get("genre"):
                parts.append(f"Gatunek: {t['genre']}")
            if t.get("bpm"):
                parts.append(f"BPM: {t['bpm']:.1f}")
            if t.get("key"):
                parts.append(f"Tonacja: {t['key']}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def _parse_response(self, response_text: str) -> TagResult:
        """
        Parsuje odpowiedź JSON z LLM.

        Args:
            response_text: Surowy tekst odpowiedzi.

        Returns:
            Słownik track_id -> tagi.

        Raises:
            LLMResponseError: Jeśli odpowiedź nie jest poprawnym JSON.
        """
        import json
        import re
        from lumbago_app.core.exceptions import LLMResponseError

        # Wyodrębnij JSON z odpowiedzi (może zawierać markdown code block)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise LLMResponseError(
                f"Brak JSON w odpowiedzi: {response_text[:200]}"
            )

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"Nieprawidłowy JSON: {exc}") from exc

        result: TagResult = {}
        for item in data.get("results", []):
            track_id = item.pop("id", None)
            if track_id is not None:
                result[track_id] = item

        return result

    def __repr__(self) -> str:
        return f"<{type(self).__name__} model={self.model!r}>"
