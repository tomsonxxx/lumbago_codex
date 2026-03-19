# UI Plan v1 — WinUI 3 „Neon Glass”

## Cel
Zdefiniować spójny styl i układ dla nowego interfejsu Lumbago Music AI na Windows.

## Styl wizualny (neon glass)
- Kierunek: ciemne tło + półprzezroczyste panele + neonowe akcenty
- Materiał bazowy: Acrylic dla paneli i kart
- Kontrast: wysoki dla tekstu i kluczowych akcji

## Paleta kolorów (v1)
- Tło główne: #0B0F14
- Tło powierzchni: #121826
- Tło powierzchni 2: #0F1622
- Tekst główny: #EAF2FF
- Tekst pomocniczy: #A8B3C7
- Linia/Divider: #1F2A3A
- Primary (cyjan): #6FE7FF
- Accent (magenta): #FF5CD6
- Accent 2 (fiolet): #8A7CFF
- Success: #4DFFB8
- Warning: #FFB86B
- Danger: #FF6B6B

## Gradienty i poświaty
- Neon edge: #6FE7FF → #FF5CD6
- Glow cyan: #6FE7FF @ 15%
- Glow magenta: #FF5CD6 @ 12%

## Typografia
- Font: Segoe UI Variable
- Skale rozmiarów: 12, 14, 16, 20, 24, 32
- Wagi: 400, 600

## Promienie i odstępy
- Promienie: 8, 12, 16
- Skala odstępów: 4, 8, 12, 16, 24, 32

## Cienie i głębia
- Glow panelu: 0 0 24px (cyan 15%) + 0 0 32px (magenta 12%)
- Border panelu: 1px #2A3447 @ 40%

## Layout i stałe wymiary
- Lewy panel nawigacji: 72px (collapsed) / 240px (expanded)
- Topbar: 56px
- Prawy panel filtrów/narzędzi: 280–320px
- Player dock: 88px

## Struktura nawigacji (v1)
- Lewy panel (SideNav): Start, Biblioteka, Import, Duplikaty, Konwerter, Ustawienia, Playlisty
- Sekcje: „Narzędzia AI” i „Playlisty” jako podsekcje
- Topbar: wyszukiwarka globalna + quick filters + przełącznik widoku
- Dock: odtwarzacz + Quick Actions
- Prawy panel: filtry i narzędzia kontekstowe

## Stany widoków (globalne, v1)
- Puste: brak danych + CTA (Importuj)
- Ładowanie: skeleton + progress
- Błąd: komunikat + retry
- Częściowy: lista z paskiem statusu (np. skanowanie)

## Mapa widoków i przepływów (v1)
- Start → szybkie akcje + skróty do modułów
- Biblioteka → centralny widok pracy
- Import → prowadzenie skanu i analizy
- Duplikaty → grupy i akcje masowe
- Konwerter XML → wejście/wyjście + mapowanie
- Tag Compare → porównanie i zatwierdzanie zmian
- Smart Tagger → analiza AI + akceptacja
- Ustawienia → API, cache, zachowanie
- Playlisty → listy i reguły smart

## Makieta Biblioteki (opis v1)
- Topbar: wyszukiwarka globalna, filtry szybkie, przełącznik lista/siatka
- Lewy panel: Start, Biblioteka, Import, Duplikaty, Konwerter, Ustawienia, Playlisty
- Główna przestrzeń: TrackList lub TrackGrid
- Prawy panel: filtry (BPM, Key, Mood) + narzędzia AI
- Dolny dock: odtwarzacz z mini-waveform, play/pause, czas, głośność
- Panel szczegółów: wysuwany z prawej (tagi, okładka, historia zmian)

## Makieta Importu (opis v1)
- Układ: pojedyncza karta „Import” na środku + pasek postępu na dole
- Krok 1: wybór źródła (Folder, Pliki, XML) + drag & drop
- Krok 2: skan i podgląd metadanych (lista mini‑tabel)
- Krok 3: auto‑naprawa (propozycje zmian z checkboxami)
- Krok 4: import + log błędów
- Prawy panel: status skanu, licznik plików, ETA, przycisk „Anuluj”
- Stany: pusty, skanowanie, błąd, zakończony

## Makieta Duplikatów (opis v1)
- Układ: główna lista grup duplikatów + panel akcji po prawej
- Górny pasek: wybór metody (hash/tag/fingerprint/etapowo)
- Główna lista: grupy z podglądem 2–3 utworów, znacznik „pewny”
- Panel akcji: „Zachowaj”, „Usuń”, „Scal metadane”, „Eksport CSV”
- Widok szczegółów: po kliknięciu grupy — pełna lista i porównanie tagów
- Stany: brak duplikatów, wynik częściowy, wynik końcowy

## Makieta Odtwarzacza (dock + Quick Actions) (opis v1)
- Układ: stały dock na dole + szybkie akcje po prawej
- Sekcje docka: okładka + tytuł + artysta, transport (prev/play/next), pasek czasu
- Dodatki: mini‑waveform, głośność, tryby (shuffle/repeat)
- Quick Actions: „Dodaj do playlisty”, „Analizuj AI”, „Porównaj tagi”
- Stany: brak utworu, odtwarzanie, pauza, błąd odtwarzania

## Makieta Tag Compare (opis v1)
- Układ: dwie kolumny „Stare tagi” i „Nowe tagi” + panel akcji
- Lista pól: Title, Artist, Album, BPM, Key, Genre, Year, Mood, Energy
- Akcje: „Zamień”, „Zachowaj stare”, „Zachowaj nowe”, „Zastosuj wszystkie”
- Wyróżnienie różnic: neonowy akcent na zmienionych polach
- Stany: brak różnic, różnice częściowe, konflikt

## Makieta Smart Tagger (opis v1)
- Układ: lista utworów + wynik AI (confidence) + panel akcji
- Wiersz wyniku: track, propozycje tagów, confidence bar
- Akcje: Akceptuj/Odrzuć na wierszu + „Zastosuj wszystkie”
- Stany: oczekujące, w trakcie, zakończone, błąd

## Makieta Start / Dashboard (opis v1)
- Układ: siatka kart startowych + panel „ostatnia aktywność”
- Karty: Import, Biblioteka, Duplikaty, Tagger AI, Konwerter XML
- Pasek skrótów: „Ostatnio dodane”, „Top playlisty”, „Szybkie skany”
- Stany: pusta biblioteka, aktywna biblioteka

## Makieta Playlisty i Smart Playlisty (opis v1)
- Układ: lewy panel z listą playlist + główny widok utworów playlisty
- Nagłówek: nazwa playlisty, liczba utworów, czas łączny
- Akcje: dodaj/edytuj/usuń, sortuj, eksportuj
- Smart Playlisty: reguły (BPM, Key, Genre, Year, Rating) + podgląd wyników
- Stany: pusta playlisty, brak wyników reguł, konflikt sortowania

## Makieta Konwerter XML (opis v1)
- Układ: dwa panele „Wejście” i „Wyjście” + panel mapowania
- Wejście: wybór pliku Rekordbox/VirtualDJ + podgląd struktury
- Mapowanie: tabela pól + walidacja braków
- Wyjście: wybór formatu + ścieżki zapisu + log zmian
- Stany: brak pliku, błąd parsowania, konwersja OK

## Makieta Ustawienia (opis v1)
- Układ: lewa lista sekcji + prawa karta ustawień
- Sekcje: AI API, Biblioteka, Cache, UI, Audio
- Pola kluczowe: klucze API, model, TTL cache, tryb walidacji
- Akcje: zapisz, testuj połączenie, przywróć domyślne
- Stany: błąd walidacji, zapis OK, brak uprawnień

## Komponenty kluczowe (v1)
- TrackRow, TrackGridItem, FilterChips
- BulkActionsBar, PlayerDock
- SideNav, TopSearch
- DetailDrawer, EmptyState, LoadingState

## Komponenty bazowe (v1)
- Button (Primary, Secondary, Ghost)
- Input (Text, Search)
- Card (Glass, Solid)
- Panel (Left, Right, Dock)
- Tag/Chip
- Slider (BPM/Year)

## Style listy/siatki i tabel (v1)
- TrackList: wiersze 44–52px, zebra subtle, hover glow
- Kolumny: Title, Artist, Album, BPM, Key, Duration, Date Added
- TrackGrid: karty 1:1 z okładką, meta pod spodem, hover reveal
- Filtry: chipy z neonową obwódką, slider BPM/Year

## Zasady kontrastu i dostępności (v1)
- Kontrast tekstu min. 4.5:1 dla treści głównych
- Focus states: widoczne neonowe obramowanie
- Nawigacja klawiaturą: Tab, Enter, Space dla akcji
- Ikony z etykietą i tooltipem

## Must-have interakcje (v1)
- Drag & drop do playlist
- Bulk actions na zaznaczonych utworach
- Kontekstowe menu PPM w TrackList i TrackGrid
- Szybkie preview (play/pause na wierszu)
