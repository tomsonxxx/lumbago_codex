from __future__ import annotations

"""
AIChatClient — uniwersalny klient czatu wspierający wszystkie skonfigurowane providery.

Działa dokładnie jak Autotagger:
- Używa services.ai_provider_resolver.resolve_ai_provider
- Wspiera: gemini, openai, grok, deepseek
- Automatyczny wybór najszybszego działającego lub ręczny wybór przez użytkownika
- Nie duplikuje konfiguracji kluczy

Per user request: czat ma współpracować ze WSZYSTKIMI aktywnymi API, tak jak Autotager.
"""

from typing import Iterator, Optional

import requests

from core.config import load_settings
from services.ai_provider_resolver import (
    resolve_ai_provider,
    format_api_error_message,
    PROVIDER_PROFILES,
)


class AIChatClient:
    """
    Klient czatu dla AI Panel.

    Użycie:
        client = AIChatClient(explicit_provider="openai")  # lub None dla auto z settings
        text = client.chat(system_prompt, user_message)
    """

    SUPPORTED_PROVIDERS = ("gemini", "openai", "grok", "deepseek")

    def __init__(self, explicit_provider: Optional[str] = None):
        self.settings = load_settings()
        self._explicit_provider = (explicit_provider or "").strip().lower() or None
        self._resolve()

    def _resolve(self):
        """Resolve aktualnego providera + dane dostępowe."""
        provider = self._explicit_provider or getattr(self.settings, "cloud_ai_provider", None)
        if provider:
            provider = provider.strip().lower()

        # Spróbuj znaleźć działający provider (preferuj jawnie ustawiony)
        candidates = []
        if provider and provider in self.SUPPORTED_PROVIDERS:
            candidates.append(provider)
        else:
            # Zbierz wszystkie, które mają klucze
            for p in self.SUPPORTED_PROVIDERS:
                key = self._get_api_key_for(p)
                if key:
                    candidates.append(p)

        self.provider = None
        self.api_key = None
        self.base_url = None
        self.model = None

        for p in candidates:
            key = self._get_api_key_for(p)
            if not key:
                continue
            try:
                resolved = resolve_ai_provider(
                    p,
                    key,
                    base_url=self._get_base_url_for(p),
                    model_hint=self._get_model_for(p),
                )
                if resolved:
                    self.provider = p
                    self.api_key = key
                    self.base_url = resolved.base_url.rstrip("/")
                    self.model = resolved.model
                    return
            except Exception:
                continue

        # Fallback — weź pierwszy z kluczem
        for p in candidates:
            key = self._get_api_key_for(p)
            if key:
                self.provider = p
                self.api_key = key
                profile = PROVIDER_PROFILES.get(p)
                self.base_url = self._get_base_url_for(p) or (profile.default_base_url if profile else "")
                self.model = self._get_model_for(p) or (profile.preferred_models[0] if profile else None)
                break

    def _get_api_key_for(self, provider: str) -> Optional[str]:
        if provider == "gemini":
            return self.settings.gemini_api_key or self.settings.cloud_ai_api_key
        if provider == "openai":
            return self.settings.openai_api_key or self.settings.cloud_ai_api_key
        if provider == "grok":
            return self.settings.grok_api_key or self.settings.cloud_ai_api_key
        if provider == "deepseek":
            return self.settings.deepseek_api_key or self.settings.cloud_ai_api_key
        return None

    def _get_base_url_for(self, provider: str) -> Optional[str]:
        if provider == "gemini":
            return self.settings.gemini_base_url
        if provider == "openai":
            return self.settings.openai_base_url
        if provider == "grok":
            return self.settings.grok_base_url
        if provider == "deepseek":
            return self.settings.deepseek_base_url
        return None

    def _get_model_for(self, provider: str) -> Optional[str]:
        if provider == "gemini":
            return self.settings.gemini_model
        if provider == "openai":
            return self.settings.openai_model
        if provider == "grok":
            return self.settings.grok_model
        if provider == "deepseek":
            return self.settings.deepseek_model
        return None

    @property
    def available_providers(self) -> list[str]:
        """Zwraca listę providerów, które mają skonfigurowany klucz."""
        avail = []
        for p in self.SUPPORTED_PROVIDERS:
            if self._get_api_key_for(p):
                avail.append(p)
        return avail

    def chat(self, system_prompt: str, user_message: str, stream: bool = False) -> str | Iterator[str]:
        if not self.provider or not self.api_key:
            return "Brak skonfigurowanego dostawcy AI (sprawdź Ustawienia → Cloud AI)."

        if self.provider == "gemini":
            return self._call_gemini(system_prompt, user_message, stream)
        else:
            return self._call_openai_compatible(system_prompt, user_message, stream)

    def _call_openai_compatible(self, system: str, user: str, stream: bool) -> str | Iterator[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": bool(stream),
            "temperature": 0.7,
        }
        try:
            if stream:
                resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=180)
                resp.raise_for_status()

                def _stream_gen():
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                import json as _json
                                chunk = _json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                continue
                return _stream_gen()
            else:
                resp = requests.post(url, json=payload, headers=headers, timeout=120)
                resp.raise_for_status()
                j = resp.json()
                return j.get("choices", [{}])[0].get("message", {}).get("content", "") or "(pusta odpowiedź)"
        except Exception as e:
            return format_api_error_message(self.provider, getattr(getattr(e, "response", None), "status_code", None), str(e))

    def _call_gemini(self, system: str, user: str, stream: bool) -> str | Iterator[str]:
        # Używamy REST (zgodne z resztą projektu)
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        contents = [{"parts": [{"text": f"{system}\n\n{user}"}]}]
        payload = {"contents": contents}

        try:
            if stream:
                # Gemini streaming jest bardziej złożone; na razie fallback do non-stream
                pass
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            j = resp.json()
            text = (
                j.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            return text or "(pusta odpowiedź)"
        except Exception as e:
            return format_api_error_message(self.provider, getattr(getattr(e, "response", None), "status_code", None), str(e))
