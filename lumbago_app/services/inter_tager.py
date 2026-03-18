"""
InterTager — pełny mechanizm automatycznej analizy, wyszukiwania i tagowania.
Port mechanizmu z inteligentny-tagger-id3 (aiService.ts) na Python.

Obsługiwani dostawcy: Gemini, OpenAI, Grok, DeepSeek
Tryby: single-file, batch (do 10 plików naraz)
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from lumbago_app.core.models import Track


_SYSTEM_INSTRUCTION = (
    "You are an expert music archivist with access to a vast database of music information, "
    "equivalent to searching across major portals like MusicBrainz, Discogs, AllMusic, Spotify, and Apple Music.\n"
    "Your task is to identify the song from the provided filename and any existing tags, "
    "and provide the most accurate and complete ID3 tag information possible.\n\n"
    "RULES:\n"
    "- Analyze the filename and existing tags to identify the track.\n"
    "- Existing tags are hints. If they seem correct, preserve them. If wrong or missing, correct/fill them.\n"
    "- If you cannot confidently determine something, return null. "
    "DO NOT use generic placeholders like 'Unknown Artist'.\n"
    "- Prioritize the original studio album. Avoid 'Greatest Hits' compilations unless it's the only source.\n\n"
    "FIELDS TO RETURN (JSON):\n"
    "title, artist, album, year (4-digit string), genre, bpm (number), key (musical key, e.g. Am or 8A), "
    "mood, trackNumber, discNumber, albumArtist, composer, copyright, originalArtist, "
    "albumCoverUrl (direct image URL to download), comments.\n\n"
    "Return ONLY valid JSON, no extra text."
)

_PROVIDER_DEFAULTS: dict[str, tuple[str, str]] = {
    "openai":   ("https://api.openai.com/v1",                  "gpt-4.1-mini"),
    "grok":     ("https://api.x.ai/v1",                        "grok-2-latest"),
    "deepseek": ("https://api.deepseek.com/v1",                "deepseek-chat"),
    "gemini":   ("https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
}

# AI fields → EasyID3 / Vorbis / write_tags keys
_FIELD_MAP = {
    "title":          "title",
    "artist":         "artist",
    "album":          "album",
    "year":           "date",
    "genre":          "genre",
    "bpm":            "bpm",
    "key":            "initialkey",
    "mood":           "comment",
    "trackNumber":    "tracknumber",
    "discNumber":     "discnumber",
    "albumArtist":    "albumartist",
    "composer":       "composer",
    "copyright":      "copyright",
    "originalArtist": "performer",
    "comments":       "description",
}


# ──────────────────────────────────────────────────────────────────────────────
# Logika smart-merge (port shouldOverwrite z aiService.ts)
# ──────────────────────────────────────────────────────────────────────────────

def _should_overwrite(new_val: Any, old_val: Any) -> bool:
    if new_val is None or new_val == "":
        return False
    if isinstance(new_val, str):
        lower = new_val.lower()
        if ("unknown" in lower or "undefined" in lower) and old_val:
            return False
    return True


def smart_merge(track: Track, ai_data: dict[str, Any]) -> dict[str, Any]:
    """Łączy wyniki AI z istniejącymi danymi tracka (inteligentny merge)."""
    existing: dict[str, Any] = {
        "title":          track.title,
        "artist":         track.artist,
        "album":          track.album,
        "year":           track.year,
        "genre":          track.genre,
        "bpm":            track.bpm,
        "key":            track.key,
        "mood":           track.mood,
        "trackNumber":    None,
        "discNumber":     None,
        "albumArtist":    None,
        "composer":       None,
        "copyright":      None,
        "originalArtist": None,
        "albumCoverUrl":  track.artwork_path,
        "comments":       None,
    }
    result: dict[str, Any] = {}
    all_keys = set(existing.keys()) | set(ai_data.keys())
    for field in all_keys:
        new_val = ai_data.get(field)
        old_val = existing.get(field)
        if _should_overwrite(new_val, old_val):
            result[field] = new_val
        elif old_val is not None:
            result[field] = old_val
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Budowanie promptu
# ──────────────────────────────────────────────────────────────────────────────

def _build_single_prompt(track: Track) -> str:
    filename = Path(track.path).name
    existing = {
        "title":  track.title,
        "artist": track.artist,
        "album":  track.album,
        "year":   track.year,
        "genre":  track.genre,
        "bpm":    track.bpm,
        "key":    track.key,
        "mood":   track.mood,
    }
    return (
        f'Identify this song and provide its complete ID3 tags.\n'
        f'Filename: "{filename}"\n'
        f'Existing tags: {json.dumps(existing, ensure_ascii=False)}'
    )


def _build_batch_prompt(tracks: list[Track]) -> str:
    items = []
    for t in tracks:
        items.append(json.dumps({
            "filename": Path(t.path).name,
            "existingTags": {
                "title": t.title, "artist": t.artist, "album": t.album,
                "year": t.year, "genre": t.genre, "bpm": t.bpm, "key": t.key,
            },
        }, ensure_ascii=False))
    file_list = ",\n".join(items)
    return (
        "I have a batch of audio files. Identify each track from its filename and existing tags. "
        "For files from the same album, ensure artist/album/albumArtist tags are identical.\n\n"
        f"Files:\n[{file_list}]\n\n"
        "Return a JSON ARRAY where each object contains 'originalFilename' and all identified tags."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Wywołania API z retry
# ──────────────────────────────────────────────────────────────────────────────

def _retry(fn, max_retries: int = 3):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise last_exc


def _safe_parse(text: str) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Spróbuj wyciąć JSON z otoczenia
        for start_ch, end_ch in [('{', '}'), ('[', ']')]:
            s = text.find(start_ch)
            e = text.rfind(end_ch)
            if s >= 0 and e > s:
                try:
                    return json.loads(text[s:e + 1])
                except json.JSONDecodeError:
                    pass
    return {}


def _call_gemini(api_key: str, model: str, prompt: str, timeout: int) -> Any:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": _SYSTEM_INSTRUCTION + "\n\n" + prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    resp = _retry(lambda: requests.post(
        url,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    ))
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _safe_parse(text)


def _call_openai_compat(base_url: str, api_key: str, model: str, prompt: str, timeout: int,
                        batch: bool = False) -> Any:
    url = f"{base_url.rstrip('/')}/chat/completions"
    messages = [
        {"role": "system", "content": _SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    # json_object mode — o ile model obsługuje (nie wszystkie DeepSeek/Grok obsługują response_format)
    try:
        payload["response_format"] = {"type": "json_object"}
        resp = _retry(lambda: requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        ))
        resp.raise_for_status()
    except Exception:
        # Fallback bez response_format
        payload.pop("response_format", None)
        resp = _retry(lambda: requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        ))
        resp.raise_for_status()

    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return _safe_parse(text)


# ──────────────────────────────────────────────────────────────────────────────
# Publiczne API
# ──────────────────────────────────────────────────────────────────────────────

def analyze_track(
    track: Track,
    provider: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Analizuje jeden utwór i zwraca surowe dane AI (bez merge)."""
    defaults = _PROVIDER_DEFAULTS.get(provider, _PROVIDER_DEFAULTS["openai"])
    effective_url = base_url or defaults[0]
    effective_model = model or defaults[1]
    prompt = _build_single_prompt(track)

    if provider == "gemini":
        return _call_gemini(api_key, effective_model, prompt, timeout)
    return _call_openai_compat(effective_url, api_key, effective_model, prompt, timeout)


def analyze_batch(
    tracks: list[Track],
    provider: str,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
    timeout: int = 60,
) -> list[dict[str, Any]]:
    """Analizuje listę utworów w jednym zapytaniu (batch). Zwraca listę dict[filename→tags]."""
    defaults = _PROVIDER_DEFAULTS.get(provider, _PROVIDER_DEFAULTS["openai"])
    effective_url = base_url or defaults[0]
    effective_model = model or defaults[1]
    prompt = _build_batch_prompt(tracks)

    if provider == "gemini":
        raw = _call_gemini(api_key, effective_model, prompt, timeout)
    else:
        raw = _call_openai_compat(effective_url, api_key, effective_model, prompt, timeout, batch=True)

    # raw powinno być listą
    if isinstance(raw, dict):
        # niektóre modele zwracają {"files": [...]} lub {"results": [...]}
        for key in ("files", "results", "tracks", "songs", "items"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            raw = [raw]

    if not isinstance(raw, list):
        return []

    # Mapuj po originalFilename
    filename_map = {Path(t.path).name: t for t in tracks}
    results: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        fname = item.get("originalFilename") or item.get("filename") or ""
        track = filename_map.get(fname)
        if track:
            merged = smart_merge(track, item)
            merged["_filename"] = fname
            results.append(merged)
    return results


def download_cover(url: str, dest_dir: Path, filename_stem: str, timeout: int = 15) -> Path | None:
    """Pobiera okładkę z URL i zapisuje do pliku. Zwraca ścieżkę lub None przy błędzie."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "image/jpeg")
        ext = ".jpg" if "jpeg" in ct or "jpg" in ct else ".png" if "png" in ct else ".jpg"
        dest = dest_dir / f"{filename_stem}_cover{ext}"
        dest.write_bytes(resp.content)
        return dest
    except Exception:
        return None


def apply_merged_to_track(track: Track, merged: dict[str, Any], cover_dir: Path | None = None) -> None:
    """Zapisuje merge'd tagi do pliku audio i aktualizuje obiekt Track."""
    from lumbago_app.core.audio import write_tags

    write_data: dict[str, str] = {}
    for ai_field, easy_key in _FIELD_MAP.items():
        val = merged.get(ai_field)
        if val is not None and val != "":
            write_data[easy_key] = str(val)

    if write_data:
        try:
            write_tags(Path(track.path), write_data)
        except Exception:
            pass

    # Aktualizuj obiekt Track
    if merged.get("title"):
        track.title = str(merged["title"])
    if merged.get("artist"):
        track.artist = str(merged["artist"])
    if merged.get("album"):
        track.album = str(merged["album"])
    if merged.get("year"):
        track.year = str(merged["year"])
    if merged.get("genre"):
        track.genre = str(merged["genre"])
    if merged.get("bpm") is not None:
        try:
            track.bpm = float(merged["bpm"])
        except (ValueError, TypeError):
            pass
    if merged.get("key"):
        track.key = str(merged["key"])
    if merged.get("mood"):
        track.mood = str(merged["mood"])

    # Okładka — pobierz i osadź
    cover_url = merged.get("albumCoverUrl")
    if cover_url and isinstance(cover_url, str) and cover_url.startswith("http"):
        dest_dir = cover_dir or Path(track.path).parent
        stem = Path(track.path).stem
        cover_path = download_cover(cover_url, dest_dir, stem)
        if cover_path:
            track.artwork_path = str(cover_path)
            _embed_cover(Path(track.path), cover_path)


def _embed_cover(audio_path: Path, cover_path: Path) -> None:
    """Osadza obraz okładki w pliku audio (APIC dla MP3, METADATA_BLOCK_PICTURE dla FLAC)."""
    try:
        from mutagen.id3 import ID3, APIC, error as ID3Error
        from mutagen.flac import FLAC, Picture
        from mutagen.mp4 import MP4, MP4Cover
        import mimetypes

        data = cover_path.read_bytes()
        mime = mimetypes.guess_type(str(cover_path))[0] or "image/jpeg"
        suffix = audio_path.suffix.lower()

        if suffix == ".mp3":
            try:
                tags = ID3(str(audio_path))
            except ID3Error:
                tags = ID3()
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
            tags.save(str(audio_path))

        elif suffix == ".flac":
            audio = FLAC(str(audio_path))
            pic = Picture()
            pic.type = 3
            pic.mime = mime
            pic.data = data
            audio.clear_pictures()
            audio.add_picture(pic)
            audio.save()

        elif suffix in (".m4a", ".mp4", ".aac"):
            audio = MP4(str(audio_path))
            fmt = MP4Cover.FORMAT_JPEG if "jpeg" in mime else MP4Cover.FORMAT_PNG
            audio["covr"] = [MP4Cover(data, imageformat=fmt)]
            audio.save()
    except Exception:
        pass
