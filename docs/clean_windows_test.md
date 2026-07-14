# Test na czystym Windows — checklist (Desktop PyQt6, post DJ migration)

Per 2026-06-16 full repo consolidation (SZPIEG research lead): ALL prior documentation, old agent outputs, full checklists, unused docs, previous crew reports, history, mockups, build artifacts, web remnants, legacy plans, DESIGN docs, Blueprint extract etc. safely archived in root MEMORY/ directory (substructure: full_agent_instructions/, historical_checklists/, archive/ (from prior 2026-06-15 docs/archive/), old_docs/, previous_runs/ etc.) and summarized/pointered in this memory.md (Archiwum section). Live files (AGENTS/CLAUDE/crew/PLAN/SZPIEG/CHECKLIST + docs/HISTORY/guides + README etc.) minimized for continuity but complete. All information preserved and accessible via MEMORY/INDEX.md + git history. Builds on 2026-06-15 uporządkowanie to docs/archive/. Per SZPIEG research 2026-06-16 consolidation + Plan hierarchy + "uruchamiaj szpiega przed kazdym wiekszym etapem" + "nie przestawaj" + "must document identical".

**Uwaga:** Testuje desktop app (PyQt6). Web parts legacy. Nowa DJ arch jest jedyną: ui/dj/* + clean dj_player_window.py.

## Założenia
- Brak zainstalowanego Pythona.
- Brak zależności dev.
- Test na świeżym profilu użytkownika.

## Przygotowanie
1. Zbuduj artefakt: `.\scripts\build_portable_windows.ps1`
2. Skopiuj `dist/LumbagoMusicAI-portable.zip` na maszynę testową.
3. Rozpakuj archiwum do nowego katalogu (np. `C:\LumbagoMusicAI`).

Automatyczny smoke na maszynie deweloperskiej:
```powershell
.\scripts\smoke_portable_windows.ps1
```

## Smoke test uruchomienia
1. Uruchom `LumbagoMusicAI.exe`.
2. Sprawdź, czy okno startuje i nie zamyka się samoczynnie.
3. Zamknij aplikację.

## Test funkcjonalny (minimum)
1. Włącz aplikację.
2. Wejdź w Import i dodaj 1–3 pliki audio (MP3/FLAC).
3. Sprawdź, czy pojawiają się w bibliotece.
4. Otwórz Detail Panel i edytuj podstawowe tagi.
5. Zapisz i sprawdź, czy tagi są zapisywane w pliku.

## Player (nowy DJ arch)
1. Otwórz DJ Player (przycisk DJ Player ▼).
2. Załaduj 1-2 utwory (z biblioteki lub drag&drop) na decki A/B.
3. Odtwórz, seek, ustaw hotcue (8/deck), loop, crossfader.
4. Sprawdź waveform, status, brak crashy przy load niezeskanowanych tracków (dzięki robust None w beatgrid/auto_cue).
5. Zatrzymaj / toggle.

Uwaga: nowa architektura sole (ui/dj/* + dj_player_window.py hardcoded True) — brak starych klas.

**Uwaga audio:** Pełny playback wymaga VLC. Na czystym Windows CI instalacja przez Chocolatey + cache (lub fallback). Gdy VLC niedostępny — Qt lub Noop fallback (testy + smoke przechodzą). Na użytkowniku: zainstaluj VLC dla pełnej jakości DJ.

**Uwaga Downloader (FIXER, post "dalej"):** Moduł Downloader/Konwerter wymaga zewnętrznych: yt-dlp (pip install) + ffmpeg (w PATH, winget/choco/videolan). Nie bundled w portable (PATH detect + guard). Na clean Windows: zainstaluj osobno przed testem downloadera (ytsearch/B, est, A wiring). Bez nich — warning w UI + graceful (nie crash). Patrz pyinstaller.spec + downloader code.

## Zakończenie
1. Sprawdź, czy w `%APPDATA%\LumbagoMusicAI` powstały pliki `lumbago.db` i `settings.json`.
2. Zapisz wynik testu oraz ewentualne błędy.

Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Duplicate Finder dopinanie to the absolute last detail (tests for staged/Etapowo/fp + match_method labels, merge on fp groups, any remaining UI/guards, no silent errors) + manual punkt 4 + full CHECKLIST closure with all auto-verifiable parts + status updates + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical. Local smoke + scripts full coverage of portable exe run/resources (SAFE); full manual (import/detail/player/DB) + clean-VM test pending per original plan + 'nie przestawaj'. 'Gotowe' local buttoned. Per PLAN.
