from __future__ import annotations

"""
CommandRegistry — rejestr bezpiecznych komend aplikacji dla AI Panel.

Każda komenda ma:
- nazwę
- opis
- EFFECT (co się realnie stanie z plikami / UI / DB)

Dispatcher będzie je wywoływał z walidacją.

Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + "dalej" + "kontynuuj" ... must document identical.
"""

from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Command:
    name: str
    description: str
    effect: str
    handler: Callable[..., Any]

_REGISTRY: dict[str, Command] = {}


def register(name: str, description: str, effect: str):
    def deco(fn: Callable) -> Callable:
        _REGISTRY[name.lower()] = Command(name, description, effect, fn)
        return fn
    return deco


def get_command(name: str) -> Command | None:
    return _REGISTRY.get(name.lower())


def list_commands() -> list[Command]:
    return list(_REGISTRY.values())


# Przykładowe komendy (stub + doc). Pełne wiring w main / dispatcher po integracji.
@register("pobierz", "Pobierz playlistę/film z YT lub SC", "EFEKT: otwiera Downloader z wypełnionym URL i formatem; start jeśli podano (auto_start E).")
def cmd_download(url: str = "", fmt: str = "mp3", **kw):
    # W pełnej wersji: MainWindow._open_downloader() + prefill + auto_start per 'dalej' E
    return {"action": "open_downloader", "url": url, "fmt": fmt}


@register("duplikaty", "Znajdź duplikaty w bibliotece", "EFEKT: otwiera DuplicatesDialog i uruchamia skan.")
def cmd_duplicates(**kw):
    return {"action": "open_duplicates"}


@register("otaguj", "Uruchom autotagowanie na folderze lub zaznaczeniu", "EFEKT: skan + AI tag na wybranych ścieżkach (nie nadpisuje istniejących wartości).")
def cmd_autotag(path: str = "", **kw):
    return {"action": "autotag", "path": path}


@register("pomoc", "Lista dostępnych komend", "EFEKT: zwraca listę komend z opisami EFFECT.")
def cmd_help(**kw):
    return {"action": "help", "commands": [ (c.name, c.description, c.effect) for c in list_commands() ]}


@register("status", "Pokaż podstawowy status biblioteki / narzędzi", "EFEKT: zwraca info o dostępnych providerach i modułach (bez zmian w DB).")
def cmd_status(**kw):
    return {"action": "status", "info": "Lumbago AI Panel + Downloader gotowe (multi-provider, yt-dlp+ffmpeg wymagane)"}

@register("status_biblioteki", "Pokaż liczbę utworów i playlist w bibliotece", "EFEKT: zwraca rzeczywiste statystyki z bazy (read-only).")
def cmd_status_biblioteki(**kw):
    # Enhanced for złożony mechanizm (dalej): try real count via repo (read-only, safe)
    try:
        from data.repository import list_tracks, list_playlists
        tracks = len(list_tracks())
        pls = len(list_playlists())
        return {"action": "status_biblioteki", "tracks": tracks, "playlists": pls}
    except Exception:
        return {"action": "status_biblioteki", "info": "stats via library (repo query)"}
