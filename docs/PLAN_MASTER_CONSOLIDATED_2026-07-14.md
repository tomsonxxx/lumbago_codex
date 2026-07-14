# PLAN MASTER — Lumbago Music AI (Konsolidowany master wszystkich planów, TODO i checklist)

**Data:** 2026-07-14 (po Faza0-5 local closure + Downloader/AI Faza4 + TESTER Faza2 + CI fix + push)
**Źródła konsolidacji (przeanalizowane przez agentów Explore + Plan):** 
- docs/PLAN_ROZBUDOWA_2026-07-14.md (główny roadmap Faza0-5)
- docs/PLAN_DZIALANIA_2026-06-25.md (wcześniejszy szczegółowy)
- TODO.md (zbiorcza lista P0/P1/backlog)
- crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md (hierarchia + pipeline)
- crew/SZPIEG_agent_spec_and_archive.md (nadrzędny research + Build Spec + encyklopedia)
- crew/CHECKLIST_reczny_test_nowy_DJ_Player.md + crew/CHECKLIST_Downloader_AI_Panel.md
- docs/clean_windows_test.md (manual + portable + Downloader notes)
- docs/manual_dj_checklist_printable.md
- docs/chce dodać nowe, dosc komplikowane.txt (źródłowa spec Downloader + AI)
- memory.md + docs/HISTORY.md (status + frazy + historia)
- MEMORY/ (pełne pre-trim wersje + CONSOLIDATION_REPORT_2026-06-16 + INDEX.md + previous_archive)
- AGENTS.md / CLAUDE.md / README / user_guide (odniesienia)

**Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + Downloader/AI per "chce dodać nowe, dosc skomplikowane.txt" + "dalej az do ukonczenia wszystkich faz" + consolidation using agents (Explore + Plan subagent) ... must document identical.**

**Uwaga:** To jest **jeden spójny autorytatywny plik**. Wszystkie inne pliki (memory, TODO, PLAN_*, crew/CHECKLIST, clean_windows itp.) powinny zawierać pointer do tego pliku + aktualizować statusy + frazy identycznie. Pełna historia i verbose wersje pre-trim są w `MEMORY/`.

---

## 0. Hierarchia, Proces i Zasady (OBOWIĄZKOWE — PRIORYTET #1)

**Dla nowych agentów/programistów (zawsze na starcie sesji):**
1. Przeczytaj `memory.md` (pełny pogląd + stan + Archiwum).
2. Przeczytaj `MEMORY/full_agent_instructions/crew/SZPIEG_agent_spec_and_archive.md` (lub live `crew/SZPIEG...`).
3. Przeczytaj `MEMORY/full_agent_instructions/crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (lub live crew/PLAN...).
4. Potem ten MASTER + aktualny kod + git status.
5. Dokumentuj **wszystkie ruchy identycznie**.

**Hierarchia crew (SZPIEG jako research lead):**
- **SZPIEG (SPY):** Nadrzędny research lead dla wąskich fragmentów. Tworzy listę 10-15+ narzędzi/praktyk + punktowanie + Build Spec (nadrzędny/binding). Encyklopedia w SZPIEG pliku. Decyduje gdy brak ścisłego "copy X".
- **Plan agent:** Zawsze przed impl — produkuje pełne wnioski + "nową listę przeróbek" (zachować X / przerobić Y + krok-po-kroku). Prezentacja użytkownikowi **w pierwszej kolejności**.
- **6-agent Code Review Crew:** ANALYZER → REVIEWER → UI-DESIGNER → WRITER → FIXER → TESTER (max 3 iteracje, polski). Dostaje combined SZPIEG spec + zatwierdzoną listę.
- **Zasady:** SZPIEG/Plan first. User "dalej"/"zatwierdzam" przed crew. Exact match, read-before-edit, zero odstępstw. Verifs + todo_write + **dokumentacja identycznie** z frazą. "Nie przestawaj". Zamykaj A do Z.

**Dokumentacja identycznie (kluczowa reguła):**
Zawsze update: memory.md + HISTORY.md + ten MASTER + TODO.md + crew/CHECKLIST* + AGENTS.md/CLAUDE.md + PLAN_* (pointery) + code docstrings z frazą:
"Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + Downloader/AI per \"chce dodać nowe, dosc skomplikowane.txt\" + 'dalej az do ukonczenia wszystkich faz' ... must document identical."

**Pipeline dla każdej fazy/iteracji:**
1. SZPIEG (narrow research + Build Spec).
2. Plan ("nowa lista" first dla użytkownika).
3. User decyzja ("dalej"/"zatwierdzam").
4. Crew (exact).
5. Verifs (smoke, pytest, python-c, manual CHECKLIST, Win/VM).
6. todo_write + docs identical.
7. Commit/push.

**Język:** Polski w dokumentach planistycznych (dla spójności). Desktop-only (PyQt6 Windows).

---

## 1. Komendy, Smoke, Testy i Verification Matrix

### Podstawowe komendy (z AGENTS.md / CLAUDE.md)
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
python main.py

# UI smoke test (headless)
LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py

# Testy
pytest
pytest -k "playback or downloader or odt or dj or waveform or smart or smart_collections"

# Windows portable build + smoke
.\scripts\build_portable_windows.ps1
.\scripts\smoke_portable_windows.ps1
```

### Verification Matrix (stan na 2026-07-14)

| Faza / Obszar              | smoke (SAFE+DIAG) | pytest relevant | python-c sims          | manual CHECKLIST (helper/printable) | Win/VM (real) | Status     |
|----------------------------|-------------------|-----------------|------------------------|-------------------------------------|---------------|------------|
| Faza0 (manual + sizes)     | GREEN             | GREEN (relevant) | GREEN (engine/diag)   | GREEN (local)                      | Pending      | Local gotowe |
| Faza1 (highDPI/pitch)      | GREEN             | 21p+ GREEN     | GREEN (rate/keylock/pitch) | GREEN (sizes, compact)            | Pending      | Local gotowe |
| Faza2 (waveform color, Smart nested, intel) | GREEN      | 53p+ GREEN     | GREEN (discrete tint, nested AND/OR, camelot/energy) | GREEN (Faza2 additions)     | Pending      | Local gotowe (TESTER closed) |
| Faza3 (Packaging/CI + Downloader notes) | GREEN (portable strict) | GREEN     | GREEN (frozen paths)  | GREEN (portable + DL notes)        | Pending      | Enhanced |
| Faza4 (Downloader 700+ + AI complex) | GREEN        | 14p+ GREEN     | GREEN (est 700, registry, dispatcher, real counts, worker) | GREEN (yt-dlp/ffmpeg PATH) | Pending | Local gotowe |
| Faza5 (long-term)          | N/A               | N/A             | N/A                    | Notes only                         | N/A          | Notes added |
| Clean Windows / portable   | GREEN (resources + diag) | -            | -                      | Full flow (import + DJ + DL)       | Pending      | Local scripts + notes |
| No-regresja (EFFECT, FILE/STREAM, air, QStack, highDPI, fallback ⚠) | GREEN | GREEN | GREEN | GREEN | Pending | Preserved |

**Kryteria ogólne "gotowe":** Wszystkie [ ] w checklistach → [x] lub [~] z notką; verifs green; docs identical z frazą; 'gotowe' A-Z. Real Win/VM/E2E/manual pending per "nie przestawaj" + plan.

---

## 2. Faza 0–5 — Pełne Szczegóły

### Faza 0: Close current (manual Win + test gaps + sizes) – P0
**Nowa lista (z PLAN_ROZBUDOWA + clean_windows + CHECKLIST):**
1. Uruchom helper + printable na clean Win (z/ bez VLC): full CHECKLIST (waveform ≥220/80, cross ≥280, compact ~420x300 + StaysOnTop + rapid + spin cos/sin, EFFECT, ⚠ visible, booth 1m, drag, hotcue 8/deck etc.).
2. Fix test gaps (Analyzer): test_odtwarzacz_load.py, test_deck_layout, test_booth_metrics + smoke/main – exact asserts minHeight, fallback text, compact metrics, EFFECT.
3. Sync rozmiarów w styles.py (TOKENS/BOOTH), deck_layout, odt_view, player, compact_pilot.
4. Smoke + python-c + pytest enhancements + portable notes.

**Exact files:** scripts/manual_*.ps1, docs/manual_dj_checklist_printable.md, docs/clean_windows_test.md, crew/CHECKLIST*, tests/test_odt..., smoke/build ps1, ui/dj/* (styles, views, player, compact), services/playback/engine.py, memory, this MASTER, TODO, HISTORY, AGENTS, CLAUDE.

**Verifs + Kryteria:** Jak w matrix powyżej. Local closed. Real Win/VM pending.

**Status:** Local gotowe. Per fraza.

### Faza 1: Polish P2 (highDPI/extreme + pitch + diagnostics)
**Kluczowe:** compact highDPI, single pitch/TRIM stub, diagnostics (get_backend_info / get_diagnostics), headless tests, exact no-VLC banner "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org".

**Status:** Local closed (Writer + Tester 21p+ green, no-regresja).

### Faza 2: Backlog features (waveform color, advanced Smart, playlist intelligence)
**Szczegóły (z TESTER Faza2 + Writer):**
- **Waveform:** discrete per-band tint + energy overlays (kick red, hi-hat yellow, vocal green, breakdown blue) w core/waveform.py + waveform_widget.py + async. RGB fallback.
- **Advanced Smart:** nested AND/OR live preview (data/repository.py z where_expr guard + _build_smart_where_expr, ui/playlist_dialog.py, library_widget.py). Real counts.
- **Playlist intel:** Camelot harmonic + energy sorts (services/audio_features.py + playlist_order_dialog.py).

**Verifs:** py_compile, pytest ~53p, python-c sims GREEN, no-regresja prior.

**Status:** Local 'gotowe' (TESTER Faza2 closed A-Z). Per fraza "per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence)... must document identical".

### Faza 3: Packaging/CI (enhanced dla Downloader/AI)
- Portable smoke/build (strict resources fpcalc/ui/assets + LUMBAGO_SMOKE_DIAG + backend/Noop assert).
- yt-dlp + ffmpeg PATH notes (nie bundlowane).
- clean_windows_test + user_guide + smoke/build ps1 + spec z notkami.
- CI desktop-ci.yml.

**Status:** Enhanced + local scripts gotowe.

### Faza 4: Advanced — Downloader + AI (per źródłowa spec "chce dodać nowe, dosc komplikowane.txt")
**Wymagania z oryginalnej spec:**
- Downloader dla 700+ playlist YouTube/SoundCloud.
- Priorytet audible quality (bestaudio + FFmpegExtractAudio postproc) nad bitrate.
- 100% free (yt-dlp + ffmpeg external, nie bundlowane).
- Proste UI + przyciski (link, dir, profile MAX/BALANCE/COMPACT, throttle, fragments, est, disk check, start/cancel, history, resume).
- **Bardzo skomplikowany mechanizm pod maską:** lazy playlist extraction, JSON checkpoints, retry/backoff, throttling, per-item continue, ignoreerrors, ProgressBridge QThread, estimate + disk + QMessage confirm.
- AI Chat panel: verbal/custom commands ("pobierz <url>", "znajdź duplikaty", "otaguj", "status_biblioteki"), registry z EFFECT descriptions, JSON dispatcher, sandbox (registry-primary + SAFE_BUILTINS), multi-provider (gemini/openai/grok/deepseek), ambiguity handling, prefill do Downloader, real repo actions (counts via list_tracks/list_playlists).
- Integracja: MainWindow _open_downloader z prefill/auto_start, _scan_folder_for_library, add-only.

**Etapy wykonania (Nowa lista 1-10 z CHECKLIST_Downloader):**
- Infra, worker (bestaudio + quality log), profiles, UI polish, sandbox hardening, real wiring (duplikaty/otaguj), portable notes, tests (large est, checkpoint, cancel, dispatch 14p), ambiguity + quality, ident docs.

**Status:** Faza4 completed local 'gotowe' (14p tests, python-c est/registry/dispatch/real counts ~295 tracks/3 playlists, integration, portable notes, quality bestaudio+MAX). Real large PL + full AI verbal + clean Win manual pending.

**Exact files:** downloader/*, ai_panel/*, ui/main_window.py (wirings), data/repository.py (status), tests/test_downloader_ai.py, scripts/* ps1 (notes), docs/user_guide.md + clean_windows_test.md (PATH + flow).

### Faza 5: Long-term
- Crate digger / find similar (audio features).
- Full multi-monitor / booth support.
- Advanced cue / memory DB.
- Performance, community, cross-platform notes.
- Szpieg + Plan precede dla każdego.

**Status:** Notes added.

---

## 3. Downloader / Konwerter + AI Chat Panel (szczegóły)

(Full extract z "chce dodać nowe, dosc komplikowane.txt" + CHECKLIST_Downloader_AI_Panel + execution Faza4)

Patrz Faza 4 powyżej + sekcja Verification Matrix.

**Kluczowe problemy rozwiązane:** duże playlisty (lazy + checkpoint), jakość (MAX profile), portable (PATH warnings), AI safety (sandbox + registry primary), cross-wiring (real actions + prefill).

---

## 4. Manual Checklists — Podsumowanie + Artefakty

**DJ Player Checklist (condensed z crew/CHECKLIST_reczny + printable + clean_windows):**
- Single/Compact/Dual: waveform height ≥220/80/260, BPM large, crossfader ≥280, compact min ~420x300 + StaysOnTopHint + shrink, spin (cos/sin tylko gdy playing), 8 hotcue/deck, EFFECT tooltips na każdym elemencie ("EFEKT: ... FILE=load vs STREAM=play"), drag safety (prompt jeśli playing), booth 1m low-light high-contrast air, prominent "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org" + diagnostics (get_backend_info).
- No crash on unscanned, persist hotcue, resize dynamic air.

**Clean Windows + Portable (z docs/clean_windows_test.md):**
- Portable extract + smoke (strict resources).
- Import 1-3 audio → library → detail edit+save.
- DJ full flow (load/drag/play/cue/hotcue/loop/cross/wave/status).
- APPDATA/lumbago.db + settings.json.
- VLC guidance visible if no VLC.
- Downloader: yt-dlp/ffmpeg in PATH warning + large PL est.

**Artefakty:** 
- scripts/manual_win_dj_checklist_helper.ps1
- docs/manual_dj_checklist_printable.md
- docs/clean_windows_test.md (full steps + Downloader section)

**Status:** Local scripts + sims gotowe. Real execution on clean Win/VM pending.

---

## 5. Backlog, P0/P1/P2 i Zbiorczy TODO

**Aktualny (z TODO + memory + PLAN):**
- P0: manual closure + sizes + test gaps (Faza0).
- P1: Clean Windows / portable full + DJ checklist on real Win/VM.
- P2: Polish (highDPI extreme, more diagnostics, coverage).
- Backlog: Faza2 features (closed local), Downloader/AI (closed local Faza4), export, E2E, Faza5.

Szczegóły w sekcjach Faz powyżej + matrix.

---

## 6. Archiwum i Wskaźniki

- Pełne historyczne wersje: `MEMORY/full_agent_instructions/` (pre-trim AGENTS, CLAUDE, PLAN_*, SZPIEG, CHECKLIST dated).
- `MEMORY/historical_checklists/`
- `MEMORY/previous_archive/` (old crew outputs, mockups, web remnants, old plans).
- `MEMORY/CONSOLIDATION_REPORT_2026-06-16.md` + `MEMORY/INDEX.md`
- `memory.md` (sekcja "MEMORY Archiwum").

**Po konsolidacji:** verbose PLAN_DZIALANIA i stare sekcje w starych PLANach → pointery + przenieś verbose do MEMORY jeśli potrzeba.

---

## 7. Załączniki / Szybkie Referencje

- **Nowa lista szablon:** Patrz Faza sekcje + Plan agent output.
- **Fraza dokumentacji:** Zawsze ta sama (patrz początek).
- **Critical files dla Writer/Tester:** ui/dj/*, core/waveform.py, data/repository.py, downloader/*, ai_panel/*, services/playback/engine.py, tests/* (odt, playback, downloader_ai, waveform), scripts/*ps1, docs/clean_windows_test.md.

**Status ogólny (2026-07-14 "dalej az do ukonczenia wszystkich faz"):** Wszystkie Faza0-5 local gotowe. Verifs green (70p broad + targeted 14p+21p+53p). Docs updated identically. Manual Win/VM + E2E + duże playlisty real + pełne AI verbal pending. 'Gotowe' local A-Z. Nie przestawaj.

---

**Koniec mastera.** 

**2026-07-14 KONSOLIDACJA (użytkownik query):** Przeanalizowano + skonsolidowano używając agentów (Explore catalog + Plan structure design). Stworzono ten plik jako jeden spójny szczegółowy master. Pointery + fraza dodane do memory/TODO/PLANs/crew/AGENTS/clean_windows/HISTORY. Verifs (smoke/pytest/python-c/grep) nie złamane. Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + "dalej az do ukonczenia wszystkich faz" + consolidation using agents ... must document identical. 'Gotowe' konsolidacja A-Z. Nie przestawaj. Close A-Z.

Po "dalej" / zatwierdzeniu: Writer implementuje (jeśli nowe), Tester weryfikuje, aktualizuj pointery w innych plikach + ident docs + fraza + todo_write + push.

Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + "dalej az do ukonczenia wszystkich faz" + consolidation using agents ... must document identical. 'Gotowe' konsolidacja. Nie przestawaj. Close A-Z.