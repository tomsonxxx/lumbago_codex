"""
Lumbago Music AI — Provider OpenAI (GPT)
==========================================
"""

import logging

from lumbago_app.services.ai.providers.base_provider import (
    BaseProvider, TagResult, TrackMeta,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """Provider AI korzystający z OpenAI GPT API."""

    provider_name = "openai"

    def is_available(self) -> bool:
        """Sprawdza dostępność klucza API."""
        return bool(self.api_key)

    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Taguje utwory używając OpenAI Chat Completions API.

        Args:
            tracks_meta: Lista metadanych utworów.

        Returns:
            Słownik track_id -> tagi.

        Raises:
            AIError: Przy błędzie API.
            RateLimitError: Przy 429.
        """
        from lumbago_app.core.exceptions import AIError, RateLimitError

        try:
            from openai import OpenAI, RateLimitError as OAIRateLimit
        except ImportError as exc:
            raise AIError("Biblioteka openai nie jest zainstalowana") from exc

        client = OpenAI(api_key=self.api_key)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(tracks_meta)},
                ],
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            logger.debug(
                "OpenAI odpowiedź: %d tokenów",
                response.usage.total_tokens if response.usage else 0,
            )
            return self._parse_response(content)

        except OAIRateLimit as exc:
            raise RateLimitError("openai") from exc
        except Exception as exc:
            raise AIError(f"Błąd OpenAI: {exc}") from exc
