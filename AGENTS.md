# AGENTS.md — TYLKO Desktop Windows Python (D:\Claude)

**GŁÓWNY FOLDER DOMOWY: D:\Claude**

Projekt to **TYLKO I WYŁĄCZNIE** aplikacja desktop PyQt6 na Windows.
Żadnych wersji web.

Agenci pracują wyłącznie na plikach desktop (core/data/services/ui, main.py, desktop docs, MEMORY, crew).

---

# AGENTS.md

**MINIMAL LIVE VERSION (2026-06-16 consolidation).**  
Full historical versions of this file (all "2026-06-15 updates", complete "dalej"/Etap4/Smart/Duplicate/Clean Windows logs, old crew outputs) + all prior agent instructions, full checklists, and context are safely archived in `MEMORY/full_agent_instructions/AGENTS_full_historical.md` (and subdirs) and consolidated in memory.md.

All prior information is preserved and accessible. See MEMORY/README_INDEX.md and memory.md "MEMORY Archiwum" section.

Per 2026-06-16 full repo consolidation and cleanup: all prior documentation, full agent instructions, checklists, history, and context memories safely archived in root MEMORY/ directory and consolidated/summarized in this memory.md. Live files trimmed to essential minimum for ongoing work but complete for continuity. All information from the project up to this point is preserved and accessible in MEMORY/.

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

Per 2026-06-16 full repo consolidation and cleanup: all prior documentation, full agent instructions, checklists, history, and context memories safely archived in root MEMORY/ directory (with subdirs) and consolidated/summarized in this memory.md. Live files trimmed to essential minimum for ongoing work but complete for continuity. All information from the project up to this point is preserved and accessible in MEMORY/.

**2026-06-16 note (post-consolidation):** Full verbose 2026-06-15 updates, old crew outputs, research, plans, and history now in MEMORY/full_agent_instructions/ (dated pre-trim copies) + MEMORY/previous_archive/ + other subs. See index in memory.md top "MEMORY Archive" section. Live docs point here for full. Per PLAN/SZPIEG hierarchy + identical docs rule honored.

## Dla nowych agentów/programistów (OBOWIĄZKOWE na starcie sesji):
1. Przeczytaj `memory.md` (pełny pogląd na zasady + stan + SZPIEG + jak dokumentować).
2. Przeczytaj `MEMORY/full_agent_instructions/crew/SZPIEG_agent_spec_and_archive.md` (research + binding spec + encyklopedia) — full pre-trim archived copy.
3. Przeczytaj `MEMORY/full_agent_instructions/crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (jak uruchamiać crew z SZPIEG/Plan first + 6-agent pipeline + God Object acceptance).
4. Potem AGENTS.md/CLAUDE.md (this trimmed) + aktualny kod + git status.
5. Dokumentuj **wszystkie ruchy identycznie** (patrz PLAN + memory). Używaj todo_write dla complex.

See full historical in MEMORY/ (full_agent_instructions/ for AGENTS/CLAUDE/PLAN/SZPIEG/CHECKLIST pre-trim dated; historical_checklists/; previous_archive/ for docs/archive integration; old_docs/; history/). 

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
# Then portable ZIP (per clean Windows P1 Plan lista step 4 + 2026-06-15 push):
# Compress-Archive -Path dist/LumbagoMusicAI/* -DestinationPath dist/LumbagoMusicAI-portable.zip -Force
```
Updated spec (2026-06-15) includes ui/assets, tools/fpcalc, hiddenimports for clean EXE (frozen path helper in core/config.py). See Checklist P1#1 + Plan lista + docs/clean_windows_test.md. Push + compact per user request.

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

**2026-06-02 update:** REVIEWER w crew (dla single Odtwarzacz MVP) — raport weryfikacji ANALYZER + fixes + remaining P0/P1 (spin paint, dual overhead, compact scalab etc) + przekazanie do SZPIEG + docs update identycznie (SZPIEG archive, memory, HISTORY, CHECKLIST). Patrz crew/SZPIEG_agent_spec_and_archive.md (REVIEWER entry) + memory current state. Zawsze czytaj memory+SZPIEG+PLAN przed crew.

**2026-06-25 TESTER update (P1.1 local buttoned):** Pełna lokalna weryfikacja Linux (smoke logic, python -c PlaybackEngine/get_backend_info/get_diagnostics/frozen paths PASS, pytest playback relevant, smoke raport check) + covered vs gaps (z fresh Szpieg P1.1) + fixes prop + docs ident update (clean_windows_test, TODO, PLAN, memory, HISTORY, this) per PLAN hierarchy exact. "per SZPIEG research 2026-06-25 Clean Windows P1 ... must document identical". Local closed. Per "nie przestawaj" od A do Z.

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

**2026-06-02 update (WRITER Odtwarzacz MVP fixes 1-12):** Zrealizowano pełną listę przeróbek per SZPIEG+Plan (QStack, compact+spin, playback/drag etc, testy, docs). Tests OK. Docs zaktualizowane identycznie (memory/HISTORY/SZPIEG/PLAN/crew/AGENTS/CLAUDE/Checklist). Przekazano FIXER/TESTER. Exact match. Patrz memory + crew/SZPIEG.
**2026-06-02 note:** SZPIEG full audit Odtwarzacz MVP (cała budowa single player) wykonany; encyklopedia + Build Spec + problemy lista + punktowanie w crew/SZPIEG... + memory/HISTORY/CHECKLIST. Hierarchy: SZPIEG/Plan first (lista user review), potem crew exact. Dokumentuj identycznie.
**2026-06-02 UI-DESIGNER:** Audyt/redesign Odtwarzacza MVP (single compact): layout air/VBox/HBox/wave/trans/spin, compact pilot (collapse+spin cos/sin fix), QStack switch, drag mime+lookup+safety, EFFECT, scalability, black/empty. Redesign doc crew/UI_Designer_Odtwarzacz_MVP_Redesign.md (po polsku jak AGENT3). Problemy handover SZPIEG/WRITER (spin P0, compact resize P1, guards P1). Updates memory/HISTORY/SZPIEG/AGENTS/CLAUDE/crew CHECKLIST identycznie + todo. Per PLAN/SZPIEG lead. Patrz memory (UI-DESIGNER wpis) + crew/UI_Designer... + SZPIEG archive.

**2026-06-02 TESTER (post WRITER/FIXER full verify Odtwarzacz MVP per task/PLAN):** Smoke exit0 OK; pytest 44p OK; python-c headless stack2/idx1/compact/_compact/spin_spinning/load/play/cue/resize/drag OK; manual adapted CHECKLIST (single clean air/BPM/wave/trans/drag/resize/compact pilot+EFFECT+cue/QStack/no gestosc/scalab) OK; edges OK; verify fixes (spin rotates cos/sin angle YES, no silent, bg surface, indices, air, init, no NameError) all OK. Gotowe max3. No fail to SZPIEG/WRITER. Docs updated identically (this + CLAUDE + memory + HISTORY + SZPIEG + crew/CHECKLIST + todo). Abs paths in reports: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py (spin fixed by FIXER) + crew/* . Ready.
**2026-06-02 FIXER:** Naprawiono bugi Odtwarzacz MVP wg SZPIEG/Plan lista (spin rot cos/sin, vis compact isVisible, load guards safety, init race, legacy single_container remove, reentr, compact playback, scalab air/dynamic/window shrink, file/stream guards/comments, drag hl, cue). Smoke/pytest/python-c OK. Docs update. Patrz memory + crew/SZPIEG + HISTORY.
**2026-06-02 REVIEWER (fresh re-audit "jeszcze raz" per PLAN/SZPIEG/task):** Cross-check ANALYZER+current code vs spec/Plan lista/CHECKLIST; baselines smoke0/pytest44p/python-c (stack2 idx1 odt current compact spin cos/sin drag OK); fixes hold; compliance 94%; remaining P1 dual overhead/compact scalab, P2 tooltip etc (no P0); raport po polsku; docs identical (SZPIEG/memory/HISTORY/CHECKLIST/AGENTS/CLAUDE); 'gotowe'. Przekaz SZPIEG side + crew. Abs: ui/dj_player_window.py + odtwarzacz_view.py + crew/*. Per "nie przestawaj" + hierarchy.
**2026-06-02 ANALYZER (Code Review Crew per PLAN + SZPIEG lead + memory "Dla nowych" + "uruchmo jeszcze raz... nie przestawaj"):** Deep audit po kolei całej budowy single Odtwarzacz MVP (D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py + ... + data/repository.py). Full step-by-step findings + fresh P0-P10 (spin vis headless P0 etc) + compare SZPIEG spec high match + re-audit triggers. Polish report + pass SZPIEG + crew. Docs updated identical (SZPIEG append full ANALYZER, memory, HISTORY, CHECKLIST, this AGENTS, CLAUDE, code docstrings "per SZPIEG... must document identical" + 2026 explicit). todo_write. Abs paths. Gotowe. Przekazuję problemy SZPIEG + crew. Per hierarchy.
**2026-06-02 SZPIEG re-audit per user "uruchmo jeszcze raz zespouł agentów do sprawdzenia po kolei calej budowy odtwarzacza, i problematyczne elementy prxzekaz dla szpiega do badań. nie przestawaj puki nie skonczysz":** Pełny re-audit po kolei całej budowy (single primary) + research/punktowanie/Build Spec/P0-P10 przekaz/side tasks. Docs updated identically (SZPIEG new entry, memory, HISTORY, PLAN, CHECKLIST, this AGENTS, CLAUDE, code docstrings "per SZPIEG Build Spec + Plan team review 2026... user explicit: uruchmo jeszcze raz... nie przestawaj puki nie skonczysz... must document identical"). 'gotowe'. Przekaz Planowi + crew (lista first). Ukończone. Do końca.

**2026-06-14 FIXER (po "dalej" + SZPIEG/Plan nowa lista 1-15 polish):** Polish edges (2,5,7,12,14,9,10 + compact prompt UX, highDPI/empty, vis timing, guards, legacy, black/empty, file/stream): prompt UX (QMessage parent=top floating pilot); highDPI/empty+vis (force apply); legacy guard. Read-before. Verifs smoke0/pytest44p/python-c/manual CHECKLIST+edges green. 'gotowe' pass TESTER. Docs identical. Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py (prompt+highDPI+legacy+vis) + crew/* . Ukończone. Do końca. "nie przestawaj". Per hierarchy.
**2026-06-02 TESTER re-run (Zespół uruchomiony ponownie, final verify post FIXER):** Pełna weryfikacja (smoke0/pytest44p/python-c create+stack2/idx1/compact/load/play/cue/resize/drag/switch/asserts OK; manual CHECKLIST single air32/24/QStack/BPM/wave/trans/drag/compact rot spin cos/sin/EFFECT/cue/scalab/safety/file-stream OK; edges+verify fixes all green). Gotowe max3. No issues. Ukończone. Do końca. "nie przestawaj honored". Docs identical (memory top, SZPIEG, HISTORY, crew/CHECKLIST, this AGENTS, CLAUDE, code). Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py + ... . Per PLAN/SZPIEG. ALL OK.

**2026-06-14 TESTER (final verify po "dalej" + nowa lista 1-15 WRITER/FIXER per PLAN/SZPIEG "nie przestawaj"):** Smoke exit0; pytest 44p+1s; python-c headless (create/lazy/compact+spin vis/load/ctrl/resize/drag/switch asserts stack=2 cur=ODT1 no crash) OK; manual CHECKLIST single + edges + lista polish (always-on-top StaysOnTop+shrink/guards/EFFECT/scalab/legacy/spin cos/sin/file-stream) all green. ALL OK 'gotowe'. Abs D:\Claude\ui\dj_player_window.py + odtwarzacz_view.py + ... . Ukończone. Do końca. Nie przestawaj honored. Docs identical (memory/SZPIEG/HISTORY/CHECKLIST/AGENTS/CLAUDE + code "per SZPIEG... uruchmo... nie przestawaj... must document identical"). Per hierarchy.

**2026-06-14 — WRITER (execute zatwierdzona nowa lista 1-15 po user "dalej" per PLAN/SZPIEG PRIORYTET#1 + "nie przestawaj"):** OBOWIĄZKOWA LEKTURA first via read/grep (memory + SZPIEG re-audit last + PLAN + CHECKLIST + UI_Designer + odt/dj_player/simple/styles/main/repo). High pressure: read before every search_replace, exact match lista + spec, zero odstępstw, Polish, only UI style/structure/polish/guards/docs/tests (no core cue/play). Grupy wykonane: 1+8 QStack/guards/init/on-demand/legacy (dj_player + odt); 2+12 compact+always-on-top/floating/reduce empty; 3+10 EFFECT/file/stream uniform; 5+9 scalab/black; 4+6+7+14 drag/cue/legacy/moreguards. Verifs: smoke0, pytest relevant green, python-c (odt ready, stack/idx, compact, load/cue/play/resize/switch no crash), CHECKLIST+edges green. 'gotowe' + pass FIXER/TESTER. Docs identical incl. "per SZPIEG Build Spec + Plan nowa lista po 'dalej' user... must document identical". Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py . Ukończone. Do końca.

**2026-06-15 dalszy 'dalej' (Duplicate Finder polish per "dalej"):** Continuation on approved backlog "Ulepszony Duplicate Finder z pełnym audio fingerprint". Fixed fp groups in fuzzy_dedup (object-based 0.97 + match_method), wired Etapowo to find_staged_duplicates (3-method pipeline live in UI + sim labels), unified scores, polished merge logic + docs in DuplicateMergeWorker/_merge_selected (fp audio dups => reliable consensus/or "logikę łączenia"). Docs identical + "per SZPIEG Build Spec + Plan nowa lista po 'zatwierdzam'/'dalej' user + 'nie przestawaj'... must document identical". todo, verifs, push. 'Gotowe' block. Nie przestawaj honored. Per hierarchy.

**2026-06-15 Clean Windows P1 closure (ALL-01 per user "execute all from start to end button to last detail without stopping or asking") + dalszy 'dalej' (dadalej / label polish per "dadalej"):** Enhanced smoke/build/spec for full clean_windows_test.md coverage (resources + manual notes for import/detail/player/DB + Etap4 VLC guidance + FILE/STREAM/no-silent/portable). Local buttoned; VM pending. Row labels for Etapowo/Fuzzy now show match_method ("Grupa X (sim 0.97, fingerprint)" etc) — 3-method stages visible. Per SZPIEG research 2026-06-15 Clean Windows P1 closure + Duplicate Finder dopinanie to the absolute last detail + manual punkt 4 + full CHECKLIST + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical. Verifs + push. 'Gotowe' local. 'Nie przestawaj'. Per hierarchy. Momentum continued.

**2026-06-25 TESTER (po "polish" z Writer (no-VLC, compact, diagnostics) + prior Szpieg/Plan research):** Pełne lokalne verifs dla DJ Player checklist auto parts i P1 local: smoke SAFE sim GREEN, python-c headless GREEN core, pytest relevant GREEN, code check no-VLC visibility + compact polish GREEN. Raport + update docs identycznie z frazą. Per SZPIEG Build Spec + Plan ... must document identical. 'gotowe' local.
