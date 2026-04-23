# Lumbago Fresh (Windows, Python)

Nowa aplikacja desktopowa napisana od zera w Pythonie (PyQt6), przygotowana na bazie analizy archiwum `Lumbago.zip`.

## Co zachowuje z oryginału
- Ciemny, prosty interfejs z lewym panelem nawigacji.
- Widoki: `Biblioteka`, `Playlisty`, `Duplikaty`, `Renamer`, `XML Konwerter`.
- Szybki import folderu audio.
- Narzędzia automatyzacji: automatyczny watch-folder + auto-tagowanie po imporcie.
- Dolny pasek odtwarzania (podstawowe sterowanie i otwieranie pliku w systemowym odtwarzaczu).

## Uruchomienie
1. Zainstaluj zależności:
   ```bash
   pip install -r lumbago_fresh/requirements.txt
   ```
2. Uruchom:
   ```bash
   python -m lumbago_fresh.main
   ```

## Dane aplikacji
Dane zapisywane są lokalnie w:
`%APPDATA%\LumbagoFresh\`

Pliki:
- `library.json` - biblioteka utworów
- `settings.json` - ustawienia (np. watch folder, interwał)

