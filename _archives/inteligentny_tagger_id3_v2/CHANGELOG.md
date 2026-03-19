# Historia Zmian - Lumbago Music AI

Wszystkie zmiany w tym projekcie będą dokumentowane w tym pliku.

## [13.0.0] - 2024-08-05

### Dodano

- **Suwak Prędkości (Pitch Slider):** W panelu odtwarzacza zaimplementowano w pełni funkcjonalny suwak do płynnej regulacji tempa utworu (w zakresie 0.5x do 1.5x). Dodano cyfrowy wskaźnik aktualnej prędkości oraz przycisk do natychmiastowego resetowania tempa.
- **Mierniki Kanałów (Channel Meters):** Wprowadzono wizualne, stereofoniczne mierniki kanałów (L/R) z dynamiczną, pulsującą animacją, która aktywuje się podczas odtwarzania utworu, symulując sygnał audio. Mierniki wykorzystują neonowy gradient, co dodaje profesjonalnego, klubowego charakteru.

### Ulepszono

- **Interfejs Odtwarzacza:** Przebudowano układ kontrolek w panelu informacyjnym, aby w sposób estetyczny i funkcjonalny pomieścić nowe, zaawansowane funkcje (pitch slider, channel meters), zachowując spójność z motywem "Dark Club".

### Polecenie AI
> Implement the player controls in the right panel, including buttons for previous, play/pause, next, and loop, along with a pitch slider and channel meters. Use the specified color scheme.

## [12.0.0] - 2024-08-04

### Dodano

- **Analizator Widma (Spektrogram):** Zintegrowano wtyczkę `wavesurfer.js-spectrogram`, dodając do odtwarzacza profesjonalny widok spektrogramu. Umożliwia to wizualną analizę częstotliwości utworu w czasie rzeczywistym.
- **Powiększenie Fali Dźwiękowej (Zoom):** Dodano dedykowany suwak zoomu, pozwalający na precyzyjne powiększanie i analizowanie fali dźwiękowej, co jest kluczowe dla dokładnego ustawiania punktów CUE i pętli.
- **Przełącznik Widoku (Waveform/Spectrogram):** Wprowadzono przycisk do płynnego przełączania się między standardowym widokiem fali (waveform) a nowym widokiem analizatora widma (spectrogram).

### Ulepszono

- **Interfejs Odtwarzacza:** Przebudowano układ panelu odtwarzacza, aby w sposób ergonomiczny i estetyczny pomieścić nowe, zaawansowane funkcje (zoom, przełącznik widoku), zachowując pełną spójność z motywem "Dark Club".

### Polecenie AI
> Dalej

## [11.0.0] - 2024-08-03

### Dodano

- **Nowy, profesjonalny interfejs:** Wprowadzono gruntowną przebudowę interfejsu w stylu "Dark Club" z neonowymi akcentami i gradientami, inspirowaną specyfikacją UI/UX.
- **Ulepszony pasek narzędzi:** Przeprojektowano górny pasek narzędzi, wprowadzając nowe, stylizowane przyciski akcji ("Import", "Scan", "Tag AI", "Convert XML", "Find Duplicates", "Rename") z gradientami i animacjami, zgodnie z nową estetyką.
- **Rozszerzony panel boczny:** Dodano sekcje "Ulubione" i "Ostatnio dodane" w panelu bocznym wraz z ikonami dla lepszej nawigacji. Nagłówki sekcji ("Sources", "Playlists") otrzymały dedykowane, neonowe kolory.
- **Dodatkowe informacje o utworach:** Do tabeli dodano kolumnę "Czas" z długością utworu oraz zaimplementowano sortowanie po tej wartości, aby umożliwić lepsze zarządzanie biblioteką.
- **Zaawansowany odtwarzacz:** W panelu informacyjnym odtwarzacz został rozbudowany o przyciski "Następny", "Poprzedni" oraz funkcję zapętlania utworu.

### Ulepszono

- **Wizualizacja fali dźwiękowej:** Wizualizacja fali dźwiękowej w odtwarzaczu wykorzystuje teraz dynamiczny, pionowy gradient kolorów od magenty do cyjanu, co znacząco poprawia estetykę i czytelność.
- **Spójność wizualna:** Zaktualizowano globalną paletę kolorów aplikacji, czcionki i zaokrąglenia, aby odpowiadały nowym wytycznym projektowym, zapewniając spójny i nowoczesny wygląd. Przycisk "Edit Tags" w panelu informacyjnym również otrzymał nowy, gradientowy styl.

### Polecenie AI
> Stwórz interaktywny UI/UX dla aplikacji desktopowej "Lumbago Music AI" (PyQt6) z ciemnym motywem, neonowymi akcentami i gradientami. Główne okno ma layout 3-kolumnowy... Dodatkowe panele: Player & Waveform, Smart Tagger AI... Styl: dark mode, gradienty neon...

## [10.0.0] - 2024-08-02

### Dodano

- **Menu Kontekstowe Utworu:**
  - Zaimplementowano menu kontekstowe (prawy przycisk myszy) dla każdego utworu w tabeli.
  - Menu zapewnia szybki dostęp do kluczowych akcji: "Analizuj z AI", "Edytuj tagi", "Usuń plik".
  - Dodano dynamiczne podmenu "Dodaj do playlisty", które listuje wszystkie dostępne playlisty.
  - Dodano opcję "Usuń z playlisty", widoczną tylko w widoku playlisty.

- **Zaawansowane Zaznaczanie (Shift + Klik):**
  - Wdrożono mechanizm zaznaczania zakresu plików poprzez kliknięcie z wciśniętym klawiszem `Shift`, co jest standardem w profesjonalnych aplikacjach.

### Ulepszono

- **Interfejs Użytkownika (UX):**
  - Dodano komponent `EmptyState`, który wyświetla przyjazny komunikat, gdy widok (np. pusta playlista) nie zawiera żadnych plików.
  - Pasek akcji masowych (`BatchActionsToolbar`) pojawia się teraz płynnie u dołu ekranu po zaznaczeniu więcej niż jednego pliku.

### Poprawiono

- **Krytyczna Naprawa Aplikacji:**
  - W pełni zaimplementowano od nowa brakującą logikę w głównym komponencie `App.tsx`, naprawiając błąd uniemożliwiający uruchomienie aplikacji.
  - Przywrócono wszystkie handlery zdarzeń, zapewniając, że przyciski i akcje działają zgodnie z oczekiwaniami.
  - Naprawiono i uzupełniono brakujący nagłówek tabeli z w pełni funkcjonalnym, wielokierunkowym sortowaniem.
  - Przywrócono renderowanie wszystkich brakujących okien modalnych.
  - Uzupełniono brakujące komponenty interfejsu, takie jak `BatchActionsToolbar`, `ActionsDropdown` i inne.

### Polecenie AI
> Kontynuuj automatycznie dodawanie brakujących elementów i usprawnień interfejs

## [8.1.0] - 2024-08-01 (Poprawka)

### Poprawiono

- **Krytyczna naprawa aplikacji:** Przywrócono brakującą logikę w komponencie `App.tsx`, naprawiono tabelę i sortowanie, uzupełniono renderowanie brakujących okien modalnych oraz w pełni zaimplementowano handlery zdarzeń, co przywróciło stabilność i pełną funkcjonalność programu.

### Polecenie AI
> Program nie uruchamia się

## [8.0.0] - 2024-08-01

### Dodano

- **Trwały Zapis Punktów Hot Cue:**
  - Punkty Hot Cue są teraz automatycznie **zapisywane w metadanych pliku** (w polu komentarza w formacie JSON).
  - Aplikacja automatycznie odczytuje zapisane punkty Hot Cue przy wczytywaniu plików.
  - W "Trybie Bezpośredniego Dostępu", ustawienie lub zmiana punktu Hot Cue powoduje natychmiastowy zapis w oryginalnym pliku na dysku.

- **Eksport Playlist do formatu DJ-skiego:**
  - W menu kontekstowym playlist dodano opcje **"Eksportuj do Rekordbox (XML)"** oraz **"Eksportuj do VirtualDJ (XML)"**.
  - Zaimplementowano silnik generujący pliki XML w pełni kompatybilne z profesjonalnym oprogramowaniem, zawierające listę utworów, ich kolejność, metadane i punkty CUE.

- **Playlist Intelligence v1 (Inteligentne Sortowanie):**
  - W menu kontekstowym playlisty dodano opcję **"Sortuj inteligentnie"**.
  - Zaimplementowano zaawansowany algorytm, który automatycznie układa utwory w playliście w optymalnej kolejności, bazując na zasadach **miksowania harmonicznego (Koło Kameralne)** i **progresji tempa (BPM)**.

### Polecenie AI
> Kontynuuj automatycznie

## [7.0.0] - 2024-07-31

### Dodano

- **Kompletny System Zarządzania Playlistami:**
  - W lewym panelu bocznym zaimplementowano w pełni funkcjonalną sekcję "Playlisty".
  - Użytkownicy mogą teraz **tworzyć** nowe, puste playlisty za pomocą dedykowanego przycisku.
  - Zaimplementowano menu kontekstowe (prawy przycisk myszy) na playlistach, które pozwala na ich **zmianę nazwy** oraz **usuwanie**.
  - Wdrożono pełne wsparcie dla mechanizmu **przeciągnij i upuść (drag-and-drop)** do dodawania jednego lub wielu utworów do playlist.
  - Kliknięcie na playlistę przełącza widok główny, pokazując tylko zawarte w niej utwory.
  - W widoku playlisty, użytkownicy mogą **zmieniać kolejność utworów** przeciągając je w górę i w dół.
  - Dodano opcję "Usuń z playlisty" w menu kontekstowym utworu (w widoku playlisty).
  - Wszystkie playlisty, ich zawartość i kolejność utworów są zapisywane w `localStorage` i przywracane przy ponownym uruchomieniu aplikacji.

### Ulepszono

- **Refaktoryzacja Kodu:**
  - Lewy panel boczny został wydzielony do dedykowanego, czystego komponentu `Sidebar.tsx`, co znacząco poprawiło organizację kodu w `App.tsx`.

### Polecenie AI
> Kontynuuj automatycznie

## [6.0.0] - 2024-07-30

### Dodano

- **Zaawansowany Odtwarzacz z Wizualizacją Fali Dźwiękowej:**
  - Zastąpiono standardowy odtwarzacz `<audio>` profesjonalnym komponentem opartym na bibliotece `wavesurfer.js`.
  - Prawy panel informacyjny został całkowicie przebudowany, aby wyświetlać dużą, interaktywną i kolorową falę dźwiękową (waveform) wybranego utworu.
  - Waveform jest w pełni interaktywny - kliknięcie w dowolnym miejscu natychmiast przewija utwór.
- **System Hot Cue:**
  - Wprowadzono możliwość ustawienia do 4 punktów Hot Cue w kluczowych momentach utworu.
  - Dodano obsługę skrótów klawiszowych (1, 2, 3, 4) do szybkiego ustawiania i przywoływania punktów Hot Cue.
  - Zapisane punkty Hot Cue są wizualnie zaznaczone na fali dźwiękowej.
- **Nowe Kontrolki Odtwarzania:**
  - Dodano nowe, stylizowane kontrolki odtwarzania (Play/Pause), suwak głośności oraz wyświetlanie czasu.
- **Refaktoryzacja Kodu:**
  - Cała logika związana z panelem informacyjnym i nowym odtwarzaczem została przeniesiona do dedykowanego komponentu `TrackInfoPanel.tsx`, co poprawiło organizację kodu.

### Polecenie AI
> Dalej

## [5.0.0] - 2024-07-29

### Dodano

- **Tryb Bezpośredniego Dostępu do Folderu:**
  - Na ekranie powitalnym dodano kluczową opcję **"Połącz z Folderem"**, wykorzystującą File System Access API.
  - Aplikacja może teraz rekursywnie skanować lokalny folder użytkownika i wczytywać pliki audio wraz z ich strukturą.
- **Zapis Zmian Bezpośrednio na Dysku:**
  - W trybie bezpośredniego dostępu, wszystkie operacje zapisu (zmiana tagów, zmiana nazw plików) odbywają się **bezpośrednio na dysku użytkownika**.
  - Zaimplementowano zaawansowaną funkcję `saveFileDirectly`, która potrafi tworzyć podfoldery i przenosić pliki zgodnie z szablonem nazw.
  - Przycisk "Pobierz" dynamicznie zmienia się na **"Zapisz zmiany"** w nowym trybie pracy.
  - W oknie edycji pojedynczego pliku dodano przycisk **"Zastosuj zmiany"** do natychmiastowego zapisu tagów w oryginalnym pliku.
- **Rozszerzone Wsparcie dla Zapisu Tagów:**
  - Dodano pełne wsparcie dla zapisu tagów w plikach **M4A (MP4)** obok istniejącego wsparcia dla MP3.

### Polecenie AI
> Kontynuuj

## [4.0.0] - 2024-07-28

### Dodano

- **Moduł Inteligentne Kolekcje (Smart Collections):**
  - Wprowadzono nową sekcję "Inteligentne Kolekcje" w lewym panelu bocznym.
  - Dodano **Kreator Inteligentnej Kolekcji**, który pozwala na tworzenie dynamicznych playlist opartych na złożonych regułach.
  - Zaimplementowano zaawansowany silnik reguł z obsługą wielu warunków, operatorów logicznych (np. "zawiera", "jest większe niż", "jest w zakresie") i logiki AND/OR.
  - Stworzone kolekcje są zapisywane w pamięci przeglądarki (`localStorage`) i wyświetlane w panelu bocznym.
  - Kliknięcie na kolekcję natychmiast filtruje główną listę utworów, a nagłówek dynamicznie pokazuje nazwę i liczbę pasujących plików.
  - Kreator wyświetla podgląd na żywo liczby utworów pasujących do zdefiniowanych reguł.

### Polecenie AI
> Dalej

## [3.0.0] - 2024-07-27

### Dodano

- **Moduł Wyszukiwarki Duplikatów:**
  - Dodano do paska narzędzi przycisk "Znajdź duplikaty", otwierający dedykowany modal.
  - Zaimplementowano dwie metody detekcji: szybką (na podstawie tagów) i dokładną (na podstawie sumy kontrolnej SHA-256 z paskiem postępu).
  - Stworzono interfejs do przeglądania wyników w grupach z możliwością wyboru plików do usunięcia.
  - Dodano funkcję "Auto-wybierz", która inteligentnie sugeruje, które duplikaty zachować (np. te z większą liczbą tagów).

- **Moduł Konwertera XML (Rekordbox ↔ VirtualDJ):**
  - Dodano do paska narzędzi przycisk "Konwerter XML", otwierający osobne narzędzie.
  - Zaimplementowano w pełni funkcjonalny, dwukierunkowy silnik konwersji, który automatycznie wykrywa format źródłowy (Rekordbox lub VirtualDJ).
  - Zapewniono precyzyjne mapowanie kluczowych danych, w tym **punktów CUE, Hot Cue i pętli (Loops)** z dokładnością do milisekund.
  - Stworzono prosty interfejs typu "przeciągnij i upuść" z podsumowaniem konwersji i opcją pobrania gotowego pliku.

### Poprawiono i Ulepszono

- **Krytyczna naprawa silnika AI (`aiService.ts`):**
  - Przywrócono i w pełni zaimplementowano brakujący serwis AI, bez którego aplikacja nie była w stanie przetwarzać plików.
  - Stworzono zaawansowany prompt systemowy dla Gemini, instruujący model do działania jako ekspert muzyczny i asystent DJ-a.
  - Ulepszono schemat odpowiedzi AI, aby priorytetowo traktował **BPM** i **tonację w notacji Camelot**.
  - Zaimplementowano logikę ponawiania prób (retry) dla zapytań do API, aby zwiększyć niezawodność.
  - Dodano w pełni działający tryb wsadowy (`fetchTagsForBatch`) do analizowania wielu plików jednocześnie, co znacząco przyspiesza pracę.

### Polecenie AI
> Dalej

## [2.0.0] - 2024-07-26

### Dodano

- **Gruntowna przebudowa interfejsu (UI/UX):** Wprowadzono nowy, profesjonalny wygląd "Dark Club" inspirowany specyfikacją, z ciemnym motywem, neonowymi akcentami i 3-kolumnowym layoutem (źródła/playlisty, lista utworów, panel informacyjny).
- **Nowy nagłówek i logo:** Aplikacja zyskała dynamiczny nagłówek z logo "Lumbago Music AI" i animowanym equalizerem.
- **Ulepszone tagowanie AI:** Rozszerzono zapytania do AI o kluczowe dla DJ-ów tagi: **BPM** i **tonację** (w notacji Camelot).
- **Panel informacyjny z podglądem:** Dodano panel boczny wyświetlający okładkę albumu, szczegóły utworu oraz odtwarzacz do szybkiego odsłuchu.
- **Zaawansowane sortowanie i zmiana nazw:** Umożliwiono sortowanie listy utworów po BPM i tonacji oraz dodano wsparcie dla nowych tagów w szablonach nazw plików.

### Polecenie AI

> Zapoznaj się z dokumentacją i zaktualizuj aplikacje aby osiągnąć w pełni sprawny program uwzględniając wszystkie założenia projektu. Podziel na etapy tak aby nie przekroczyc limitu długości wiadomości