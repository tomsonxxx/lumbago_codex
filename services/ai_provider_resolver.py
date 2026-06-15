"""Automatyczne wykrywanie działającego połączenia z dostawcami Cloud AI."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

import requests

from core.config import cache_dir

_MODEL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$", re.IGNORECASE)
_SKIP_MODEL_PREFIXES = (
    "text-embedding",
    "embed-",
    "whisper",
    "tts-",
    "dall-e",
    "davinci",
    "babbage",
    "gpt-image",
    "omni-moderation",
    "sora-",
)


@dataclass(frozen=True)
class ProviderProfile:
    default_base_url: str
    preferred_models: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedAIProvider:
    provider: str
    base_url: str
    model: str
    source: str
    detail: str = ""


LEGACY_AI_SETTING_KEYS: tuple[str, ...] = (
    "GEMINI_BASE_URL",
    "GEMINI_MODEL",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "GROK_BASE_URL",
    "GROK_MODEL",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
)


def cleared_legacy_ai_settings() -> dict[str, str]:
    """Wartości do zapisu w settings.json — usuwa ręczne modele i base URL."""
    return {key: "" for key in LEGACY_AI_SETTING_KEYS}


_PROVIDER_LABELS: dict[str, str] = {
    "gemini": "Google Gemini",
    "openai": "OpenAI",
    "grok": "xAI Grok",
    "deepseek": "DeepSeek",
}

_BILLING_HINTS: dict[str, str] = {
    "deepseek": "Doładuj konto na platform.deepseek.com (sekcja Billing / Top-up).",
    "openai": "Dodaj metodę płatności na platform.openai.com → Billing.",
    "grok": "Sprawdź saldo i limity na console.x.ai.",
    "gemini": "Sprawdź limity i rozliczenia w Google AI Studio (aistudio.google.com).",
}

_RESOLVE_SOURCE_LABELS: dict[str, str] = {
    "preferred": "wybrany automatycznie",
    "preferred_fuzzy": "dopasowany automatycznie",
    "preferred_fallback": "domyślny profil",
    "configured_valid": "z zapisanej konfiguracji",
    "configured_fuzzy": "dopasowany do konfiguracji",
    "probe": "zweryfikowany testem",
    "cache": "z pamięci podręcznej",
    "api_list": "z listy API",
    "api_list_fallback": "pierwszy z listy API",
}


def provider_display_name(provider: str) -> str:
    return _PROVIDER_LABELS.get((provider or "").strip().lower(), provider or "dostawca AI")


def format_resolve_source_label(source: str) -> str:
    return _RESOLVE_SOURCE_LABELS.get(source, source)


def format_api_error_message(
    provider: str,
    status_code: int | None,
    raw_message: str = "",
) -> str:
    """Przetłumacz typowy komunikat API na polski, zrozumiały dla użytkownika."""
    text = (raw_message or "").strip()
    lowered = text.lower()
    label = provider_display_name(provider)
    base = ""

    if any(
        marker in lowered
        for marker in (
            "insufficient balance",
            "insufficient funds",
            "insufficient credit",
            "payment required",
            "billing hard limit",
            "exceeded your current quota",
            "quota exceeded",
        )
    ):
        base = "Na koncie dostawcy nie ma wystarczających środków lub limit został wyczerpany."
    elif any(
        marker in lowered
        for marker in (
            "incorrect api key",
            "invalid api key",
            "invalid authentication",
            "unauthorized",
            "permission denied",
            "authentication",
        )
    ):
        base = "Klucz API jest nieprawidłowy lub wygasł."
    elif any(
        marker in lowered
        for marker in (
            "model not found",
            "invalid model",
            "unknown model",
            "does not exist",
            "no such model",
        )
    ):
        base = "Wybrany model nie jest dostępny na Twoim koncie."
    elif any(marker in lowered for marker in ("rate limit", "too many requests", "retry after")):
        base = "Przekroczono limit zapytań — odczekaj chwilę i spróbuj ponownie."
    elif text:
        base = text

    if not base and status_code is not None:
        status_messages = {
            401: "Brak autoryzacji — sprawdź klucz API.",
            402: "Niewystarczające saldo na koncie dostawcy (kod HTTP 402).",
            403: "Brak uprawnień do tego zasobu.",
            404: "Nie znaleziono zasobu API (adres lub model).",
            429: "Zbyt wiele zapytań — spróbuj za chwilę.",
            500: "Błąd serwera dostawcy.",
            502: "Bramka dostawcy niedostępna.",
            503: "Serwis dostawcy tymczasowo niedostępny.",
        }
        base = status_messages.get(status_code, f"Błąd HTTP {status_code}.")

    if not base:
        base = "Nieznany błąd połączenia z API."

    if status_code == 402 or "insufficient" in lowered or "payment required" in lowered:
        hint = _BILLING_HINTS.get((provider or "").strip().lower(), "")
        if hint:
            return f"{label}: {base} {hint}"
    return f"{label}: {base}"


PROVIDER_PROFILES: dict[str, ProviderProfile] = {
    "gemini": ProviderProfile(
        default_base_url="https://generativelanguage.googleapis.com/v1beta",
        preferred_models=(
            "gemini-2.5-flash",
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
        ),
    ),
    "openai": ProviderProfile(
        default_base_url="https://api.openai.com/v1",
        preferred_models=(
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-3.5-turbo",
        ),
    ),
    "grok": ProviderProfile(
        default_base_url="https://api.x.ai/v1",
        preferred_models=(
            "grok-2-latest",
            "grok-3-latest",
            "grok-3-mini",
            "grok-2-1212",
            "grok-beta",
        ),
    ),
    "deepseek": ProviderProfile(
        default_base_url="https://api.deepseek.com/v1",
        preferred_models=(
            "deepseek-chat",
            "deepseek-reasoner",
        ),
    ),
}


def _cache_path() -> Any:
    return cache_dir() / "ai_provider_cache.json"


def _cache_key(provider: str, api_key: str) -> str:
    digest = hashlib.sha256(f"{provider}:{api_key}".encode("utf-8")).hexdigest()[:16]
    return f"{provider}:{digest}"


def _load_cache() -> dict[str, dict[str, str]]:
    path = _cache_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _store_cache(entry_key: str, payload: dict[str, str]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _load_cache()
    data[entry_key] = payload
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def invalidate_cached_provider(provider: str, api_key: str) -> None:
    entry_key = _cache_key(provider, api_key)
    data = _load_cache()
    if entry_key in data:
        del data[entry_key]
        _cache_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_valid_model_hint(model: str | None) -> bool:
    if not model:
        return False
    text = str(model).strip()
    if not text or " " in text:
        return False
    return bool(_MODEL_ID_RE.match(text))


def is_model_not_found_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = (
        "model not found",
        "invalid model",
        "unknown model",
        "does not exist",
        "invalid-argument",
        "model_not_found",
        "no such model",
    )
    return any(marker in text for marker in markers)


def _profile(provider: str) -> ProviderProfile | None:
    return PROVIDER_PROFILES.get((provider or "").strip().lower())


def _normalize_base_url(provider: str, base_url: str | None) -> str:
    profile = _profile(provider)
    text = (base_url or "").strip()
    if text:
        return text.rstrip("/")
    return profile.default_base_url if profile else ""


def _parse_gemini_models(payload: Any) -> list[str]:
    models = payload.get("models", []) if isinstance(payload, dict) else []
    result: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if name.startswith("models/"):
            name = name.split("/", 1)[1]
        methods = item.get("supportedGenerationMethods") or item.get("supported_generation_methods") or []
        if methods and "generateContent" not in methods:
            continue
        if name:
            result.append(name)
    return result


def _parse_openai_compatible_models(payload: Any) -> list[str]:
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    result: list[str] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            continue
        lowered = model_id.lower()
        if any(lowered.startswith(prefix) for prefix in _SKIP_MODEL_PREFIXES):
            continue
        result.append(model_id)
    return result


def list_provider_models(
    provider: str,
    api_key: str,
    *,
    base_url: str | None = None,
    timeout: int = 10,
) -> tuple[list[str], str | None]:
    profile = _profile(provider)
    if profile is None:
        return [], "Nieznany dostawca"
    resolved_base = _normalize_base_url(provider, base_url)
    if not api_key:
        return [], "Brak klucza API"

    try:
        if provider == "gemini":
            url = f"{resolved_base.rstrip('/')}/models"
            resp = requests.get(url, params={"key": api_key}, timeout=timeout)
            if resp.status_code != 200:
                resp = requests.get(
                    url,
                    headers={"x-goog-api-key": api_key},
                    timeout=timeout,
                )
        else:
            url = f"{resolved_base.rstrip('/')}/models"
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
        if resp.status_code != 200:
            raw_message = ""
            try:
                payload = resp.json()
                error = payload.get("error")
                if isinstance(error, dict):
                    raw_message = str(error.get("message", "") or error.get("detail", "")).strip()
                elif isinstance(error, str):
                    raw_message = error.strip()
            except Exception:
                raw_message = resp.text[:180].strip()
            return [], format_api_error_message(provider, resp.status_code, raw_message)
        payload = resp.json()
        if provider == "gemini":
            return _parse_gemini_models(payload), None
        return _parse_openai_compatible_models(payload), None
    except Exception as exc:
        return [], str(exc)


def _pick_model(provider: str, available: list[str], model_hint: str | None) -> tuple[str | None, str]:
    profile = _profile(provider)
    if not profile:
        return None, "unknown_provider"

    available_set = {item.casefold(): item for item in available}
    if is_valid_model_hint(model_hint):
        hint_key = model_hint.strip().casefold()
        if hint_key in available_set:
            return available_set[hint_key], "configured_valid"
        # fuzzy: grok-2-latest vs grok-2-1212
        for key, original in available_set.items():
            if hint_key in key or key in hint_key:
                return original, "configured_fuzzy"

    for preferred in profile.preferred_models:
        key = preferred.casefold()
        if key in available_set:
            return available_set[key], "preferred"
        for api_name, original in available_set.items():
            if api_name.startswith(f"{key}-") or api_name.startswith(f"{key}_"):
                return original, "preferred_fuzzy"
            if key.startswith(api_name) and len(api_name) >= 8:
                return original, "preferred_fuzzy"

    for model_id in available:
        lowered = model_id.lower()
        if provider == "grok" and "grok" in lowered:
            return model_id, "api_list"
        if provider == "deepseek" and "deepseek" in lowered:
            return model_id, "api_list"
        if provider == "openai" and lowered.startswith("gpt-"):
            return model_id, "api_list"
        if provider == "gemini" and lowered.startswith("gemini-"):
            return model_id, "api_list"

    if available:
        return available[0], "api_list_fallback"
    return profile.preferred_models[0], "preferred_fallback"


def _candidate_models_for_probe(
    provider: str,
    available: list[str],
    model_hint: str | None,
) -> tuple[list[str], str, str]:
    primary, pick_source = _pick_model(provider, available, model_hint)
    profile = _profile(provider)
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(model_id: str | None) -> None:
        if not model_id:
            return
        key = model_id.casefold()
        if key in seen:
            return
        seen.add(key)
        candidates.append(model_id)

    _add(primary)
    if profile:
        for preferred in profile.preferred_models:
            _add(preferred)
    for model_id in available:
        _add(model_id)

    return candidates, pick_source, primary or ""


def _probe_chat_model(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    *,
    timeout: int = 12,
) -> tuple[bool, str]:
    prompt = "Reply with exactly: OK"
    try:
        if provider == "gemini":
            url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0},
            }
            attempts = (
                {"headers": {"x-goog-api-key": api_key, "Content-Type": "application/json"}, "params": None},
                {"headers": {"Content-Type": "application/json"}, "params": {"key": api_key}},
            )
            last_detail = "Test połączenia Gemini nie powiódł się."
            for attempt in attempts:
                resp = requests.post(
                    url,
                    headers=attempt["headers"],
                    params=attempt["params"],
                    json=payload,
                    timeout=timeout,
                )
                if resp.status_code == 200:
                    return True, "OK"
                last_detail = _http_error_detail(resp, provider=provider)
            return False, last_detail

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        base_body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        last_detail = "Test połączenia nie powiódł się."
        for use_json_mode in (False, True):
            body = dict(base_body)
            if use_json_mode:
                body["response_format"] = {"type": "json_object"}
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
            if resp.status_code == 200:
                return True, "OK"
            last_detail = _http_error_detail(resp, provider=provider)
            if resp.status_code not in (400, 422):
                break
        return False, last_detail
    except Exception as exc:
        return False, f"Błąd sieci: {exc}"


def _http_error_detail(resp: requests.Response, *, provider: str = "") -> str:
    raw_message = ""
    try:
        payload = resp.json()
        error = payload.get("error")
        if isinstance(error, dict):
            raw_message = str(error.get("message", "") or error.get("detail", "")).strip()
        elif isinstance(error, str):
            raw_message = error.strip()
    except Exception:
        raw_message = resp.text[:180].strip()
    return format_api_error_message(provider, resp.status_code, raw_message)


def resolve_ai_provider_with_detail(
    provider: str,
    api_key: str | None,
    *,
    base_url: str | None = None,
    model_hint: str | None = None,
    force_refresh: bool = False,
    timeout: int = 10,
) -> tuple[ResolvedAIProvider | None, str]:
    """Wykryj działający base URL + model; zwraca (wynik, komunikat błędu)."""
    normalized_provider = (provider or "").strip().lower()
    profile = _profile(normalized_provider)
    if profile is None:
        return None, "Nieznany dostawca AI"
    if not api_key:
        return None, "Brak klucza API"

    resolved_base = _normalize_base_url(normalized_provider, base_url)
    entry_key = _cache_key(normalized_provider, api_key)
    if not force_refresh:
        cached = _load_cache().get(entry_key)
        if isinstance(cached, dict) and cached.get("base_url") and cached.get("model"):
            return (
                ResolvedAIProvider(
                    provider=normalized_provider,
                    base_url=str(cached["base_url"]),
                    model=str(cached["model"]),
                    source="cache",
                    detail=str(cached.get("detail") or ""),
                ),
                "",
            )

    available, list_error = list_provider_models(
        normalized_provider,
        api_key,
        base_url=resolved_base,
        timeout=timeout,
    )
    candidates, pick_source, _primary = _candidate_models_for_probe(
        normalized_provider,
        available,
        model_hint,
    )
    if not candidates:
        return None, list_error or "Brak kandydatów modelu do testu"

    probe_timeout = max(timeout, 12)
    last_probe_error = list_error or ""
    for model in candidates[:14]:
        ok, probe_detail = _probe_chat_model(
            normalized_provider,
            api_key,
            resolved_base,
            model,
            timeout=probe_timeout,
        )
        if ok:
            source = pick_source if model == _primary else "probe"
            resolved = ResolvedAIProvider(
                provider=normalized_provider,
                base_url=resolved_base,
                model=model,
                source=source,
                detail=f"model={model}",
            )
            _store_cache(
                entry_key,
                {
                    "provider": normalized_provider,
                    "base_url": resolved.base_url,
                    "model": resolved.model,
                    "source": resolved.source,
                    "detail": resolved.detail,
                },
            )
            return resolved, ""

        if probe_detail:
            last_probe_error = probe_detail

    if list_error and last_probe_error:
        detail = f"{list_error} Ostatni test: {last_probe_error}"
    else:
        detail = last_probe_error or list_error or (
            f"{provider_display_name(normalized_provider)}: "
            "Nie udało się automatycznie skonfigurować działającego modelu."
        )
    return None, detail


def resolve_ai_provider(
    provider: str,
    api_key: str | None,
    *,
    base_url: str | None = None,
    model_hint: str | None = None,
    force_refresh: bool = False,
    timeout: int = 10,
) -> ResolvedAIProvider | None:
    """Wykryj działający base URL + model dla podanego klucza API."""
    resolved, _ = resolve_ai_provider_with_detail(
        provider,
        api_key,
        base_url=base_url,
        model_hint=model_hint,
        force_refresh=force_refresh,
        timeout=timeout,
    )
    return resolved


def resolve_provider_triplet(
    provider: str,
    settings,
    *,
    force_refresh: bool = False,
) -> tuple[str | None, str | None, str | None]:
    """Zwraca (api_key, base_url, model) gotowe do CloudAiTagger."""
    normalized = (provider or "").strip().lower()
    api_key = None
    base_hint = None
    model_hint = None
    if normalized == "gemini":
        api_key = settings.gemini_api_key or settings.cloud_ai_api_key
        base_hint = settings.gemini_base_url
        model_hint = settings.gemini_model
    elif normalized == "openai":
        api_key = settings.openai_api_key or settings.cloud_ai_api_key
        base_hint = settings.openai_base_url
        model_hint = settings.openai_model
    elif normalized == "grok":
        api_key = settings.grok_api_key or settings.cloud_ai_api_key
        base_hint = settings.grok_base_url
        model_hint = settings.grok_model
    elif normalized == "deepseek":
        api_key = settings.deepseek_api_key or settings.cloud_ai_api_key
        base_hint = settings.deepseek_base_url
        model_hint = settings.deepseek_model
    else:
        return None, None, None

    if not api_key:
        return None, None, None

    hint = model_hint if is_valid_model_hint(model_hint) else None
    resolved = resolve_ai_provider(
        normalized,
        api_key,
        base_url=base_hint,
        model_hint=hint,
        force_refresh=force_refresh,
    )
    if resolved is None:
        profile = _profile(normalized)
        fallback_model = profile.preferred_models[0] if profile else None
        fallback_base = _normalize_base_url(normalized, base_hint)
        return api_key, fallback_base, fallback_model
    return api_key, resolved.base_url, resolved.model