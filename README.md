# Lumbago Music AI (Python, Windows)

Desktopowa wersja aplikacji do zarządzania biblioteką muzyczną dla DJ-ów i kolekcjonerów. UI w PyQt6, lokalna baza SQLite, hybrydowe AI (lokalne heurystyki + opcjonalne API w chmurze).

## Start

1. Utwórz venv i zainstaluj zależności:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Uruchom aplikację:
   ```powershell
   python -m lumbago_app.main
   ```

## Konfiguracja

Aplikacja zapisuje bazę danych i cache w `%APPDATA%\\LumbagoMusicAI`.

Opcjonalne klucze API (ustawienia w UI lub `.env`):
- `ACOUSTID_API_KEY`
- `MUSICBRAINZ_APP_NAME`
- `DISCOGS_TOKEN`
- `CLOUD_AI_PROVIDER` (`openai`, `gemini`, `grok`, `deepseek`)
- `CLOUD_AI_API_KEY`
- `GROK_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`


## Praca z Codex i repozytorium

Aby połączyć Codex z tym repozytorium w sesji CLI:

1. Otwórz katalog projektu jako bieżący katalog roboczy (`/workspace/lumbago_codex`).
2. Sprawdź gałąź roboczą i stan plików:
   ```bash
   git status --short --branch
   ```
3. Wykonuj zmiany lokalnie, a następnie zatwierdzaj je commitem:
   ```bash
   git add <pliki>
   git commit -m "Opis zmiany"
   ```
4. (Opcjonalnie) dodaj zdalne repozytorium i wypchnij branch:
   ```bash
   git remote add origin <url_repo>
   git push -u origin <branch>
   ```

To wystarcza, żeby Codex pracował bezpośrednio na historii Git tego projektu.

## Zakres MVP
- Library Browser: lista/siatka, filtry, wyszukiwanie.
- Import i skan folderów z metadanymi (Mutagen).
- Panel szczegółów utworu.
- Podstawowy player (QtMultimedia).
- Lokalny tagger AI (heurystyki).
- Duplikaty: hash + tag-based (fingerprint opcjonalny).

## Linux (headless / CI)

W środowisku bez GUI (np. kontener/CI) uruchom przez Xvfb:

```bash
./scripts/run_headless.sh
```

Skrypt przekazuje argumenty do aplikacji, np.:

```bash
./scripts/run_headless.sh --help
```
