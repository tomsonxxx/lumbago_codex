# Test na czystym Windows — checklist

## Założenia
- Brak zainstalowanego Pythona.
- Brak zależności dev.
- Test na świeżym profilu użytkownika.

## Przygotowanie
1. Skopiuj `dist/LumbagoMusicAI-portable.zip` na maszynę testową.
2. Rozpakuj archiwum do nowego katalogu (np. `C:\LumbagoMusicAI`).

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

## Player
1. Odtwórz utwór.
2. Sprawdź seek bar i czas odtwarzania.
3. Zatrzymaj odtwarzanie.

## Zakończenie
1. Sprawdź, czy w `%APPDATA%\LumbagoMusicAI` powstały pliki `lumbago.db` i `settings.json`.
2. Zapisz wynik testu oraz ewentualne błędy.
