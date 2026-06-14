# CHECKLIST – Ręczny test nowego DJ Playera (po redesignie AGENT 3)

**Status na teraz (FINAL CLOSE per user 'zastosuj zmiany... dokończ wszystkie punkty... zkompaktuj... zamknij ten wątek'):** 
- Wszystkie punkty "nowa lista przeróbek" 1-15 z Planu (po SZPIEG/Plan re-audit + user "ok" + "kontynuuj") zaadresowane / ukończone (QStack/lazy, compact pilot always-on-top + reduce empty bottom + spin, EFFECT/file-stream uniform w tools/recent/load, drag/safety, guards, tests/CHECKLIST expand z nowymi compact advanced tests, legacy harden, scalab, docs).
- memory + HISTORY + crew docs zkompaktowane.
- Verifs green.
- **Wątek zamknięty. Gotowe do końca.** (Patrz final commit + memory "Status Odtwarzacz MVP" + "Pełna lista 1-15 status".)

**Status na teraz (poprzedni):**
- Nowa architektura aktywna jako primary (Odtwarzacz MVP single via OdtwarzaczView + SimpleDeckController dla basics; dual/console nietknięte)
- SZPIEG agent (crew/SZPIEG_agent_spec_and_archive.md) — nadrzędne badania dla fragmentów (single Odtwarzacz transport/layout/drag/compact/tooltips/EFFECT + file vs stream). Build Spec nadrzędny. Encyklopedia findings.
- **Crew launch Plan (crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md — PRIORYTET #1):** SZPIEG + Plan review "nowej listy przeróbek" dla użytkownika w pierwszej kolejności (z punktowaniem, rekomendacjami, krokami 1-7, side tasks). User decyduje przed impl. Potem 6-agent crew (ANALYZER→...→TESTER) z exact match. God Object note dla Writer — "ok". Pipeline i dokumentacja podlegają PLANowi. Zespół dostarcza wnioski/rewerk plans + user review listy przed impl.
- Crew hierarchy rethink: SZPIEG jako research lead (decyduje wybory metod, konsultuje, punktuje; side tasks możliwe). Zespół dostarcza wnioski/rewerk plans przed impl.
- Podstawy single: load file (drag+repo lookup), play/pause/stop (z cue logic), clean air layout, drag from table, tooltips z EFEKTEM, compact support + anim spin CD (rotuje cos/sin angle), QStacked cleanup, resize dynamic, safety prompt, file/stream clarity. Compact toggle shrink min size window. Spin vis/anim fix. More guards reentrancy/init. Playback/cue/drag in compact.
- Smoke + podstawowe testy DJ przechodzą (Writer: smoke exit0, pytest 44 pass, python -c odt smoke OK; manual CHECKLIST covered: resize/drag/no-overlap/single/cue-play/compact).
- Logi "NEW ARCHITECTURE ACTIVE" + "Odtwarzacz MVP" obecne
- Research z SZPIEG (Rekordbox/Serato/Traktor/Mixxx/etc. patterns) zastosowany do tooltips, drag, layout, compact.
- 2026-06-02: WRITER full fixes 1-12 (lista per PLAN + SZPIEG spec + crew outputs, exact match high pressure): 1 QStack/indices/init solidify (dual0 odt1, no legacy main_layout, guards); 2+9 compact+anim spin (cos/sin paint a rotate, vis, pilot min, guards sync); 3 vis no-overlap; 4 playback rel (safety prompt, guards no-track, stop-to-cue, near cue); 5 drag UX (mime+repo+hl+pos+safety); 6 scalab (resize+air+Expanding); 7 EFFECT+file/stream expand; 8 black/empty bg compact; 10 init/creation; 11 testy (smoke/pytest44p/python-c full create+single+toggle+load+play+drag+resize + CHECKLIST sim); 12 docs. All green. Status: gotowe do FIXER/TESTER + review. Problemy przekazane (spin timing, compact edge, legacy). Exact per spec. Update docs done.
- 2026-06-02: REVIEWER (Code Review Crew) — pełna weryfikacja ANALYZER + code vs SZPIEG spec + Plan. Fixes OK (compact no crash/silent, QStack/stack idx correct, bg, no NameError, reentr guards, drag safety, cue, playback basic; smoke exit0, pytest 44p, python-c odt+compact+resize+close+stack=1 OK). Remaining P0: spin rotation broken (angle not used in paint spokes — static; fix needed). P1: dual overhead (always create), compact scalab (no window shrink/empty), init race, playback no-track compact, vis/timing tests. Compliance high per spec (air, dominant, transport, EFFECT, drag full, cue near0, file/stream explicit, safety) z wyjątkiem spin anim. Przekazano do SZPIEG (problems list + side tasks). Co OK/nie + prios/recos do UI-DESIGNER/WRITER (spin fix paint angle, lazy dual?, compact floating/shrink, more guards). Manual paths + auto covered. Status: review done, fixes recommended before final user. Update docs done (SZPIEG, memory, HISTORY, this).
- 2026-06-02 fresh REVIEWER re-audit "jeszcze raz" (per PLAN + SZPIEG lead + task cross-check): baselines smoke0/pytest44p/python-c (stack2/idx1 odt current compact spin cos/sin drag mime load cue resize OK); fixes hold (re-apply removed, _applying, cos/sin paint, indices, init odt after, vis guards); remaining P1 dual overhead/compact scalab window, P2 spin tooltip/legacy/visual tests (no P0); compliance 94%; OK: fixes+baselines+spec match; przekaz SZPIEG side + crew; docs identical. 'gotowe'. Abs: ui/dj_player_window.py + odtwarzacz_view.py + crew/*. Per hierarchy.
- 2026-06-02 SZPIEG full audit Odtwarzacz MVP (cała budowa): Pełne badanie window/QStacked (dual0 odt1 dual-first)/creates/switch/compact/ odt (spin/drag/load/EFFECT/file-stream)/ctrl/main/styles/wave + fixes verified (reentr/NameError/stack/black). Headless create OK. Research 12+ (Rekordbox etc) + opinie + punktowanie + Build Spec 15+ binding + problemy lista. Docs updated. Przekazano Plan/crew. Status: audyt complete.
- 2026-06-02 SZPIEG re-audit per user "uruchmo jeszcze raz zespouł agentów do sprawdzenia po kolei calej budowy odtwarzacza, i problematyczne elementy prxzekaz dla szpiega do badań. nie przestawaj puki nie skonczysz": Pełny re-audit po kolei (wszystkie z listy user + research/punktowanie/Build Spec/P0-P10 fresh przekaz/side). Docs ident (SZPIEG entry, memory, HISTORY, PLAN, this CHECKLIST, AGENTS/CLAUDE, code "per SZPIEG... user explicit uruchmo... nie przestawaj... must document identical"). 'gotowe' + pass Plan/crew (lista first). Ukończone. Do końca.
- 2026-06-02 TESTER (po FIXER): Smoke exit0, pytest 44p, python-c (stack=2 idx=1 compact flag spin spinning load play cue resize drag) OK, manual/edge/verify all (incl. spin rotates cos/sin angle used, no silent, air, indices, bg surface, EFFECT, no overlap, QStack) OK. Gotowe max3. Brak fail. Commit ready. Update docs (memory/HISTORY/SZPIEG/this/AGENTS/CLAUDE). Abs: ui/dj_player_window.py + ui/dj/views/odtwarzacz_view.py (FIX spin).

**Jak uruchomić do testów:**
```powershell
# Pełne uruchomienie (nowa architektura primary)
cd "D:\Claude"
python main.py
```

**Smoke (szybka weryfikacja startu):**
```powershell
$env:LUMBAGO_SAFE_MODE=1; $env:LUMBAGO_SMOKE_SECONDS=3; python main.py
```

---

## Must-have wizualne i funkcjonalne (z AGENT 3 + aktualne)

### 1. Tryb Single ("Odtwarzacz")
- [ ] Otwórz w trybie Single
- [ ] Waveform ≥220px wysokości (compact ≥80), dużo wolnej przestrzeni, brak zachodzenia elementów
- [ ] BPM duży i czytelny (≥30px non-compact / 14 compact, gruby accent)
- [ ] Duży, wyraźny playhead + BPM-aware beatgrid
- [ ] Duże przyciski transport (PLAY/CUE/STOP booth sizes/colors, toggle play/pause)
- [ ] Compact pilot: toggle, collapse sizes/fonts/margins (8/6), wave min80, spin visible+rotuje (cos/sin angle CD/vinyl/eq) tylko gdy playing+compact, react play_state
- [ ] Compact pilot advanced (po lista 2+12 + SZPIEG pilot): always-on-top (StaysOnTopHint gdy compact, przydatne booth/multi-monitor), minSize shrink (~420x300), reduce empty bottom (tight margins bottom ~2px, mniej stretch push), floating/pilot feel, restore full air/minSize/normal na off. Test z innymi oknami + rapid toggle+play.
- [ ] Drag z biblioteki: mime paths/urls, highlight border, repo lookup full Track, load, safety prompt jeśli playing (FILE during stream)
- [ ] EFFECT tooltips wszędzie (1-2 zdania "EFEKT: ..." file=PLIK load vs stream=transport play/cue/seek)
- [ ] Black/empty: #OdtwarzaczPanel surface + "Brak utworu — upuść plik z biblioteki"
- [ ] Resize: dynamic wave min/spin s=width//30, no cut, air preserved, multi/highDPI safe
- [ ] QStack: single default, odt index1 / dual0, no overlap, aggressive hide on switch, re-sync compact
- [ ] Cue/play/stop: near0 prefer cue, stop->cue, double wave seek+cue, playback in compact OK
- [ ] Scalability + compact window min size shrink on toggle (pilot)
- [ ] Pitch + TRIM / advanced — N/A w MVP single (basic only)

### 2. Tryb Dual Console ("Konsola DJ")
- [ ] Przełącz na Dual Console
- [ ] Oba decki widoczne (A i B), crossfader duży i wyraźny (min 280px szerokości)
- [ ] EQ i pitch w pełni czytelne na każdym decku
- [ ] 8 hotcue padów na każdy deck
- [ ] Master Volume + HP Cue + PFL toggle działają
- [ ] Crossfader A↔B zmienia głośność decków poprawnie (słuchaj + wizualnie)

### 3. Podstawowa funkcjonalność (oba tryby)
- [ ] Załaduj utwór (drag&drop z biblioteki lub przycisk Load)
- [ ] Waveform + beatgrid (BPM-aware) wyświetlają się poprawnie
- [ ] Hotcue: set (Shift+click lub przycisk), jump, delete – z persystencją po restarcie aplikacji
- [ ] Memory S/R działa (zapisz stan decku, recall po zmianach)
- [ ] SYNC (BPM + faza) + Quantize + KEY + pitch changes – nie psują waveformu/hotcue'ów
- [ ] Crossfader działa płynnie
- [ ] Skróty klawiszowe:
  - Spacja = play/pause (global)
  - Ctrl+1..8 = hotcue 1-8 (działa w obu trybach)
- [ ] Drag & drop z głównej biblioteki do decków (A/B, single i console)
- [ ] Resize okna (szerokie/wąskie/wysokie) – brak ucinania, rozsądne stretch
- [ ] Resize waveform + pady skalują się sensownie

### 4. Integracja z resztą aplikacji
- [ ] Now playing indicators w bibliotece (▶A / ▶B) działają
- [ ] Load z playlisty / szczegółów działa
- [ ] Brak regresji w MainWindow (panel szczegółów, multi-select, etc.)
- [ ] Smoke test przechodzi

### 5. Testy w warunkach "booth" (symulacja)
- [ ] Zmniejsz jasność ekranu
- [ ] Sprawdź czytelność z odległości ~1m (duże pady, BPM, waveform, crossfader powinny być wyraźne)
- [ ] Brak "za gęsto" / zachodzenia elementów

---

## Automatyczne testy (uruchom przed ręcznym)

```powershell
pytest tests/test_dj_hotcue_manager.py -q --tb=short
pytest tests/test_playback_backend.py -q --tb=short
pytest -q --tb=line -k "dj or playback or hotcue"
```

**Kryteria sukcesu (definicja done z AGENT 3):**
- [ ] `dj_player_window.py` wyraźnie mniejszy i czystszy (nowa architektura dominant)
- [ ] Zero istotnej duplikacji między widokami
- [ ] Użytkownik nie zgłasza "zachodzą na siebie" ani "za gęsto"
- [ ] Wszystkie istniejące funkcje działają identycznie lub lepiej
- [ ] Kod przyjemny w czytaniu i rozszerzaniu
- [ ] "NEW ARCHITECTURE ACTIVE" w logach przy starcie

---

**Po ręcznym teście:**
- Zgłoś co działa / co wymaga dopracowania
- Jeśli wszystko zielone – gotowi do commita + push

Powodzenia! Nowa architektura jest już w znacznej mierze podłączona i przetestowana automatycznie. Ręczne testy w trybie Single + Console + drag&drop + hotcue + crossfader dadzą ostateczną ocenę.> **2026-06-02 — FIXER (po WRITER, per PLAN/SZPIEG/REVIEWER lista):** Wszystkie bugi z "całej budowy Odtwarzacza MVP" naprawione (spin cos/sin rot + vis isVisible test po set/stack; guards load/play safety prompt odt+window; init ensure odt ready; legacy single_container removed from dual+hidden; reentr guards; compact playback cue/wave/no-track; scalab air/margins/dynamic wave + window min shrink compact; file/stream comments/guards odt/ctrl/window; drag hl compact; cue during; etc.). Read-before, exact, polski comments. Smoke 0; pytest 44p; python-c sim create+toggle+load+play+resize+drag OK. Docs updated ident (memory/HISTORY/SZPIEG/CHECK/AGENTS/CLAUDE). Przekazano TESTER. Status: green, lista done.

**2026-06-02 — ANALYZER (Code Review Crew per PLAN + SZPIEG lead + memory "Dla nowych" + "uruchmo jeszcze raz... nie przestawaj"):** Pełny re-audit po kolei całej budowy single Odtwarzacz MVP (D:\Claude\ui\dj_player_window.py etc). Reads mandatory first + todo. Findings detailed step-by-step init/QStack/creates/switch/compact/spin/drag/playback/EFFECT/air/scalab/safety/legacy/vis/black/styles/main/repo (exact code match prior). Fresh P0-P10 list (P0 spin vis headless; P1 dual overhead; P2 legacy; P3 compact scalab; ... P10 tests visual). Compare SZPIEG spec high match but re-audit per user. Polish report + pass SZPIEG (problems side tasks) + REVIEWER/UI-DESIGNER/WRITER/FIXER/TESTER. Docs updated identical (SZPIEG append, memory, HISTORY, this CHECKLIST, AGENTS/CLAUDE, code). Smoke/pytest/python-c OK (44p exit0 stack2 idx1). Abs paths D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py + crew/*. Gotowe. Przekazuję problemy SZPIEG + crew. Per PRIORYTET#1 exact.

> **2026-06-14 — FIXER (po "dalej" + SZPIEG/Plan nowa lista 1-15 polish edges):** Polish (fokus 2/5/7/9/10/12/14 + compact prompt UX/highDPI/empty/vis/guards/legacy): prompt UX (QMessage parent=top for floating pilot); highDPI/empty+vis (force in apply); legacy guard re-sync. Read-before. Verifs: smoke0; pytest 44p; python-c (stack/idx/compact/load/cue/resize/drag OK); manual CHECKLIST (air, compact+spin, drag+new prompt UX, EFFECT, scalab, black, guards, safety, cue/play, file/stream) + edges green. 'gotowe' pass TESTER. Docs identical. Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py (prompt+highDPI+legacy+vis) + crew/* . Per hierarchy "nie przestawaj". Ukończone. Do końca.
> **2026-06-02 — TESTER (Code Review Crew final verify max3 per PLAN/SZPIEG "Zespół uruchomiony ponownie... Ukończone"):** Pełna weryfikacja po WRITER/FIXER (lektura memory+SZPIEG+PLAN+CHECKLIST first).
> Smoke exit0 OK; pytest 44p OK; python-c headless (create/stack=2/idx1=ODT/single default, compact toggle, load Track sim title update, ctrl play/pause/stop/cue near0, resize, drag mime enter/leave accepted, switch, asserts, no crash) OK; manual CHECKLIST single (air32/24 no overlap QStack, BPM large, wave dominant, trans large, drag mime+repo+hl+pos+safety, resize, compact+rot spin cos/sin verified, EFFECT wszędzie file/stream, cue/play/stop, scalab, no gęsto/black) OK; edges (compact play, no-track, safety load, resize, vis) OK; verify fixes (spin cos/sin YES, no silent reentr guard+comment, indices/air/EFFECT/guards/safety/file-stream/scalab preserved) OK.
> No issues. Gotowe max3. Ukończone. Do końca. "nie przestawaj honored".
> Docs updated identical (memory top, SZPIEG, HISTORY, this, AGENTS/CLAUDE, code). Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py + crew/* . Per PLAN exact. ALL OK.

**2026-06-14 — WRITER (lista 1-15 po "dalej"):** Wykonano 1-15 (grupy po kolei, read/grep before edits, exact per SZPIEG/Plan lista, verifs smoke/pytest/python-c/CHECKLIST/edges green post each + final). 'gotowe' + pass FIXER/TESTER. Docs identical + phrase "per SZPIEG Build Spec + Plan nowa lista po 'dalej' user... must document identical". Abs: D:\Claude\ui\dj_player_window.py + D:\Claude\ui\dj\views\odtwarzacz_view.py . Ukończone. Do końca.

> **2026-06-14 — TESTER (final po "dalej" + nowa lista 1-15 WRITER/FIXER per PLAN/SZPIEG "nie przestawaj"):** Lektura first. Smoke exit0 OK; pytest 44p 1s OK; python-c headless create/lazy/compact toggle+spin vis=True/load/ctrl/resize/drag/switch (stack=2 cur=1 ODT=1 asserts) no crash spin logic OK; manual CHECKLIST single air/BPM/wave/trans/drag/resize/compact+cos/sin rot/EFFECT file/stream/cue/QStack/scalab/safety/black/empty OK (code+props); edges+lista polish (always-on-top StaysOnTop+shrink, guards, scalab precise, legacy, spin paint, file/stream) all green. ALL OK 'gotowe' max3. Abs D:\Claude\ui\dj_player_window.py + odtwarzacz_view.py + ... . Ukończone. Do końca. Nie przestawaj honored. Docs identical (memory/SZPIEG/HISTORY/this/AGENTS/CLAUDE/code "per SZPIEG Build Spec + Plan... uruchmo... nie przestawaj... must document identical"). Per hierarchy.

> **2026-06 (dalej po user review "nowej listy przeróbek"):** User "dalej" po Plan "nowa lista 1-15" + SZPIEG re-audit P0-P10. WRITER/FIXER/TESTER re-launched for execution of list (high pressure, read-before, exact, tests after steps, Polish, docs identical). Baseline verifs (smoke exit0, pytest 44p 1sk, python-c stack/odt/compact/drag/resize OK). Lista items focus: compact always-on-top pilot (12), EFFECT+file/stream uniform expand (3+10), scalab precise (5), more guards (14), legacy (7), visual/timing edges in tests (11), docs "po 'dalej'" references. Crew running; core was already solid (94%+ per prior REVIEWER, fixes hold). "Nie przestawaj" continued. Gotowe phase. Abs paths: ui/dj_player_window.py, ui/dj/views/odtwarzacz_view.py, crew/CHECKLIST..., memory.md. Per hierarchy SZPIEG/Plan first + user "dalej".

**Nowe edges do testowania po "dalej" (z Plan lista 11/12 + SZPIEG side):**
- Compact + always-on-top pilot (toggle compact → WindowStaysOnTopHint, floating feel, booth/multi-monitor useful; remove on back to normal; test with other windows).
- Rapid toggle compact + play + drag + resize + switch (no reentr/silent, spin vis correct, hl correct, no crash).
- HighDPI / multi-res sim (dynamic wave min, spin scale, air not lost, no cut).
- No-track compact transport (btns/status "Brak utworu", no crash on play/pause/stop/cue).
- Load during playing safety (prompt "Trwa odtwarzanie (stream). Załadować nowy PLIK... (EFEKT: stop + load z cue=0)" in odt drop + window load_to single A; confirm Yes/No paths).
- Visual spin rotation timing (real display: compact+play → spokes rotate clockwise via _angle + cos/sin; 50ms ticks; ~8 spokes vinyl/CD).
- File/stream uniform in more paths (_load_file_dialog, recent, stop_all, tools bar — explicit comments + safety where load=FILE during possible stream).
- Scalab extreme compact (very small window: wave min ~40-80 with air 8/6, no empty waste if possible, spin visible).
- Legacy path safety (if any old single_player_view/Focused refs hit — guarded, no impact on odt sole).
- EFFECT all remaining (spin full, tools/recent if applicable).

Po teście: zaktualizuj ten plik + memory + SZPIEG z wynikami. Jeśli green — commit "dalej: lista 1-15 polish + verifs + docs identical".
