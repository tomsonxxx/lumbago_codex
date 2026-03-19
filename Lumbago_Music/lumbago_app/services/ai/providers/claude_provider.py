"""
Lumbago Music AI — Provider Anthropic Claude
=============================================
"""

import logging

from lumbago_app.services.ai.providers.base_provider import (
    BaseProvider, TagResult, TrackMeta,
)

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseProvider):
    """Provider AI korzystający z Anthropic Claude API."""

    provider_name = "anthropic"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Taguje utwory używając Anthropic Messages API.

        Raises:
            AIError: Przy błędzie API.
            RateLimitError: Przy przeciążeniu serwera.
        """
        from lumbago_app.core.exceptions import AIError, RateLimitError

        try:
            import anthropic
        except ImportError as exc:
            raise AIError("Biblioteka anthropic nie jest zainstalowana") from exc

        client = anthropic.Anthropic(api_key=self.api_key)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self._build_system_prompt(),
                messages=[
                    {"role": "user", "content": self._build_user_prompt(tracks_meta)},
                ],
                temperature=0.3,
            )
            content = response.content[0].text if response.content else "{}"
            logger.debug(
                "Claude odpowiedź: %d tokenów (in=%d, out=%d)",
                response.usage.input_tokens + response.usage.output_tokens,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
            return self._parse_response(content)

        except anthropic.RateLimitError as exc:
            raise RateLimitError("anthropic") from exc
        except anthropic.APIError as exc:
            raise AIError(f"Błąd Claude API: {exc}") from exc
