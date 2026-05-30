# Lumbago Music AI

**Desktopowa aplikacja** do zarządzania biblioteką muzyczną dla DJ-ów i kolekcjonerów.

- UI: PyQt6 (Windows primary)
- Baza: SQLite (SQLAlchemy + Alembic)
- AI: hybrydowe (lokalne heurystyki + opcjonalne API w chmurze: Gemini / OpenAI / Grok / DeepSeek)
- DJ Player: wbudowany profesjonalny dual-deck (Rekordbox-style) w osobnym oknie

**Projekt jest wyłącznie desktopowy.** Wersje web (FastAPI + React), standalone React (tagerv2) i planowana migracja na WinUI 3 zostały usunięte z repozytorium w celu uproszczenia i skupienia na głównej funkcjonalności.

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
