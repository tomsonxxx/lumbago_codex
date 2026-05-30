# Memory — Lumbago Music AI

**Data ostatniej aktualizacji:** 2026-05 (po sesji z DJ Playerem + naprawami CI/testów)

---

## 1. Ogólny stan projektu

Lumbago Music AI to aplikacja desktopowa (PyQt6) do zarządzania biblioteką muzyczną dla DJ-ów i kolekcjonerów.

- **Główny entry point:** `python main.py`
- **Główny fokus ostatnich miesięcy:** Profesjonalny, niezależny **DJ Player** (dual-deck) w osobnym oknie, wzorowany na Rekordbox / Traktor / Serato.
- Język komunikacji z AI: **zawsze po polsku** (użytkownik kategorycznie tego wymaga).

---

## 2. Najważniejsza funkcjonalność — DJ Player (stan na maj 2026)

### Architektura
- **DJPlayerWindow** (`ui/dj_player_window.py`) — główne okno z przełączaniem trybów:
  - **"Odtwarzacz"** (SinglePlayerView) — czysty, czytelny single-deck
  - **"Konsola DJ"** — pełny dual-deck (A/B) + crossfader, top mixer, EQ, 4/8 hotcue'ów
- **PlaybackEngine** (`services/playback/engine.py`) — abstrakcja dual-deck
  - Priorytet: **VlcAudioBackend**
  - Fallback: **QtAudioBackend**
  - Ostatnia deska ratunku: **_NoopAudioBackend** (dla CI i środowisk bez audio)
- **WaveformWidget** — waveform z beatgridem muzycznym (BPM-aware), playhead, loop region
- **Hotcue** — pełna persystencja w bazie (tabela `cue_points`), 4 lub 8 padów, kolory, right-click clear
- Zaawansowane funkcje:
  - Quantize (Q)
  - SYNC z dopasowaniem fazy
  - Memory Save/Recall (S/R) per deck
  - Recent History (ostatnie 8 utworów na deck)
  - Pełna integracja z biblioteką (drag & drop, menu kontekstowe "Załaduj do Deck A/B", wskaźniki ▶A / ▶B w tabeli)

### Kluczowe poprawki z ostatniej sesji
- Naprawiona synchronizacja hotcue'ów i stanu między trybami Single ↔ Console (wcześniej dochodziło do desynchronizacji przy szybkim przełączaniu).
- Naprawione crashe: `vol_val`, błędne wiązanie przycisku "Wczytaj plik..." w Single view.
- Poprawione bezpieczne ładowanie waveformu (WaveformRunnable + token zamiast funkcji).
- Ulepszony `_NoopAudioBackend` — teraz pamięta rate/keylock/loop (testy DJ nie padają w CI bez VLC).
- Dodano instalację VLC w GitHub Actions (`desktop-ci.yml`) — prawdziwe testy playbacku w CI.
- Uzupełniono `_TRACK_META_FIELDS` w `data/repository.py` (brakowało `albumartist`, `composer`, `publisher` itd.) — naprawiło wiele testów z nowymi polami Track.

---

## 3. Baza danych i modele

- **Domain models:** `core/models.py` (czysty dataclass `Track`, `CuePoint`, `AnalysisResult` itd.)
- **ORM:** `data/schema.py` (`TrackOrm` i inne)
- **Repozytorium:** `data/repository.py` — jedyne miejsce do odczytu/zapisu (nigdy bezpośredni dostęp do Session z UI)
- Nowe pola Track (albumartist, composer, publisher, tracknumber, discnumber, isrc, grouping, copyright) zostały dodane zarówno do modelu, jak i do bazy + mechanizmów kopiowania.

---

## 4. Testy i CI

- **Desktop CI** (`.github/workflows/desktop-ci.yml`):
  - Windows + Python 3.11
  - `pip install -e .`
  - Od maja 2026: automatyczna instalacja VLC (żeby testy DJ Playera używały prawdziwego backendu)
  - Testy playbacku są teraz odporne na brak VLC (noop fallback + odpowiednie skipy)
- Kluczowe testy DJ: `tests/test_playback_backend.py`
- Smoke test: `LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py`

---

## 5. Ważne konwencje i decyzje

- **Język:** Wszystkie odpowiedzi i komunikacja z użytkownikiem — **po polsku**.
- **DJ Player** jest całkowicie oddzielnym oknem (nie bazuje na starym `ui/player_widget.py`, który jest deprecated).
- Przy przełączaniu trybów Single ↔ Console staramy się unikać pełnego reloadu tracka (używamy `_sync_deck_a_state_between_views`).
- Wszystkie zapisy hotcue'ów idą przez `save_cue_point` / `delete_cue_point` z repository.
- `AnalysisResult` → `Track` zawsze przez `ai_tagger_merge._merge_analysis_into_track()` (nie nadpisujemy istniejących wartości bez powodu).
- Nie mieszamy domain models (`core/models.py`) z ORM (`data/schema.py`).

---

## 6. Co jest stabilne / co wymaga uwagi (maj 2026)

**Stabilne / gotowe:**
- Podstawowa architektura DJ Playera (engine + backendy)
- UI w dwóch trybach (po wielu iteracjach czytelności)
- Hotcue 4/8 + persystencja
- Memory S/R, Recent, SYNC, Quantize
- Integracja z biblioteką
- CI z VLC + odporne testy

**Ostatnio naprawione:**
- Desynchronizacja hotcue'ów między trybami
- Błędy ładowania i crashe w Single view
- Brakujące pola Track w mechanizmach repository
- Testy DJ Playera w środowisku bez VLC

**Możliwe kolejne tematy (do potwierdzenia z użytkownikiem):**
- Dalsze polerowanie UI DJ Playera (jeśli użytkownik zgłosi problemy z czytelnością)
- Dodanie waveform markers dla hotcue'ów bezpośrednio na waveformie
- Pełniejsze testy integracyjne DJ Playera
- Ewentualne usprawnienia w obsłudze błędów backendu audio

---

## 7. Jak zaczynać nową sesję

1. Otwórz `memory.md` i przeczytaj sekcje 1–6.
2. Sprawdź aktualny stan: `git status` + `git log --oneline -5`
3. Jeśli użytkownik powie "rozmawiamy tylko po polsku" — od razu przełącz się na polski.
4. Najważniejsze aktualne zadanie z ostatniej sesji: **DJ Player** (dual-deck, Rekordbox-style).

---

**Plik memory.md ma służyć jako trwała pamięć między sesjami.** Aktualizuj go po większych zmianach lub na koniec sesji.