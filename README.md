# Lumbago Music AI

Desktopowa aplikacja do zarządzania biblioteką muzyczną dla DJ-ów i kolekcjonerów.
UI w PyQt6, lokalna baza SQLite, hybrydowe AI (lokalne heurystyki + opcjonalne API w chmurze).

## Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python main.py
```

## Konfiguracja

Baza danych i cache: `%APPDATA%\LumbagoMusicAI\lumbago.db`

Opcjonalne klucze API (ustawienia w UI lub `.env`):
```
ACOUSTID_API_KEY
MUSICBRAINZ_APP_NAME
DISCOGS_TOKEN
CLOUD_AI_PROVIDER   # openai | gemini | grok | deepseek
CLOUD_AI_API_KEY
```

## Build (Windows EXE)

```powershell
pyinstaller pyinstaller.spec --noconfirm
# output: dist/LumbagoMusicAI/
```

## Testy

```powershell
pytest
```
