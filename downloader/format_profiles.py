from __future__ import annotations

"""
Format + Quality Profiles dla Downloader/Konwertera.

Priorytet absolutny: maksymalna słyszalna jakość (prompt).
- Najpierw bestaudio/best z yt-dlp.
- Potem konwersja wg profilu.

Profile:
- MAX: najwyższa możliwa (FLAC jeśli źródło pozwala, lub V0/256+)
- BALANCE (default): V0 MP3 / AAC 256 / WAV 24/48 gdy sensowne
- COMPACT: niższa jakość / mniejszy rozmiar

Per lumbago_grok_build_prompt.txt + guidelines.
"""

from typing import Any

PROFILES = ("MAX", "BALANCE", "COMPACT")
FORMATS = ("MP3", "WAV", "M4A")


def normalize_profile(p: str | None) -> str:
    p = (p or "BALANCE").upper().strip()
    return p if p in PROFILES else "BALANCE"


def normalize_format(f: str | None) -> str:
    f = (f or "MP3").upper().strip()
    return f if f in FORMATS else "MP3"


def get_profile_opts(profile: str, out_format: str) -> dict[str, Any]:
    """
    Zwraca słownik opcji dla yt_dlp.YoutubeDL.

    Preferujemy audio only + postprocessor FFmpegExtractAudio.
    Dla WAV wymuszamy wysokiej jakości PCM gdy możliwe.
    """
    profile = normalize_profile(profile)
    out_format = normalize_format(out_format)

    # Bazowo: najlepszy dostępny strumień audio
    ydl_opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": "%(title)s [%(id)s].%(ext)s",  # placeholder, worker nadpisze
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
        "postprocessors": [],
    }

    # Post-processor audio extract
    if out_format == "MP3":
        if profile == "MAX":
            # V0 lub wyższy VBR
            pp = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # V0 ~245kbps
            }
        elif profile == "BALANCE":
            pp = {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}
        else:
            pp = {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
        ydl_opts["postprocessors"].append(pp)

    elif out_format == "M4A":
        # AAC
        q = "256" if profile in ("MAX", "BALANCE") else "128"
        ydl_opts["postprocessors"].append(
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": q}
        )

    elif out_format == "WAV":
        # WAV = PCM. Dla MAX/BALANCE staramy się 24-bit / 48k jeśli źródło pozwala.
        # yt-dlp + ffmpeg: użycie wav + dodatkowe parametry przez postprocessor args.
        pp = {"key": "FFmpegExtractAudio", "preferredcodec": "wav"}
        if profile in ("MAX", "BALANCE"):
            # Dodatkowe parametry dla jakości (ffmpeg)
            pp["postprocessor_args"] = ["-ar", "48000", "-acodec", "pcm_s24le"]
        else:
            pp["postprocessor_args"] = ["-ar", "44100"]
        ydl_opts["postprocessors"].append(pp)

    # Embed thumbnail + metadata (jeśli dostępne)
    ydl_opts["postprocessors"].append({"key": "FFmpegMetadata"})
    ydl_opts["postprocessors"].append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

    # Throttling / fragments będą sterowane z workera (konfigurowalne)
    return ydl_opts


def get_quality_label(profile: str, fmt: str) -> str:
    p = normalize_profile(profile)
    f = normalize_format(fmt)
    if f == "MP3":
        return {"MAX": "MP3 V0 (~245 kbps)", "BALANCE": "MP3 V0", "COMPACT": "MP3 128kbps"}[p]
    if f == "M4A":
        return {"MAX": "M4A AAC 256kbps", "BALANCE": "M4A AAC 256kbps", "COMPACT": "M4A 128kbps"}[p]
    if f == "WAV":
        return {"MAX": "WAV 24-bit/48kHz", "BALANCE": "WAV 24-bit/48kHz", "COMPACT": "WAV 16-bit/44kHz"}[p]
    return f"{f} {p}"
