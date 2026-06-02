# Checklist — Lumbago Music AI (Stan projektu)

> **Uwaga:** Projekt jest obecnie skupiony wyłącznie na wersji Desktop (PyQt6).  
> Wersje Web MVP (FastAPI + React), tagerv2 (React standalone) i planowana migracja na WinUI 3 zostały usunięte z aktywnego repozytorium w maju 2026 w celu uproszczenia i skupienia na głównej aplikacji desktopowej + DJ Playerze.  
> Poniższa checklist dotyczy tylko aktualnej wersji Desktop.  
> Wygenerowano: 2026-04-28. Ostatnia aktualizacja po sprzątaniu: 2026-05.

## Legenda
- [x] zrobione
- [ ] do zrobienia
- [~] pominięte / odłożone
- **P0** krytyczne · **P1** ważne · **P2** nice-to-have

---

## 1. Desktop App (PyQt6)

### 1.1 Fundamenty i infrastruktura
- [x] Struktura projektu (`core/`, `data/`, `ui/`, `services/`)
- [x] `requirements.txt`, `pyproject.toml`, `.env.example`
- [x] Ikona aplikacji (`assets/icon.ico`, `icon.svg`)
- [x] Konfiguracja z priorytetami: `settings.json` → env → Windows Registry
- [x] Fallback danych do `.lumbago_data/` gdy brak uprawnień do `%APPDATA%`
- [x] Logi: `startup.log`, `app.log`, `crash.log`, `qt.log`
- [x] Tryb bezpieczny (`LUMBAGO_SAFE_MODE=1`)
- [x] Tryb smoke (`LUMBAGO_SMOKE_SECONDS=N`)

### 1.2 Baza danych
- [x] Modele domenowe (`core/models.py`): `Track`, `Playlist`, `Tag`, `AnalysisResult`, `CuePoint`, `BeatMarker`, `AudioFeatures`, `WatchFolder`
- [x] SQLAlchemy ORM (`data/schema.py`) z indeksami i constraints
- [x] Repository pattern — jedyny punkt zapisu/odczytu DB (`data/repository.py`)
- [x] Migracje inline (auto `ALTER TABLE` dla brakujących kolumn)
- [x] Migracje Alembic (`migrations/`) — drugoplanowe
- [x] Tabela settings, change_log, metadata_cache
- [x] Cache metadanych z TTL (SQLite)

### 1.3 Import i skan
- [x] Skan folderu rekurencyjny (`.mp3 .flac .m4a .mp4 .wav .ogg .aac .aiff`)
- [x] Import Wizard (4 kroki, batch commit, anulowanie, raport błędów)
- [x] Import z Rekordbox / VirtualDJ XML
- [x] Odczyt tagów Mutagen (ID3, Vorbis, MP4, AIFF)
- [x] Odczyt z nazw plików i struktury katalogów
- [x] Odczyt z `.cue`, `folder.json`, sidecar `.json`

### 1.4 Library Browser (UI)
- [x] Sidebar (narzędzia + playlisty)
- [x] Header (search, filtry, view toggle)
- [x] TrackList — sort, resize kolumn, kontekstowe menu (PPM)
- [x] TrackGrid — okładki, placeholder, animacje
- [x] Detail Panel — podgląd + edycja tagów + zapis
- [x] Detail Panel — okładka + zmiana + historia zmian
- [x] Bulk Edit dialog (akcje na wielu plikach)

### 1.5 Player i Waveform
- [x] Odtwarzacz QtMultimedia (play/pause/seek)
- [x] Seek bar + licznik czasu
- [x] Hotcues (Cue A/B) + pętla A-B
- [x] Waveform (generowanie librosa/ffmpeg + cache)

### 1.6 AI Tagger (hybryda)
- [x] Lokalny tagger (heurystyki BPM → mood/energy)
- [x] Cloud AI: Gemini (natywne API), OpenAI/Grok/DeepSeek (OpenAI-compatible)
- [x] Merge wyników: `ai_tagger_merge._merge_analysis_into_track()` — nie nadpisuje istniejących
- [x] UI: Accept/Reject zmian per wiersz + zbiorcze
- [x] Zapis AI tagów do DB z oznaczeniem źródła
- [x] Pomijanie wywołania chmury gdy nie ma brakujących pól
- [x] Walidacja BPM/Key/energy + confidence score

### 1.7 Rozpoznawanie i metadane
- [x] AcoustID / Chromaprint (fpcalc)
- [x] MusicBrainz + Discogs provider
- [x] Cover Art Archive (pobieranie okładek)
- [x] Kolejka rozpoznawania z workerem
- [x] Batch uzupełnianie metadanych (AcoustID → MusicBrainz → Discogs)
- [x] Tryby walidacji: `strict` / `balanced` / `lenient`
- [x] Filtr kompilacji (odrzucanie "Greatest Hits" przy albumie studyjnym)

### 1.8 Analizy audio
- [x] Analiza loudness (LUFS) i normalizacja
- [x] Beatgrid + auto-cue (intro/outro) z cache
- [x] Auto-key detection z mapowaniem Camelot
- [x] Audio features (MFCC, spectral centroid, danceability, valence)

### 1.9 Duplikaty
- [x] Hash duplicate finder
- [x] Tag-based duplicate finder (title + artist + duration)
- [x] Fingerprint duplicate finder (AcoustID)
- [x] Fuzzy dedup (`rapidfuzz`)
- [x] UI: grupy + akcje (Keep/Delete/Merge) + eksport CSV

### 1.10 Renamer
- [x] Wzorce renamingu (konfigurowalne regexy)
- [x] Preview zmian z wykrywaniem konfliktów
- [x] Undo

### 1.11 XML Converter
- [x] Parser Rekordbox XML
- [x] Generator VirtualDJ XML
- [x] Mapowanie pól + tryb dry-run + log zmian

### 1.12 Playlisty
- [x] CRUD playlist w sidebarze
- [x] Drag & drop z gridu do playlisty
- [x] Reorder tracków
- [x] Smart playlists (rules-based)
- [x] Eksport playlisty → VirtualDJ XML

### 1.13 Inne funkcje
- [x] Auto-backup bazy i ustawień (start/wyjście)
- [x] Historia zmian tagów (audit log / `ChangeLogOrm`)
- [x] Watch folder (model i schema `WatchFolderOrm`)

### 1.14 Packaging
- [x] PyInstaller spec (`pyinstaller.spec`) — onedir + EXE
- [x] Bundle `fpcalc.exe` z `tools/`
- [x] Portable ZIP
- [~] Test na czystym Windows — odłożony na prośbę
- [x] Checklist testu czystego Windows (`docs/clean_windows_test.md`)

### 1.15 Testy
- [x] Unit testy (renamer, duplikaty, XML, walidacja)
- [x] Integration test (import → DB → odczyt)
- [x] UI smoke test (subprocess, SAFE_MODE)
- [x] `pytest.ini` izolujący testy do `tests/`
- [ ] (P2) Test na czystym Windows (fizyczna maszyna lub VM)

### 1.16 UX / UI polish
- [x] Zaokrąglony UI + animowane przyciski (`AnimatedButton`)
- [x] Animacje przejść lista ↔ siatka
- [x] Skróty klawiszowe + tooltips + polskie etykiety
- [x] Motyw `cyber` + design tokens (`assets/themes/`)

---

## 2. Wersje historyczne (usunięte z repozytorium w maju 2026)

Wersje Web MVP, tagerv2 i WinUI 3 zostały całkowicie usunięte z aktywnego kodu w celu uproszczenia projektu. Poniżej jedynie krótka notatka historyczna.

**Web MVP (FastAPI + React)** — prototyp webowy z backendem FastAPI i frontendem React/Vite. Usunięty.

**tagerv2 (React standalone)** — samodzielna aplikacja React do tagowania. Usunięta.

**WinUI 3** — planowana pełna migracja UI na WinUI 3 (C#). Usunięta z planów na rzecz dalszego rozwoju PyQt6 Desktop + DJ Player.

Szczegóły historyczne znajdują się w `docs/HISTORY.md` i `RECOVERY.md`.

### 2.1 Backend FastAPI
- [x] `web/backend/api.py` — FastAPI app
- [x] Reuse `lumbago_app.data` (ten sam SQLite co desktop)
- [x] Własna lekka DB (`web_backend.sqlite3`) — settings, cache, tag_history
- [x] Migracje raw SQL (`web/backend/migrations/0001_core_tables.sql`)
- [x] Endpointy: `GET /health`, `GET|PUT /settings/{key}`, `GET|PUT /cache/{key}`, `POST /tag-history`
- [x] Endpointy: `GET /tracks`, `POST /tracks/import-preview`, `POST /tracks/import-commit`
- [x] Endpoint: `POST /duplicates/analyze` (hash / fingerprint / metadata)

### 2.2 Frontend React
- [x] `App.tsx` — biblioteka, search, filtr key, player
- [x] `web/src/api/client.ts` — jedyny plik API klienta
- [x] `AudioPlayer` — odtwarzacz
- [x] `ImportWizardModal` — 4-krokowy import
- [x] `DuplicateFinderModal` — grupy + akcje
- [x] `web/src/utils/camelot.ts` — mapowanie Camelot ↔ klucz muzyczny
- [x] `web/src/utils/filterTracks.ts` — filtrowanie biblioteki
- [x] Deployment na Vercel (`vercel.json`)
- [x] CI (`web-ci.yml`) — warunkowy na zmiany `web/**`

### 2.3 Testy Web
- [x] `web/tests/camelot.test.ts` — unit test mapowań Camelot (vitest)
- [x] (P1) Integration test: import → zapis → odczyt przez API
- [x] (P1) Test przepływu UI — filterTracks unit tests (vitest)
- [ ] (P2) Test `DuplicateFinderModal` (UI + API)

## 5. Infrastruktura i CI/CD

- [x] Desktop CI (`desktop-ci.yml`) — pytest na Windows + build PyInstaller
- [x] CodeQL (`codeql.yml`) — security scanning (Python)
- [x] CLAUDE.md — dokumentacja dla AI assistants
- [x] vercel-plugin (manifesty .claude-plugin/ itp. w repo) + minimalna warstwa Next.js (`app/`, vercel.json framework nextjs, SpeedInsights) — wyłącznie dla kompatybilności deployu na Vercel i wsparcia agentów (Claude/Cursor/Codex) skillsami Vercel/Next.js. Nie jest to pełna aplikacja web (stara web MVP usunięta).
- [ ] (P2) Automatyczne testy E2E (Playwright/Cypress)
- [ ] (P2) Coverage report w CI
- [ ] (P2) Automatyczny release do GitHub Releases po tagu

---

## 6. Priorytety natychmiastowe (P0/P1 pending)

> Stan po sprzątaniu repozytorium (maj 2026). Skupienie wyłącznie na wersji Desktop (PyQt6 + DJ Player). Stare wersje (Web MVP, tagerv2, WinUI 3) usunięte.

| # | Zadanie | Komponent | Priorytet | Stan |
|---|---------|-----------|-----------|------|
| 1 | Test na czystym Windows (PyInstaller build) | Desktop | P1 | ⏳ |
| 2 | Naprawić failing test: `test_unified_autotagger_picks_best_candidate` | Desktop | P1 | ⏳ |
| 3 | Pełna dokumentacja DJ Playera (hotcue, memory, sync) | Desktop | P1 | ⏳ |

---

## 7. Future / Backlog (tylko Desktop — rzeczy z blueprintu odłożone)

> Zapisane na prośbę użytkownika 2026-05. Skupiamy się wyłącznie na wersji desktopowej (PyQt6).
> Te funkcjonalności są uznane za wartościowe, ale odłożone na później.

- [ ] **Library Builder** — kreator struktury folderów według szablonu (`{genre}/{year}/{artist}/{album}`).  
  Już istnieje `core/renamer.py` + import wizard — zrobić jako osobny "Library Organizer".

- [ ] **Ulepszony Duplicate Finder z pełnym audio fingerprint**  
  Obecny: `fuzzy_dedup.py` + AcoustID. Blueprint zakłada 3 metody (hash + tags + fingerprint) + automatyczne merge. Warto dopracować UI i logikę łączenia.

- [ ] **Metadata Auto-Complete w tle (batch mode dla całej biblioteki)**  
  Już częściowo zaimplementowane przez `BackgroundEnrichmentService` + `AnalysisJob` + `BackgroundAutotagWorker`.  
  Do rozbudowy: lepsza wizualizacja postępu, ręczne uruchamianie dla całej biblioteki, raporty.

- [ ] **Waveform Color Coding** — kolorowanie waveformu według charakteru dźwięku  
  (🔴 kick/bass, 🟡 hi-hat/percussion, 🟢 wokale, 🔵 breakdown).  
  Wymaga dobrego playera + dodatkowej analizy spektralnej.

- [ ] Inne potencjalne rzeczy z blueprintu warte rozważenia później (tylko desktop):
  - Bardziej zaawansowane Smart Collections (rule engine z AND/OR)
  - Playlist Intelligence (sortowanie wg harmonic mixing + energy flow)
  - Crate Digger / "Find Similar Tracks"
  - Export Manager zoptymalizowany pod CDJ / XDJ / Engine Prime
  - Lepsze wsparcie cue points / memory points w DB i UI

