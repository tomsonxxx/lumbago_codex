# AGENT 3 – UI Designer: Rekordbox-Style Redesign DJPlayerWindow
**Projekt:** Lumbago Music AI (PyQt6 Desktop DJ Tool)  
**Agent:** AGENT 3 – UI Designer (Code Review Crew)  
**Data:** 2026-05-30  
**Kontekst:** Pełna analiza `ui/dj_player_window.py` (~3520 linii) + powiązanych modułów (PlaybackEngine, HotcueManager, WaveformWidget, main_window.py, core/models.py, ui/theme.py).  

---

## 1. Executive Summary – Dlaczego obecny UI jest zły i co go ratuje

**Obecny stan to anty-wzorzec "God Object" na sterydach:**

- Jeden plik `ui/dj_player_window.py` zawiera ~3520 linii. Klasy `DeckWidget` (~1300+ aktywnych linii logiki + layoutu) i `SinglePlayerView` (~400 linii) duplikują 70-80% kodu: osobne `_load_waveform_async`, własne timery playhead, własne metody hotcue (nawet po częściowym wyciągnięciu `HotcueManager`), własne `load_track`, `_update_playhead`, `_snap_to_beat`, memory S/R, sync logic itd.
- `HotcueManager` to tylko plaster na warstwę danych/persystencji – UI padów, eventów, rebuild gridów i aktualizacji tooltipów pozostaje w 100% zduplikowane.
- Przełączanie trybów ("Odtwarzacz" vs "Konsola DJ") to prymitywne `setVisible(True/False)` + ręczny, kruchy `_sync_deck_a_state_between_views` (ponad 160 linii kodu z guardami, powtórnymi loadami waveformu, kopiowaniem stanów BPM/hotcue/loop/playhead). Efekt: race conditiony, "podwójny tryb pojedynczy", zachodzące na siebie elementy, znikające waveformy, desynchronizacja.
- Layouty są **zbyt gęste** (spacing 8-14px, marginesy 16-20px, ale w praktyce za dużo kontrolek na małej przestrzeni). Użytkownik zgłaszał wielokrotnie: "okno jest kompletnie nieczytelne", "ikony zachodzą na siebie", "za gęsto", "tryb pojedynczy jest podwójny!!! wszystko zachodzi na siebie", "małe pady".
- Waveform ma minimalną wysokość 162-170px (zamiast wymaganych 180-220+). BPM-y są za małe (13-14px). Przyciski pamięci 22×20px, pitch slidery 108px szerokości – nieczytelne w warunkach bootha (słabe światło, szybka praca, rękawiczki).
- Brak spójnego języka wizualnego: inline stylesheety w 50+ miejscach, kolory zdefiniowane lokalnie (tylko 4 hotcue kolory dla 8 padów), niekorzystanie z `ui/theme.py`, słabe kontrasty w stanie disabled/hover.
- Crossfader, mixer strip i toggle bar (Pokaż/Ukryj) dodane jako hacki na końcu – powodują dalsze nakładanie się.
- Brak separacji odpowiedzialności: logika playbacku + stan DJ (quantize, sync, memory) + budowanie layoutu + rysowanie + persystencja w jednej klasie.

**Co ratuje projekt (konkretne, wykonalne rozwiązania):**

- **Dekompozycja na małe, wielokrotnego użytku widgety** (TransportBar, HotcuePadGrid, EQStrip, PitchControl, WaveformSection, MixerStrip, MemoryBar). Jedna implementacja = zero duplikacji.
- **Wspólny DeckController (QObject)** – czysta separacja: kontroler zarządza PlaybackEngine, HotcueManager, timerami, waveform loading coordination, sync, memory. Dwa różne widoki (ConsoleDeckView i FocusedDeckView) subskrybują sygnały – zero duplikacji logiki.
- **Dwa naprawdę odrębne tryby wizualne** (nie show/hide tego samego): Single = wielki, oddychający fokus (waveform 220-280px + 8 dużych padów); Dual Console = side-by-side lub stacked pro decki z pełnym mikserem zawsze widocznym.
- **Profesjonalny booth language inspirowany Rekordbox 6/7 + Traktor** (duże pady 2×4 z 8 unikalnymi kolorami, wysoki waveform z muzycznym beatgridem BPM-aware, grube suwaki, 28-36px BPM, 16-20px spacing, wysoki kontrast).
- **Zachowanie 100% istniejącej funkcjonalności** (8 hotcue z persystencją w CuePoint.hotcue_index + color/label, Memory S/R, SYNC faza+keylock, Quantize, PFL wizualny, KEY, loop, waveform seek+shift+double, drag&drop z biblioteki, crossfader via engine.set_deck_trim + volumes).
- **Minimalny breaking change dla backendu** – używamy istniejącego `PlaybackEngine`, `HotcueManager`, `WaveformWidget` i metod (`set_deck_rate`, `set_deck_eq`, `set_deck_keylock`, `seek_deck`, `get_deck_state` itd.).

Efekt końcowy: czytelne, "booth-ready" okno, które nie powoduje frustracji przy 140 BPM w ciemnym clubie. Kod zmniejszony o ~60-70%, łatwy w utrzymaniu.

---

## 2. Nowy język wizualny (Booth-First Design Language)

**Inspiracja:** Rekordbox 6/7 (duże, kwadratowe pady z numerami + kolorami, wysoki waveform z wyraźnym gridem co beat/bar, duże BPM, dużo czarnej przestrzeni, wyraźne A/B oznaczenia, grube suwaki z detentami). Uzupełnione elementami Traktor (wyraźne sekcje mixer) i Serato (kontrast).

### Paleta kolorów (stała, zdefiniowana centralnie)
```python
BOOTH_COLORS = {
    "bg": "#0a0d14",                    # główne tło okna
    "surface": "#12171f",               # panele decków
    "surface_elev": "#1a212c",          # podniesione karty (single mode)
    "border": "#2a3442",
    "border_strong": "#3a4556",
    "text_primary": "#f0f4f8",
    "text_secondary": "#a8b3c2",
    "text_muted": "#6b7688",
    "accent": "#00e0ff",                # cyan (info, BPM, deck labels) – nowoczesny Rekordbox feel
    "accent_orange": "#ff8a00",         # energia, playhead alternatywa
    "play": "#22c55e",
    "stop": "#ef4444",
    "cue": "#f43f5e",
    "loop": "#3b82f6",
    "warning": "#eab308",
    "hotcue": [                         # 8 unikalnych, wysokokontrastowych (Rekordbox style)
        "#ef4444", "#f97316", "#eab308", "#22c55e",
        "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"
    ],
    "wave_bg": "#0f141c",
    "wave_peak": "#67e8f9",
    "wave_rms": "#1e3a52",
    "playhead": "#f43f5e",
    "playhead_glow": "#fb7185",
    "sync_active": "#166534",
}
```

### Spacing & Density (sztywne reguły)
- Marginesy zewnętrzne paneli: **16-24px** (nigdy mniej niż 16).
- Odstępy między sekcjami (header / waveform / transport / hotcues / mixer): **18-24px**.
- Wewnątrz grupy kontrolek (np. transport buttons): **10-14px**.
- Między suwakami EQ/pitch: **6-8px** (ale pady i waveform mają priorytet powietrza).
- "Oddychanie" w single mode: +30-40% więcej paddingu niż w console.
- Min. wysokość okna w trybie dual: **720px**, szerokość **920px** (dla side-by-side). Single: 680×620 min.

### Typografia (hierarchia czytelna w 0.5s)
- **BPM (must-have #1):** 30-36px, font-weight: 900, letter-spacing: -0.5px, color: accent. Monospace fallback dla cyfr.
- **Tytuł utworu:** 16-18px, weight 700, text_primary. Elide na końcu.
- **Czas (0:00 / 3:42):** 16-18px, Consolas / "JetBrains Mono" / monospace, weight 600, text_secondary.
- **Etykiety sekcji (HOT CUES, EQ, PITCH, LOOP, MIXER):** 10-11px, weight 800, uppercase, letter-spacing: 1.5-2px, text_muted.
- **Przyciski transport (▶ / CUE / STOP):** 15-17px, weight 800.
- **Hotcue pady (liczby + ewentualny custom label):** 18-20px bold + 9-10px label poniżej.
- **Suwaki value labels:** 12-13px, weight 700.

### Rozmiary kontrolek (booth-friendly – duże, grube, precyzyjne)
- **Hotcue pady:** 82×62px (lub 78×58 przy bardzo wąskim oknie). Zawsze 2×4 grid. Zaokrąglenie 8-10px. Numer + opcjonalny 1-liniowy label (późniejsza funkcja).
- **Waveform:** min-height **220px** (single: 260-300px, stretch). Playhead: 4px + potrójny glow.
- **Transport główne:** PLAY 92×58px, CUE 78×52px, STOP 68×52px.
- **Suwaki pitch/trim (poziome):** wysokość rowka 8-10px, handle 22-26px. Długość 160-220px.
- **EQ (pionowe):** wysokość 92-110px, szerokość rowka 14px.
- **Crossfader:** wysokość 32-36px, szeroki (min 280px), wyraźny detent w środku (linia + "A | B" nad suwakiem).
- **Przyciski pro (KEY, SYNC, PFL, Q, IN/OUT/LOOP):** 52-64px szerokości × 36-42px wysokości. Duże fonty.

### Stany interaktywne (wyraźne, natychmiast rozpoznawalne)
- **Normal:** surface + border.
- **Hover:** border → accent (cyan), lekkie rozjaśnienie tła (+8-12% lightness).
- **Pressed/Active:** ciemniejsze tło + mocniejszy border accent, ewentualnie scale 0.98.
- **Checked (toggle):** tło = accent (dla KEY/SYNC) lub dedykowany zielony dla Q/PFL gdy ON. Tekst biały.
- **Disabled:** opacity 0.45, border muted, cursor default. Nigdy nie znika całkowicie.
- **Hotcue set:** pełne wypełnienie kolorem z listy + biały border + ciemny tekst.
- **Hotcue empty:** ciemne tło + kolorowy border 2px + kolorowa liczba.
- **Playhead + beatgrid:** zawsze najwyższy kontrast (biały/żółty grid na ciemnym waveformie).

### Dodatkowe zasady booth
- Zero drobnych ikon bez etykiet tekstowych na kluczowych kontrolkach.
- Duże, grube linie beatgridu (co beat: dotted 1px 55% alpha, co bar: solid 1.5-2px 85% alpha) – BPM-aware dokładnie jak w WaveformWidget.
- Memory S/R: małe, ale wyraźne "S" / "R" z tooltipami 3-liniowymi.
- Statusy (backend, sync, loaded): 10-11px, zawsze w tym samym miejscu (prawy górny róg decku).

---

## 3. Propozycja nowej architektury komponentów

**Cel:** Usunąć 80% duplikacji. Zamiast dwóch potworów – jeden kontroler + kompozycja małych widgetów + dwa czyste layouty prezentacyjne.

### Proponowana struktura (czysta, skalowalna)

```
ui/
├── dj_player_window.py          # ZOSTAJE, ale zostaje OBCIĘTY do ~250-350 linii (tylko orchestrator)
│
├── dj/                          # NOWY PAKIET (sub-package)
│   ├── __init__.py
│   ├── deck_controller.py       # KLUCZOWY: DeckController (QObject) – logika, stany, sygnały
│   ├── views/
│   │   ├── __init__.py
│   │   ├── base_deck_view.py    # Wspólna baza (opcjonalnie mixin lub ABC dla interfejsu)
│   │   ├── console_deck_view.py # DeckConsoleView – bogaty, 8 hotcue, EQ, pitch, full pro
│   │   ├── focused_deck_view.py # FocusedDeckView – tryb single, ogromny waveform + pady
│   │   ├── hotcue_pad.py        # HotcuePad (ulepszony, z custom label support)
│   │   ├── hotcue_grid.py       # HotcuePadGrid (zawsze 2×4, konfigurowalny rozmiar)
│   │   ├── waveform_section.py  # Waveform + beatgrid toggle + playhead label (kompozycja)
│   │   ├── transport_bar.py     # Duże przyciski PLAY/CUE/STOP + time
│   │   ├── pitch_control.py     # Pitch slider + range combo + value + keylock
│   │   ├── eq_strip.py          # 3-band vertical EQ z labelami
│   │   ├── mixer_strip.py       # Globalny (master vol, cue vol, crossfader z A/B)
│   │   └── memory_controls.py   # S / R buttons + stan
│   └── styles.py                # BOOTH_COLORS + get_deck_stylesheet() + get_pad_stylesheet(idx)
│
└── theme.py                     # (istniejący) – rozszerzony o booth tokens jeśli potrzeba
```

### DeckController (najważniejszy element refactoru)
- `class DeckController(QtCore.QObject):`
  - Posiada referencję do `playback_engine` i `deck_name: "A"|"B"`.
  - Wewnętrznie: `HotcueManager(max_cues=8)`, `_main_cue_ms`, `_quantize_enabled`, `_memory`, `_original_bpm`, `_is_synced`.
  - Emituje sygnały Qt (czysta komunikacja z view):
    - `track_loaded(Track)`
    - `playhead_changed(int ms)`
    - `hotcue_changed(int index, int|None time_ms)`
    - `bpm_changed(float|None)`
    - `loop_changed(int|None, int|None)`
    - `sync_state_changed(bool)`
    - `keylock_changed(bool)`
    - etc.
  - Metody publiczne: `load_track(track)`, `toggle_play()`, `seek(ms)`, `set_hotcue(index)`, `jump_hotcue(index)`, `set_pitch(pct)`, `set_trim(val)`, `set_eq(l,m,h)`, `toggle_quantize()`, `do_sync(other_controller)`, `save_memory()`, `recall_memory()`, `snap_to_beat(ms)`.
  - Obsługuje cały async waveform loading (wspólny `WaveformRunnable` + token logic) – **jedno miejsce**.
  - Obsługuje cały timer playhead (40ms) i dystrybucję do waveform.
  - Persystencja hotcue'ów – deleguje do istniejącego HotcueManager (zachowane).

**Zalety:** Każdy DeckConsoleView / FocusedDeckView dostaje **jeden** kontroler. W dual: dwa kontrolery (A + B) + jeden PlaybackEngine. W single: tylko kontroler A (FocusedDeckView). Sync między trybami = przekazanie referencji kontrolera lub prosty re-attach widoku.

**Brak duplikacji:** Cała logika `_load_waveform_async`, hotcue handling, sync, memory, quantize snapping, effective BPM – tylko w controllerze.

### Widoki prezentacyjne (dumb, ale piękne)
- `FocusedDeckView(QFrame)` i `DeckConsoleView(QFrame)` budują layout wyłącznie z małych widgetów (`self.transport = TransportBar(...)`; `self.hotcues = HotcuePadGrid(8, pad_size=(82,62))`).
- Connectują się do sygnałów kontrolera w `__init__` i wołają metody kontrolera z button clicked.
- Zero własnego stanu DJ poza czysto wizualnym (np. aktualny tekst na przycisku play).
- Różne layouty: Focused ma dużo stretch na waveform + centered transport cluster; Console ma klasyczny pro układ z EQ obok pitcha itp.

### Inne korzyści
- `HotcuePadGrid` i `HotcuePad` – jedna implementacja (rozszerzona o custom label w tooltipie i ewentualnie mały tekst na padzie).
- `WaveformWidget` zostaje prawie bez zmian (tylko ewentualnie minimalne API rozszerzenie).
- DJPlayerWindow staje się cienkim "shell": tworzy PlaybackEngine, dwa DeckController, dwa widoki (lub jeden), buduje globalny MixerStrip + crossfader, obsługuje drag&drop z main library (deleguje do controllerów), przełączanie trybów (teraz proste: ukryj jeden główny kontener, pokaż drugi – bez sync hacków, bo kontroler A jest wspólny).

**Tryby jako odrębne kontenery:**
- `self.single_container = FocusedDeckView(controller_a)`
- `self.dual_container = DualConsoleWidget(controller_a, controller_b, global_mixer)`
- Przełączanie = `single_container.setVisible(...)` + `dual_container.setVisible(...)` + ewentualnie resize policy. Zero kopiowania stanu.

---

## 4. Szczegółowy layout dla trybu Single ("Odtwarzacz")

**Cel wizualny:** Czysty, dominujący, "jeden utwór w centrum uwagi". Dużo powietrza. Wygląda jak dedykowany high-end odtwarzacz (Rekordbox Performance Mode lub standalone player).

**Hierarchia (QVBoxLayout na FocusedDeckView, margins: 24, 20, 24, 20, spacing: 20):**

```
┌────────────────────────────────────────────────────────────┐
│  [TRACK TITLE – 18px bold, stretch]          [BPM 34px 900] │  ← Header HBox (spacing 16)
├────────────────────────────────────────────────────────────┤
│                                                            │
│                 WAVEFORM WIDGET                            │
│                 (minHeight=260, stretch=7)                 │
│                 + wyraźny BPM-aware beatgrid               │
│                 + gruby playhead + glow                    │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                    0:00  /  4:12   (18px mono, center)     │  ← Time label (fixed, 0 stretch)
├────────────────────────────────────────────────────────────┤
│                                                            │
│   [CUE 78×52]     [▶ ODTWÓRZ  96×58]     [■ STOP 68×52]    │  ← Transport HBox (stretch 0, centered with stretches on sides)
│                                                            │
├────────────────────────────────────────────────────────────┤
│  PITCH  [====|====] +12.4%  [±16% ▼]     TRIM [========]   │  ← Controls HBox (spacing 22)
│         (duży slider 180px)                                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   1  2  3  4     ← 8 hotcue padów 2×4 (82×60) z kolorami   │  ← HotcuePadGrid (fixed height)
│   5  6  7  8                                             │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  KEY  |  Q  |  SYNC (opcjonalnie w single – małe)         │  ← Advanced row (compact, right aligned lub hidden by default)
└────────────────────────────────────────────────────────────┘
```

**Stretch factors:**
- Waveform: stretch 7 (dominuje)
- Header / Time / Transport / Controls / Hotcues / Advanced: stretch 0 (fixed natural size + padding)

**Różnice vs obecny:** Znacznie większy waveform, 8 padów zamiast 4, dużo więcej powietrza (marginesy 24px), centered transport cluster z wielkimi przyciskami, BPM ogromny w prawym górnym rogu. Brak EQ (lub collapsible advanced panel po prawej – opcjonalny w fazie 2).

---

## 5. Szczegółowy layout dla trybu Dual Console ("Konsola DJ")

**Cel wizualny:** Profesjonalna dwudeckowa konsola jak Rekordbox + DJM mixer. Oba decki widoczne jednocześnie, wyraźne A/B, pełna kontrola bez ukrywania.

**Dwie opcje (wybieramy jedną na implementację):**

**Opcja zalecana (najbardziej "Rekordbox-like" i czytelna):** Side-by-side (QHBoxLayout w DualConsoleWidget).

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────── DECK A (ConsoleDeckView) ────────────────┐  ┌────────────── DECK B ───────────────┐ │
│  │ DECK A          [Tytuł]                    128.4 BPM     │  │ DECK B          [Tytuł]                    132.0 BPM     │ │
│  │ ┌──────────────────────────────────────────────────────┐ │  │ ┌──────────────────────────────────────────────────────┐ │ │
│  │ │                  WAVEFORM (min 200px)                │ │  │ │                  WAVEFORM (min 200px)                │ │ │
│  │ │                  + mocny beatgrid                    │ │  │ │                  + mocny beatgrid                    │ │ │
│  │ └──────────────────────────────────────────────────────┘ │  │ └──────────────────────────────────────────────────────┘ │ │
│  │ [CUE] [▶] [■]   TRIM [====]   PITCH [==|==] 12% [±16%]   │  │ [CUE] [▶] [■]   TRIM [====]   PITCH [==|==] 12% [±16%]   │ │
│  │ KEY  SYNC  PFL  Q                                      │  │ KEY  SYNC  PFL  Q                                      │ │
│  │ LOW|MID|HI  (pionowe EQ 95px)                          │  │ LOW|MID|HI  (pionowe EQ 95px)                          │ │
│  │ ┌──────────────────────────────────────────────────────┐ │  │ ┌──────────────────────────────────────────────────────┐ │ │
│  │ │ 1 2 3 4                                              │ │  │ │ 1 2 3 4                                              │ │ │
│  │ │ 5 6 7 8   (8 dużych padów 78×56)                     │ │  │ │ 5 6 7 8   (8 dużych padów 78×56)                     │ │ │
│  │ └──────────────────────────────────────────────────────┘ │  │ └──────────────────────────────────────────────────────┘ │ │
│  │ S   R   (memory)    IN OUT LOOP                        │  │ S   R   (memory)    IN OUT LOOP                        │ │
│  └────────────────────────────────────────────────────────┘  └────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ A ████████████████████|████████████████████ B     CROSSFADER (32px)    │ │
│  │          MASTER VOL [========]     CUE VOL [====]   (MixerStrip)       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Opcja alternatywna (jeśli okno za wąskie):** Stacked (A nad B) + crossfader na samym dole – podobny do obecnego, ale z dużo większymi elementami i 24px+ spacing.

**W obu przypadkach:**
- Każdy deck to osobny `DeckConsoleView` (identyczny kod, dwa wystąpienia).
- Globalny `MixerStrip` (QFrame) na dole lub z boku: Master Volume, Headphone Cue Volume, ewentualnie Master EQ (jeśli backend wspiera), crossfader z dużymi etykietami "A" / "B" i wyraźną linią środka.
- Brak żadnych "Pokaż/Ukryj" toggle barów na dole – wszystko jest zawsze widoczne. Jeśli potrzeba więcej miejsca – okno się skaluje (QSplitter między deckami w side-by-side).

**Różnica wizualna między trybami:** Single = jeden wielki panel z ogromnym waveformem i centrowanymi elementami. Dual = dwa symetryczne, węższe panele z pełnym zestawem kontrolek (EQ zawsze widoczne).

---

## 6. Konkretny plan zmian plikowych

**Pliki do EDYCJI (nie kasowania):**
1. `ui/dj_player_window.py` – **radykalne obcięcie** (z 3520 → <400 linii). Zostaje:
   - Klasa `DJPlayerWindow` jako orchestrator.
   - Usunięcie wszystkich definicji DeckWidget, SinglePlayerView, HotcuePad (przeniesione).
   - Usunięcie COLORS (przeniesione do `ui/dj/styles.py`).
   - Usunięcie duplikatów utility (zostaje tylko importy).
   - Nowa logika: tworzenie 2× DeckController + FocusedDeckView / DualConsoleWidget.
   - Obsługa drag&drop z biblioteki (delegacja do controllerów).
   - Przełączanie trybów (proste visible switch + ewentualny resize).
   - Zachowanie publicznych API (`load_track_to_deck`, sygnały `deck_track_loaded` itd.) dla kompatybilności z `main_window.py`.

2. `ui/main_window.py` – minimalne zmiany (tylko jeśli nazwy klas się zmienią; sygnały zostają identyczne).

3. `ui/theme.py` – opcjonalnie: dodanie booth tokenów lub funkcji `get_booth_palette()`.

**Pliki do USUNIĘCIA / ZASTĄPIENIA (po migracji testów):**
- Żadne na początku – refaktoryzujemy inkrementalnie. Na końcu można usunąć stare klasy po pełnym teście.

**Pliki NOWE (tworzymy od zera – małe, testowalne):**
- `ui/dj/__init__.py`
- `ui/dj/styles.py` (BOOTH_COLORS + stylesheet helpers)
- `ui/dj/deck_controller.py` (główny ratunek przed duplikacją)
- `ui/dj/views/focused_deck_view.py`
- `ui/dj/views/console_deck_view.py`
- `ui/dj/views/dual_console_widget.py` (opcjonalnie – kontener na dwa console + mixer)
- `ui/dj/views/hotcue_pad.py` + `hotcue_grid.py`
- `ui/dj/views/transport_bar.py`
- `ui/dj/views/pitch_control.py`
- `ui/dj/views/eq_strip.py`
- `ui/dj/views/mixer_strip.py`
- `ui/dj/views/waveform_section.py` (opcjonalnie – wrapper na WaveformWidget + toggle)
- `ui/dj/views/memory_controls.py`

**Testy:**
- `tests/test_dj_hotcue_manager.py` – rozszerzyć o testy controller + nowe widoki (headless gdzie możliwe).
- Nowe testy UI smoke + manualne checklisty.

**Kolejność implementacji (dla Writer/Fixer):**
1. Stwórz `ui/dj/styles.py` + `deck_controller.py` (z pełnym portem logiki).
2. Stwórz małe widgety (HotcuePad/Grid, TransportBar itd.).
3. Zbuduj `FocusedDeckView` + `ConsoleDeckView` używając controller + małych widgetów.
4. Przepisz `DJPlayerWindow` na nowy model (dwa tryby jako osobne kontenery).
5. Usuń stary kod z `dj_player_window.py` (po zielonych testach).
6. Dostosuj min. rozmiary okna, style globalne.

---

## 7. Lista "Must Have" – elementy, które MUSZĄ być duże i wyraźne

1. **BPM** – 30-36px, weight 900, zawsze widoczny w prawym górnym rogu każdego decku (efektywny z pitch).
2. **Waveform** – minimum 220px wysokości (lepiej 260+), dominujący element wizualny, wyraźny muzyczny beatgrid (BPM-aware bars + beats).
3. **8 Hotcue padów na deck** – zawsze 2×4 grid, pady 78-82×58-64px, 8 unikalnych wysokokontrastowych kolorów, numery + miejsce na custom label.
4. **Crossfader** – szeroki (min 280-320px), wysoki 32-36px, wyraźne "A" i "B" z lewej/prawej + linia środka.
5. **Główne transport (PLAY / CUE / STOP)** – PLAY minimum 90×56px, pozostałe proporcjonalnie duże.
6. **Pitch slider + value** – długi slider + wielka, czytelna wartość procentowa.
7. **EQ 3-band** (w dual) – pionowe suwaki minimum 90-100px wysokości z wyraźnymi "LOW / MID / HI".
8. **Czas (position / duration)** – 16-18px monospace, zawsze czytelny.

Wszystko inne (KEY, SYNC, PFL, Q, Memory S/R, Loop IN/OUT) może być mniejsze, ale nigdy mniejsze niż 36-42px wysokości i z wyraźnym hover/active.

---

## 8. Propozycje nazw klas i plików

**Pakiet:**
- `ui/dj/` (lub `ui/views/dj/` jeśli wolimy płaską strukturę ui/ – zalecam `ui/dj/` dla jasności)

**Kluczowe klasy:**
- `DeckController` (ui/dj/deck_controller.py)
- `FocusedDeckView` (ui/dj/views/focused_deck_view.py)
- `ConsoleDeckView` (ui/dj/views/console_deck_view.py)
- `DualConsoleWidget` (ui/dj/views/dual_console_widget.py)
- `HotcuePad` (ui/dj/views/hotcue_pad.py) – ew. rozszerzenie istniejącego
- `HotcuePadGrid` (ui/dj/views/hotcue_grid.py)
- `TransportBar`
- `PitchControl`
- `EQStrip`
- `MixerStrip` (zawiera crossfader + master controls)
- `MemoryControls`
- `BoothStyles` / funkcje w `ui/dj/styles.py`

**Stare nazwy do deprecacji po migracji:**
- `DeckWidget` → zastąpiony przez `ConsoleDeckView`
- `SinglePlayerView` → zastąpiony przez `FocusedDeckView`
- Lokalne `HotcuePad`, `HotcueGrid`, `SectionLabel`, `WaveformRunnable` (część przeniesiona do kontrolera)

**Publiczne API do zachowania (dla main_window):**
- `DJPlayerWindow.load_track_to_deck(deck: str, track: Track)`
- Sygnały: `deck_track_loaded`, `deck_track_unloaded`, `all_stopped`

---

## 9. Checklist dla kolejnych agentów (Writer, Fixer, Tester)

**Dla AGENT 4 (Writer / Implementer):**
- [ ] Utwórz strukturę katalogów `ui/dj/views/` i pliki zgodnie z sekcją 6.
- [ ] Zaimplementuj `DeckController` jako pierwsze – przenieś 100% logiki z DeckWidget + SinglePlayerView (waveform token logic, snap_to_beat, memory, sync helpers, hotcue DB bridge via istniejący manager).
- [ ] Stwórz `styles.py` z pełną paletą + helperami stylesheet (zero inline w widokach).
- [ ] Zbuduj małe widgety od najprostszych (HotcuePad/Grid, TransportBar).
- [ ] Zaimplementuj `FocusedDeckView` + `ConsoleDeckView` używając kompozycji + connect do kontrolera.
- [ ] Przepisz `DJPlayerWindow` – usuń stare klasy, dodaj dwa kontrolery + dwa widoki + prosty switch.
- [ ] Zachowaj wszystkie istniejące skróty klawiszowe (Ctrl+1..8 dla hotcue).
- [ ] Upewnij się, że drag&drop z library_widget działa identycznie.
- [ ] Po każdej większej zmianie uruchamiaj: `LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py`

**Dla AGENT 5 (Fixer / Refactor Cleaner):**
- [ ] Usuń wszystkie duplikaty kodu po pełnej migracji (stare metody _load_waveform_async itp.).
- [ ] Ujednolić nazewnictwo sygnałów i metod między controller a view.
- [ ] Usuń wszystkie back-compat aliasy (`_hotcues`, `_sync_hotcues_alias`) jeśli nie są już używane nigdzie poza testami.
- [ ] Przenieś ewentualne resztki waveform runnable do kontrolera lub core/.
- [ ] Zaktualizuj docstringi i komentarze REFACTOR.
- [ ] Sprawdź, czy `ui/theme.py` może zastąpić część styles.py (lub odwrotnie).

**Dla Testera / QA (ręczny + automatyczny):**
- [ ] **Must-have wizualne:** Otwórz w trybie Single → sprawdź czy waveform ≥220px, BPM ≥30px, 8 dużych hotcue padów bez nakładania, dużo wolnej przestrzeni, brak zachodzenia elementów.
- [ ] Przełącz na Dual Console → oba decki widoczne, crossfader duży i wyraźny, EQ i pitch w pełni czytelne, pady 8 na każdy deck.
- [ ] Załaduj utwór → sprawdź waveform + beatgrid (BPM-aware), hotcue set/jump/delete (z persystencją po restarcie), Memory S/R.
- [ ] SYNC + Quantize + KEY + pitch changes – sprawdź, czy nie psują waveformu ani hotcue'ów.
- [ ] Crossfader A↔B → głośność decków zmienia się poprawnie (słuchaj + wizualnie na volume_slider).
- [ ] Drag & drop z głównej biblioteki do obu decków w obu trybach.
- [ ] Skróty Ctrl+1..8 działają w obu trybach.
- [ ] Resize okna (szerokie/wąskie/wysokie) – brak ucinania, rozsądne stretch.
- [ ] Smoke test + pytest `tests/test_dj_hotcue_manager.py` + `tests/test_playback_backend.py` + `tests/test_ui_smoke.py`.
- [ ] Ręczne testy w warunkach "booth" (zmniejsz jasność ekranu, sprawdź czytelność z 1m).
- [ ] Sprawdź, czy nie ma regresji w integracji z MainWindow (now playing indicators, load z playlisty).

**Kryteria sukcesu (definicja done):**
- Plik `dj_player_window.py` < 450 linii.
- Zero istotnej duplikacji między widokami decków.
- Użytkownik nie może zgłosić "zachodzą na siebie" ani "za gęsto".
- Wszystkie istniejące funkcje działają identycznie lub lepiej.
- Kod jest przyjemny w czytaniu i rozszerzaniu.

---

**AGENT 3 – UI Designer – ZAKOŃCZONY. Czekam na przekazanie do AGENT 4 (Writer).**