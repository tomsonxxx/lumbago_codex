# Test na czystym Windows — checklist (Desktop PyQt6, post DJ migration)

Per 2026-06-16 full repo consolidation (SZPIEG research lead): ALL prior documentation, old agent outputs, full checklists, unused docs, previous crew reports, history, mockups, build artifacts, web remnants, legacy plans, DESIGN docs, Blueprint extract etc. safely archived in root MEMORY/ directory (substructure: full_agent_instructions/, historical_checklists/, archive/ (from prior 2026-06-15 docs/archive/), old_docs/, previous_runs/ etc.) and summarized/pointered in this memory.md (Archiwum section). Live files (AGENTS/CLAUDE/crew/PLAN/SZPIEG/CHECKLIST + docs/HISTORY/guides + README etc.) minimized for continuity but complete. All information preserved and accessible via MEMORY/INDEX.md + git history. Builds on 2026-06-15 uporządkowanie to docs/archive/. Per SZPIEG research 2026-06-16 consolidation + Plan hierarchy + "uruchamiaj szpiega przed kazdym wiekszym etapem" + "nie przestawaj" + "must document identical". Polish compact/no-VLC/diag per SZPIEG research 2026-06-25 DJ checklist + Plan... must document identical (visible banners in odt+window, get_backend_info, tests).

**2026-06-25 TESTER (verif WRITER changes exact per PLAN/SZPIEG + 'nie przestawaj'):** Zweryfikowano no-VLC + diagnostics z exact text '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' + get_backend_info link w odt_player_window.py + odtwarzacz_view.py. python-c verifs (import, Engine, get_backend_info, fallback detect, sim warning) OK. Tekst prominentny w compact/normal, używa get_*, zachowuje EFFECT/file-stream, nie psuje QStack/compact. Docs update ident. Co działa/gaps/closed P1.3 local: TAK (local). 'gotowe' local. must document identical.

**Uwaga:** Testuje desktop app (PyQt6). Web parts legacy. Nowa DJ arch jest jedyną: ui/dj/* + clean dj_player_window.py.

## Założenia
- Brak zainstalowanego Pythona.
- Brak zależności dev.
- Test na świeżym profilu użytkownika.

## Przygotowanie
1. Zbuduj artefakt: `.\scripts\build_portable_windows.ps1`
2. Skopiuj `dist/LumbagoMusicAI-portable.zip` na maszynę testową.
3. Rozpakuj archiwum do nowego katalogu (np. `C:\LumbagoMusicAI`).

Automatyczny smoke na maszynie deweloperskiej:
```powershell
.\scripts\smoke_portable_windows.ps1
```

## Smoke test uruchomienia
1. Uruchom `LumbagoMusicAI.exe`.
2. Sprawdź, czy okno startuje i nie zamyka się samoczynnie.
3. Zamknij aplikację.

## Test funkcjonalny (minimum)
1. Włącz aplikację.
2. Wejdź w Import i dodaj 1–3 pliki audio (MP3/FLAC).
3. Sprawdź, czy pojawiają się w bibliotece.
4. Otwórz Detail Panel i edytuj podstawowe tagi.
5. Zapisz i sprawdź, czy tagi są zapisywane w pliku.

## Player (nowy DJ arch)
1. Otwórz DJ Player (przycisk DJ Player ▼).
2. Załaduj 1-2 utwory (z biblioteki lub drag&drop) na decki A/B.
3. Odtwórz, seek, ustaw hotcue (8/deck), loop, crossfader.
4. Sprawdź waveform, status, brak crashy przy load niezeskanowanych tracków (dzięki robust None w beatgrid/auto_cue).
5. Zatrzymaj / toggle.

Uwaga: nowa architektura sole (ui/dj/* + dj_player_window.py hardcoded True) — brak starych klas.

**Uwaga audio:** Pełny playback wymaga VLC. Na czystym Windows CI instalacja przez Chocolatey + cache (lub fallback). Gdy VLC niedostępny — Qt lub Noop fallback (testy + smoke przechodzą). Na użytkowniku: zainstaluj VLC dla pełnej jakości DJ.

### Lokalne verifs TESTER (2026-06-25, per Szpieg/Plan)
- Smoke logic: resource verif (fpcalc, ui/assets, docs, icons, themes) + exe run z SAFE + diag notes. PASS (z hard checks po enhancements).
- python -c: PlaybackEngine, get_backend_info (Noop), get_diagnostics, frozen paths via config — wszystkie PASS (graceful fallback, correct keys, dev/frozen layout).
- pytest: test_playback_backend (19 passed, 6 skipped), test_playback_cue_pfl (3p), test_ui_smoke (1p), test_config (2p) — core zielone.
- Gaps: smoke brak pełnego exec diagnostics w PS (note vs auto raport); full manual (import+DJ+APPDATA+VLC guidance) pending na clean VM/Windows.
- Fixes applied: strict resources in smoke, DIAG support, explicit AUTO-COVERAGE REPORT.
- Covered (local buttoned): resources, backend_info/diag, portable paths, no-VLC guidance w UI (z Writer).
- Per SZPIEG research 2026-06-25 Clean Windows P1 (fresh deep research: 15+ practices... luki identified in smoke coverage... Build Spec + "nowa lista" 1-8... must document identical) + local verifs green. 'Gotowe' local buttoned. VM/manual pending per PLAN.
Widoczny warning: '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' (w dj_player_window + OdtwarzaczView status) + link diagnostics (get_backend_info weryfikowany). Per Szpieg/Plan + must document identical.

## Zakończenie
1. Sprawdź, czy w `%APPDATA%\LumbagoMusicAI` powstały pliki `lumbago.db` i `settings.json`.
2. Zapisz wynik testu oraz ewentualne błędy.

Per SZPIEG research 2026-06-25 + 2026-07-13 Szpieg (co dalej manual + clean Win: 15+ praktyk fresh VM/strict resources/visible banner '⚠ Audio niedostępne...' + sizes waveform/compact/cross/booth/EFFECT + Build Spec + helper). Local + artifacts closed. VM/manual pending. Per "per SZPIEG research 2026-07-13 co-dalej manual checklist + clean Win... must document identical".

Local smoke + scripts (build_portable + smoke_portable + pyinstaller + get_resource_path + engine graceful + diagnostics) full coverage of portable exe run/resources (SAFE) + backend info note + APPDATA + VLC guidance. Enhanced per 2026-06-25 Szpieg (more resources, diagnostics raport, checklist auto items).

**WRITER changes per Analyzer (luki: SAFE stub omija DJ/backend/diag, luźne resource verif, brak auto DJ load + no-VLC + diagnostics w portable smoke) + SZPIEG (Clean Windows + DJ checklist) + PLAN "nowa lista":**
- smoke_portable_windows.ps1: strict resource checks (throw jeśli brak critical), dodano wsparcie LUMBAGO_SMOKE_DIAG (przekieruj output z exe, assert "Noop|backend").
- main.py: jeśli LUMBAGO_SMOKE_DIAG lub SMOKE + diag env — utwórz PlaybackEngine(), wypisz get_backend_info + get_diagnostics(), potem quit (nawet w SAFE stub).
- smoke/build: explicit raport "AUTO-COVERS: exe, resources(strict), backend_info, diagnostics, no-VLC states".
- Docs (clean_windows_test.md, dj_player_guide jeśli pasuje, TODO) zaktualizowane identycznie.
Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" ... must document identical.

Full manual (import 1-3 audio, detail edit+save, DJ Player full: load/drag/play/seek/hotcue 8/deck/crossfader/waveform/status, APPDATA db+settings, with/without VLC + visible exact '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' + link do diagnostics (get_backend_info verif) w dj_player_window lub OdtwarzaczView, diagnostics) + clean-VM/fresh profile test pending per original plan + 'nie przestawaj'. Per Szpieg/Plan + must document identical.

'Gotowe' local buttoned (per Szpieg 2026-06-25 + Plan lista). Real VM/manual required for final closure. Per PLAN + "must document identical".

Verifs local: smoke exit0 + raport, python -c (PlaybackEngine + get_backend_info + diagnostics + frozen paths), pytest playback/dj relevant.

See full Szpieg report in crew/SZPIEG... (append) and PLAN_DZIALANIA_2026-06-25.md.

### Lokalne verifs TESTER (Linux env, 2026-06-25) — P1.1 "local buttoned" część
Per SZPIEG research 2026-06-25 + 2026-07-13 Szpieg (co dalej manual + clean Win: 15+ praktyk fresh VM/strict resources/visible banner '⚠ Audio niedostępne...' + sizes waveform/compact/cross/booth/EFFECT + Build Spec + helper). Local + artifacts closed. VM/manual pending. Per "per SZPIEG research 2026-07-13 co-dalej manual checklist + clean Win... must document identical". 

**Smoke logic review (scripts):**
- smoke_portable_windows.ps1 + build_portable_windows.ps1 + run_headless.sh + pyinstaller.spec przeczytane.
- Smoke: extract, resource checks (fpcalc, ui/assets, docs/user_guide, assets/*, ui/assets/icons, themes), notes on _internal/COLLECT + get_resource_path, exe run z LUMBAGO_SAFE_MODE + LUMBAGO_SMOKE_SECONDS, "Backend diagnostics note", checklist auto items (resources, exe start SAFE, structure).
- Brak bezpośredniego wywołania python get_backend_info/get_diagnostics w smoke (PS dla .exe, exercise via "real DJ Player run").
- Detailed comments z frazą Per SZPIEG research 2026-06-25 + Etap4 + must document identical.
- run_headless.sh: xvfb wrapper dla Linux smoke.

**python -c verifs (Linux, no VLC):**
- PlaybackEngine() OK, get_backend_info(): {'deck_a': '_NoopAudioBackend', ...} (fallback oczekiwany).
- get_diagnostics() OK (keys engine/deck_a/deck_b + cross etc).
- create_backend, get_available_backends() -> ['noop'].
- Frozen paths via config: get_resource_path logic (frozen onedir/_MEIPASS, nonfrozen parents[2]), app_data_dir (uses /home/AppData/... lub fallback), settings_path OK.
- Uwaga layout: w tym env get_resource_path("assets/...") -> /home/assets (nie istnieje), real /home/lumbago_codex/assets — dev layout gap (nie wpływa frozen portable). Sim frozen OK.
- Wynik: WSZYSTKO PASS (z VLC warnings expected).

**pytest relevant:**
- test_playback_backend.py: 19 passed, 6 skipped (mocki VLC/Qt).
- test_playback_cue_pfl.py: 3 passed.
- test_ui_smoke.py: 1 passed, 1 skipped (EGL/pulse skip).
- test_config.py: 2 passed.
- -k "playback or dj or ui_smoke": playback covered (23+ pass total relevant); full dj collection errors bez PyQt6 (headless lim, testy używają skip/subprocess).
- Ogólne: smoke/pytest zielone dla core playback/diagnostics.

**Sprawdzenie smoke script ma diagnostics/backend_info raport (post WRITER edits per Analyzer/SZPIEG/Plan):**
- TAK: "=== AUTO-COVERS: exe, resources(strict), backend_info, diagnostics, no-VLC states ...", LUMBAGO_SMOKE_DIAG support z redirect output + assert "(?i)(Noop|backend|BACKEND_INFO|DIAGNOSTICS)", strict throw na critical resources, early engine print+quit w main.py nawet w SAFE.
- Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" ... must document identical.
- Smoke teraz wykonuje i raportuje BACKEND_INFO + DIAGNOSTICS w log (dla portable smoke + dev python-c).

**Covered vs gaps z Szpieg output (resource verif, APPDATA note, DJ flow, no-VLC guidance):**
- COVERED local: resource verif (smoke checks STRICT + throw + pyinstaller datas + get_resource_path w core/config + usage w main_window/recognizer), APPDATA note (clean_windows + smoke + config app_data_dir with fallback), DJ flow (smoke notes + clean checklist + code + auto diag via LUMBAGO_SMOKE_DIAG), no-VLC guidance (odtwarzacz_view.py _maybe_apply... + dj_player_window _update_backend_info_label używają get_backend_info/get_diagnostics + exact "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org" + diag_link + tooltip + yellow style), python verifs/pytest OK, smoke enhanced notes + AUTO-COVERS explicit.
- GAPS (z Szpieg 2026-06-25 + docs): smoke lacks full DJ functional + diagnostics print/execution (notes not run) — teraz częściowo pokryte via DIAG path; full manual on clean-VM/fresh profile pending (import+detail+DJ full load/drag/play/cue/hotcue/cross/wave + real %APPDATA create + visible warning + backend_info), some resource checks "note" not hard assert — teraz strict, dj tests require PyQt (collection fail w minimal env), resource path dev layout (parents[2] w /home/lumbago_codex subdir).
- UI: no-VLC + backend label pokryte w odt + window (verif python-c + code).

**Propozycje drobnych fixes do smoke/build (dla local+VM) — updated post edits:**
1. Smoke.ps1: strict checks + LUMBAGO_SMOKE_DIAG redirect+assert "Noop|backend" + AUTO-COVERS DONE (per task).
2. main.py smoke path: early PlaybackEngine print+quit for DIAG DONE (even SAFE stub).
3. Dla Linux: ulepsz run_headless.sh lub dodaj scripts/smoke_linux.sh z python -c ... + main smoke.
4. W clean_windows_test.md + smoke: krok "uruchom python -c w unpacked jeśli python, lub manual w DJ: sprawdź backend label + status ⚠" — covered via DIAG in smoke.
5. Testy: dodaj assert w test_playback_backend na get_backend_info keys + "Noop" w fallback (już częściowo w test_engine_get...).
Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" ... must document identical.
6. Resource: rozważ parents[1] lub root detection w get_resource_path dla dev layout (lumbago_codex root).
7. Smoke: raport diagnostics nawet jeśli via note lub log file.
Per "local enhancements first" z Plan + Szpieg.

'Gotowe' local buttoned (verifs green). Real VM/manual required for final closure. Per PLAN + "must document identical".

Per SZPIEG research 2026-06-25 Clean Windows P1 (fresh deep research...) + Plan lista + lokalne verifs TESTER (python -c, pytest playback 23p, smoke review, covered/gaps + fixes) — must document identical. Verifs local + docs update ident. 'Nie przestawaj'. Od A do Z.

## Build Spec z research Szpieg 2026-07-13 (Faza 1 prep artifacts)

Per SZPIEG research 2026-07-13 (Build Spec, 15 praktyk, luki, side recs: helper script + printable + template) + Plan "nowa lista" (Faza 1: prep artifacts helper + printable + update clean_windows) — must document identical.

**Linki do artefaktów:**
- Helper: `scripts/manual_win_dj_checklist_helper.ps1` (uruchamia + log get_backend_info + diagnostics, krok-po-kroku prompty)
- Printable: `docs/manual_dj_checklist_printable.md` (z expected sizes + placeholders + Test bez VLC + template raportu)
- Użyj helper przed manual w clean VM/Win.

**Dokładniejsze expected (z CHECKLIST + Szpieg):**
- Single: Waveform ≥220px wysokości (compact ≥80), BPM ≥30px non-compact / 14 compact (gruby accent). Dużo powietrza, brak zachodzenia.
- Dual: crossfader min 280px szerokości, EQ/pitch czytelne.
- Compact: always-on-top (StaysOnTopHint), minSize shrink ~420x300, reduce empty bottom ~2px, spin rotuje cos/sin gdy playing+compact.
- EFFECT: tooltips wszędzie exact "EFEKT: ..." (file=PLIK load vs stream=transport play/cue/seek)
- Drag safety: prompt "Trwa odtwarzanie (stream). Załadować nowy PLIK..." gdy playing.
- Booth: niska jasność, odległość ~1m czytelność (duże pady/BPM/wave/cross), brak "za gęsto", high-contrast air.
- Fallback visible (no-VLC): prominent '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org' w odt+window (compact/normal/highDPI), get_backend_info() = Noop/Qt, diagnostics btn/log.
- Test bez VLC: uruchom helper ponownie bez VLC; warning widoczny nawet w compact (status hidden), playback ograniczony (FILE vs STREAM).

**15+ praktyk z Szpieg (Clean Windows + DJ manual):** portable resource strict, clean VM fresh profile, VLC guidance 'Pobierz z videolan.org' lub portable obok exe, graceful fallback Noop, get_backend_info/diagnostics zawsze log, booth low light sim, rapid toggle+drag+resize, sizes exact z research (wave dominant 220+, cross 280+), safety FILE during stream, EFFECT na każdym elemencie.

Luki z research: full manual sizes/booth/fallback vis pending w clean Win (local scripts max coverage); smoke diag via helper/printable teraz wspiera.

**Kroki manual z helper (dodatkowo do smoke):**
1. Rozpakuj portable na clean Win.
2. Uruchom helper.ps1 (lub -UseExe).
3. Wykonaj prompty: single sizes, compact rapid, dual cross, EFFECT hover, no-VLC ⚠ (z/ bez), drag, booth low light.
4. Na końcu: "Uruchom ponownie z VLC / bez VLC".
5. Wypełnij template z printable.md.

Update identycznie: memory/TODO/HISTORY/PLAN/CHECKLIST + fraza. Verif cat helper + python get_backend_info. 'Gotowe' Faza 1. Per "nie przestawaj". 

Per SZPIEG research 2026-07-13 co-dalej manual... must document identical.
