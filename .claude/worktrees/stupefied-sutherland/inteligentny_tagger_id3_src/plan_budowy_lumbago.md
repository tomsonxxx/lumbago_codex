# **Plan Budowy Systemu Lumbago Music AI**
## **z priorytetem: Przeglądarka Biblioteki Multimediów**

---

# **1. Cel projektu**
Celem projektu jest stworzenie kompletnego, nowoczesnego i modularnego systemu **Lumbago Music AI**, w którym centralnym elementem staje się **Przeglądarka Biblioteki Multimediów** (Library Browser). To główne okno aplikacji, służące jako punkt wyjścia dla wszystkich funkcji, narzędzi i modułów sztucznej inteligencji.

---

# **2. Główne założenia projektu**
- Przeglądarka Biblioteki Multimediów stanowi **podstawowy widok**, widoczny od momentu uruchomienia aplikacji.
- Wszystkie moduły poboczne (np. Tagger AI, Duplicate Finder, XML Converter) działają jako **modale lub panele nakładkowe** otwierane bez opuszczania głównego widoku.
- Interfejs może bazować na makietach z dokumentu *Blueprint* lub czerpać inspiracje z najpopularniejszych aplikacji, takich jak: Rekordbox, iTunes, Serato DJ Pro czy Traktor.
- Moduł pełni funkcję **centrum zarządzania biblioteką**, integrując funkcje audio, analizy AI oraz narzędzia organizacyjne.

---

# **3. Zakres funkcjonalny przeglądarki biblioteki**
### **Widoki i elementy UI:**
- Widok listy utworów (Track List) — tabela z kluczowymi metadanymi.
- Widok siatki (Artwork Grid) — miniatury okładek albumów.
- Globalna wyszukiwarka (Search Bar).
- Filtry zaawansowane (BPM, tonacja, gatunek, ocena, data dodania).
- Lewy panel z sekcjami: Playlists, Sources, Favorites.
- Prawy panel informacji o utworze (Track Info Panel).
- Pasek narzędzi (Import, Scan, Tag AI, Duplicate Finder, Rename, Convert XML).
- Dock Player z waveformem oraz obsługą hot-cue i metadanych.
- Drag & drop do playlist.
- Kontekstowe menu (PPM) dla tracków i playlist.

---

# **4. Rozszerzony plan wdrożenia**
Poniższy harmonogram został uzupełniony o nowy priorytet — stworzenie Przeglądarki Biblioteki Multimediów na wczesnym etapie projektu.

## **Faza 0: Bootstrap projektu**
- Inicjalizacja backendu (FastAPI).
- Inicjalizacja frontendu (React + Vite).
- Konfiguracja Tailwind, Zustand i React Router.
- Przygotowanie środowiska Docker (Postgres, Redis).

## **Faza 1: Przeglądarka Biblioteki Multimediów (PRIORYTET 1)**
- Stworzenie podstawowego layoutu: lewy panel, główne okno, panel szczegółów, dolny odtwarzacz.
- Implementacja TrackList z paginacją, sortowaniem i dynamicznym układem kolumn.
- Implementacja TrackGrid (widok artworków).
- System filtrowania + globalne wyszukiwanie.
- Widok szczegółów utworu (Track Info).
- Integracja startowych modali powiązanych z biblioteką.

## **Faza 2: Import & Scanner**
- Wybór źródła folderów.
- Wczytywanie metadanych przy użyciu Mutagen.
- Raporty błędów i logowanie skanowania.

## **Faza 3: Smart Tagger AI**
- Analiza BPM, tonacji, gatunku i nastroju.
- Panel Accept/Reject dla sugerowanych metadanych.
- Pełna integracja z widokiem biblioteki.

## **Faza 4: Duplicate Finder**
- Obsługa trzech metod: hash, tag-based, fingerprint.
- Interfejs w formie modalnego okna nakładkowego.

## **Faza 5: XML Converter (Rekordbox ↔ VirtualDJ)**
- Parser i generator plików XML.
- Zaawansowane mapowanie pól.

## **Faza 6: Player & Waveform**
- Obsługa odtwarzania audio.
- Hotcues, waveform preview.
- Pitch i Key Lock.

## **Faza 7: Playlist Intelligence**
- Sugestie AI dotyczące kolejności utworów.
- Wizualizacja energii i BPM.

## **Faza 8: Crate Digger Mode**
- Wyszukiwanie podobnych utworów.
- Dopasowania na podstawie analizy akustycznej.

## **Faza 9: Cloud Sync**
- Synchronizacja, backup, panel historii wersji.

## **Faza 10: Renamer, Export, Mobile Port**
- Narzędzia masowej zmiany nazw.
- Eksport biblioteki.
- Port mobilny (Android, Jetpack Compose).

---

# **5. Inspiracje UI (opcjonalne)**
- **Rekordbox 6** — zaawansowany panel boczny i tracklist.
- **Serato DJ Pro** — widok waveformów i kontrolki.
- **iTunes/Music** — klasyczna lista i filtracja.
- **Traktor Pro** — system paneli i filtrowania.

---

# **6. Docelowy efekt końcowy**
Przeglądarka Biblioteki Multimediów staje się centralnym, zawsze aktywnym widokiem aplikacji. Wszystkie pozostałe moduły działają jako nakładki, co zapewnia płynny workflow oraz spójne doświadczenie użytkownika.

---

# **7. Legenda — najważniejsze pojęcia techniczne**
| Termin          | Znaczenie                                               |
|-----------------|----------------------------------------------------------|
| **Library Browser** | Główne okno wyświetlające utwory i metadane            |
| **TrackList**       | Widok tabelaryczny z informacjami o utworach           |
| **Grid View**       | Widok miniatur okładek albumów                         |
| **Dock Player**     | Stały odtwarzacz audio umieszczony na dole aplikacji   |
| **Modal**           | Nakładkowe okno dialogowe bez opuszczania widoku       |
| **Overlay**         | Pełnoekranowy modal obsługujący zaawansowane funkcje   |
| **Filtering**       | System filtrowania po metadanych                       |

---

Dokument został uporządkowany, doszlifowany stylistycznie i przygotowany jako spójny plan realizacji projektu.


---

# **8. Lokalna Czeklista Startowa**
Lista zadań do natychmiastowego rozpoczęcia automatycznej budowy projektu.

## **Backend (FastAPI)**
- [ ] Utworzyć strukturę katalogów backendu
- [ ] Zainicjalizować projekt FastAPI
- [ ] Skonfigurować Poetry lub pip + venv
- [ ] Dodać pierwsze endpointy: `/health`, `/version`
- [ ] Przygotować modele Pydantic (User, Track, Playlist)
- [ ] Skonfigurować PostgreSQL + SQLAlchemy + Alembic
- [ ] Utworzyć migracje baz danych
- [ ] Dodać obsługę logów i wyjątków

## **Frontend (React + Vite)**
- [ ] Utworzyć projekt Vite React/TS
- [ ] Skonfigurować Tailwind + design tokens
- [ ] Dodać React Router + podstawowy routing
- [ ] Stworzyć layout aplikacji (topbar, leftbar, content, player)
- [ ] Przygotować komponenty UI: Button, Panel, Modal
- [ ] Skonfigurować Zustand (globalne store)

## **Przeglądarka Biblioteki Multimediów (priorytet)**
- [ ] Stworzyć `LibraryBrowser.tsx`
- [ ] Dodać TrackList (tabela)
- [ ] Dodać TrackGrid (okładki)
- [ ] Dodać panel filtrowania BPM/Key/Genre
- [ ] Dodać panel szczegółów utworu
- [ ] Dodać wyszukiwarkę globalną
- [ ] Zintegrować Dock Player z biblioteką

## **Integracja API**
- [ ] Połączyć frontend z backendem (axios + React Query)
- [ ] Dodać obsługę logowania + tokenów
- [ ] Dodać pobieranie danych: tracks, playlists
- [ ] Obsłużyć upload tracków

## **Modale funkcjonalne**
- [ ] Smart Tagger AI (podstawowy szkielet)
- [ ] Duplicate Finder (UI modal)
- [ ] XML Converter (UI modal)
- [ ] Import Wizard

## **Usprawnienia i automatyzacja**
- [ ] Skonfigurować Docker do dev environment
- [ ] Skonfigurować docker-compose
- [ ] Dodać automatyzację buildów (GitHub Actions)
- [ ] Dodanie ESLint + Prettier

---

# **9. Start Automatycznego Pisania Projektu**
Automatyczne generowanie projektu można rozpocząć od **Fazy 0**, zgodnie z checklistą powyżej. Kolejne działania będą rozwijane krok po kroku na bazie tej listy, generując:

- strukturę katalogów,
- pliki startowe backendu i frontendu,
- komponenty UI,
- API i modele,
- integracje,
- modale i widoki.

System będzie sukcesywnie dopisywał kolejne elementy zgodnie z priorytetami projektu.

## **ETAP 3 – Import & Wstępna Analiza Plików**
Dodano:
- Drag & Drop plików.
- Wybór źródła (Local / External / Cloud).
- 4‑etapowy Import Wizard (Choose → Scan → Preview/Auto‑Fix → Import).
- Wykrywanie uszkodzonych plików.
- Automatyczną analizę nazw plików (Artist – Title, Remix, BPM, Key, Year).
- Podgląd waveformu i okładki (placeholder).
- Oznaczanie braków metadanych.
- Przygotowanie do analizy AI.

## **ETAP 4 – AI Tagger (Mock) + Integracja**
Dodano:
- Moduł backendowy `ai_tagger` z funkcją `analyze_metadata`.
- Mockowe klasyfikatory: Genre, Mood, Energy, Confidence.
- Automatyczne sugerowanie BPM/Key.
- Endpointy `/api/ai/analyze` i `/api/ai/enrich`.
- Modal frontendowy **AIEnrichModal** z Accept/Reject.
- Symulację działania AI (`simulate_ai.py`).

Projekt jest gotowy do dalszej integracji AI oraz rozbudowy pracy workerów.

## **ETAP 5 – Integracja Workerów, Kolejek Zadań i Pełna Automatyzacja Analizy AI**
Dodano plan i zakres prac:
- Uruchomienie Celery jako głównego systemu kolejkowania zadań.
- Osobny **AI Worker** do obsługi ciężkich analiz audio: ekstrakcja feature’ów, BPM/Key, embeddings.
- Endpoint `/api/ai/job/start` zwracający `job_id` oraz `/api/ai/job/status` z postępem.
- System progresu w UI (real-time progress bar): 10% → 40% → 70% → 90% → 100%.
- Obsługa błędów workerów (timeout, file unreadable, failed analysis).
- Bufor wyników w Redis + auto-clean po 24h.
- Integracja z Import Wizard: automatyczne wysyłanie nowo dodanych utworów do kolejki AI.
- Integracja z Library Browser: status „Analyzing…” w TrackList i pod „i” w detail panel.
- Plan podłączenia prawdziwego modelu audio (Essentia/CLAP/ONNX) na późniejszym etapie.


## **ETAP 6 – Usprawnienia Wszystkich Funkcji + Pełny Pipeline Waveform/Artwork/UX**
Wprowadzone globalne usprawnienia:

### **1. Usprawnienia interfejsu (UI/UX)**
- Spójny motyw neon/cyber w całej aplikacji (kolory, grubości, promienie, animacje).
- Ujednolicone modale: Import, AI Tagger, Duplicate Finder, Metadata Panel.
- Dodanie skeletonów ładowania (tracklist, grid, detail panel).
- Usprawnienie paginacji i sortowania w TrackList.
- Lepszy debounce wyszukiwania globalnego (300 ms).
- Ujednolicone ikony i tooltipy.
- Responsywność poprawiona pod pełny zakres urządzeń.

### **2. Usprawnienia Import Wizard**
- Drag&drop z podświetleniem i stanami hover/active.
- Inteligentniejsza analiza folderów: wykrywanie albumów, struktur katalogów.
- Zaawansowany Auto-Fix: poprawa kodowania znaków, whitespace fixing, normalizacja tytułów.
- Prezentacja wykrytych błędów z kolorami priorytetu (warning/error/info).
- Panel „Insights”: BPM/Key/Mood jeśli tagi istnieją.

### **3. Wstępna analiza metadanych (rozszerzona)**
- Bardziej precyzyjne rozpoznawanie remixów, editów, extended wersji.
- Rozpoznawanie BPM/Key w wielu formatach (np. 124 BPM, 124bpm, 124.0 BPM).
- Wykrywanie roku w wielu wariantach (folder/year, tytuł, tagach ID3).
- Kolorowe odznaki brakujących pól.

### **4. Waveform Pipeline (pełny)**
- Generowanie waveformu PNG z niskiej i wysokiej rozdzielczości.
- Generowanie JSON waveform data do animacji.
- Cache’owanie waveformów przy imporcie.
- Wyświetlanie mini-waveformów w TrackGrid i TrackList.
- Podgląd realtime w TrackDetailPanel.

### **5. Artwork Pipeline**
- Podstawowy: ID3 -> APIC extraction.
- Fallback: folder.jpg / cover.png.
- Auto-resize i konwersja do WebP.
- Placeholder neon „no-artwork”.
- Ujednolicenie proporcji artworków do 1:1.

### **6. Przeglądarka Biblioteki (Library Browser) – ulepszenia**
- Lepszy system filtrów (zakres BPM, tonacja, gatunek, tagi AI).
- Dostępne od razu informacje: BPM/Key/Genre/Mood.
- TrackDetailPanel z mini-playerem i stations: waveform, metadata, AI.
- Kontekstowe menu z opcjami: Add to playlist, Analyze AI, Duplicate Scan.

### **7. Integracja z AI (poprawiona)**
- AI Tagger działa płynnie z Import Wizard.
- Widok „AI Pending” w bibliotece.
- Podgląd confidence score w UI.
- API `/api/ai/analyze` i `/api/ai/enrich` przystosowane do integracji z workerami (ETAP 5).

### **8. Przygotowanie do ETAP 7 – Pełnej Analizy Audio i Modeli ML**
- Cała struktura projektu dostosowana pod podpięcie prawdziwych modeli AI.
- Gotowy interfejs wejściowy/wyjściowy dla AI.
- Placeholders i mocki mogą zostać zastąpione 1:1 backendem ML.
- Koordynacja pipeline'ów: IMPORT → AI → LIBRARY → PLAYLISTS.

