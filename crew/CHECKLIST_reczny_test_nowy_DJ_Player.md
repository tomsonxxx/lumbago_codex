# CHECKLIST – Ręczny test nowego DJ Playera (po redesignie AGENT 3)

**Status na teraz (po równoległej integracji + SZPIEG research + Writer reworks per spec):**
- Nowa architektura aktywna jako primary (Odtwarzacz MVP single via OdtwarzaczView + SimpleDeckController dla basics; dual/console nietknięte)
- SZPIEG agent (crew/SZPIEG_agent_spec_and_archive.md) — nadrzędne badania dla fragmentów (single Odtwarzacz transport/layout/drag/compact/tooltips/EFFECT + file vs stream). Build Spec nadrzędny. Encyklopedia findings.
- **Crew launch Plan (crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md — PRIORYTET #1):** SZPIEG + Plan review "nowej listy przeróbek" dla użytkownika w pierwszej kolejności (z punktowaniem, rekomendacjami, krokami 1-7, side tasks). User decyduje przed impl. Potem 6-agent crew (ANALYZER→...→TESTER) z exact match. God Object note dla Writer — "ok". Pipeline i dokumentacja podlegają PLANowi. Zespół dostarcza wnioski/rewerk plans + user review listy przed impl.
- Crew hierarchy rethink: SZPIEG jako research lead (decyduje wybory metod, konsultuje, punktuje; side tasks możliwe). Zespół dostarcza wnioski/rewerk plans przed impl.
- Podstawy single: load file (drag+repo lookup), play/pause/stop (z cue logic), clean air layout, drag from table, tooltips z EFEKTEM, compact support + anim spin CD, QStacked cleanup, resize dynamic, safety prompt, file/stream clarity.
- Smoke + podstawowe testy DJ przechodzą (Writer: smoke exit0, pytest 44 pass, python -c odt smoke OK; manual CHECKLIST covered: resize/drag/no-overlap/single/cue-play/compact).
- Logi "NEW ARCHITECTURE ACTIVE" + "Odtwarzacz MVP" obecne
- Research z SZPIEG (Rekordbox/Serato/Traktor/Mixxx/etc. patterns) zastosowany do tooltips, drag, layout, compact.
- 2026-06-02: Writer impl reworks (kroki 1-7 per Plan) — QStacked, EFFECT expand, compact+spinning, resize, cue/drag+safety, testy, docs update. Exact match spec. Status: gotowe do review.

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
- [ ] Waveform ≥220px wysokości, dużo wolnej przestrzeni, brak zachodzenia elementów
- [ ] BPM duży i czytelny (≥30px, gruby)
- [ ] 8 dużych hotcue padów (2×4 grid, 82×62px lub zbliżone, 8 różnych wysokokontrastowych kolorów)
- [ ] Duży, wyraźny playhead + BPM-aware beatgrid
- [ ] Duże przyciski transport (PLAY/CUE/STOP)
- [ ] Pitch + TRIM czytelne, EQ jeśli widoczne
- [ ] Memory S/R, SYNC, Q, KEY – duże i wyraźne

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

Powodzenia! Nowa architektura jest już w znacznej mierze podłączona i przetestowana automatycznie. Ręczne testy w trybie Single + Console + drag&drop + hotcue + crossfader dadzą ostateczną ocenę.