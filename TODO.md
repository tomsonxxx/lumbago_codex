# TODO — Lumbago Music AI (zbiorcza lista)

**Ostatnia aktualizacja:** 2026-07-14 Tester Faza1 item3 pitch stub: full verif A-Z (read exact odt_view/simple_deck_controller/pitch_control/test_odt + window/engine; py_compile; pytest playback 21p rate/keylock; python-c engine+ctrl sims; no-regresja EFFECT/fallback/air/QStack/FILE-STREAM/highDPI preserved; assert exact tooltip "EFEKT: zmienia tempo/pitch utworu (FILE load, STREAM playback)", compact hide, presence/wiring single; GREEN all + gaps Qt/Win manual only). per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub for Odtwarzacz MVP)... must document identical. 'gotowe' Tester pitch. (Writer closed before, highDPI item1 prior)

**Analyzer 2026-07-13 (zintegrowane):** ~60-70% auto-covered (engine/diag/backend_info, compact StaysOnTop/pilot, metrics dynamic, fallback label, smoke DIAG, QStack). Gaps: exact sizes (wave 220/80 vs tokens 184/68, cross 280 vs ~240), EFFECT full asserts, booth 1m visual, real compact/highDPI warning visibility, full clean VM flow (import+DJ+APPDATA). Rekomendacje: wzmocnij test_odtwarzacz_load + deck_layout + booth_metrics + smoke (exact minHeight, text "⚠ Audio niedostępne...", margins 420x300, cross, BPM). Sync BOOTH_SIZES. Side Szpieg. Po: docs identical. Per SZPIEG research 2026-07-13 + Analyzer + Plan... must document identical.

'Gotowe' local + research/plan. (poprzednie 2026-06-25 FINAL local P1)

**Kontekst:** Projekt skupiony wyłącznie na desktop (PyQt6 + DJ Player). Wiele faz zamkniętych jako "gotowe" (Odtwarzacz MVP 1-15, Etap4 playback, Smart Collections, Organizer/Library Builder, Duplicate 3-metody, Clean Windows local scripts). 

**Zasady pracy (per PLAN + SZPIEG):**
- Zawsze uruchamiaj SZPIEG (lub research) przed większymi etapami.
- Nowa lista przeróbek najpierw do decyzji użytkownika ("dajcie mi w pierwszej kolejności").
- Exact match + read-before-edit + verifs na bieżąco (smoke, pytest, python-c, manual CHECKLIST).
- Dokumentuj **identycznie** w memory.md, HISTORY.md, crew/CHECKLIST, AGENTS/CLAUDE, code (fraza "per SZPIEG Build Spec + Plan... must document identical").
- "Nie przestawaj" — kontynuuj po "dalej"/"zatwierdzam".

Wszystkie historyczne checklisty i pełne raporty w `MEMORY/`.

---

## P0 — Stabilność / Blokujące (CI, core, fallbacks)

- [ ] **Brak** aktywnych P0 w kodzie (po fixes 2026-06-25). CI desktop stabilne dzięki Chocolatey + cache + fallback + `continue-on-error`.
- [ ] Monitorować flaky network w CI Windows przy fallback download VLC (obecnie 5 retry + size check + choco primary).
- [x] Playback graceful degradation (VLC → Qt → _Noop) działa + `get_backend_info()` + diagnostics dostępne. (wzmocniono prominent banner/status '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' + get_backend_info w odt/dj_player + compact/highDPI + diagnostics btn w tools + testy) per SZPIEG research 2026-06-25 DJ checklist + Plan... must document identical.

## P1 — Wysoki priorytet (weryfikacja + packaging + manual)

**Status po wszystkich research + execution (2026-06-25, final Writer polish 119 calls + TESTER verifs + smoke/build Writer 71 calls implementing Analyzer + Szpieg):**
- P1.1: Local buttoned closed (TESTER verifs + enhancements: strict resources, DIAG, raport). VM/manual pending.
- P1.2: Local polish (Writer 119 calls: dedicated fallback label for compact/highDPI visibility, tighter compact per Mixxx/Winamp, diagnostics btn, extended tests) + TESTER verifs closed. Full manual/booth on Windows pending.
- P1.3: Local no-VLC warning + diag UI (Writer + TESTER) closed. Real test pending.
- 2026-07-13 Writer (per Analyzer 2026-07-13 + SZPIEG 2026-07-13): wzmocniono test_odtwarzacz_load.py / test_deck_layout.py / test_booth_metrics_cue.py + smoke (ps1 + main DIAG) z exact asserts (wave >=220/80/260, fallback exact "⚠ ...", compact 420x300+StaysOnTop, _maybe label, EFFECT "EFEKT:", cross, BPM). Verifs python-c/pytest playback green, syntax OK. Docs updated ident. Nie ruszano core. 'Gotowe' Writer local.
- Per Szpieg/Plan/Analyzer/Writer/TESTER: local A-Z closed gdzie doable (playback/diag/compact/no-VLC/warning verifs GREEN); real Windows + VLC dla pełnego manual/VM/booth. Docs identycznie. 'Gotowe' local.

**Uwaga od TESTER 2026-06-25 (lokalna weryfikacja P1.1 wg Szpieg/Plan/Analyzer):** Local buttoned closed dla smoke + engine/diag/frozen paths (python-c PASS, pytest core zielone, resources strict + diag raport w smoke). Gaps: full DJ functional exec w smoke, VM/manual pending. Fixes: strict checks, DIAG support. Per SZPIEG research 2026-06-25 Clean Windows P1 (fresh deep research: 15+ practices... luki identified in smoke coverage... Build Spec + "nowa lista" 1-8... must document identical). 'Gotowe' local. VM pending.

1. **Pełny test na czystym Windows (P1 #1 z poprzednich list)**
   - [~] Uruchomić na fizycznej czystej maszynie/VM (bez Pythona, bez dev deps). **Local Linux verifs buttoned 2026-06-25 (TESTER).**
   - [~] Wykonać pełny manual wg `docs/clean_windows_test.md`:
     - Portable ZIP (build + smoke_portable) — local sim OK.
     - Import 1-3 plików / Detail / DJ Player full — pending VM/manual.
     - Sprawdzenie %APPDATA% / VLC guidance (⚠ + "Pobierz VLC z videolan.org") — notes + code covered.
   - [x] Zaktualizować status w `docs/clean_windows_test.md`, memory, crew/CHECKLIST (local OK vs VM pending) — verifs + docs ident done.
   - Skrypty już wzmocnione + local verifs: smoke logic review OK, python -c (PlaybackEngine, get_backend_info, get_diagnostics, frozen config) PASS (Noop fallback), pytest playback relevant (23+ passed relevant), smoke raport diagnostics note OK (gaps noted).
   - Per SZPIEG research 2026-06-25 Clean Windows P1 (fresh...) + Plan + TESTER local buttoned: covered (resource, APPDATA, no-VLC in code, DJ notes) vs gaps (full DJ auto in smoke, VM manual, diagnostics print exec). Fixes proposals in clean_windows. 'Gotowe' local. VM pending. must document identical.

2. **Ręczne testy DJ Player wg pełnej checklisty (booth + dual + compact)**
   - [ ] Przejść `crew/CHECKLIST_reczny_test_nowy_DJ_Player.md` na real Windows (z VLC).
   - Szczegóły otwarte:
     - Single: waveform ≥220px, BPM rozmiar, playhead + beatgrid, transport buttons, drag safety + prompt, EFFECT tooltips wszędzie, resize dynamic, QStack, cue/play/stop logic, black/empty state.
     - Compact pilot advanced: always-on-top (StaysOnTopHint), minSize shrink ~420x300, reduce empty bottom, floating feel, rapid toggle + play + drag + resize (multi-monitor).
     - Dual Console: oba decki + crossfader (min 280px), EQ/pitch czytelne, 8 hotcue/deck, Master/HP Cue/PFL, crossfader działa wizualnie + słuchowo.
     - Ogólne: hotcue persystencja, Memory S/R, SYNC/Quantize/KEY/pitch nie psują, skróty, drag&drop, skalowalność.
     - Booth symulacja: niska jasność, odległość ~1m, brak "za gęsto"/zachodzenia, high-contrast air.
   - [~] Pełna symulacja booth odłożona per PLAN (środowisko headless/Linux nie wspiera pełnego PyQt6 real-time visual).
  - 2026-07-13: local auto wzmocnione (testy + smoke DJ sim) per Analyzer recs + SZPIEG research 2026-07-13 + Plan... must document identical. Exact asserts dodane w odt/deck/booth tests + smoke. Verifs green.
- 2026-07-14 (kontynuacja): Test enhancements już w kodzie (wave minHeight, fallback exact, compact 420x300+StaysOnTop, cross, EFFECT, BPM). Local Faza0 test part closed (code verif). Real Win manual pending. Per plan rozbudowy 2026-07-14.

3. **Weryfikacja fallbacków i diagnostyki w praktyce**
   - [ ] Na maszynie bez VLC: potwierdzić widoczne ostrzeżenie w Odtwarzaczu, `get_backend_info()` pokazuje Noop/Qt, playback FILE vs STREAM działa ograniczony. (exact: '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' + diagnostics link dodane do dj_player_window + OdtwarzaczView status)
   - [ ] Testy playback (`tests/test_playback_backend.py`) + `test_odtwarzacz_load.py` + `test_dj_hotcue_manager.py` przechodzą (z mockami lub na Windows z VLC).
   Per Szpieg/Plan + must document identical.

4. **Inne P1 z historycznych tabel**
   - [x] Naprawa `test_unified_autotagger_picks_best_candidate` (done).
   - [x] Pełna dokumentacja DJ Playera (`docs/dj_player_guide.md` + backendy) (done lokalnie).

## P2 — Polish, ulepszenia UI/UX, drobne braki

- [~] **Single mode** — minimal pitch/TRIM stub closed for Odtwarzacz MVP (Faza1 item3 per PLAN): PitchControl reused in odt after controls + compact hide + set_rate/set_pitch/set_keylock in simple ctrl wired to engine; EFFECT tooltip exact "EFEKT: zmienia tempo/pitch utworu (FILE load, STREAM playback)"; no full dual. Advanced EQ later. Tester full verif A-Z (py 21p, sims, no-regresja, asserts) GREEN. per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub for Odtwarzacz MVP)... must document identical. (Writer+Tester closed A-Z local, verifs green; manual pending)
- [ ] Compact pilot: dodatkowe weryfikacje highDPI, extreme małe okno (wave min ~40-80px z zachowanym air), spin rotation timing (real 50ms cos/sin).
- [ ] Dual: pełne pokrycie EQ, pitch, PFL, crossfader wizualny + audio w manualu.
- [ ] UI dla diagnostyki audio (np. przycisk "Pokaż info backendów" w oknie DJ lub Ustawieniach).
- [ ] Lepsza widoczność ostrzeżenia "⚠ Audio niedostępne" + link/instrukcja instalacji VLC (obecnie w playerze + docs).
- [ ] Dodatkowe guardy / edge: load podczas odtwarzania (prompt), no-track compact, legacy refs (już mocno wzmocnione).
- [ ] Testy: dodać więcej headless-friendly unit testów dla dj/playback (obecne collection errors na bez-X11).

## Backlog / Przyszłość (odłożone, warte rozważenia)

- [ ] **Waveform Color Coding** — kolorowanie wg charakteru (🔴 kick/bass, 🟡 hi-hat, 🟢 wokale, 🔵 breakdown). Wymaga dodatkowej analizy spektralnej + playera.
- [ ] **Zaawansowane Smart Collections** — pełny rule engine z AND/OR, więcej operatorów, live preview ulepszone.
- [ ] Ulepszony Duplicate Finder — dalszy polish merge logic / UI (częściowo zrobione 3-metody + match_method labels).
- [ ] Playlist Intelligence (harmonic mixing + energy flow sort).
- [ ] Crate Digger / "Find Similar Tracks".
- [ ] Export Manager zoptymalizowany pod CDJ/XDJ/Engine Prime.
- [ ] Lepsze wsparcie cue/memory points w DB/UI (już częściowo przez hotcue + memory).
- [ ] E2E automated (Playwright / pytest-qt) — P2 z dawnych list.
- [ ] Coverage report + fail threshold w CI.
- [ ] Automatyczny release z changelogiem + tagi (obecny release.yml prosty).

## CI / Packaging / Release

- [ ] Rozważyć dodanie opcjonalnego kroku "VLC verify" z jaśniejszym warn (obecnie continue-on-error + warning).
- [ ] Pełny clean-VM test w dokumentacji + ewentualnie w release notes.
- [ ] Sprawdzać, czy portable ZIP zawiera wszystkie zasoby (fpcalc, ui/assets, docs) — już w smoke.
- [ ] CodeQL: tylko actions + python (javascript-typescript usunięty słusznie).

## Dokumentacja i proces

- [ ] Zsynchronizować statusy checkboxów w `crew/CHECKLIST_reczny_test_nowy_DJ_Player.md` po pełnym manualu (wiele [ ] nadal żywych jako specyfikacja manualna).
- [ ] Utrzymywać "must document identical" przy każdej większej zmianie.
- [ ] Aktualizować tę listę + memory.md + HISTORY.md po każdym bloku.
- [ ] Dla nowych: najpierw `memory.md` + `MEMORY/.../SZPIEG...` + `crew/PLAN...`.

---

## Co jest zrobione niedawno (2026-06-25) + Plan execution start + Writer execution

**WRITER 2026-06-25 (P1.3)**: Zakończono local A-Z dla widocznego no-VLC warning + diagnostics:
- Dodano exact "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org" + link do get_backend_info/get_diagnostics w dj_player_window.py (banner + label) i odtwarzacz_view.py (status + tooltip).

**2026-07-13 TESTER (Code Review Crew per PLAN hierarchy + Szpieg 2026-07-13 + Plan Faza 1 + Analyzer):** Verif A-Z Faza1 (Writer artifacts: helper.ps1 + printable.md + clean_windows update). 1. Existence+structure: PASS. 2. python -c: PlaybackEngine, get_backend_info(_Noop), get_diagnostics: PASS (no-VLC sim perfect for helper). 3. Grep: "Per SZPIEG research 2026-07-13", "Waveform ≥220px", "⚠ Audio niedostępne", "must document identical" (many), "Build Spec", "helper", "printable": PASS in key files. 4. Helper usage sim (cat): prompts map exactly to CHECKLIST [ ] + Szpieg research sizes/booth/fallback (wave ≥220px, cross min280px, compact advanced always-on-top ~420x300 spin, EFFECT tooltips file=PLIK vs stream, ⚠ banner, booth 1m low-light, get_backend_info, raport template). 5. Ident updates verif: memory/TODO/HISTORY/CHECKLIST: full 07-13 entries present; PLAN/SZPIEG: no detailed Faza1 (gap). 6. Report: działa (lista passed), gaps (PLAN/SZPIEG, real Win), recs (uruchom helper na Win, wypełnić printable). 'Gotowe' A-Z verif prep. Update docs ident. Per SZPIEG research 2026-07-13 co-dalej manual checklist + clean Win... must document identical.
- Używa get_backend_info dla detect Noop/Qt.
- Docstrings + EFFECT + "per Szpieg/Plan + must document identical".
- Docs (dj_player_guide, clean_windows_test, TODO) identycznie.
- Verifs core: python-c, compile OK.
- Local closed. Real Win test pending (compact, highDPI, visible banner).

**Pełny zintegrowany plan** w docs/PLAN_DZIALANIA_2026-06-25.md + tej liście. Zespół uruchomiony (Szpieg, Plan, Analyzer, Writer x2, Tester). Research Szpieg precede. Local closures dla smoke (P1.1), UI warning (P1.3). Manual na Windows pending per plan A-Z.

**NOWY KOMPLETNY PLAN DZIAŁANIA + FRESH SZPIEG/PLAN OUTPUTS (2026-06-25):** 
- Szczegółowy plan w `docs/PLAN_DZIALANIA_2026-06-25.md` (fazy, Szpieg precede dla każdego, A-Z kroki, verifs, identical docs, closure).
- **Świeży Szpieg research dla P1.1 (Clean Windows)**: 15+ praktyk (PyInstaller, clean VM, resource verif, VLC guidance, choco CI, graceful diagnostics, FILE/STREAM, DJ apps examples), luki w smoke (brak full DJ functional + diagnostics print), Build Spec binding, "nowa lista przeróbek" 1-8 (local enhancements first: smoke checks, docs, then VM/manual), local doable (python-c, smoke SAFE, pytest), wymaga real Win/VM dla full manual, closure A-Z z ident docs + fraza.

**Świeży Szpieg research dla P1.2 (DJ Checklist — zakończony)**: 
- Zaimplementowane/auto-verified: QStack, compact cos/sin spin, EFFECT wszędzie (file/stream), safety prompts, get_backend_info/fallbacks, drag mime+repo+hl, air/scalab, cue logic, single default.
- Tylko manual pending: real sizes (wave/BPM/cross), highDPI extreme compact, always-on-top multi-monitor, dual full audio, booth 1m/low light sim, spin timing visual, no-VLC visibility polish.
- Luki: no-VLC banner visibility (w compact/highDPI), compact reduce empty/extreme, diagnostics UI button, więcej headless testów.
- Build Spec: zachować air/wave dominant, compact pilot (always-top + cos/sin), EFFECT, drag safety; wzmocnić visibility fallback + polish compact/highDPI.
- Nowa lista local-doable: wzmocnij no-VLC visibility/banner/button, compact polish (empty/highDPI), UI diagnostics, headless tests.
- Real Windows: pełny manual CHECKLIST + dual audio + booth sim + sizes.
- Punktowanie: air/wave 10/10, compact 8.5/10, EFFECT 9/10, fallback visibility 7.5/10.
- Closure: po manual update [x] + notes w CHECKLIST, ident docs (memory/HISTORY/TODO/CHECKLIST + fraza "per SZPIEG research 2026-06-25 DJ checklist + Plan... must document identical").

**Świeży Analyzer report (2026-06-25, 57 tool calls):** Luki w smoke/build: SAFE_MODE stub w main.py omija całkowicie DJPlayerWindow/PlaybackEngine/backend_info/diagnostics/get_diagnostics; resource verif w smoke.ps1 luźne ("note" zamiast strict fail/throw); brak auto-weryfikacji DJ load basic, no-VLC states (Noop banner), APPDATA creation, portable resources strict w exe flow. Smoke pokrywa tylko bazowy exe run (stub). Rekomendacje: strict resource checks (throw), dodaj LUMBAGO_SMOKE_DIAG support w main.py + smoke capture/output assert, basic DJ load w smoke (python-c or enhanced stub), explicit "AUTO-COVERAGE REPORT" w smoke. 

**WRITER execution (per task + hierarchy):** 
Wykonano dokładne zmiany (read-before-edit, exact match):
1. Wzmocniono smoke_portable_windows.ps1: strict resource checks (throw jeśli brak critical), dodano wsparcie LUMBAGO_SMOKE_DIAG lub flagi (przekieruj output, assert "Noop|backend").
2. Ulepszono main.py dla smoke: jeśli LUMBAGO_SMOKE_DIAG lub SMOKE + diag env — utwórz PlaybackEngine(), wypisz get_backend_info + get_diagnostics(), potem quit (nawet w SAFE stub). 
3. Dodano w smoke/build: explicit raport "AUTO-COVERS: exe, resources(strict), backend_info, diagnostics, no-VLC states". 
4. Zaktualizowano docs (clean_windows_test.md, dj_player_guide jeśli pasuje, TODO) identycznie.
Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" ... must document identical.
- Update status: smoke/build enhanced, main.py smoke-diag path active, verifs planned. Full report w subagent + docs.

- **Plan agent "nowa lista przeróbek"**: Prezentowana w pierwszej kolejności. Faza 1 P1 z Szpieg precede, szczegółowe A-Z, verifs, pliki ident, kryteria closure. Pełne w outputs subagentów + zintegrowane tutaj i w PLAN_DZIALANIA.

Zespół (Szpieg x2, Plan, Analyzer, Writer, Tester) uruchomiony, outputs użyte do integracji i akcji. Lokalne closure P1.1 rozpoczęte (smoke ulepszony, verifs PASS, docs updated). Per hierarchy.

- Szpieg research uruchomieni dla P1.1 (clean Windows) i P1.2 (DJ checklist) — background, głęboka analiza w toku (read/grep/list).
- Plan agent uruchomiony dla "nowej listy przeróbek" + detailed execution (user review first).
- Analyzer + Writer uruchomieni na doable (luki w smoke + no-VLC warning visibility w UI).
- Lokalne verifs: PlaybackEngine + get_backend_info() + diagnostics — PASS (Noop fallback działa).
- Smoke portable ulepszony o explicit raport checklist auto-items + note diagnostics.
- Zidentyfikowana luka: brak prominent tekstu warning "⚠ Audio niedostępne" w ui/ (tylko w docs) — w trakcie adresowania.
- Pełny zespół w akcji per PLAN hierarchy.

### Postęp faz (śledzenie)
- Faza 0: Inicjalizacja + PLAN + spawns — done.
- Faza 1 (P1.1 clean Win): local scripts enhanced, research pending, manual VM pending.
- Faza 2 (P1.2 DJ checklist): research pending, local polish/test enhance w toku.
- P1.3/P2 + backlog: w planie, Szpieg + crew.

## Co jest zrobione niedawno (2026-06-25)

- Stabilny VLC w desktop-ci.yml (Chocolatey primary + cache + curl fallback + retries + verify libvlc + plugins + continue-on-error).
- 4 failing testy naprawione (gemini-2.5-flash, broad genre 0.35→0.70, waveform peaks + load, get_backend_info w engine).
- Playback testy teraz poprawnie skip/fallback gdy brak VLC.
- CodeQL wyczyszczony z JS.
- Dokumentacja zaktualizowana (README Audio sekcja, dj_player_guide backendy, HISTORY, clean_windows_test, memory).
- Wszystko przetestowane, push.

**Źródła otwartych pozycji:** crew/CHECKLIST_reczny_test_nowy_DJ_Player.md (manual must-have), memory.md (P1 + backlog), docs/clean_windows_test.md (VM pending), docs/dj_player_guide.md + code comments, HISTORY.

Po "dalej" lub "zatwierdzam" — uruchamiamy SZPIEG/Plan → lista → impl + verifs.

**2026-07-13 WRITER Faza 1 (per Plan "nowa lista" + Szpieg 2026-07-13 output):** Stworzono helper scripts/manual_win_dj_checklist_helper.ps1 (PS run + prompty exact CHECKLIST dla manual Win). Verif + update identycznie memory+TODO+HISTORY+PLAN+CHECKLIST (notka local prep) + "per SZPIEG research 2026-07-13 co-dalej manual... must document identical". Krótki wpis. + printable create: docs/manual_dj_checklist_printable.md (extract + sizes + Test bez VLC + template). Verif cat. + update clean_windows: Build Spec + expected sizes/booth + linki. Verif. Powodzenia!
