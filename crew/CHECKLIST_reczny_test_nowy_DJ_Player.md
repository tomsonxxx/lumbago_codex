# CHECKLIST – Ręczny test nowego DJ Playera (po redesignie AGENT 3)

**Status na teraz (po równoległej integracji):**
- Nowa architektura aktywna jako primary (`_HAS_NEW_DJ_VIEWS = True`)
- `DeckController` + `FocusedDeckView` / `ConsoleDeckView` / `DualConsoleWidget` + `MixerStrip` + `MemoryControls` podłączone
- HotcueManager w czystym module (`ui/dj/hotcue_manager.py`) – zero ryzyka cyklu
- Stary kod (`DeckWidget` / `SinglePlayerView`) jako pełny fallback
- Smoke + podstawowe testy DJ przechodzą
- Logi "NEW ARCHITECTURE ACTIVE" obecne

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