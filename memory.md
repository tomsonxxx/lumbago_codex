# Memory — Lumbago Music AI (DJ Player Project)

**Data ostatniej aktualizacji:** Maj 2026 (po dużym sprzątaniu repozytorium)  
**Cel pliku:** Pełna, trwała pamięć projektu — wszystko co zostało omówione, zbudowane, naprawione i postanowione od początku pracy nad DJ Playerem.

---

## 1. Podstawowe zasady komunikacji

- **Język:** Użytkownik kategorycznie wymaga, żeby **wszystko** (odpowiedzi, wyjaśnienia, podsumowania) było po polsku. Od pewnego momentu sesji padło wyraźne: „rozmawiamy tylko po polsku”.
- Użytkownik często resetuje sesje ("zamknij sesję i uruchom nową") i oczekuje, że AI będzie pamiętało kontekst dzięki temu plikowi.
- Styl pracy: użytkownik często mówi „dalej”, „do końca”, „nie pytaj co chwila”, „sam sukcesywnie podejmuj decyzje”, „poprawiaj błędy”.

---

## 2. Chronologiczna historia pracy nad DJ Playerem (główny temat sesji)

### Faza 1 – Początek (żądanie pełnego, profesjonalnego playera)
- Użytkownik zażądał stworzenia **kompletnego, niezależnego dual-deck DJ Playera** w osobnym oknie.
- Wymagania: 4 lub 8 hotcue’ów z pełną persystencją w bazie, duży waveform z beatgridem (BPM-aware), 3-pasmowy EQ, crossfader, Volume, Pitch, Loop In/Out, KEY, SYNC (z fazą), PFL, Quantize, Master + HP Cue, Memory Save/Recall, Recent History per deck.
- Silna integracja z biblioteką (drag&drop, menu kontekstowe, wskaźniki „teraz gra w playerze”).
- Dwa tryby w jednym oknie: **„Odtwarzacz”** (single) i **„Konsola DJ”** (dual).
- Użytkownik wielokrotnie podkreślał, że player ma być „osobnym ciałem”, nie bazować na starym wbudowanym odtwarzaczu (`ui/player_widget.py` został uznany za deprecated).

### Faza 2 – Iteracje UI i walka o czytelność (najdłuższa i najbardziej emocjonalna część)
Użytkownik był bardzo wymagający co do jakości interfejsu:
- Wielokrotne narzekania: „okno jest kompletnie nie czytelne”, „ikony zachodzą na siebie”, „za gęsto”, „wszystko zachodzi na siebie i przykrywa jedno przez drugie”, „tryb pojedynczy jest podwójny!!!”.
- Prośby o większe pady hotcue, większe czcionki, więcej powietrza, styl „booth” / Rekordbox.
- Kilka rund przeprojektowywania układu (marginesy, spacingi, rozmiary padów 72×52 → 88×58 → 92×60 itd.).
- Na pewnym etapie użytkownik poprosił: **„zatrudnij agenta do projektowania UI który od nowa zaprojektuje okno dj playera kopiując rozwiązania UI programu rekordbox”**.
- Powstały dwa tryby w jednym oknie z przełącznikiem (SinglePlayerView + DeckWidget dual).

### Faza 3 – Ciężka praca nad stabilnością i błędami („poprawiaj błędy”)
Użytkownik wielokrotnie wracał do tematu naprawiania błędów ładowania i odtwarzania:
- Krytyczne bugi:
  - `QThreadPool.start(worker)` gdzie worker był funkcją → TypeError (naprawione przez `WaveformRunnable` + token).
  - Backendy ustawiały `self._enabled = False` po błędzie → deck na zawsze zablokowany.
  - Duplikacja metod cue_points w `repository.py`.
  - Zepsute wiązanie przycisku „Wczytaj plik…” w Single view.
  - Desynchronizacja hotcue’ów i main cue przy przełączaniu trybów Single ↔ Console.
  - Brak `vol_val` w SinglePlayerView → crash przy zmianie głośności.
- Użytkownik wybierał ścieżki napraw (np. „b” = głęboka naprawa synchronizacji hotcue’ów między trybami).
- Powtarzające się polecenia: „poprawiaj błędy”, „testuj wszystko na gotowo”, „dalej”.

### Faza 4 – Wzmocnienie architektury Playback
- Stworzenie solidnego `PlaybackEngine` + warstwowych backendów (VLC jako priorytet).
- Poprawki w `_NoopAudioBackend`, żeby testy DJ działały nawet bez VLC.
- Dodanie instalacji VLC w GitHub Actions (`desktop-ci.yml`).

### Faza 5 – Dokończenie spójności modelu danych (ostatnie duże zadanie)
- Nowe pola w `Track`: `albumartist`, `composer`, `publisher`, `tracknumber`, `discnumber`, `isrc`, `grouping`, `copyright`.
- Problem: pola były w dataclassu i w ORM, ale nie były kopiowane w `_TRACK_META_FIELDS` w `repository.py` → `AttributeError` i tracone dane.
- Naprawione w `data/repository.py` + wypchnięte.

---

## 3. Kluczowe decyzje architektoniczne

- **DJ Player jako całkowicie osobne okno** (nie integrujemy go głęboko ze starym player widgetem).
- **Dwa tryby w jednym oknie** z możliwością przełączania (Single + Dual Console).
- **PlaybackEngine** jako czysta warstwa logiki (niezależna od UI).
- Priorytet backendów audio: **VLC → QtMultimedia → Noop**.
- Hotcue’e przechowywane wyłącznie w tabeli `cue_points` (pełny CRUD w repository).
- Przy przełączaniu trybów staramy się robić lekką synchronizację stanu zamiast pełnego przeładowania tracka (`_sync_deck_a_state_between_views`).
- Używanie `QThreadPool + QRunnable` do ciężkich operacji (waveform extraction).
- Wszystkie zapisy do bazy tylko przez `data/repository.py`.

---

## 4. Najważniejsze problemy i ich rozwiązania (dla przyszłych sesji)

| Problem | Objawy | Rozwiązanie |
|--------|--------|-----------|
| Desynchronizacja hotcue’ów przy zmianie trybu | Hotcue’e znikały lub nie działały po przełączeniu Single ↔ Console | Lepsza funkcja `_sync_deck_a_state_between_views` + odświeżanie waveformu i padów |
| Crash przy ładowaniu waveformu | `TypeError: QThreadPool.start() argument 1 must be QRunnable` | Wprowadzenie `WaveformRunnable` z tokenem ścieżki |
| Backend blokował się na zawsze | Po błędzie ładowania deck nie chciał już nic odtwarzać | Usunięcie `self._enabled = False` z `_set_error()` w backendach |
| Testy DJ padały w CI | Brak VLC → noop nie pamiętał rate/loop | Ulepszenie `_NoopAudioBackend` + skipy w testach wymagających realnego audio |
| Brakujące pola Track po wczytaniu z bazy | `AttributeError: 'Track' object has no attribute 'albumartist'` | Uzupełnienie `_TRACK_META_FIELDS` w repository |
| Bardzo zła czytelność UI | „Ikony zachodzą”, „za gęsto”, „tryb pojedynczy jest podwójny” | Wiele iteracji layoutu + prośba o redesign w stylu Rekordbox |

---

## 5. Aktualny stan (maj 2026)

**Co działa dobrze:**
- Pełny, profesjonalny DJ Player z dwoma trybami
- 4/8 hotcue’ów z persystencją
- Waveform + muzyczny beatgrid
- Memory, SYNC z fazą, Quantize, Recent History
- Stabilne ładowanie i odtwarzanie (VLC jako główny backend)
- Dobra integracja z biblioteką
- CI z automatyczną instalacją VLC + odporne testy

**Co jest w miarę stabilne, ale może wymagać dalszej pracy:**
- Synchronizacja stanu między trybami (działa, ale warto monitorować przy dalszych zmianach)
- Czytelność UI (użytkownik był bardzo wymagający – przy kolejnych zmianach warto od razu sprawdzać feedback)

**Otwarte / potencjalne tematy na przyszłość:**
- Rysowanie markerów hotcue’ów bezpośrednio na waveformie
- Jeszcze lepsze komunikaty błędów przy problemach z plikami audio
- Pełniejsze testy integracyjne całego playera z biblioteką
- Ewentualne dodatkowe opcje zaawansowane (np. więcej kontroli nad loopami, beatjump itd.)

---

## 6. Jak korzystać z tego pliku w nowych sesjach

1. Na początku nowej rozmowy poproś AI o przeczytanie `memory.md`.
2. AI powinno od razu przełączyć się na język polski.
3. Przed większymi zmianami lub na koniec sesji – aktualizuj ten plik.
4. Najważniejsze jest zachowanie:
   - Historii decyzji (dlaczego coś zrobiliśmy tak, a nie inaczej)
   - Bolesnych lekcji (jakie błędy się powtarzały)
   - Feedbacku użytkownika (szczególnie negatywnego – to one napędzały największe poprawy)

---

**Ten plik ma być „pamięcią instytucjonalną” projektu.** Im bardziej szczegółowy i szczery będzie, tym łatwiej będzie kontynuować pracę po resetach sesji.

---

## 7. Duże sprzątanie repozytorium (maj 2026)

Na żądanie użytkownika przeprowadzono gruntowne porządki:

- Usunięto wszelkie ślady starych wersji:
  - Web MVP (FastAPI + React / Vite)
  - tagerv2 (standalone React tagger)
  - Plany migracji na WinUI 3
- Usunięto: vercel.json, docs/recovery_tagerv2_*.md oraz kilka tymczasowych skryptów debugujących z roota.
- Wyczyszczono requirements.txt (usunięto fastapi, uvicorn, httpx).
- Naprawiono pliki konfiguracyjne .claude/ (launch.json, settings.local.json) – usunięto stare konfiguracje webowe i odniesienia do nieistniejącej struktury `lumbago_app/`.
- Zaktualizowano dokumentację (README, user_guide.md, memory.md), aby jasno komunikować, że projekt jest wyłącznie desktopowy (PyQt6).
- Repozytorium jest teraz czyste i skupione wyłącznie na aplikacji desktopowej + DJ Playerze.

Po sprzątaniu zweryfikowano:
- Struktura: core/, data/, services/, ui/, tests/, main.py na poziomie głównym.
- Brak folderów web/react/winui.
- Testy przechodzą (141 passed).
- Aplikacja uruchamia się poprawnie.