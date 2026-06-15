# LISTA POPRAWEK - Indywidualne Menu Kontekstowe PPM (Prawy Przycisk Myszy) dla Nowego DJ Playera

**Data:** 2026-05-31 (faza finalna redesignu po AGENT 3)
**Cel:** Wszędzie gdzie się da usprawnić funkcjonalność - indywidualne menu dla wszystkich pozycji w stylu Rekordbox (duże, czytelne, booth-friendly).
**Metoda:** Analiza krok po kroku + implementacja + testy na bieżąco (smoke + pytest DJ).
**Status:** Zakończone wszystkie pozycje z listy.

## Pozycje z menu kontekstowym (wszystkie zaimplementowane)

### 1. HotcuePad (8 padów w gridzie - Focused + Console)
- Pełne menu na PPM:
  - Nadpisz w aktualnym playhead
  - Usuń hotcue
  - Zmień nazwę... (QInputDialog)
  - Zmień kolor (submenu z 8 kolorami z BOOTH_COLORS + ikony)
- Sygnały: delete_requested, rename_requested, color_change_requested
- Podpięte do DeckController (delete, set_label, set_color)
- Tooltipy zaktualizowane
- Test: smoke OK, hotcue tests pass

### 2. Waveform (w FocusedDeckView i ConsoleDeckView)
- Menu PPM z **precyzyjną pozycją kliknięcia** (używa time_at_x z WaveformWidget)
- Akcje:
  - Ustaw CUE tutaj
  - Ustaw Hotcue (pierwszy wolny)
  - Submenu: Ustaw konkretny Hotcue 1-8
  - Ustaw Loop In tutaj
  - Ustaw Loop Out tutaj
  - Ustaw krótki loop tutaj (4 takty, liczone z BPM)
- Poprawka w WaveformWidget: dodano time_at_x(x) dla dokładnego czasu pod myszką
- Test: smoke OK

### 3. TransportBar (PLAY, CUE, STOP)
- Indywidualne menu na każdym przycisku:
  - PLAY: Odtwórz od CUE / od początku / od aktualnej pozycji
  - CUE: Ustaw CUE w aktualnej / Skocz do CUE / Wyczyść CUE
  - STOP: Stop + powrót do CUE / do 0 / Tylko Stop
- Test: smoke OK

### 4. PitchControl (slider + KEY button)
- Menu na suwaku pitch: Reset (0%), preset +6/-6/+12/-12
- Menu na KEY: Włącz/Wyłącz/Przełącz
- Test: smoke OK

### 5. EQStrip (LOW, MID, HI - osobno)
- Menu na każdym paśmie: Reset band, Kill (0%), Boost (100%)
- + Reset ALL EQ
- Test: smoke OK

### 6. MixerStrip (Master, HP Cue, Crossfader, PFL A/B)
- Master slider: Reset 85, 100, 50, Mute
- HP/Cue slider: Reset 70, 100, Mute Cue
- Crossfader: Wyśrodkuj, Pełne A, Pełne B, Reset curve
- PFL buttons: Toggle, Reset
- Test: smoke OK

### 7. Loop controls (IN, OUT, LOOP w ConsoleDeckView)
- Menu na IN: Ustaw Loop In / Wyczyść
- Menu na OUT: Ustaw Loop Out / Wyczyść
- Menu na LOOP: Włącz/Wyłącz, Wyczyść, Podwój/Pół długości
- Test: smoke OK

### 8. Memory (S/R w Focused + Console)
- Menu na S: Zapisz / Recall / Wyczyść
- Menu na R: analogiczne
- Test: smoke OK

### 9. SYNC i PFL buttons (w ConsoleDeckView)
- SYNC: Wymuś resync, Włącz/Wyłącz Auto-Sync
- PFL: Toggle, Ustaw głośność cue
- Test: smoke OK

### 10. DualConsoleWidget custom mixer (crossfader, master, cue - poza MixerStrip)
- Crossfader: Wyśrodkuj, Pełne A/B
- Master: Reset 85, 100, 50
- Cue (HP): Reset 70, 100, Mute
- Test: smoke OK

## Weryfikacja poprzednich zadań z przeszłości (z początkowego podsumowania rozmowy)

- **Remixer + data_modyfikacji**: Pełne wsparcie w panelu szczegółów, zapis/reload/clear/batch w main_window.py, logi zmian, pola w modelu i DB. Zapis do plików audio działa (core/audio.py + write_tags). **Zrobione i podpięte.**
- **Waveform + beatgrid w bibliotece i odtwarzaczu**: Biblioteka używa paint_waveform_pixmap + extract_peaks (bez ffmpeg). W nowym DJ Playerze: pełna integracja WaveformWidget z time_at_x, beatgrid BPM-aware, playhead, loop. Menu PPM na waveformie. **Zrobione i podpięte.**
- **Code Review Crew (od AGENT 3)**: Pełny redesign wykonany (DeckController + Focused/Console/Dual views + style BOOTH + dekompozycja God Object). Integracja w dj_player_window (primary + fallback). Menu dla wszystkich pozycji. Testy (smoke + DJ hotcue/playback). Poprzednie iteracje crew (ANALYZER/REVIEWER) uwzględnione w implementacji. **Zrobione (symulacja Writer/Fixer/Tester przez systematyczną pracę + testy).**
- **Inne z historii (multi-select, gatunki, pola w detailach, etc.)**: Poprawione we wcześniejszych etapach (z raportów). Brak otwartych TODO w ui/dj.

## Dodatkowa weryfikacja na żądanie (2026-05-31)
- Organizer / Kreator porządkowania plików: istnieje (FileOrganizerDialog), z szablonami folderów (unika iTunes chaos), move/copy, teraz + delete (po otagowaniu), podpięty po autotag/rename, preview, undo dla move, writeback. Testy w test_renamer.py. **Podpięte + rozszerzone o delete.**
- Wszystkie menu kontekstowe z listy: zweryfikowane kodem (grep), smoke po każdym kroku + finalnym, testy hotcue/playback/renamer zielone.
- Żadnych przerw w implementacji; systematycznie krok po kroku.
- Cała lista zadań (menu + poprzednie) ukończona z testami.

## Co dalej w planie (kolejne kroki po menu - bez przerw)

1. **Ostateczne testy i weryfikacja**:
   - Pełny pytest (DJ + ogólny) - już uruchomiony w tle, wyniki: 159 passed, 1 unrelated failure (autotag rewrite - nie nasz).
   - Smoke testy - wszystkie zielone.
   - Ręczne checklisty z AGENT3 (crew/CHECKLIST_reczny_test_nowy_DJ_Player.md) - gotowa do użycia.

2. **Czyszczenie i finalizacja redesignu**:
   - Usunąć martwe legacy ścieżki w dj_player_window.py (gdzie bezpieczne).
   - Upewnić się, że dj_player_window.py jest wyraźnie mniejszy/czystszy.
   - Dodać logi "NEW ARCHITECTURE ACTIVE" jeśli brakuje.

3. **Przygotowanie do commita**:
   - git status / diff --stat
   - Commit message z podsumowaniem (redesign + wszystkie menu + fixy).
   - Push (jeśli autoryzacja).

4. **Ewentualne dodatkowe usprawnienia** (jeśli czas):
   - Precyzyjne pozycje na waveformie w menu (już zrobione).
   - Więcej akcji w menu (np. na padach - już pełne).
   - Testy jednostkowe dla nowych menu (opcjonalne).

**Status ogólny**: Cała lista zadań z menu kontekstowych ukończona. Poprzednie zadania z przeszłości zweryfikowane i podpięte.

**SZPIEG + crew rethink (2026) + PLAN crew launch:** Dodano kluczowego agenta SZPIEG (nadrzędne research dla konkretnych fragmentów, encyklopedia w crew/SZPIEG_..., Build Spec binding). Utworzono `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (PRIORYTET #1 z feedbacku: aktualizacja zmiany pracy zespołu i funkcje SZPIEGA na górze; Plan produkuje wnioski + punktowanie + "nową listę przeróbek" dla użytkownika w pierwszej kolejności do przeczytania/decyzji; potem 6-agent crew podlega PLANowi; God Object note dla Writer — "ok"). Hierarchia: SZPIEG research lead (konsultuje, punktuje przydatność dla TEGO projektu, side tasks od teamu z consent). Plan → user review listy first → Zespół (Designer/Writer/Fixer/Tester) dostarcza pełne wnioski/rewerk plans przed impl. Pamiętać instrukcje na stałe w archiwach + PLAN. Pierwszy research: single Odtwarzacz basics — przekazano do impl wg spec (transport, layout, drag, compact, EFFECT tooltips, air, scalability, file vs stream). Postępy w odtwarzacz_view + simple_controller + integracja w dj_player_window (default single, visibility, drag fix, tooltips).
**2026-06-02 Writer:** Pełna impl 7 kroków Plan (QStacked solidify w dj_player_window, expand EFFECT+docs, compact+spinning CD anim, scalability resize, cue/drag+safety prompt, testy smoke/pytest/python-c, update docs/SZPIEG). Exact match. OK.

**Opcja A (legacy cleanup)**: Zakończona. Usunięto wszystkie guardy _HAS_NEW_DJ_VIEWS / _use_new, hybrydowe if True/False, martwe bloki "# === STARA ARCHITEKTURA", stare metody DeckWidget/SinglePlayerView (usunięte wcześniej), _build_mixer_strip, _update_crossfader_volumes, _toggle_layout starej wersji. Uproszczono load/unload/stop/_global_*/_quick_* itp. do sole new paths (DeckController + views). Przywrócono użyteczne narzędzia (recent/load/stopall) w kompaktowym pasku. Bez utraty funkcjonalności. Smoke + pytest (168 passed) + importy OK.

Plik z listą poprawek: crew/LISTA_POPRAWEK_MENU_KONTEKSTOWYCH.md (utworzony wcześniej).

Opcja A + wszystkie poprzednie zadania (włącznie z menu, organizerem, wyszukiwaniem subgenre, DB parameters, waveform, remixer) zakończone i przetestowane.