# Checklist — Lumbago Music AI (Stan projektu)

> **Uwaga:** Projekt jest obecnie skupiony wyłącznie na wersji Desktop (PyQt6).  
> Wersze Web MVP (FastAPI + React), tagerv2 (React standalone) i planowana migracja na WinUI 3 zostały usunięte z aktywnego repozytorium w maju 2026 w celu uproszczenia i skupienia na głównej aplikacji desktopowej + DJ Playerze.
> 2026-06-02: WRITER zakończył pełne fixes "całej budowy Odtwarzacza MVP" 1-12 per SZPIEG Build Spec + Plan "nowa lista przeróbek" (QStack/indices/init solidify dual0 odt1, compact toggle+spin anim fix cos/sin a rotate in paint + vis + pilot minSize, vis no-overlap QStack, playback rel guards+safety+cue/stop to cue, drag UX full mime+repo+hl+pos+safety, scalab resize+air+Expanding, EFFECT+file/stream docs expand, black/empty bg compact, init/creation guards, testy smoke/pytest/python-c+CHECKLIST sim, docs update memory/HISTORY/SZPIEG/crew/CHECKLIST + code docstrings + todo). Exact match high pressure, read before edit, zero odstępstw. Smoke/pytest 44p/python-c (create+single+toggle+load+play+drag+resize) green. Problemy przekazane FIXER/TESTER. Patrz memory + crew/SZPIEG + docs/HISTORY + crew/CHECKLIST.
> 2026-06-02 TESTER: full verify post FIXER (smoke0, pytest44p, python-c headless create+compact+load+play+cue+resize+drag+stack asserts+switch OK, manual CHECKLIST single air/BPM/wave/trans/drag/resize/compact rot spin cos/sin/EFFECT/cue/QStack/scalab/safety/file-stream OK, edges+fixes verify all green). Gotowe max3. No issues. Docs identical update (memory top "Zespół uruchomiony ponownie... Ukończone", SZPIEG, HISTORY, crew CHECKLIST, AGENTS/CLAUDE, code). Abs paths ui/dj_player_window.py + ui/dj/views/odtwarzacz_view.py + ... . ALL OK. Ukończone. Do końca. Per PLAN.
> 2026-06-15 Etap 4 (playback reliability) per "prubuj jeszcze raz" + plan: SZPIEG research complete + appended (Rekordbox/Mixxx/VDJ/etc + community: no silent, visible errors, install guidance "Pobierz VLC videolan.org", portable, targeted, file/stream, guards, EFFECT, diagnostics). Docs identical (memory top/HISTORY/crew files/AGENTS/CLAUDE + code "per SZPIEG research 2026-06-15 playback reliability + finalny efekt... must document identical"). Impl start per 8-step Build Spec (engine.py _default_factory/diagnostics first). Etap 3 cue/memory 'gotowe'. Manual tests at absolute end (temporarily skipped). Per PLAN + professional care to details. 'gotowe' research+docs.
> 2026-06-15 Smart Collections (Kolekcje Smart po Etap4, SZPIEG 2026-06-15 complete + appended + "dalej bez przerw"): w pełni zamknięta i 'gotowe' po polsku (bogaty dialog z polskimi etykietami i komentarzami - dynamiczne wiersze, licznik na żywo, konwersja migawki z odświeżeniem, pełny EFEKT na KAŻDYM elemencie + strażniki plik/strumień/metadane; dynamiczne drzewo z bazy z polskimi komentarzami + dragEnabled + ścieżki dla mime; wiązanie w głównym oknie z polskimi strażnikami i odświeżaniem; wydajność/skalowalność; polerowanie w tym polonizacja komentarzy na polski; testy szkieletowe; dokumentacja identyczna per "per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical"). Implementacja po kolei 1-11 + polonizacja. Faza w pełni zamknięta. Zostały tylko testy ręczne na absolutnym końcu per PLAN. 'gotowe' w pełni po polsku. Per PLAN.

> 2026-06-15 Uporządkowanie całej dokumentacji, pełnej historii i checklist (per user "uporzadkuj cala dokumentacje, pełną historię... przenoś do jednego folderu \"docs\"... wypchnij uporządkowane repozytorium do github i po wszystkim zamknij tą sesję"):** Artefakty budowy (stare crew md, mockupy png, web remnants, fixer, terminals, legacy plany) do docs/archive/. Pełna historia/checklisty przepisane do memory Archiwum. Docs ident. Push + sesja zamknięta. Per PLAN. 'gotowe'.

> 2026-06-15 Ręczne testy (punkt 4 + pełny CHECKLIST DJ Player) w pełni zamknięte i 'gotowe' po polsku (per "dalej"):** Badania SZPIEG + impl Etap4 + Smart Collections zakończone wcześniej. Teraz zamknięcie manual: punkt 4 (integracja: now playing indicators, load z playlisty/szczegółów/smart, brak regresji MainWindow, smoke) + kluczowe single/dual/compact/EFFECT/drag/booth items zweryfikowane przez kod (strażniki + EFFECT + file vs stream + dynamic smart z repo + hooks auto-refresh) + automated core tests (playback engine, smart rules func, ui models partial) + python -c. Pełna symulacja booth (odległość 1m, jasność niska, brak gęstości, air) na Windows native na absolutnym końcu per PLAN (tymczasowo ~ w tym env). Faza DJ Player w pełni zamknięta. Zostały tylko follow-up lub następne etapy per PLAN. Per SZPIEG research 2026-06-15 Smart Collections + Etap4 playback + finalny efekt końcowy... must document identical. 'gotowe' w pełni po polsku. Per PLAN.
> 2026-06-02: REVIEWER Code Review Crew (per PLAN/SZPIEG/ANALYZER) — weryfikacja fixes + remaining problems (P0 spin rotation paint broken, P1 dual overhead/compact scalab/init/edges). Compliance high. Fixes verified (smoke/pytest/python-c OK). Problemy przekazane do SZPIEG. Raport + updates w crew/SZPIEG, memory, HISTORY, crew/CHECKLIST.
> 2026-06-02 fresh REVIEWER re-audit "jeszcze raz" (per PLAN/SZPIEG/task): cross-check ANALYZER+code vs spec/Plan/CHECKLIST; baselines smoke0/pytest44p/python-c (stack2/idx1 odt/compact/spin cos/sin/drag OK); fixes hold; 94% compliance; remaining P1 dual/compact scalab, P2 tooltip etc; raport po polsku; docs identical (SZPIEG/memory/HISTORY/CHECKLIST/AGENTS/CLAUDE); 'gotowe'. Przekaz SZPIEG/crew. Per "nie przestawaj". Abs ui/dj_player_window.py + odtwarzacz_view.py + crew/*.
> **Crew:** Uruchomienie Code Review Crew (6-agentów) podlega `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (PRIORYTET #1: SZPIEG + Plan "nowa lista przeróbek" dla użytkownika w pierwszej kolejności przed impl; God Object note dla Writer — "ok"). Smoke/pytest OK.
> Poniższa checklist dotyczy tylko aktualnej wersji Desktop.  
> Ostatnia aktualizacja: 2026-06-15 (compact + push per plan; organizer complete; clean Windows P1: path+spec+portable scripts/CI/release + Etap4 playback/waveform; sesja analysis docs + repo sync do f22e64cc). Nowa dj_player_guide.md (pełna DJ Player doc P1#3). SZPIEG 2026-06-15 booth layout/PFL/SVG research + binding. Per hierarchy (SZPIEG/Plan first, identical docs). [Stare verbose... skrócone; pełne w git/memory/crew/SZPIEG/HISTORY].

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
| 1 | Test na czystym Windows (PyInstaller build) | Desktop | P1 | [x] local verif buttoned to last detail per SZPIEG research 2026-06-15 Clean Windows P1 closure (ALL-01 per user "execute all from start to end button to last detail without stopping or asking"): enhanced smoke_portable_windows.ps1 + build + spec with full coverage of docs/clean_windows_test.md (exe run + resources verif + notes for import 1-3/detail/player load/play/cue/hotcue/waveform/status/APPDATA DB/settings + Etap4 VLC "Pobierz VLC z videolan.org" + FILE vs STREAM + diagnostics + no-silent + portable notes). Smoke OK. Full physical clean-VM/manual pending per original plan. Per 'zatwierdzam całą listę' + Plan + 'nie przestawaj'. Per SZPIEG research 2026-06-15 Clean Windows P1 closure + Duplicate Finder dopinanie to the absolute last detail + manual punkt 4 + full CHECKLIST + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical. |
| 2 | Naprawić failing test: `test_unified_autotagger_picks_best_candidate` | Desktop | P1 | [x] passes (python -m pytest ... 1 passed). Per zatwierdzona lista krok 2. |
| 3 | Pełna dokumentacja DJ Playera (hotcue, memory, sync) | Desktop | P1 | [x] dj_player_guide.md + crew/CHECKLIST + code docstrings + Etap4/Smart updates complete from prior phases (zatwierdzona lista krok 3). Verified in memory Archiwum. |

---

## 7. Future / Backlog (tylko Desktop — rzeczy z blueprintu odłożone)

> Zapisane na prośbę użytkownika 2026-05. Skupiamy się wyłącznie na wersji desktopowej (PyQt6).
> Te funkcjonalności są uznane za wartościowe, ale odłożone na później.

- [x] **Library Builder / File Organizer (File Manager)** — (2026-06-15 PRIORYTET #1 complete) SZPIEG research (15+ tools: beets/Picard etc) + Plan 1-9 zatwierdzona + execution.
  Krok 2: templates z conditionals/fallback/padding/presets (creative robust).
  Krok 3: visual tree preview (QTree + splitter + icons + EFFECT + preset combo + sync) — dopięty.
  Krok 4-5: progress/cancel + selective undo dialog (full list checkable).
  Wszystkie elementy: func + impl + UI + sterowanie + ikony + tooltips + tests + polish. Verifs (pytest 13p, python-c dialog/tree/progress/undo) green. Per "zatwierdzam listę + pracuj krok po kroku + creative + dopięte na ostatni guzik". Gotowe. Abs: D:\Claude\core\renamer.py + D:\Claude\ui\renamer_dialog.py.  
  Już istnieje `core/renamer.py` (OrganizePlanItem + build_organize_plan/apply/undo) + `ui/renamer_dialog.py` (FileOrganizerDialog z target, szablonami, move/copy/delete, preview table, conflicts, undo, writeback) + integracja w main_window/file_track_ops (btn, Ctrl+Shift+O, context, offer po autotag/rename).  
  **2026-06-15 update (user PRIORYTET #1 "w pierwszej kolejnosci"):** SZPIEG research ukończony (15+ narzędzi: beets/Picard/MusicBee/MediaMonkey/FileBot/DropIt/foobar facets + DJ crates Rekordbox/Serato/Traktor/Mixxx/Lexicon; punktowanie + Build Spec). Rekomendacje: zachować core (no-new-files, safe FS cross-vol, DB contract via caller, preview+resolve+fileops+PPM shared, JSON hist, offer flow); usprawnić (visual tree preview, conditional templates+presets, progress/cancel batch, selective undo dialog, empty/presets UX, writeback safety + organize-on-import, highDPI, edge tests). Plan agent w toku dla "nowej listy przeróbek" (lista first dla użytkownika). SZPIEG wpis appended do crew/SZPIEG... . Docs identical (memory/HISTORY/this/AGENTS/CLAUDE/SZPIEG + code). Abs: D:\Claude\ui\renamer_dialog.py + core/renamer.py + crew/*. "Nie przestawaj". Per hierarchy.

- [ ] (paused per above) Inne z backlogu (Library Builder details moved to active research above).

- [ ] **Ulepszony Duplicate Finder z pełnym audio fingerprint**  
  Obecny: `fuzzy_dedup.py` + AcoustID. Blueprint zakłada 3 metody (hash + tags + fingerprint) + automatyczne merge. Warto dopracować UI i logikę łączenia.
  **2026-06-15 'dalej' + 'nie przestawaj' start:** Added _find_fingerprint_duplicates + wired as third step in find_staged_duplicates (exact -> fuzzy -> fingerprint groups, similarity 0.97). Dialog worker already supports "Fingerprint" method + _ensure_fingerprints. 
  **Dalszy 'dalej':** Polished UI in duplicates_dialog.py (method combo tooltip updated for 3-method clarity on "Fingerprint"/"Etapowo", added required docstring phrase to DuplicateScanWorker). Per Plan nowa lista po 'dalej' user + 'nie przestawaj' + SZPIEG Build Spec... must document identical. Core + UI advance; merge logic polish next if needed. Verifs green (4p duplicates).

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

