"""
Lumbago Music AI — Provider xAI Grok
=======================================
Grok używa OpenAI-compatible API z innym base_url.
"""

import logging

from lumbago_app.services.ai.providers.base_provider import (
    BaseProvider, TagResult, TrackMeta,
)

logger = logging.getLogger(__name__)

GROK_BASE_URL = "https://api.x.ai/v1"


class GrokProvider(BaseProvider):
    """Provider AI korzystający z xAI Grok API (OpenAI-compatible)."""

    provider_name = "grok"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Taguje utwory używając xAI Grok API.

        Raises:
            AIError: Przy błędzie API.
            RateLimitError: Przy 429.
        """
        from lumbago_app.core.exceptions import AIError, RateLimitError

        try:
            from openai import OpenAI, RateLimitError as OAIRateLimit
        except ImportError as exc:
            raise AIError("Biblioteka openai nie jest zainstalowana") from exc

        client = OpenAI(api_key=self.api_key, base_url=GROK_BASE_URL)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(tracks_meta)},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_response(content)

        except OAIRateLimit as exc:
            raise RateLimitError("grok") from exc
        except Exception as exc:
            raise AIError(f"Błąd Grok API: {exc}") from exc
