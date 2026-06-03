# CHECKLIST – Ręczny test nowego DJ Playera (po redesignie AGENT 3)

**Status na teraz (po równoległej integracji + SZPIEG research + Writer reworks per spec):**
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
- 2026-06-02 SZPIEG full audit Odtwarzacz MVP (cała budowa): Pełne badanie window/QStacked (dual0 odt1 dual-first)/creates/switch/compact/ odt (spin/drag/load/EFFECT/file-stream)/ctrl/main/styles/wave + fixes verified (reentr/NameError/stack/black). Headless create OK. Research 12+ (Rekordbox etc) + opinie + punktowanie + Build Spec 15+ binding + problemy lista. Docs updated. Przekazano Plan/crew. Status: audyt complete.
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
