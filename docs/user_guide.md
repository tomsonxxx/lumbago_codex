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

## Downloader / Konwerter (sugestie z promptu)
- Narzędzia > Downloader / Konwerter.
- Wklej URL (YT/SC, playlisty do 700+).
- Wybierz folder, format (MP3/WAV/M4A), profil jakości (MAX dla audible quality prio).
- Estymacja rozmiaru/czasu przed start + warning dla dużych/WAV.
- Szukaj na YT (ytsearch).
- Zapisz/wczytaj profile (D).
- Historia pobrań (F).
- Checkbox "Dodaj do biblioteki" po zakończeniu (A) - skan/import.
- AI integracja: komenda "pobierz [url] jako MP3" prefill + auto-start (E, z safety).
- Wymaga yt-dlp (pip) + ffmpeg w PATH (100% free).

## AI Chat Panel (Pomocnik)
- Narzędzia > AI Pomocnik (komendy).
- Zwijany panel, historia sesji.
- Wspiera wszystkie providery (jak Autotager: gemini/openai/grok/deepseek) - Auto lub wybór.
- Komendy: "pobierz ...", "duplikaty", "otaguj", "pomoc".
- Dispatcher + sandbox (bezpieczne).
- Integracja z Downloader (prefill + start).
- System prompt opisuje operacje Lumbago.

Per SZPIEG research + Plan + "dalej do konca" 2026-06-27 ... must document identical.
