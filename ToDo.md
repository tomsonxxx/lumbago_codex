# ToDo — Lumbago Music AI (Python/Windows)

## Legenda
- [ ] do zrobienia
- [x] zrobione
- [~] pominięte

## Priorytety
- **P0** — krytyczne (MVP)
- **P1** — bardzo ważne
- **P2** — ważne
- **P3** — nice-to-have

## Estymacje (orientacyjne)
- **S**: 1–3h
- **M**: 4–8h
- **L**: 1–2 dni
- **XL**: 3–5 dni

---

# Sprint 0 — Fundamenty (P0/P1)
- [x] (P0, S) Utworzyć strukturę projektu (`core/`, `data/`, `ui/`, `services/`)
- [x] (P0, S) Dodać `requirements.txt`
- [x] (P0, S) Dodać `README.md`
- [x] (P1, S) Dodać `.env.example`
- [x] (P2, S) Dodać ikonę aplikacji
- [x] (P1, M) Dodać `pyproject.toml` (opcjonalnie)

# Sprint 1 — Baza i Import (P0)
- [x] (P0, M) Modele domenowe + schema SQLite
- [x] (P0, M) Repozytorium: init, upsert, list, update
- [x] (P0, M) Import Wizard (4 kroki)
- [x] (P1, M) Batch commit co N plików
- [x] (P1, S) Raport błędów importu
- [x] (P1, M) Anulowanie importu w trakcie

# Sprint 2 — Library Browser (P0/P1)
- [x] (P0, M) Sidebar + Header + Layout
- [x] (P0, M) TrackList: sort + resize
- [x] (P0, M) TrackGrid + placeholder + mini-waveform
- [x] (P1, S) Detail Panel (podgląd)
- [x] (P1, M) Detail Panel edycja tagów + zapis
- [x] (P1, M) Okładka w detail + zmiana okładki
- [x] (P2, S) Kontekstowe menu na liście

# Sprint 3 — Player & UX polish (P1)
- [x] (P1, S) Podstawowy player
- [x] (P1, S) Placeholder waveform w detail
- [x] (P1, M) Seek bar + czas odtwarzania
- [x] (P2, M) Hotcues + loop
- [x] (P1, S) Zaokrąglony UI + animowane przyciski
- [x] (P2, M) Animacje przejść między widokami
- [x] (P2, S) Tooltips i ikony
- [x] (P2, S) Skróty klawiszowe

# Sprint 4 — AI & Metadata (P1/P2)
- [x] (P1, S) Lokalny tagger (heurystyki)
- [x] (P1, S) UI ustawień API (Grok/DeepSeek/OpenAI)
- [x] (P1, M) Cloud AI realne wywołania
- [x] (P2, M) Panel Accept/Reject zmian
- [x] (P2, M) Zapis AI tagów do DB
- [x] (P1, M) Kolejka rozpoznawania
- [x] (P1, M) Uzupełnianie metadanych (batch)
- [x] (P2, M) Pobieranie okładek

# Sprint 5 — Duplikaty, Renamer, XML (P1/P2)
- [x] (P1, M) Hash duplicate finder
- [x] (P1, M) Tag-based duplicate finder
- [x] (P1, M) Fingerprint duplicate finder
- [x] (P2, M) UI: grupy + akcje (Keep/Delete/Merge)
- [x] (P2, S) Raport eksportu
- [x] (P1, M) Renamer: wzorce + preview + konflikty + undo
- [x] (P1, L) XML Converter: parser + generator + mapowanie + dry-run

# Sprint 6 — Playlisty (P1/P2)
- [x] (P1, S) Lista playlist w sidebar
- [x] (P1, S) Drag & drop z gridu do playlist
- [x] (P1, M) CRUD playlist
- [x] (P2, M) Reorder tracków w playliście
- [x] (P3, L) Smart playlists (rules)

# Sprint 7 — Packaging & Testy (P0/P1)
- [ ] (P0, L) PyInstaller spec
- [ ] (P0, M) Bundle `fpcalc`
- [ ] (P1, M) Portable ZIP
- [ ] (P1, S) Test na czystym Windows
- [ ] (P1, L) Testy unit/integration
- [ ] (P2, S) UX smoke test

# Sprint 8 — Dokumentacja (P1/P2)
- [x] (P1, S) Build.md — historia zmian
- [x] (P1, S) ToDo.md — checklist + plan
- [ ] (P2, M) Instrukcja użytkownika (PDF/MD)

---

# 0. Bootstrap i repo
- [x] Utworzyć strukturę projektu (`core/`, `data/`, `ui/`, `services/`)
- [x] Dodać `requirements.txt`
- [x] Dodać `README.md` (instrukcja uruchomienia)
- [x] Dodać `pyproject.toml` (opcjonalnie)
- [x] Dodać `.env.example`
- [x] Dodać ikonę aplikacji (ico/png)

# 1. Baza danych i modele
- [x] Zdefiniować modele domenowe (`Track`, `Playlist`, itd.)
- [x] Zdefiniować schema SQLite (tracks, tags, playlists, playlist_tracks)
- [x] Dodać repozytorium (init, upsert, list, update)
- [x] Dodać migracje (Alembic)
- [x] Dodać indeksy i constraints
- [x] Dodać tabelę ustawień (settings)

# 2. Import & Scan
- [x] Skan folderu (rekurencja + rozszerzenia)
- [x] Import Wizard (4 kroki)
- [x] Raport błędów importu
- [x] Batch commit co N plików
- [x] Anulowanie importu w trakcie
- [x] Import z plików XML (Rekordbox/VirtualDJ)

# 3. Library Browser (UI)
- [x] Sidebar (narzędzia + playlisty)
- [x] Header (search, filtry, view toggle)
- [x] TrackList + sort + resize kolumn
- [x] TrackGrid z okładkami + placeholder
- [x] Detail Panel (podgląd)
- [x] Detail Panel edycja tagów
- [x] Detail Panel: okładka + zmiana okładki
- [x] Detail Panel: historia zmian
- [x] Kontekstowe menu na liście (PPM)

# 4. Player & Waveform
- [x] Podstawowy odtwarzacz (QtMultimedia)
- [x] Placeholder waveform w detail panel
- [x] Prawdziwy waveform (librosa/ffmpeg)
- [x] Seek bar + czas odtwarzania
- [x] Hotcues + loop

# 5. AI Tagger (Hybryda)
- [x] Lokalny tagger (heurystyki)
- [x] UI ustawień API (Grok/DeepSeek/OpenAI)
- [x] Integracja cloud (OpenAI/Grok/DeepSeek) — realne wywołania
- [x] Panel Accept/Reject zmian
- [x] Zapis AI tagów do DB

# 6. Audio Recognizer / Metadata
- [x] Moduł rozpoznawania AcoustID (stub)
- [x] MusicBrainz / Discogs provider
- [x] Kolejka rozpoznawania
- [x] Uzupełnianie metadanych (batch)
- [x] Pobieranie okładek

# 7. Duplicate Finder
- [x] Hash duplicate finder
- [x] Tag-based duplicate finder
- [x] Fingerprint duplicate finder
- [x] UI: grupy + akcje (Keep/Delete/Merge)
- [x] Raport eksportu

# 8. Renamer
- [x] Wzorce renamingu
- [x] Preview zmian
- [x] Konflikty nazw
- [x] Undo

# 9. XML Converter (Rekordbox ↔ VirtualDJ)
- [x] Parser Rekordbox XML
- [x] Generator VirtualDJ XML
- [x] Mapowanie pól
- [x] Tryb dry-run + log zmian

# 10. Playlisty
- [x] Lista playlist w sidebar
- [x] Drag & drop z gridu do playlist
- [x] CRUD playlist
- [x] Reorder tracków w playliście
- [x] Smart playlists (rules)

# 11. UX / UI polish
- [x] Zaokrąglone elementy i przyjazny styl
- [x] Animowane przyciski
- [x] Animacje przejść między widokami
- [x] Spójne ikony i tooltips
- [x] Skróty klawiszowe

# 12. Packaging / Release
- [x] PyInstaller spec
- [x] Bundle `fpcalc`
- [x] Portable ZIP
- [ ] Test na czystym Windows

# 13. Testy
- [ ] Unit tests (parsery, duplikaty, renamer)
- [ ] Integration tests (import → DB → UI)
- [ ] UX smoke test

# 14. Dokumentacja
- [x] Build.md — historia zmian
- [x] ToDo.md — checklist i plan
- [x] Instrukcja użytkownika (PDF/MD)

---

# Propozycje funkcji (dodatkowe)
- [ ] Analiza loudness (LUFS) i normalizacja
- [ ] Beatgrid + auto-cue (np. intro/outro)
- [ ] Auto-key detection (np. Camelot), z mapowaniem i filtrem w UI
- [ ] Smart crates (reguły i auto-aktualizacja)
- [ ] Historia zmian tagów (audit log)
- [ ] Eksport setów (playlist → Rekordbox/VirtualDJ)
- [ ] Auto-backup bazy i ustawień
