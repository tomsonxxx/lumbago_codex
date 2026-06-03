# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Lumbago Music AI is a music library management tool for DJs and collectors.
Single application: **Desktop App** — PyQt6 GUI, Windows primary target.

Entry point: `python main.py`

---

## Commands

### Run

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt && pip install -e .
python main.py
```

UI smoke test (exits after 3 s, no display required on CI):
```bash
LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py
```

### Tests

```bash
pytest                        # all tests (configured in pytest.ini)
pytest tests/test_renamer.py  # single file
pytest -k test_name           # single test by name
```

### Windows Release Build

```bash
pyinstaller pyinstaller.spec --noconfirm  # output: dist/LumbagoMusicAI/
```

---

## Architecture

**Four packages at repo root:**

- `core/` — Pure logic, no Qt. `models.py` defines all dataclasses (`Track`, `AnalysisResult`, `Playlist`, etc.). `audio.py` reads/writes audio tags via Mutagen. `config.py` resolves settings with priority: `settings.json` → env vars → Windows registry. `services.py` contains heuristic analysis and duplicate detection logic.
- `data/` — SQLAlchemy ORM. `schema.py` defines all ORM classes (`TrackOrm`, `TagOrm`, `PlaylistOrm`, etc.). `repository.py` is the single point of DB access. `db.py` manages the engine/session factory (lazy singleton). DB lives at `%APPDATA%/LumbagoMusicAI/lumbago.db` (or `.lumbago_data/` fallback).
- `services/` — Pluggable analysis services: `ai_tagger.py` (local heuristics + cloud AI via OpenAI-compatible API or Gemini), `ai_tagger_merge.py` (merges `AnalysisResult` onto `Track`, filling blanks without overwriting), `metadata_providers.py` (MusicBrainz, Discogs, TheAudioDBProvider, ListenBrainzProvider + FallbackMetadataChain), `free_music_portals.py` (Deezer/ListenBrainz/TheAudioDB/Last.fm/... + new LRCLIB, Lyrics.ovh public no-auth for lyrics+genre+year), `recognizer.py` (AcoustID/fpcalc), `key_detection.py`, `loudness.py`, `beatgrid.py`, `fuzzy_dedup.py`. Network sources now include more public fallbacks for missing genre/year/lyrics/tags.
- `ui/` — PyQt6 dialogs and widgets. `main_window.py` is the central hub that wires all dialogs together.

**DB schema evolution:** `repository.init_db()` calls `Base.metadata.create_all()` then manually `ALTER TABLE` for any missing columns. Alembic migrations in `migrations/` exist but are secondary to the inline approach.

---

## Key Conventions

### Python

- All files use `from __future__ import annotations`.
- Formatter: `black` with `line-length = 100` (`pyproject.toml`).
- Domain models are pure dataclasses in `core/models.py`. ORM models are separate in `data/schema.py`. Never mix them.
- All DB writes go through `data/repository.py`; never call `Session` directly from UI code.
- `AnalysisResult` → `Track` merging always uses `ai_tagger_merge._merge_analysis_into_track()` to avoid overwriting valid existing metadata.
- Settings are read via `load_settings()` — do not read env vars directly in feature code.

### Cloud AI Providers

Supported: `gemini`, `openai`, `grok`, `deepseek`. All non-Gemini providers use the OpenAI-compatible chat completions endpoint. Provider, base URL, model, and API key are all configurable via env/settings. Defaults are set in `core/config.py`.

### Audio Formats

Supported extensions: `.mp3`, `.flac`, `.m4a`, `.mp4`, `.wav`, `.ogg`, `.aac`, `.aiff` (defined in `core/audio.py`).

---

## CI

- **Desktop CI** (`.github/workflows/desktop-ci.yml`): runs `pytest` on Windows, then builds the PyInstaller artifact. Python version pinned to 3.11.

## Agent Tooling

Vercel plugin (https://github.com/vercel/vercel-plugin) is registered for this project:

- Installed via: `npx plugins add vercel/vercel-plugin --target claude-code --scope project --yes` (and same for codex, cursor)
- Manifests committed: `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` (lightweight JSON registration + marketplace)
- Enables 26 Vercel/Next.js skills, 3 specialist agents (ai-architect, deployment-expert, performance-optimizer), custom commands and hooks when using supported agent CLIs/IDEs (Claude Code, Cursor, Codex) inside this directory.
- Skills cover: nextjs, vercel-cli, deployments-cicd, ai-sdk, vercel-functions, workflow, env-vars, marketplace etc.
- After `npx plugins ...` run, restart the agent tool to load. Full content lives in `~/.claude/plugins/cache/vercel/...` (or equivalent for codex/cursor).
- Relevant here because of `vercel.json` + `app/` (Next.js presence layer added to support Vercel deploys for the desktop project) and any future web-facing work.

To re-run / update: `npx plugins add vercel/vercel-plugin --target <claude-code|codex|cursor> --scope project --yes`

## Crew Launch Plan + Hierarchy (2026 — SZPIEG jako research lead, Plan review listy jako pierwszy krok użytkownika)

**PRIORYTET #1 (z feedbacku użytkownika na plan):** Aktualizacja zmiany pracy zespołu i funkcje SZPIEGA muszą być wzięte pod uwagę **w pierwszej kolejności**.

**Obowiązkowa lektura przed jakimkolwiek uruchomieniem crew lub pracą na fragmentach:**
- `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (ten plan uruchomienia 6-agent crew, z SZPIEG + Plan review "nowej listy przeróbek" jako sekcją 1 binding; user musi przeczytać listę przeróbek najpierw i zdecydować; pipeline ANALYZER→... podlega nowemu procesowi; God Object note dla Writer — "ok" potwierdzone).
- `memory.md` (centralna encyklopedia: zasady, aktualny stan, hierarchy, jak dokumentować identycznie dla multi-team continuity).
- `crew/SZPIEG_agent_spec_and_archive.md` (nadrzędny research + Build Spec + encyklopedia findings + Plan wnioski/punktowanie).

**Podsumowanie hierarchii (szczegóły w PLANie powyżej):**
- **SZPIEG (SPY):** Nadrzędny research lead dla wąskich fragmentów. Listy 10-15+ narzędzi, punktowanie przydatności dla TEGO projektu, Build Spec binding, encyklopedia, compact pilot/EFFECT/file-vs-stream/air/scalability etc. Decyduje przy braku ścisłego "copy X". Side tasks tylko wyjątkowe + consent.
- **Plan agent:** Zawsze przed impl — produkuje pełne wnioski + punktowanie + "nową listę przeróbek" (zachować X / przerobić Y + krok-po-kroku). Prezentacja użytkownikowi **w pierwszej kolejności** do przeczytania i decyzji ("dajcie mi w pierwszej kolejnosci przeczytać..."). Dopiero po "dalej" — crew przechodzi do działania.
- **6-agent Code Review Crew (ANALYZER → REVIEWER → UI-DESIGNER → WRITER → FIXER → TESTER, max 3 iteracje, polski):** Dostaje combined SZPIEG spec + zatwierdzoną listę z Planu jako primary. High pressure "exact match", read-before-edit, zero odstępstw. Writer: nie zmienia radykalnie logiki biznesowej w UI (tylko styl i strukturę) — **OK** (per user feedback). Po Opcja A architektura jest separated (controllers + dumb views), więc bezpieczniej.
- **Zasady dokumentacji (dla odrębnych zespołów/multi-team):** Zawsze update memory + HISTORY + SZPIEG archive + AGENTS/CLAUDE + crew/CHECKLIST/LISTA + code docstrings ("per nadrzędny SZPIEG Build Spec + Plan team review... must document identical") + todo_write + clear commits. Bez tego nie ma continuity.

**Dla nowych agentów/programistów (OBOWIĄZKOWE na starcie sesji):** 
1. Przeczytaj `memory.md` (pełny pogląd na zasady + stan + SZPIEG + jak dokumentować).
2. Przeczytaj `crew/SZPIEG_agent_spec_and_archive.md` (research + binding spec + encyklopedia).
3. Przeczytaj `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (jak uruchamiać crew z SZPIEG/Plan first + 6-agent pipeline + God Object acceptance).
4. Potem AGENTS.md/CLAUDE.md + aktualny kod + git status.
5. Dokumentuj **wszystkie ruchy identycznie** (patrz PLAN + memory). Używaj todo_write dla complex.

See `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` + `crew/SZPIEG_agent_spec_and_archive.md` + `memory.md` jako primary living docs. Stary crew output (np. AGENT3) jest historycznym przykładem — nowe uruchomienia muszą iść wg zaktualizowanego PLANU.
