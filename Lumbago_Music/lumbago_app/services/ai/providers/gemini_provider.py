"""
Lumbago Music AI — Provider Google Gemini
==========================================
"""

import logging

from lumbago_app.services.ai.providers.base_provider import (
    BaseProvider, TagResult, TrackMeta,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Provider AI korzystający z Google Gemini API."""

    provider_name = "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Taguje utwory używając Google Gemini API.

        Raises:
            AIError: Przy błędzie API.
            RateLimitError: Przy przekroczeniu limitu.
        """
        from lumbago_app.core.exceptions import AIError, RateLimitError

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise AIError("Biblioteka google-generativeai nie jest zainstalowana") from exc

        genai.configure(api_key=self.api_key)
        gemini_model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=self._build_system_prompt(),
        )

        try:
            prompt = self._build_user_prompt(tracks_meta)
            response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )
            content = response.text or "{}"
            logger.debug("Gemini odpowiedź: %d znaków", len(content))
            return self._parse_response(content)

        except Exception as exc:
            error_str = str(exc).lower()
            if "quota" in error_str or "rate" in error_str:
                raise RateLimitError("gemini") from exc
            raise AIError(f"Błąd Gemini API: {exc}") from exc
