# LUMBAGO MUSIC AI — TYLKO WERSJA DESKTOP WINDOWS (Python + PyQt6)

**GŁÓWNY FOLDER DOMOWY PROJEKTU: D:\Claude**

Ten projekt jest **wyłącznie** aplikacją okienkową na Windows w języku Python (PyQt6).
Nie rozwijamy żadnych wersji web, WinUI, Next.js ani innych.

Agenci (Szpieg, Plan, crew itd.) **muszą** pracować tylko i wyłącznie na plikach desktop:
- main.py
- core/, data/, services/, ui/
- .github/workflows/desktop-ci.yml
- docs/ (tylko desktop)
- scripts/ (Windows PowerShell)
- MEMORY/, crew/

Wszystkie pozostałości web zostały usunięte z głównego drzewa.
Struktura jest czysta, zgodna z najlepszymi praktykami (beets/Picard style + src-like separation + living docs + agent-friendly).

Per 2026-06-16 full repo consolidation (SZPIEG research lead): ALL prior documentation, old agent outputs, full checklists, unused docs, previous crew reports, history, mockups, build artifacts, web remnants, legacy plans, DESIGN docs, Blueprint extract etc. safely archived in root MEMORY/ directory (substructure: full_agent_instructions/, historical_checklists/, archive/ (from prior 2026-06-15 docs/archive/), old_docs/, previous_runs/ etc.) and summarized/pointered in this memory.md (Archiwum section). Live files (AGENTS/CLAUDE/crew/PLAN/SZPIEG/CHECKLIST + docs/HISTORY/guides + README etc.) minimized for continuity but complete. All information preserved and accessible via MEMORY/INDEX.md + git history. Builds on 2026-06-15 uporządkowanie to docs/archive/. Per SZPIEG research 2026-06-16 consolidation + Plan hierarchy + "uruchamiaj szpiega przed kazdym wiekszym etapem" + "nie przestawaj" + "must document identical".

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

## Audio / DJ Player

Aplikacja używa **VLC** jako preferowanego backendu playbacku (wysoka jakość, niskie opóźnienia, crossfading).

- Na Windows CI (`desktop-ci.yml`) VLC jest instalowany automatycznie przez **Chocolatey** + cache + fallback do direct download (stabilne, nieblokujące).
- W razie braku VLC aplikacja gracefully przełącza się na **Qt backend** lub **Noop** (testy i smoke przechodzą).
- Dla pełnej funkcjonalności DJ Playera na maszynie użytkownika: zainstaluj VLC z https://videolan.org lub rozpakuj portable obok exe.

W kodzie: `services/playback/` (VlcAudioBackend prio → Qt → _NoopAudioBackend), `PlaybackEngine.get_backend_info()`.

## Kompatybilność z Vercel i narzędziami agentów

Projekt jest **wyłącznie desktopowy** (PyQt6 + DJ Player). Wersje web i inne zostały usunięte.

**CodeQL**: Analiza `javascript-typescript` wyłączona (tylko zarchiwizowane resztki Next.js w `docs/archive/web-remnants/`). Aktywne języki: `actions` + `python`.

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
