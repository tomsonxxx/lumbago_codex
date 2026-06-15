from __future__ import annotations

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