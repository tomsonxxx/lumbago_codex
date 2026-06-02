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

## Kompatybilność z Vercel i narzędziami agentów

Projekt jest **wyłącznie desktopowy** (PyQt6 + DJ Player). Wersje web i inne zostały usunięte.

Dla poprawnego działania na platformie Vercel (obejście wykrywania `main.py` jako funkcji serverless) dodano minimalną, nieaktywną warstwę Next.js:

- `vercel.json` (framework: "nextjs")
- `app/` (prosty App Router z `layout.tsx` zawierającym `import { SpeedInsights } from "@vercel/speed-insights/next"`)
- `package.json` ze skryptami build/dev Next

**vercel-plugin** (https://github.com/vercel/vercel-plugin) jest zarejestrowany w repo (manifesty `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` — lekkie pliki JSON).

Aby załadować skills, agentów (ai-architect, deployment-expert, performance-optimizer) i komendy Vercel/Next.js do Claude Code / Cursor / Codex:

```powershell
npx plugins add vercel/vercel-plugin --target claude-code --scope project --yes
# analogicznie dla codex lub cursor
```

Pełna treść (26 skills: nextjs, vercel-cli, deployments-cicd itd.) trafia do cache agenta (`~/.claude/plugins/cache/...`). Po instalacji zrestartuj narzędzie agenta.

To nie jest pełna aplikacja web — tylko obecność wymagana przez Vercel + wsparcie dla AI agentów pracujących z tym repo.
