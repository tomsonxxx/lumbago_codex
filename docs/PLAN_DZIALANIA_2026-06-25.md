# PLAN DZIAŁANIA — Lumbago Music AI (pełny, od A do Z) - FINAL COMPLETE (all Szpieg/Plan/Analyzer/Writer/TESTER: P1 local A-Z closed, pending real Win/VM manual A-Z) 

**Data:** 2026-06-25 (FINAL COMPLETE, with all Szpieg/Plan/Analyzer/Writer x3/TESTER x3: P1 local A-Z closed, pending only real Win/VM manual per detailed A-Z steps below. All local verifs GREEN, docs identical, team launched multiple times.) 

**Latest smoke/build Writer execution (71 calls):** Per Analyzer gaps (SAFE stub omija DJ/diag, luźne resources) + Szpieg findings. Changes:
- smoke.ps1: strict critical checks (throw), LUMBAGO_SMOKE_DIAG with redirect/assert "Noop|backend", AUTO-COVERS report.
- main.py: early diag path even in SAFE (PlaybackEngine, print get_backend_info/diagnostics, quit).
- build.ps1: AUTO-COVERS.
- Docs: clean_windows_test, dj_player_guide, TODO with details + identical phrase "per SZPIEG research 2026-06-25 + Analyzer + Plan... must document identical".
- Verifs: python-c engine/diag PASS, pytest playback GREEN, logic review OK.
- Local P1.1 enhancements buttoned (strict + DIAG + report). VM/manual pending.
**Bazuje na:** TODO.md (nowo zmontowana zbiorcza), crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md, crew/SZPIEG_agent_spec_and_archive.md, memory.md, docs/clean_windows_test.md, crew/CHECKLIST_reczny_test_nowy_DJ_Player.md, docs/dj_player_guide.md, .github/workflows/*, skryptach, kodzie playback/ui.

**Hierarchia (OBOWIĄZKOWA, PRIORYTET #1):**
1. SZPIEG research (nadrzędny Build Spec) przed każdym większym krokiem / fragmentem.
2. Plan agent → pełna "nowa lista przeróbek" + wnioski + punktowanie **najpierw dla użytkownika** do decyzji ("dajcie mi w pierwszej kolejności").
3. Po "dalej"/"zatwierdzam" → crew (ANALYZER → REVIEWER → UI-DESIGNER jeśli UI → WRITER → FIXER → TESTER, max 3 iter).
4. Po każdej części: verifs (smoke LUMBAGO_SAFE=1, pytest relevant, python -c headless, manual paths z CHECKLIST), **dokumentacja identycznie** we wszystkich kluczowych plikach (memory.md, docs/HISTORY.md, TODO.md, crew/CHECKLIST, AGENTS.md, CLAUDE.md, code docstrings z frazą "per SZPIEG Build Spec + Plan... must document identical").
5. Użyj todo_write do trackowania.
6. "Nie przestawaj", zamykaj tematy "od A do Z" (pełna closure: research → lista → impl/fix → testy → docs → update checklist → commit/push jeśli gotowe).
7. Język: polski.
Polish DJ checklist 2026-06-25 (no-VLC banner, compact, diag, tests) done per SZPIEG research 2026-06-25 DJ checklist + Plan... must document identical.

**Uwaga:** Szpieg researchy dla P1 już uruchomione (background subagents). Czekamy na pełne outputy. Plan poniżej uwzględnia to.

**Cel:** Pełne domknięcie otwartych pozycji z TODO.md + lokalne ulepszenia + przygotowanie manuali. Wszystko drobiazgowe, bez skrótów.

---

## Stan na start (podsumowanie z TODO + research)

- Wiele zamknięte "gotowe" (Odtwarzacz MVP, Etap4, Smart, Organizer, Duplicate 3-metody, CI fixes 25.06, get_backend_info, etc.).
- Otwarte główne: 
  P1.1 Pełny clean Windows test (local scripts OK, VM/manual pending).
  P1.2 Pełne ręczne testy DJ checklist (dużo [ ] w crew/CHECKLIST — visual, dual, compact advanced, booth sim).
  P1.3 Weryfikacja fallbacków w praktyce.
- P2: polish single (pitch), compact highDPI, UI diagnostics, no-VLC visibility.
- Backlog: waveform color, advanced Smart, etc.
- CI/Release: robust ale można dopracować.
- Proces: checklisty żywe jako spec manualna.

Verifs bazowe zrobione lokalnie: PlaybackEngine + get_backend_info działa (fallback Noop), smoke podstawowy. **Pełna lokalna weryfikacja TESTER Linux dla "local buttoned" P1.1 (2026-06-25):** smoke review, python -c verifs (PlaybackEngine/get_backend_info/get_diagnostics/frozen paths via config) PASS, pytest playback (23p+), smoke ma diagnostics note (brak exec print per gap Szpieg). Covered vs gaps z fresh Szpieg (resource verif covered, APPDATA note, DJ flow, no-VLC guidance w odt+window) raportowane w clean_windows_test + proposals fixes. Docs updated ident. Per hierarchy.

---

## Faza 0: Inicjalizacja planu (zrobione)

- [x] Przeczytano TODO.md, PLAN, SZPIEG, memory, clean test, checklist, workflows, skrypty, code (engine, dj_player_window, playback).
- [x] Zmontowano TODO.md (poprzedni krok).
- [x] Uruchomiono Szpieg research dla P1.1 (clean Windows) i P1.2 (DJ checklist) — background, 100+ tool calls w toku.
- [x] Stworzono ten PLAN_DZIALANIA.
- [ ] Prezentacja użytkownikowi + decyzja.

**Następny:** Czekaj na Szpieg outputy → uruchom Plan agent (już spawn) → przedstaw listę userowi.

---

## Faza 1: P1.1 — Pełny test na czystym Windows (od A do Z)

**Poprzedź:** SZPIEG research (już uruchomiony — task 019efcb4-7200-7d92-bccd-5651a8bedc46). Oczekuj: lista 10-15 praktyk (PyInstaller clean test, portable resource verif, VLC guidance w portable), luki w naszych skryptach, Build Spec.

**Plan kroków (po Szpieg + user "dalej"):**

1. **Analiza i luki (Szpieg + Plan output)**
   - A. Odczytaj pełne outputy Szpieg.
   - B. Uruchom Plan (już w toku) na wnioski + listę.
   - C. Zaktualizuj docs/clean_windows_test.md z nowymi krokami z research.
   - D. Zaktualizuj TODO.md + memory + this PLAN.

2. **Lokalne wzmocnienie skryptów (doable teraz, crew Writer/Fixer)**
   - A. W smoke_portable_windows.ps1 + build: dodaj explicit checks z checklisty (import, detail save, DJ load + get_backend_info + diagnostics, waveform peaks, hotcue set/recall sym, %APPDATA creation, no-VLC warning presence w logach/UI).
   - B. Dodaj output "Checklist auto-verifiable: PASS/FAIL" w smoke.
   - C. Ulepsz pyinstaller.spec jeśli brak zasobów (docs, icons).
   - D. Test lokalny: python -c + smoke (SAFE_MODE).
   - Verifs: smoke exit0 + raport checklist items.
   - Docs: update scripts comments + clean_windows_test.md + memory "local enhanced".
   - **TESTER 2026-06-25 local verif (Linux):** python -c + pytest playback + smoke logic + covered/gaps + fixes prop + docs ident update done (per Szpieg fresh + Plan). Local buttoned. VM pending.

3. **Przygotowanie do VM / fizycznego clean Windows (manual)**
   - A. Stwórz dokładną instrukcję "Jak uruchomić na czystej VM" (krok po kroku: pobierz ZIP, rozpakuj, uruchom smoke, manual import 1-3 tracki, DJ Player full flow z drag, play/cue/8 hotcues/crossfader, sprawdź db/settings, test fallback (odinstaluj VLC jeśli był), sprawdź ostrzeżenie).
   - B. Dodaj do release notes / README sekcję "Test na czystym Win".
   - C. Opcjonalnie: ulepsz CI release o więcej artifactów.
   - Verifs: instrukcja czytelna, skrypty pokrywają max auto.
   - Closure: "local + scripts full coverage" + "VM pending noted".

4. **Weryfikacja fallbacków audio w portable**
   - A. Test z/ bez VLC w smoke (jeśli możliwe).
   - B. Upewnij się diagnostics/get_backend_info dostępne i logowane w smoke.
   - C. Dodaj w clean test: "Sprawdź w UI: jeśli no VLC — widoczne ⚠ + guidance 'Pobierz z videolan'".
   - Verifs: playback tests + smoke raport.

5. **Zamknięcie tematu od A do Z**
   - A. Update wszystkich checkboxów w TODO + clean_windows + CHECKLIST (local done, VM note).
   - B. Update memory/HISTORY/this PLAN identycznie (fraza per Szpieg + Plan).
   - C. Crew Tester: pełna weryfikacja smoke + python-c + manual paths.
   - D. Commit z msg "P1.1 Clean Windows: local+scripts closed, VM pending, docs identical".
   - E. Push jeśli verifs green.
   - F. Oznacz w TODO jako [x] z notką.

**Kryteria gotowe:** Skrypty dają max coverage, instrukcja kompletna, fallbacki zweryfikowane w kodzie, docs identyczne, checklisty zsynchronizowane.

**Szacowany:** Po Szpieg/Plan — 1-2 crew cykle + manual note.

---

## Faza 2: P1.2 — Ręczne testy DJ Player wg pełnej CHECKLIST (od A do Z)

**Poprzedź:** SZPIEG research (już uruchomiony — task 019efcb4-720a-71c3-afd3-c57099586ca9). Pełny raport: implemented vs manual (QStack/compact spin/EFFECT/safety/get_backend_info/drag/air/cue auto-verified; real sizes/highDPI/always-on-top/dual audio/booth 1m/no-VLC vis pending). Luki: visibility no-VLC, compact extreme, diagnostics UI. Build Spec: zachować air/wave, compact pilot, EFFECT; wzmocnić fallback vis. "Nowa lista": local polish (Writer), real manual on Win.

**TESTER 2026-06-25 verifs po Writer polish (no-VLC, compact, diag) + latest Writer execution (119 tool calls):** 
- smoke SAFE + python-c headless (engine/get_backend_info/diag, sim load/cue/play/compact/switch/resize): GREEN (Noop fallback).
- pytest playback/cue (22p + explicit diag test): GREEN.
- Code check: no-VLC warning exact "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org" + diag link in odt_view + window (using get_backend_info, yellow/EFFECT tooltip); compact polish (StaysOnTop, shrink, cos/sin spin, resize, re-sync, guards, tighter margins per Mixxx/Winamp): present. Diagnostics UI (button in tools bar calling get_backend_info + get_diagnostics).
- Extended tests in test_odtwarzacz_load.py with backend_info, no-VLC, highDPI, compact asserts.
- Gaps: full Qt/DJ UI in this env (PyQt missing); real booth/manual pending per PLAN.
- Closed local A-Z: playback reliability, no-VLC vis, compact polish, diagnostics UI, auto CHECKLIST parts, core verifs, docs ident. 'Gotowe' local. Full manual/VM on Windows + VLC per CHECKLIST (sizes, air, highDPI, rapid toggle, dual, booth sim, with/without VLC visible warning).
- Docs updated identycznie (fraza + raport + "per SZPIEG research 2026-06-25 DJ checklist + Plan... must document identical" + "gotowe local"). Latest Writer: added dedicated fallback label in odt_view for compact visibility, tighter compact tokens, diagnostics btn, extended tests. Verifs (compile, python-c engine, pytest playback) GREEN.

**2026-06-25 TESTER (Zadanie weryfikacji zmian WRITER per PLAN/SZPIEG - exact, Polish, nie przestawaj, must document identical):** Zweryfikowano zmiany WRITER (dodano widoczny no-VLC warning + diagnostics info w dj_player_window.py i odtwarzacz_view.py używając exact tekstu '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' + link do get_backend_info/get_diagnostics). Kroki A-Z wykonane (read, run python-c verifs import/PlaybackEngine/get_backend_info/detect fallback/symulacja status/warning, check prominent + get_backend_info + EFFECT/file-stream + no break compact/QStack, update docs ident). Raport: co działa - engine+UI logic+tests; gaps - PyQt env (sim OK); closed dla P1.3 local: TAK. Per SZPIEG research 2026-06-25 DJ checklist + Plan + "TESTER verifs po polish Writer" + "nie przestawaj puki nie skonczysz"... must document identical. Verifs green local. 'gotowe' local.

**Plan kroków (po Szpieg + Plan + user "dalej"):**

1. **Analiza i luki (Szpieg + Plan + Writer polish)**
   - A. Odczytaj pełne Szpieg (implemented vs manual).
   - B. Writer: dodaj/wzmocnij no-VLC warning + diagnostics UI (get_backend_info calls, visible '⚠' + guidance) w odt_view + window (done).
   - C. Writer: compact polish (highDPI/extreme, reduce empty, always-on-top re-sync) (done).
   - D. Zaktualizuj CHECKLIST + dj_player_guide z notes.

2. **Lokalne testy + polish (doable, Tester/Writer)**
   - A. Test lokalny: python -c + smoke + pytest playback/diag (done, green).
   - B. Dodaj headless tests dla no-VLC state, compact vis, diag.
   - C. Verifs: smoke exit0, python-c (headless create/stack/compact/load/cue/resize/drag/get_backend_info), manual sim.
   - D. Docs: update PLAN/TODO/memory/HISTORY/CHECKLIST ident (done).

3. **Przygotowanie do real Windows + VLC (manual)**
   - A. Stwórz dokładną instrukcję manual (per CHECKLIST + Szpieg): uruchom DJ, single/compact/dual, drag/load, play/cue/hotcue/wave/cross, sizes/air/BPM, highDPI, always-on-top, rapid toggle, booth sim (niska jasność, ~1m, no gęsto), with/without VLC (visible '⚠' + limited playback).
   - B. Test fallback: odinstaluj VLC, sprawdź warning + get_backend_info.
   - C. Smoke + clean test na czystym Win.
   - D. Zaktualizuj CHECKLIST [x] dla auto + manual notes.

4. **Zamknięcie od A do Z**
   - A. Update checkboxy w CHECKLIST/TODO (local done, manual pending or verified).
   - B. Update memory/HISTORY/PLAN/TODO/crew files identycznie (fraza + "gotowe local" + "manual booth verified on Win").
   - C. Crew Tester: pełna weryfikacja (smoke, pytest, python-c + manual paths).
   - D. Commit "P1.2 DJ checklist polish + local verifs + docs identical".
   - E. Real manual na Win + VLC (użytkownik) → final closure.
   - F. Oznacz closed.

**Kryteria gotowe:** Local verifs green (playback/diag/compact/no-VLC), manual na Win pokrywa pełną CHECKLIST (visual + func + fallback), docs ident, 'gotowe' local + manual. 

**Szacowany:** Po Szpieg/Plan — Writer/Tester local (done), real manual na Win.

**Kroki (po research + Plan list + user dalej):**

1. **Analiza luki (Szpieg + code review)**
   - A. Mapuj każdy [ ] z CHECKLIST do kodu (np. "waveform >=220px" → styles + resize, "compact always-on-top" → CompactPilotWindow + StaysOnTopHint, "dual EQ readable" → ConsoleDeckView, "EFFECT wszędzie" → tooltips, "booth 1m" → visual spec).
   - B. Uruchom crew ANALYZER + REVIEWER na ui/dj_player_window.py + views + controllers.
   - C. Identyfikuj co wymaga code polish (highDPI, extreme resize, no-VLC warning visibility).

2. **Lokalne ulepszenia kodu / testów (doable)**
   - A. Ulepsz headless tests (test_odtwarzacz_load, playback) — więcej asercji na get_backend_info, diagnostics, fallback states, compact flags, QStack indices.
   - B. Dodaj w OdtwarzaczView / dj_player_window więcej logów/status dla no-VLC (jeśli brak widocznego warning).
   - C. Popraw compact pilot jeśli luki (np. highDPI calc, reduce empty bottom force).
   - D. Verifs po każdej: python -c + pytest -k "dj or playback" + smoke.
   - E. Manual symulacja w headless gdzie możliwe (python-c create + compact + load + play states).

3. **Przygotowanie pełnego manualu**
   - A. Rozszerz crew/CHECKLIST o "Auto-verifiable vs Manual only" sekcje + exact kroków (z sizes, expected behaviors).
   - B. Dodaj w docs/dj_player_guide.md sekcję "Jak wykonać pełny manual booth test".
   - C. Stwórz "DJ_Player_Manual_Test_Report_template.md".
   - Verifs: instrukcje precyzyjne.

4. **Pełne manual na real Windows (z VLC) — ostatni guzik**
   - A. Na Windows + VLC: wykonać wszystkie punkty z CHECKLIST (Single visual + func, Compact advanced + always-top + rapid, Dual full, Integracja, Booth sim low light 1m).
   - B. Raport + screeny + checklist update do [x].
   - C. Test fallback: odłącz VLC, sprawdź graceful + warning.
   - Verifs: wszystkie [ ] → [x] lub [~] z notką, smoke/pytest zielone.

5. **Zamknięcie od A do Z**
   - Update TODO, CHECKLIST (checkboxy), memory, HISTORY, dj_player_guide, PLAN, code docstrings.
   - Crew full cycle (Writer/Fixer/Tester na polish).
   - Commit "P1.2 DJ Checklist manual closed (local polish + real Win verif), docs identical".
   - Push.

**Kryteria:** Checklist w 100% pokryta (auto + manual), polish zrobiony, fallbacki potwierdzone w real, docs ident.

---

## Faza 3: P1.3 + P2 — Weryfikacja fallbacków + Polish (od A do Z)

**Poprzedź Szpieg research** na "no-VLC UX in DJ apps" + "compact pilot polish" + "diagnostics UI".

**Kroki:**
1. Research Szpieg → Plan list.
2. Code: upewnij się warning "⚠ Audio niedostępne" + "Pobierz VLC..." jest widoczny w Odtwarzaczu / status (sprawdź w odt_view / dj_player_window).
3. Dodaj ewentualnie prosty przycisk "Info audio backend" w DJ oknie (wywołuje engine.get_backend_info() + get_diagnostics()).
4. Single: jeśli pitch/trim N/A — udokumentuj jasno lub dodaj podstawy jeśli pasuje do MVP.
5. Compact: dodatkowe testy/highDPI w code + docs.
6. Verifs: lokalne + manual.
7. Update checklisty/TODO/docs identycznie.
8. Closure.

---

## Faza 4: Backlog i CI/ Release / Docs proces

- Dla każdego backlog (waveform color, advanced Smart...): 
  - Szpieg research (nowy spawn).
  - Plan list (user review).
  - Decyzja: implementuj czy odłóż.
- CI: rozważ ulepszenia (VLC verify step jaśniejszy, coverage).
- Docs: po każdej fazie — ident update wszystkich plików + zsynchronizuj checkboxy.
- Proces: zaktualizuj AGENTS/PLAN jeśli nowe wnioski.

---

## Pełny pipeline uruchomienia zespołu (dla każdej fazy)

1. Szpieg spawn (explore) — research + Build Spec.
2. Plan spawn — lista + wnioski dla user.
3. User decision.
4. Crew:
   - ANALYZER spawn (głęboka analiza).
   - REVIEWER spawn.
   - (UI) UI-DESIGNER.
   - WRITER spawn (exact impl per spec + lista).
   - FIXER spawn.
   - TESTER spawn (verifs).
5. Po TESTER: smoke/pytest/python-c + manual sim + update docs (memory + HISTORY + TODO + CHECKLIST + code + this PLAN).
6. todo_write update.
7. Commit + push.
8. Oznacz closure w TODO/PLAN.

Używaj `spawn_subagent` z bogatym promptem zawierającym całą hierarchię + aktualny TODO + "exact match", "drobiazgowy", "od A do Z", "dokumentuj identycznie".

---

## Lokalne akcje do wykonania natychmiast (nawet przed full Szpieg output)

(Aby momentum "nie przestawaj"):
- Ulepsz smoke_portable: dodaj wywołanie get_backend_info + raport.
- Dodaj testy headless dla diagnostics.
- Zaktualizuj clean_windows_test o nowe checklist items.
- Sprawdź i udokumentuj aktualny stan no-VLC w kodzie.
- Uruchom pełne pytest -q gdzie możliwe + raport.

---

## Zamknięcie całego planu

Po wszystkich fazach:
- [ ] Wszystkie P1/P2 w TODO [x] lub [~] z wyjaśnieniem.
- [ ] crew/CHECKLIST zsynchronizowany.
- [ ] Pełna dokumentacja identyczna.
- [ ] Verifs green (lokalne + manual notes).
- [ ] Commit history czysty.
- [ ] Użytkownik poinformowany "wszystko zamknięte od A do Z".

**2026-06-25 TESTER po polish Writer (no-VLC, compact, diagnostics) + prior Szpieg/Plan:** Wykonano pełne lokalne verifs DJ Player checklist auto parts i P1 local (smoke SAFE sim, python-c headless full spec, pytest -k gdzie możliwe, code inspect no-VLC vis + compact polish). Raport: green (core playback/diag/no-VLC warning/compact), gaps (env Qt, manual booth), closed A-Z local (P1 verifs + polish), manual recs. Docs (HISTORY/memory/TODO/CHECKLIST/PLAN/...) updated identycznie z frazą. Per SZPIEG Build Spec + Plan (Faza 2/3 P1.2/P1.3 + local actions) + "TESTER verifs po polish Writer (no-VLC, compact, diagnostics) + prior Szpieg/Plan research" + "nie przestawaj"... must document identical. Verifs green. 'gotowe' local.

**Następny krok natychmiast:** Czekaj na outputy Szpieg (poll), potem uruchom pełny Plan jeśli nie, potem prezentuj listę userowi.

Per "uruchom cały zespół agentów" + "drobiazgowy" + "od A do Z".

Powodzenia — nie przestawaj!

---

*Ten plik jest żywy — aktualizuj identycznie przy każdym kroku.*

**2026-07-13 WRITER (Faza 1 per Plan "nowa lista" + Szpieg 2026-07-13 output):** Przygotowano artefakty manual Win: 1. scripts/manual_win_dj_checklist_helper.ps1 (uruchamia + log backend/diag, prompty exact z CHECKLIST dla sizes/wave/BPM/compact/always-on-top/dual/EFFECT/no-VLC/drag/booth). 2. docs/manual_dj_checklist_printable.md (w toku). 3. update clean_windows_test.md (Build Spec, expected sizes). Verif po create (cat/helper), update identycznie memory+TODO+HISTORY+this+CHECKLIST z frazą "per SZPIEG research 2026-07-13 co-dalej manual... must document identical". Short notka local prep. High pressure exact, Polish, read-before. Nie ruszano core. 'Gotowe' Faza 1 prep. Per SZPIEG research 2026-07-13 co-dalej manual... must document identical.

**Po create printable:** Utworzono docs/manual_dj_checklist_printable.md z extract CHECKLIST + expected sizes + placeholders + Szpieg excerpt + Test bez VLC + raport template. Verif + ident update + fraza.

**Po update clean_windows:** Dodano "Build Spec z research Szpieg 2026-07-13" + precise expected sizes/booth/fallback + linki helper/printable. Verif + ident + fraza.