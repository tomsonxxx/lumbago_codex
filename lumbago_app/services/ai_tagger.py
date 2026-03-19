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
            payload = _postprocess_payload(payload)
            return AnalysisResult(
                title=_to_str(payload.get("title")),
                artist=_to_str(payload.get("artist")),
                album=_to_str(payload.get("album")),
                year=_to_year(payload.get("year")),
                bpm=_to_float(payload.get("bpm")),
                key=_to_str(payload.get("key")),
                mood=_to_str(payload.get("mood")),
                energy=_to_float(payload.get("energy")),
                danceability=_to_float(payload.get("danceability")),
                genre=_to_str(payload.get("genre")),
                track_number=_to_str(payload.get("track_number") or payload.get("trackNumber")),
                disc_number=_to_str(payload.get("disc_number") or payload.get("discNumber")),
                album_artist=_to_str(payload.get("album_artist") or payload.get("albumArtist")),
                composer=_to_str(payload.get("composer")),
                copyright=_to_str(payload.get("copyright")),
                encoded_by=_to_str(payload.get("encoded_by") or payload.get("encodedBy")),
                original_artist=_to_str(payload.get("original_artist") or payload.get("originalArtist")),
                comments=_to_str(payload.get("comments")),
                album_cover_url=_to_str(payload.get("album_cover_url") or payload.get("albumCoverUrl")),
                isrc=_to_str(payload.get("isrc")),
                release_type=_to_str(payload.get("release_type") or payload.get("releaseType")),
                record_label=_to_str(payload.get("record_label") or payload.get("recordLabel")),
                description=_to_str(payload.get("description")),
                confidence=_to_float(payload.get("confidence")),
            )
        except Exception as exc:
            return AnalysisResult(description=f"Cloud AI error: {exc}", confidence=0.0)


def _missing_fields(track: Track) -> list[str]:
    missing = []
    if not track.title:
        missing.append("title")
    if not track.artist:
        missing.append("artist")
    if not track.album:
        missing.append("album")
    if not track.year:
        missing.append("year")
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
    if not track.track_number:
        missing.append("track_number")
    if not track.disc_number:
        missing.append("disc_number")
    if not track.album_artist:
        missing.append("album_artist")
    if not track.composer:
        missing.append("composer")
    if not track.original_artist:
        missing.append("original_artist")
    if not track.comments:
        missing.append("comments")
    if not track.record_label:
        missing.append("record_label")
    return missing


def _build_prompt(track: Track, missing: list[str]) -> str:
    return f"""
Zwroc wyłącznie JSON. Uzupełnij tylko pola: {", ".join(missing)}.
Wartości niepewne ustaw na null.
ZASADY:
- nie nadpisuj danych gorszą wartością typu "Unknown", "N/A", "various artists"
- preferuj wydanie studyjne (nie kompilacje typu Greatest Hits)
- rok ma mieć format YYYY
- energy i danceability skala 0-1
- bpm dodatni, key w notacji Camelot lub muzycznej

Dane wejściowe:
Tytul: {track.title or ''}
Artysta: {track.artist or ''}
Album: {track.album or ''}
Rok: {track.year or ''}
Gatunek: {track.genre or ''}
BPM: {track.bpm or ''}
Tonacja: {track.key or ''}
Nastroj: {track.mood or ''}
Energia: {track.energy or ''}
Numer utworu: {track.track_number or ''}
Numer dysku: {track.disc_number or ''}
Album Artist: {track.album_artist or ''}
Komentarz: {track.comments or ''}
ISRC: {track.isrc or ''}
""".strip()


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


def _to_year(value: Any) -> str | None:
    text = _to_str(value)
    if not text:
        return None
    if len(text) >= 4 and text[:4].isdigit():
        return text[:4]
    return None


def _postprocess_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            stripped = value.strip()
            if _is_placeholder(stripped):
                cleaned[key] = None
                continue
            cleaned[key] = stripped
            continue
        cleaned[key] = value
    return cleaned


def _is_placeholder(value: str) -> bool:
    lowered = value.lower().strip()
    if not lowered:
        return True
    placeholders = {
        "unknown",
        "n/a",
        "na",
        "none",
        "undefined",
        "various artists",
        "brak danych",
    }
    return lowered in placeholders
