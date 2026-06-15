# Test na czystym Windows — checklist (Desktop PyQt6, post DJ migration)

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

## Zakończenie
1. Sprawdź, czy w `%APPDATA%\LumbagoMusicAI` powstały pliki `lumbago.db` i `settings.json`.
2. Zapisz wynik testu oraz ewentualne błędy.

Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Duplicate Finder dopinanie to the absolute last detail (tests for staged/Etapowo/fp + match_method labels, merge on fp groups, any remaining UI/guards, no silent errors) + manual punkt 4 + full CHECKLIST closure with all auto-verifiable parts + status updates + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical. Local smoke + scripts full coverage of portable exe run/resources (SAFE); full manual (import/detail/player/DB) + clean-VM test pending per original plan + 'nie przestawaj'. 'Gotowe' local buttoned. Per PLAN.
