from __future__ import annotations

import html
import re
from pathlib import Path

_CATEGORY_PREFIX = {
    "[bg-service]": "» Uzupełnianie w tle",
    "[autotag-bg]": "» Autotag w tle",
    "[autotag]": "» Autotag",
    "[scan]": "» Skan biblioteki",
    "[import]": "» Import",
}

_SOURCE_LABELS = {
    "manual": "ręcznie",
    "autotag_finish": "po zakończeniu autotagu",
}

_PROVIDER_LABELS = {
    "_search_musicbrainz": "MusicBrainz",
    "_search_discogs": "Discogs",
    "_search_ai": "AI",
    "_search_itunes": "Apple Music",
    "_search_deezer": "Deezer",
    "_search_theaudiodb": "TheAudioDB",
    "_search_listenbrainz": "ListenBrainz",
    "_search_lrclib": "LRCLIB",
    "_search_lyrics_ovh": "Lyrics.ovh",
    "_search_filename_remixer": "Nazwa pliku (remixer)",
}


def track_filename(path: str | None) -> str:
    if not path:
        return "nieznany plik"
    try:
        return Path(path).name
    except Exception:
        return str(path)


def format_queue_status(pending: int, running: int) -> str:
    parts: list[str] = []
    if pending:
        parts.append(f"{pending} oczekuje")
    if running:
        parts.append(f"{running} w trakcie")
    return ", ".join(parts) if parts else "kolejka pusta"


def format_source_label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source.replace("_", " "))


def _humanize_autotag_provider_line(message: str) -> str | None:
    if not message.startswith("[autotag] source="):
        return None

    tokens = dict(re.findall(r"(\w+)=(\S+)", message.replace("[autotag] ", "")))
    fn = tokens.get("source", "")
    stage = tokens.get("stage", "")
    if not fn or not stage:
        return None

    filename = tokens.get("file")
    elapsed_ms = tokens.get("elapsed_ms")
    status = tokens.get("status")
    error = tokens.get("error")
    score = tokens.get("score")
    provider = _PROVIDER_LABELS.get(fn, fn.removeprefix("_search_").replace("_", " ").title())
    file_part = f" — {filename}" if filename else ""

    if stage == "start":
        return f"   · {provider}: wyszukiwanie{file_part}"
    if stage == "done":
        seconds = ""
        if elapsed_ms:
            seconds = f", {int(elapsed_ms) / 1000:.1f} s"
        if status == "hit" and score:
            return f"   · {provider}: dopasowanie {score} pkt{seconds}{file_part}"
        if status == "error":
            detail = f" — {error}" if error else ""
            return f"   · {provider}: błąd{detail}{file_part}"
        if status == "miss":
            return f"   · {provider}: brak wyniku{seconds}{file_part}"
    return None


def humanize_process_log(message: str) -> str:
    """Delikatna humanizacja surowych wpisów procesów (PL, czytelniej)."""
    text = " ".join(message.split())

    for raw, label in _CATEGORY_PREFIX.items():
        if text.startswith(raw):
            text = f"{label}: {text[len(raw) :].lstrip()}"
            break

    provider_line = _humanize_autotag_provider_line(message)
    if provider_line:
        return provider_line

    replacements = [
        (r"start \| tracks=(\d+)", r"Rozpoczęto — utworów: \1"),
        (r"done \| processed=(\d+) updated=(\d+) errors=(\d+)", r"Zakończono — przetworzono: \1, zapisano: \2, błędów: \3"),
        (r"finished \| updated=(\d+)/(\d+)", r"Zakończono — uzupełniono \1 z \2 utworów"),
        (r"(\d+)/(\d+) \| ([^|]+) \| (.+)", r"\1/\2: \3 — \4"),
        (r"start \| folder=(.+)", r"Rozpoczęto folder: \1"),
        (r"done \| tracks=(\d+) errors=(\d+)", r"Zakończono — utworów: \1, problemów: \2"),
        (r"źródło: manual", "uruchomienie: ręczne"),
        (r"źródło: autotag_finish", "uruchomienie: po autotagu"),
        (r"\(kolejka: pending=(\d+), running=(\d+)\)", _queue_repl),
        (r"pending=(\d+), running=(\d+)", _queue_repl),
        (r"running → pending", "przywrócono do kolejki"),
        (r"track_id=(\d+)", r"utwór #\1"),
        (r"job_id=(\d+)", r"zadanie #\1"),
        (r"no background fields after (\d+) sources file=(\S+)", r"Brak dodatkowych pól (sprawdzono \1 źródeł) — \2"),
        (r"writeback errors file=(\S+) errors=(\d+)", r"Błąd zapisu tagów w pliku \1 (błędów: \2)"),
        (r"writeback failed file=(\S+) err=(.+)", r"Nie udało się zapisać tagów — \1: \2"),
        (r"failed to enqueue jobs: (.+)", r"Nie udało się dodać zadań do kolejki: \1"),
        (r"mode=(\S+) best=(\S+) score=(\d+) total=(\d+)", r"Tryb \1 — najlepsze: \2 (\3 pkt), źródeł: \4"),
        (r"mode=(\S+) best=none total=(\d+)", r"Tryb \1 — brak dopasowania (sprawdzono \2 źródeł)"),
        (r"ERROR processing track \| err=(.+)", r"Błąd przetwarzania utworu: \1"),
        (r"FATAL error in _run_single_track file=(\S+) err=(.+)", r"Krytyczny błąd autotagu — \1: \2"),
    ]

    for pattern, repl in replacements:
        if callable(repl):
            text = re.sub(pattern, repl, text)
        else:
            text = re.sub(pattern, repl, text)

    return text


def _queue_repl(match: re.Match[str]) -> str:
    pending = int(match.group(1))
    running = int(match.group(2))
    return f"(kolejka: {format_queue_status(pending, running)})"


# (etykieta legendy, kolor HTML)
SOURCE_COLORS: dict[str, tuple[str, str]] = {
    "youtube": ("YouTube", "#FF3B30"),
    "soundcloud": ("SoundCloud", "#0099FF"),
    "musicbrainz": ("MusicBrainz", "#C8509A"),
    "discogs": ("Discogs", "#F28C28"),
    "deezer": ("Deezer", "#A855F7"),
    "apple_music": ("Apple Music", "#FA2D48"),
    "theaudiodb": ("TheAudioDB", "#3B82F6"),
    "listenbrainz": ("ListenBrainz", "#EF4444"),
    "lastfm": ("Last.fm", "#D51007"),
    "lrclib": ("LRCLIB", "#22C55E"),
    "lyricsovh": ("Lyrics.ovh", "#94A3B8"),
    "ai": ("AI", "#8B5CF6"),
    "spotify": ("Spotify", "#1DB954"),
    "genius": ("Genius", "#FACC15"),
    "bandcamp": ("Bandcamp", "#1DA0C3"),
    "bg_enrichment": ("Uzupełnianie w tle", "#38BDF8"),
    "autotag_bg": ("Autotag w tle", "#FBBF24"),
    "autotag": ("Autotag", "#F59E0B"),
    "scan": ("Skan biblioteki", "#10B981"),
    "import": ("Import", "#64748B"),
    "recognition": ("Rozpoznawanie", "#EC4899"),
    "duplicates": ("Duplikaty", "#F97316"),
    "default": ("Inne", "#CBD5E1"),
}

LEGEND_SOURCE_ORDER: tuple[str, ...] = (
    "youtube",
    "soundcloud",
    "musicbrainz",
    "discogs",
    "deezer",
    "apple_music",
    "theaudiodb",
    "listenbrainz",
    "lastfm",
    "lrclib",
    "ai",
    "bg_enrichment",
    "autotag",
    "autotag_bg",
    "scan",
    "recognition",
    "duplicates",
    "default",
)

_PROVIDER_NAME_TO_KEY: dict[str, str] = {
    "musicbrainz": "musicbrainz",
    "discogs": "discogs",
    "ai": "ai",
    "apple music": "apple_music",
    "deezer": "deezer",
    "theaudiodb": "theaudiodb",
    "listenbrainz": "listenbrainz",
    "lrclib": "lrclib",
    "lyrics.ovh": "lyricsovh",
    "youtube": "youtube",
    "soundcloud": "soundcloud",
    "last.fm": "lastfm",
    "spotify": "spotify",
    "genius": "genius",
    "bandcamp": "bandcamp",
}

_PROVIDER_FN_TO_KEY: dict[str, str] = {
    "_search_musicbrainz": "musicbrainz",
    "_search_discogs": "discogs",
    "_search_ai": "ai",
    "_search_itunes": "apple_music",
    "_search_deezer": "deezer",
    "_search_theaudiodb": "theaudiodb",
    "_search_listenbrainz": "listenbrainz",
    "_search_lrclib": "lrclib",
    "_search_lyrics_ovh": "lyricsovh",
    "_search_youtube": "youtube",
    "_search_soundcloud": "soundcloud",
}


def legend_entries() -> list[tuple[str, str, str]]:
    """Lista (klucz, etykieta, kolor) do legendy w UI."""
    return [
        (key, SOURCE_COLORS[key][0], SOURCE_COLORS[key][1])
        for key in LEGEND_SOURCE_ORDER
        if key in SOURCE_COLORS
    ]


def color_for_source_key(source_key: str) -> str:
    return SOURCE_COLORS.get(source_key, SOURCE_COLORS["default"])[1]


def detect_log_source_key(line: str) -> str:
    """Przypisuje wiersz logu do źródła (kolor w oknie logów)."""
    text = line.strip()
    if not text:
        return "default"

    bullet = re.search(r"·\s*([^:]+):", text)
    if bullet:
        name = bullet.group(1).strip().lower()
        for label, key in _PROVIDER_NAME_TO_KEY.items():
            if name == label or name.startswith(label):
                return key

    lowered = text.lower()
    category_rules = [
        ("» uzupełnianie w tle", "bg_enrichment"),
        ("[bg-service]", "bg_enrichment"),
        ("» autotag w tle", "autotag_bg"),
        ("[autotag-bg]", "autotag_bg"),
        ("» skan biblioteki", "scan"),
        ("[scan]", "scan"),
        ("» import", "import"),
        ("[import]", "import"),
        ("[recognition]", "recognition"),
        ("» rozpoznawanie", "recognition"),
        ("[duplicates]", "duplicates"),
        ("[dupmerge]", "duplicates"),
    ]
    for needle, key in category_rules:
        if needle in lowered:
            return key

    fn_match = re.search(r"source=(_search_\w+)", text)
    if fn_match:
        return _PROVIDER_FN_TO_KEY.get(fn_match.group(1), "autotag")

    portal_match = re.search(r"\b(youtube|soundcloud|spotify|genius|bandcamp)\b", lowered)
    if portal_match:
        return portal_match.group(1)

    if "» autotag" in lowered or "[autotag]" in lowered:
        return "autotag"

    return "default"


def format_log_line_html(line: str) -> str:
    escaped = html.escape(line)
    color = color_for_source_key(detect_log_source_key(line))
    return f'<span style="color:{color}; white-space:pre;">{escaped}</span>'


def build_colored_log_html(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    body = "<br>".join(format_log_line_html(line) for line in lines)
    return (
        '<pre style="font-family:Consolas,monospace; font-size:10pt; '
        f'margin:0; line-height:1.35;">{body}</pre>'
    )