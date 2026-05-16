# Checklist — Lumbago Music AI (Stan projektu)

> Wygenerowano: 2026-04-28. Aktualizacja: 2026-05-16. Obejmuje wszystkie cztery aplikacje: Desktop, Web MVP, tagerv2 i WinUI 3.

## Legenda
- [x] zrobione
- [ ] do zrobienia
- [~] pominięte / odłożone
- **P0** krytyczne · **P1** ważne · **P2** nice-to-have

---

## 1. Desktop App (`lumbago_app/`)

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

## 2. Web MVP (`web/`)

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
- [ ] (P1) Integration test: import → zapis → odczyt przez API
- [ ] (P1) Test przepływu UI (Import Wizard krok 1→4)
- [ ] (P2) Test `DuplicateFinderModal` (UI + API)

### 2.4 Brakujące funkcje Web MVP
- [x] (P1) Edycja tagów przez API webowy — TrackEditPanel (kliknięcie na track, pola edycji, PUT /tracks)
- [x] (P1) Zapis tagów do pliku audio przez backend — PUT /tracks/{path} wywołuje write_tags() w Mutagen
- [ ] (P2) Paginacja wyników `/tracks` (przy dużych bibliotekach)
- [ ] (P2) Autoryzacja / zabezpieczenie API

---

## 3. tagerv2 (`tagerv2/`)

### 3.1 Core
- [x] Standalone — brak backendu, dostęp do plików przez File System Access API
- [x] State w `localStorage` (pliki + playlisty)
- [x] `useLibrary` — lista plików, playlisty, sort/filter
- [x] `useAIProcessing` — batch enrichment przez Gemini
- [x] `useSettings` — API keys, preferences
- [x] `services/aiService.ts` — Gemini + Grok + OpenAI (client-side)
- [x] `services/cacheService.ts` — cache wyników AI
- [x] `services/geminiService.ts` — native Gemini API calls

### 3.2 UI komponenty
- [x] Pełny zestaw komponentów (TrackTable, TrackGrid, Sidebar, PlayerDock, FilterBar, itp.)
- [x] SmartTaggerModal — batch AI tagging
- [x] EditTagsModal, BulkEditModal, RenameModal
- [x] DuplicateResolverModal
- [x] XmlConverterModal
- [x] SmartPlaylistModal
- [x] MediaBrowser, DirectoryConnect, FileDropzone
- [x] Dashboard z statystykami biblioteki
- [x] Tailwind CSS + dark/light mode

### 3.3 Utilities
- [x] `utils/audioUtils.ts` — odczyt ID3 (browser)
- [x] `utils/csvUtils.ts` — eksport CSV
- [x] `utils/djUtils.ts` — Camelot mapping, BPM utils
- [x] `utils/duplicateUtils.ts` — wykrywanie duplikatów
- [x] `utils/filenameUtils.ts` — wzorce renamingu
- [x] `utils/sortingUtils.ts`, `utils/stringUtils.ts`

### 3.4 Jakość kodu i testy
- [ ] (P0) `npm run lint` przechodzi bez ostrzeżeń (max-warnings 0)
- [ ] (P1) Unit testy dla kluczowych utilities (aiService, duplicateUtils, djUtils)
- [ ] (P1) Testy vitest dla hook `useLibrary` i `useAIProcessing`

### 3.5 Brakujące funkcje
- [ ] (P1) Zapis tagów z powrotem do pliku audio (File System Access API + ID3 writer)
- [ ] (P2) Eksport playlisty do Rekordbox/VirtualDJ XML (pełny flow)
- [ ] (P2) PWA / offline support
- [~] Backend / serwer — nie w zakresie (browser-only by design)

---

## 4. WinUI 3 Rewrite (ToDo2.md — Etap 6-10)

> Nowy UI na Windows, planowany jako następna iteracja po obecnym PyQt6.

### 4.1 Decyzje i architektura
- [x] Styl: „neon glass" / WinUI 3
- [x] Makiety wszystkich widoków (v1 + v2 w `docs/winui3/previews/`)
- [x] Theme.xaml, App.xaml, strony (`docs/winui3/`)
- [x] Decyzja o modelu integracji UI ↔ logika — lokalny HTTP 127.0.0.1 (FastAPI) — patrz `docs/winui3/ipc_decision.md`
- [x] Definicja zakresu MVP nowego UI — Library, Start, Settings + ApiClient + BackendLauncher

### 4.2 Implementacja
- [x] Szkielet aplikacji WinUI 3 (shell, nawigacja, routing) — `winui/LumbagoWinUI/` (18 plików; wymaga VS 2022 + Windows App SDK workload do kompilacji)
- [x] Widok Biblioteki (lista + siatka + filtry + detail panel) — przełącznik lista↔siatka, filtry Gatunek/Tonacja/BPM, panel edycji tagów, PUT /tracks/{path} w backend
- [x] (P1) Import, Duplikaty, Konwerter XML — ImportPage (FolderPicker + podgląd + commit), DuplicatesPage (3 tryby + karty grup + usuwanie), ConverterPage (Rekordbox→VirtualDJ); backend: DELETE /tracks/{path} + POST /convert/rekordbox-to-virtualdj
- [x] (P1) Smart Tagger — strona AI z kolejką analizy, podglądem decyzji per pole i zatwierdzaniem (POST /analysis/jobs, polling, apply)
- [x] (P1) Globalny odtwarzacz (dock) — play/pause/seek/prev/next, autoplay kolejki, czas pozycji
- [x] (P1) Podłączenie danych z logiką (tracki, playlisty, tagi)
- [x] (P1) Akcje masowe i edycje w UI — BulkEditDialog (multi-select Ctrl+klik, checkboxy per pole, batch PUT /tracks)
- [x] (P1) Integracja AI Taggera i kolejek

### 4.3 Testy i dokumentacja WinUI 3
- [ ] (P1) Testy UI kluczowych flow
- [ ] (P1) Testy dostępności (WCAG)
- [ ] (P2) Testy wydajności listy przy >10k tracks
- [ ] (P1) Aktualizacja `Build2.md`
- [ ] (P2) Checklist testu na czystym Windows (nowy UI)

---

## 5. Infrastruktura i CI/CD

- [x] Desktop CI (`desktop-ci.yml`) — pytest Ubuntu + Windows + build PyInstaller
- [x] Web CI (`web-ci.yml`) — warunkowy build frontendu
- [x] CodeQL (`codeql.yml`) — security scanning (Python + JS/TS)
- [x] CLAUDE.md — dokumentacja dla AI assistants
- [ ] (P2) Automatyczne testy E2E (Playwright/Cypress)
- [ ] (P2) Coverage report w CI
- [ ] (P2) Automatyczny release do GitHub Releases po tagu

---

## 6. Priorytety natychmiastowe (P0/P1 pending)

> Stan na 2026-05-16. Testy: 95 passed / 1 failed (`test_autotag_rewrite::test_unified_autotagger_picks_best_candidate`) / 1 skipped.

| # | Zadanie | Komponent | Priorytet | Stan |
|---|---------|-----------|-----------|------|
| 1 | `npm run lint` bez błędów w tagerv2 | tagerv2 | P0 | ⏳ |
| 2 | Zapis tagów do pliku audio (browser, tagerv2) | tagerv2 | P1 | ⏳ |
| 3 | ~~Decyzja: model integracji WinUI 3 ↔ logika~~ | Desktop rewrite | P0 | ✅ |
| 4 | Integration testy Web API | Web MVP | P1 | ⏳ |
| 5 | Test na czystym Windows (PyInstaller build) | Desktop | P1 | ⏳ |
| 6 | ~~Edycja tagów przez Web API~~ | Web MVP | P1 | ✅ |
| 7 | Naprawić failing test: `test_unified_autotagger_picks_best_candidate` | Desktop | P1 | ⏳ |
