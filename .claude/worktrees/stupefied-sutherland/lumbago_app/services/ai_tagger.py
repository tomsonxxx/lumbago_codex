from __future__ import annotations

import json
from typing import Any

import requests

from lumbago_app.core.models import AnalysisResult, Track
from lumbago_app.core.services import heuristic_analysis


class LocalAiTagger:
    def analyze(self, track: Track) -> AnalysisResult:
        return heuristic_analysis(track)


class CloudAiTagger:
    def __init__(
        self,
        provider: str | None,
        api_key: str | None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 25,
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def analyze(self, track: Track) -> AnalysisResult:
        if not self.provider or not self.api_key:
            return AnalysisResult(description="Cloud AI not configured", confidence=0.0)
        if self.provider == "gemini":
            base_url = self.base_url or "https://generativelanguage.googleapis.com/v1beta"
            model = self.model or "gemini-2.5-flash"
        else:
            base_url = self.base_url
            model = self.model
        if not base_url or not model:
            return AnalysisResult(description="Cloud AI missing base URL or model", confidence=0.0)

        missing = _missing_fields(track)
        if not missing:
            return AnalysisResult(description="No missing fields", confidence=1.0)
        prompt = _build_prompt(track, missing)
        try:
            if self.provider == "openai":
                text = _call_openai_responses(base_url, self.api_key, model, prompt, self.timeout)
            elif self.provider == "gemini":
                text = _call_gemini_generate_content(base_url, self.api_key, model, prompt, self.timeout)
            else:
                text = _call_openai_compatible_chat(
                    base_url, self.api_key, model, prompt, self.timeout
                )
            payload = _safe_json(text)
            if not isinstance(payload, dict):
                return AnalysisResult(description="Cloud AI returned non-JSON response", confidence=0.0)
            return AnalysisResult(
                bpm=_to_float(payload.get("bpm")),
                key=_to_str(payload.get("key")),
                mood=_to_str(payload.get("mood")),
                energy=_to_float(payload.get("energy")),
                genre=_to_str(payload.get("genre")),
                description=_to_str(payload.get("description")),
                confidence=_to_float(payload.get("confidence")),
            )
        except Exception as exc:
            return AnalysisResult(description=f"Cloud AI error: {exc}", confidence=0.0)


def _missing_fields(track: Track) -> list[str]:
    missing = []
    if not track.bpm:
        missing.append("bpm")
    if not track.key:
        missing.append("key")
    if not track.mood:
        missing.append("mood")
    if not track.energy:
        missing.append("energy")
    if not track.genre:
        missing.append("genre")
    return missing


def _build_prompt(track: Track, missing: list[str]) -> str:
    return (
        "Zwroc JSON tylko dla pol: "
        + ", ".join(missing)
        + ". Wartosci puste ustaw na null. "
        "Dane wejsciowe:\n"
        f"Tytul: {track.title or ''}\n"
        f"Artysta: {track.artist or ''}\n"
        f"Album: {track.album or ''}\n"
        f"Gatunek: {track.genre or ''}\n"
        f"BPM: {track.bpm or ''}\n"
        f"Tonacja: {track.key or ''}\n"
        f"Nastroj: {track.mood or ''}\n"
        f"Energia: {track.energy or ''}\n"
    )


def _call_openai_responses(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_responses(data)


def _call_openai_compatible_chat(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Zwracaj tylko JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_chat_completions(data)


def _call_gemini_generate_content(
    base_url: str, api_key: str, model: str, prompt: str, timeout: int
) -> str:
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ]
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return _extract_text_from_gemini(data)


def _extract_text_from_responses(data: dict[str, Any]) -> str:
    output = data.get("output", [])
    if not isinstance(output, list):
        return ""
    for item in output:
        if item.get("type") == "message":
            content = item.get("content", [])
            for part in content:
                if part.get("type") in {"output_text", "text"}:
                    return part.get("text", "")
    return ""


def _extract_text_from_chat_completions(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return message.get("content", "") or ""


def _extract_text_from_gemini(data: dict[str, Any]) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        return ""
    text = parts[0].get("text", "")
    return text or ""


def _safe_json(text: str) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
