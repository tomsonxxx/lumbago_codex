"""
Lumbago Music AI — LLM Cost Router
=====================================
Automatycznie wybiera najtańszego dostępnego providera AI.
Obsługuje fallback i logowanie kosztów.
"""

import logging
from typing import Optional

from lumbago_app.core.constants import AI_PROVIDERS_COST
from lumbago_app.services.ai.providers.base_provider import (
    BaseProvider, TagResult, TrackMeta,
)

logger = logging.getLogger(__name__)


class CostRouter:
    """
    Router wybierający najtańszego dostępnego providera AI.

    Priorytet wyboru (rosnący koszt):
      gemini → deepseek → openai → anthropic → grok

    Jeśli wybrany provider zawiedzie, automatycznie próbuje kolejny.
    """

    def __init__(self) -> None:
        self._providers: list[BaseProvider] = []
        self._build_providers()

    def _build_providers(self) -> None:
        """Inicjalizuje i sortuje providerów wg kosztu."""
        from lumbago_app.core.config import get_settings
        settings = get_settings()

        # Mapa: nazwa -> (klucz API, model, klasa)
        provider_map = {
            "openai": (
                settings.OPENAI_API_KEY,
                settings.OPENAI_MODEL,
                "lumbago_app.services.ai.providers.openai_provider.OpenAIProvider",
            ),
            "anthropic": (
                settings.ANTHROPIC_API_KEY,
                settings.ANTHROPIC_MODEL,
                "lumbago_app.services.ai.providers.claude_provider.ClaudeProvider",
            ),
            "grok": (
                settings.GROK_API_KEY,
                settings.GROK_MODEL,
                "lumbago_app.services.ai.providers.grok_provider.GrokProvider",
            ),
            "deepseek": (
                settings.DEEPSEEK_API_KEY,
                settings.DEEPSEEK_MODEL,
                "lumbago_app.services.ai.providers.deepseek_provider.DeepSeekProvider",
            ),
            "gemini": (
                settings.GEMINI_API_KEY,
                settings.GEMINI_MODEL,
                "lumbago_app.services.ai.providers.gemini_provider.GeminiProvider",
            ),
        }

        # Sortuj wg priorytetu kosztu (priority=0 = najtańszy)
        sorted_names = sorted(
            AI_PROVIDERS_COST.keys(),
            key=lambda n: AI_PROVIDERS_COST[n].get("priority", 99),
        )

        for name in sorted_names:
            if name not in provider_map:
                continue
            api_key, model, class_path = provider_map[name]
            if not api_key:
                logger.debug("Provider %s pominięty — brak klucza API", name)
                continue

            try:
                provider_cls = self._import_class(class_path)
                provider = provider_cls(api_key=api_key, model=model)
                self._providers.append(provider)
                cost = AI_PROVIDERS_COST[name]
                logger.info(
                    "Provider %s załadowany (model=%s, koszt_in=%.5f$/1k)",
                    name, model, cost.get("input_per_1k", 0),
                )
            except Exception as exc:
                logger.warning("Nie można załadować providera %s: %s", name, exc)

        if not self._providers:
            logger.warning(
                "Brak dostępnych providerów AI — tagowanie AI wyłączone"
            )

    @staticmethod
    def _import_class(dotted_path: str) -> type:
        """Dynamicznie importuje klasę ze ścieżki 'moduł.Klasa'."""
        module_path, _, class_name = dotted_path.rpartition(".")
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @property
    def has_providers(self) -> bool:
        """Zwraca True jeśli jest co najmniej jeden skonfigurowany provider."""
        return len(self._providers) > 0

    def get_cheapest(self) -> Optional[BaseProvider]:
        """Zwraca najtańszego dostępnego providera lub None."""
        for provider in self._providers:
            if provider.is_available():
                return provider
        return None

    def tag_tracks(self, tracks_meta: list[TrackMeta]) -> TagResult:
        """
        Taguje utwory używając najtańszego dostępnego providera.
        Przy błędzie automatycznie przechodzi do następnego.

        Args:
            tracks_meta: Lista metadanych utworów.

        Returns:
            Słownik track_id -> tagi.

        Raises:
            NoProviderAvailableError: Gdy żaden provider nie jest dostępny.
        """
        from lumbago_app.core.exceptions import NoProviderAvailableError

        if not self._providers:
            raise NoProviderAvailableError(
                "Brak skonfigurowanych providerów AI. "
                "Dodaj klucz API do pliku .env"
            )

        last_error: Exception | None = None
        for provider in self._providers:
            if not provider.is_available():
                continue
            try:
                logger.info(
                    "Tagowanie %d utworów przez %s",
                    len(tracks_meta), provider.provider_name,
                )
                result = provider.tag_tracks(tracks_meta)
                logger.info(
                    "Otrzymano tagi dla %d/%d utworów od %s",
                    len(result), len(tracks_meta), provider.provider_name,
                )
                return result
            except Exception as exc:
                logger.warning(
                    "Provider %s nie powiódł się: %s — próbuję następny",
                    provider.provider_name, exc,
                )
                last_error = exc

        raise NoProviderAvailableError(
            f"Wszystkie providery AI zawiodły. Ostatni błąd: {last_error}"
        )

    def estimate_cost(
        self, track_count: int, avg_tokens_per_track: int = 150
    ) -> dict[str, float]:
        """
        Szacuje koszt tagowania dla każdego skonfigurowanego providera.

        Args:
            track_count: Liczba utworów.
            avg_tokens_per_track: Średnia liczba tokenów na utwór.

        Returns:
            Słownik provider -> szacowany koszt USD.
        """
        total_tokens = track_count * avg_tokens_per_track
        estimates: dict[str, float] = {}
        for provider in self._providers:
            name = provider.provider_name
            if name in AI_PROVIDERS_COST:
                cost = AI_PROVIDERS_COST[name]
                usd = (total_tokens / 1000) * (
                    cost.get("input_per_1k", 0) + cost.get("output_per_1k", 0) * 0.3
                )
                estimates[name] = round(usd, 4)
        return estimates


# Singleton routera
_router: CostRouter | None = None


def get_router() -> CostRouter:
    """Zwraca singleton CostRouter."""
    global _router
    if _router is None:
        _router = CostRouter()
    return _router
