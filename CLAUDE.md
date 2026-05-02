# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lumbago Music AI is a music library management tool for DJs and collectors. The repository contains three independently runnable applications that share a common Python backend core:

1. **Desktop App** (`lumbago_app/`) — PyQt6 GUI, Windows primary target
2. **Web MVP** (`web/`) — React/TypeScript frontend + FastAPI backend, deployed on Vercel
3. **tagerv2** (`tagerv2/`) — Standalone browser-only React tagger with client-side Gemini AI

`lumbago_fresh/` and `_analysis/` are earlier prototypes/reference material, not actively developed.

---

## Commands

### Desktop App (Python)

```bash
python -m venv .venv && source .venv/bin/activate  # Linux
pip install -r requirements.txt && pip install -e .
python -m lumbago_app.main
```

On Linux/CI (requires Xvfb for PyQt6):
```bash
./scripts/run_headless.sh
```

### Python Tests

```bash
pytest                           # all tests (configured in pytest.ini)
pytest tests/test_renamer.py     # single file
pytest -k test_name              # single test by name
xvfb-run -a python -m pytest -q tests  # Linux headless
```

UI smoke test (no display required, exits after 3s):
```bash
LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python -m lumbago_app.main
```

### Web Backend (FastAPI)

```bash
uvicorn web.backend.api:app --reload
```

### Web Frontend (`web/`)

```bash
cd web && npm ci
npm run dev     # dev server
npm test        # vitest
npm run build   # production build (output: web/dist, deployed via Vercel)
```

### tagerv2 (`tagerv2/`)

```bash
cd tagerv2 && npm install
npm run dev     # dev server on port 5173
npm run build
npm run lint    # ESLint, max-warnings 0
```

### Windows Release Build

```bash
pyinstaller pyinstaller.spec --noconfirm  # output: dist/LumbagoMusicAI/
```

---

## Architecture

### Desktop App — `lumbago_app/`

**Four packages:**

- `core/` — Pure logic, no Qt. `models.py` defines all dataclasses (`Track`, `AnalysisResult`, `Playlist`, etc.). `audio.py` reads/writes audio tags via Mutagen. `config.py` resolves settings with priority: `settings.json` → env vars → Windows registry. `services.py` contains heuristic analysis and duplicate detection logic.
- `data/` — SQLAlchemy ORM. `schema.py` defines all ORM classes (`TrackOrm`, `TagOrm`, `PlaylistOrm`, etc.). `repository.py` is the single point of DB access. `db.py` manages the engine/session factory (lazy singleton). DB lives at `%APPDATA%/LumbagoMusicAI/lumbago.db` (or `.lumbago_data/` fallback on Linux).
- `services/` — Pluggable analysis services: `ai_tagger.py` (local heuristics + cloud AI via OpenAI-compatible API or Gemini), `ai_tagger_merge.py` (merges `AnalysisResult` onto `Track`, filling blanks without overwriting), `metadata_providers.py` (MusicBrainz, Discogs), `recognizer.py` (AcoustID/fpcalc), `key_detection.py`, `loudness.py`, `beatgrid.py`, `fuzzy_dedup.py`.
- `ui/` — PyQt6 dialogs and widgets. `main_window.py` is the central hub that wires all dialogs together.

**DB schema evolution:** `repository.init_db()` calls `Base.metadata.create_all()` then manually `ALTER TABLE` for any missing columns. Alembic migrations in `migrations/` exist but are secondary to the inline approach.

### Web Backend — `web/backend/`

`api.py` is a single FastAPI app that:
- **Re-uses** the desktop's `lumbago_app.data` layer (same SQLite DB) for track storage
- Has its own lightweight SQLite (`web_backend.sqlite3`) via `web/backend/db.py` for settings, cache, and tag history
- Migrations for the second DB are raw SQL files in `web/backend/migrations/`

Key routes: `GET /tracks`, `POST /tracks/import-preview`, `POST /tracks/import-commit`, `POST /duplicates/analyze`, `GET|PUT /settings/{key}`, `GET|PUT /cache/{key}`, `POST /tag-history`.

### Web Frontend — `web/src/`

Minimal React app (no CSS framework). `App.tsx` fetches tracks from the backend, filters them, and renders a list with an audio player, import wizard, and duplicate finder. `web/src/api/client.ts` is the single API client file. Deployed to Vercel as configured in `vercel.json`.

### tagerv2 — `tagerv2/`

Fully browser-side; no backend. Files are loaded directly via the File System Access API. State is persisted to `localStorage`. AI analysis is called client-side via `@google/genai` (Gemini). Key hooks: `useLibrary` (file list, playlists, sorting/filtering), `useAIProcessing` (batch tag enrichment), `useSettings` (API keys, preferences).

---

## Key Conventions

### Python

- All files use `from __future__ import annotations`.
- Formatter: `black` with `line-length = 100` (`pyproject.toml`).
- Domain models are pure dataclasses in `core/models.py`. ORM models are separate in `data/schema.py`. Never mix them.
- All DB writes go through `data/repository.py`; never call `Session` directly from UI code.
- `AnalysisResult` → `Track` merging always uses `ai_tagger_merge._merge_analysis_into_track()` to avoid overwriting valid existing metadata.
- Settings are read via `load_settings()` — do not read env vars directly in feature code.

### TypeScript

- React 18 + TypeScript 5; Vite as bundler.
- `tagerv2` uses Tailwind CSS; `web/` uses plain CSS.
- Central type definitions: `tagerv2/types.ts` and `web/src/types.ts`.

### Cloud AI Providers (Desktop)

Supported: `gemini`, `openai`, `grok`, `deepseek`. All non-Gemini providers use the OpenAI-compatible chat completions endpoint. Provider, base URL, model, and API key are all configurable via env/settings. Defaults are set in `config.py`.

### Audio Formats

Supported extensions: `.mp3`, `.flac`, `.m4a`, `.mp4`, `.wav`, `.ogg`, `.aac`, `.aiff` (defined in `core/audio.py`).

---

## CI

- **Desktop CI** (`.github/workflows/desktop-ci.yml`): runs `pytest` on Ubuntu (via `xvfb-run`) and Windows, then builds the Windows PyInstaller artifact.
- **Web CI** (`.github/workflows/web-ci.yml`): installs and builds the `web/` frontend; triggered only when web-related files change.
- Python version pinned to 3.11 in CI.
