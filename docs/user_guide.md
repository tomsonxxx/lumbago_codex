# Instrukcja użytkownika — Lumbago Music AI

Per 2026-06-16 full repo consolidation (SZPIEG research lead): ALL prior documentation, old agent outputs, full checklists, unused docs, previous crew reports, history, mockups, build artifacts, web remnants, legacy plans, DESIGN docs, Blueprint extract etc. safely archived in root MEMORY/ directory (substructure: full_agent_instructions/, historical_checklists/, archive/ (from prior 2026-06-15 docs/archive/), old_docs/, previous_runs/ etc.) and summarized/pointered in this memory.md (Archiwum section). Live files (AGENTS/CLAUDE/crew/PLAN/SZPIEG/CHECKLIST + docs/HISTORY/guides + README etc.) minimized for continuity but complete. All information preserved and accessible via MEMORY/INDEX.md + git history. Builds on 2026-06-15 uporządkowanie to docs/archive/. Per SZPIEG research 2026-06-16 consolidation + Plan hierarchy + "uruchamiaj szpiega przed kazdym wiekszym etapem" + "nie przestawaj" + "must document identical".

> **Uwaga:** Aplikacja jest w pełni desktopowa (PyQt6). Wersje webowe i eksperymentalne React/WinUI zostały usunięte z repozytorium.

## Start
1. Uruchom aplikację.
2. Wejdź w **Ustawienia** i wprowadź klucze API (opcjonalnie).
3. Kliknij **Importuj / Skanuj** i wskaż folder z muzyką.

## Biblioteka
- Użyj wyszukiwarki i filtrów (BPM, tonacja, gatunek).
- Zmieniaj widok na listę lub siatkę.
- Kliknij utwór, aby zobaczyć szczegóły i edytować tagi.

## Tagi i metadane
- **Odczytaj z pliku**: wczytuje tagi z pliku audio.
- **Zapisz do pliku**: zapisuje tagi z panelu do pliku.
- **Metadane lokalne**: uzupełnia tagi z nazwy pliku, folderu, CUE i JSON.
- **Porównaj tagi**: zestawia stare i nowe tagi w dwóch kolumnach.

## AI Tagger
- **Tagger AI**: analiza wybranych utworów.
- **AutoTagowanie**: AI + auto‑pobieranie brakujących danych z internetu.

## Playlisty
- Kliknij prawym przyciskiem na listę playlist, aby dodać/edytować/usuwać.
- **Playlisty smart** filtrują utwory według reguł (np. BPM, gatunek).
- **Kolejność**: ręcznie zmieniaj kolejność utworów w playliście.

## Duplikaty
- Wybierz metodę: hash, tagi, fingerprint lub etapowo.
- Zaznacz duplikaty i wykonaj akcje: przenieś, usuń, scal metadane.

## Import XML
- Obsługuje Rekordbox i VirtualDJ.
- Wczytaj XML i zaimportuj metadane do bazy.

## Downloader / Konwerter + AI Chat Panel

**Wymagania (100% free):**
- `pip install yt-dlp`
- ffmpeg w PATH (zalecane: https://www.gyan.dev/ffmpeg/builds/ lub videolan.org dla Windows build). Bez ffmpeg konwersja ograniczona.

**Narzędzia > Downloader / Konwerter**
- Wklej URL (pojedynczy film lub playlista YT/SC — specjalizacja w dużych playlistach do 700+ pozycji).
- Wybierz folder docelowy, format wyjściowy (MP3 / WAV / M4A), profil jakości:
  - MAX: najwyższa audible jakość (V0 MP3 lub 24/48 WAV PCM).
  - BALANCE: dobry kompromis.
  - COMPACT: mniejsze pliki.
- Przed startem: estymacja rozmiaru/czasu na podstawie probe pierwszych wpisów + ostrzeżenie dla >5GB lub dużych WAV.
- Wyszukiwarka: przycisk "Szukaj na YouTube" (ytsearch: prefix).
- Profile: Zapisz / Wczytaj / Lista nazwanych profili (D).
- Historia: pokaż ostatnie checkpointy z liczbą pobranych + sample (F).
- "Dodaj pobrane do biblioteki" (A): po zakończeniu automatyczny skan + upsert do biblioteki.
- Progres: dwa bary (playlista + bieżący plik) + log + per-item błędy (kontynuacja).
- AI integracja (E): komenda "pobierz https://... jako MP3" → prefill + auto_start z safety est.
- Mechanizmy dla dużych playlist: lazy extract, checkpoint JSON (resume), retry+throttle, dedup po video ID, atomic move.

**Narzędzia > AI Pomocnik (komendy)**
- Zwijany panel czatu.
- Wspiera wszystkie providery Cloud AI (gemini / openai / grok / deepseek) — Auto lub ręczny wybór (identycznie jak Autotagger).
- Przykładowe komendy (wysyłaj po polsku):
  - "pobierz https://youtube.com/... jako WAV"
  - "duplikaty"
  - "otaguj folder C:/muzyka"
  - "pomoc"
- Pod maską: system prompt + JSON dispatch do registry → sandbox (prefer registry dispatch, whitelist). Pełna integracja z Downloader (prefill + auto-start).
- Historia sesji + "Myślę..." indicator.
- Jeśli niepewny — prosi o doprecyzowanie.

**Uwagi techniczne**
- Wszystkie długie operacje w QThread (UI responsywne).
- Brak konfliktów z istniejącym kodem (add-only).
- Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + "dalej" + "zsynchronizuj z github" + "kontynuuj" ... must document identical.

Per SZPIEG research + Plan + "dalej do konca" 2026-06-27 + kontynuacja po sync ... must document identical.
