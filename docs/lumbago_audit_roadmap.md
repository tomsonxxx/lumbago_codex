# Audyt i Roadmapa dla `Lumbago Music AI`

## Założenia i sposób oceny

Ten materiał dotyczy desktopowego programu `Lumbago Music AI` w Pythonie/PyQt6, z kodem w `lumbago_app/`. Analiza została oparta na realnym stanie modułów, a nie wyłącznie na historycznych opisach w `Build.md`, `Build2.md`, `ToDo.md` i `ToDo2.md`.

Najważniejsze kryteria oceny:

- workflow DJ-a: szybkość pracy, mała liczba kliknięć, dobra orientacja w bibliotece
- bezpieczeństwo operacji masowych: backup, undo, soft delete, jasny feedback
- jakość danych: trafność metadanych, confidence, możliwość cofnięcia zmian
- wydajność przy dużej bibliotece: 10k+ rekordów, ciężkie skany, cache
- utrzymanie kodu: podział odpowiedzialności, ograniczanie logiki w `ui/main_window.py`

Legenda priorytetów:

- `P0` krytyczne
- `P1` wysokie
- `P2` średnie
- `P3` nice-to-have

Kategorie problemów:

- `UX` ergonomia i czytelność
- `Core` logika biznesowa i jakość danych
- `Perf` wydajność i skala
- `Safety` odwracalność zmian i bezpieczeństwo danych
- `Arch` architektura i utrzymanie

## Stan ogólny produktu

Projekt jest funkcjonalnie szeroki jak na lokalne narzędzie DJ-skie:

- import i skan biblioteki
- list/grid browser
- detail panel z edycją
- player oparty o `QMediaPlayer`
- AI tagger lokalny i chmurowy
- recognizer oparty o `fpcalc` + AcoustID + MusicBrainz
- duplikaty, renamer, XML, playlisty, loudness, key detection, beatgrid, backup, audit log

Największe problemy systemowe:

- `ui/main_window.py` jest monolitem 1600+ linii i skupia zbyt dużo logiki UI, audio, playlist, historii, playera i narzędzi
- część funkcji jest "produkcyjna", a część nadal ma charakter MVP lub pół-mocka
- opisy historyczne i aktualny kod nie zawsze się pokrywają
- bezpieczeństwo operacji destrukcyjnych i masowych nadal jest za słabe jak na aplikację do pracy na realnej bibliotece DJ-a

---

## 1. Import i skan muzyki

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/import_wizard.py`
- `lumbago_app/core/audio.py`

Aktualny stan:

- działa 4-krokowy kreator importu oparty o `QDialog` i `QStackedWidget`
- krok 1 wybiera folder
- krok 2 zbiera opcje: `recursive`, lista rozszerzeń, `batch_size`
- krok 3 uruchamia `ScanWizardWorker`, który używa `iter_audio_files()` i `extract_metadata()`
- krok 4 uruchamia `ImportWizardWorker`, który batchowo wykonuje `upsert_tracks()`
- lokalny pipeline metadanych jest szeroki: ID3/Mutagen, `folder.json`, sidecar `.json`, regexy filename, `.cue`, struktura folderów

### Mocne strony

- dobry podział na worker skanujący i worker importujący
- jest anulowanie skanu i importu
- import używa batch commit, co ogranicza koszty I/O
- pipeline fallbacków w `core/audio.py` daje sporą szansę uzupełnienia danych nawet bez ID3

### Problemy

- `UX`: preview pokazuje tylko `Title`, `Artist`, `Album`, `Path`; dla DJ-a brakuje co najmniej `BPM`, `Key`, `Duration`, statusu braków
- `UX`: rozszerzenia są wpisywane ręcznie jako string, co jest podatne na błędy
- `UX`: raport błędów zapisuje się do TXT, bez czytelnego podsumowania w UI
- `Core`: import nie robi ostrzeżeń o duplikatach już podczas preview/importu
- `Core`: pipeline metadanych jest szeroki, ale nie ma jasnego raportu, które źródło wygrało dla danego pola
- `Perf`: skan zbiera całą listę plików do pamięci przed przetwarzaniem
- `Safety`: brak pre-import backup i brak trybu "dry run import do biblioteki"

### Co można usunąć

- `_apply_cue_metadata()` jako funkcję domyślnie aktywną, jeśli produkt nie jest nastawiony na kolekcje albumowe z CUE
- `_apply_sidecar_json()` z domyślnej ścieżki, jeśli realnie nie jest używany przez użytkowników
- `batch_size` z głównego UI; może zostać jako ustawienie ukryte lub stała

### Co można zmienić

- rozszerzyć preview o kolumny `BPM`, `Tonacja`, `Duration`, `Format`, `Źródło metadanych`
- przenieść `batch_size` i regex filename patterns do `Advanced`
- zamienić pole rozszerzeń na listę checkboxów z presetami
- dodać czytelny raport po imporcie: liczba zaimportowanych, zaktualizowanych, pominiętych, błędnych, zdeduplikowanych
- rozszerzyć `AUDIO_EXTENSIONS` o `.wma` i `.opus`
- rozważyć streaming scan/import zamiast pełnego `list(iter_audio_files(...))`

### Co można dodać

- drag & drop folderu/pliku na główne okno
- watchfolder / auto re-scan
- deduplikację przy imporcie na poziomie `path`, `hash`, opcjonalnie `fingerprint`
- import playlist `M3U/PLS`
- mini preview player i okładkę w kroku preview
- ETA skanowania/importu
- tryb "Import + Auto AI tagging nowych plików"

### Sugestie własne

- najwyższą wartość ma drag & drop na główne okno oraz deduplikacja już na etapie importu
- warto uprościć kreator do "folder -> preview -> import", a resztę przenieść do `Advanced`
- potrzebny jest jawny model "confidence źródła metadanych", bo dziś pipeline jest bogaty, ale nieprzezroczysty

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie; największe ryzyko dotyczy zmian w pipeline fallbacków
- Zależności: `core/audio.py`, `data/repository.py`, ewentualnie przyszły system duplikatów i watchfolder

---

## 2. Library Browser - widok list/grid

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/main_window.py`
- `lumbago_app/ui/models.py`

Aktualny stan:

- `QTableView` + `TrackTableModel` z 27 kolumnami
- `QListView` + `TrackGridDelegate`
- search działa przez `TrackFilterProxy` po `title/artist/album`
- filtry po `genre`, `key`, `bpm_min`, `bpm_max`
- grid używa pseudo-waveformu generowanego ze `seed` ścieżki
- playlisty filtrują widok, smart playlisty działają przez JSON rules

### Mocne strony

- solidny model tabeli z wieloma kolumnami i formatterami
- działa sortowanie, resize i chowanie kolumn
- jest zarówno list, jak i grid
- grid/list są spięte z tym samym modelem danych
- sidebar playlist już istnieje i działa

### Problemy

- `UX`: 27 kolumn domyślnie to za dużo i przytłacza
- `UX`: grid karta 140x160 jest mała, a pseudo-waveform wygląda wiarygodniej niż jest
- `UX`: brak presetów kolumn pod różne style pracy
- `UX`: brak inline statusów jakości metadanych, AI, braków artwork
- `Core`: search nie obejmuje `tags`, `mood`, `energy`, `year`, `rating`
- `Perf`: model i widoki ładują wszystko naraz; brak paginacji, lazy loading okładek i realnej optymalizacji pod bardzo duże biblioteki
- `Arch`: biblioteka jest mocno związana z `MainWindow`, a logika filtrów siedzi częściowo w `TrackFilterProxy`, częściowo w UI

### Co można usunąć

- pseudo-waveform z `TrackGridDelegate`, jeśli nie zostanie zastąpiony prawdziwym waveformem
- część technicznych kolumn z domyślnego widoku, zwłaszcza `sample_rate`, `hash`, `fingerprint`, `mtime`

### Co można zmienić

- ograniczyć domyślny zestaw kolumn do 10-12 najważniejszych
- zwiększyć rozmiar grid card i artwork
- dodać toolbar z presetami widoku: `DJ`, `Metadata`, `Technical`, `Full`
- rozbudować search/filter o `rating`, `year`, `energy`, `mood`, `AI tags`
- zastąpić surowy join tagów badge'ami
- dodać licznik wyników i aktywnych filtrów

### Co można dodać

- inline rating w tabeli
- kolorowanie wg energii lub nastroju
- ikony statusu: kompletne tagi, brak cover, AI tagged, recognition confidence
- "Now Playing" marker
- lazy loading okładek
- FTS5 i/lub pełnotekstowe wyszukiwanie w bazie

### Sugestie własne

- z punktu widzenia DJ-a najważniejsze są presety kolumn i szybkie skanowanie wzrokiem po `BPM`, `Key`, `Energy`, `Rating`
- pseudo-waveform warto usunąć wcześniej niż później, bo buduje fałszywe oczekiwania
- smart playlisty i filtry zasługują na bycie pełnoprawnym systemem pracy, a nie tylko dodatkiem

### Priorytet, ryzyko, zależności

- Priorytet: `P0`
- Ryzyko: średnie; największe przy optymalizacjach dużych bibliotek
- Zależności: `ui/models.py`, `data/repository.py`, przyszły FTS/paginacja

---

## 3. Detail Panel - edycja tagów

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/main_window.py`

Aktualny stan:

- panel pokazuje tekstowy podgląd wybranego tracka
- pola edycyjne: `title`, `artist`, `album`, `year`, `genre`, `bpm`, `key`, `loudness`
- jest podgląd okładki, zmiana okładki, zapis do DB, zapis tagów do pliku, czyszczenie tagów, historia zmian
- waveform jest statycznym obrazem PNG z `generate_waveform()`

### Mocne strony

- detail panel nie jest tylko viewerem; pozwala edytować i zapisywać
- zapis do DB jest logowany przez `add_change_log()`
- jest szybki podgląd cover i waveform
- można zapisać tagi bezpośrednio do pliku oraz przeładować je z pliku

### Problemy

- `UX`: zapis wymaga ręcznego kliknięcia
- `UX`: zakres pól jest węższy niż opis historyczny; brak `comment`, brak pełniejszego panelu analitycznego
- `UX`: waveform jest statyczny i niepołączony z cue editing
- `Core`: `loudness` jest read-only, ale nie ma czytelnego kontekstu co oznacza
- `Safety`: brak autosave z debounce, ale też brak undo dla zmian z panelu poza ręcznym odtworzeniem z historii
- `Arch`: detail panel i logika zapisu siedzą w `MainWindow`

### Co można usunąć

- tekstowy blok `detail_text`, jeśli panel formularza ma być głównym miejscem pracy

### Co można zmienić

- dodać autosave z debounce albo przynajmniej "dirty state"
- rozszerzyć panel o `comment`, `rating`, `mood`, `energy`, `play count`, `artwork status`
- zwiększyć cover preview
- zamienić waveform PNG na widget lub przynajmniej klikany timeline

### Co można dodać

- przycisk `Tap BPM`
- przycisk `Auto key`
- wskaźnik jakości tagów
- related tracks tego samego artysty
- odtwarzanie z kliknięciem w waveform
- undo dla ostatniej zmiany z detail panelu

### Sugestie własne

- tu największy zwrot da `dirty state + autosave/debounce`
- historia zmian powinna być ściślej połączona z panelem i umożliwiać przywrócenie wartości bez ręcznego przepisywania

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: niskie do średniego
- Zależności: `data/repository.py`, `change_log`, `core/waveform.py`, przyszły undo/restore

---

## 4. Player

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/main_window.py`

Aktualny stan:

- player dock na dole okna
- `QMediaPlayer` + `QAudioOutput`
- przyciski: `Odtwarzaj/Pauza`, `Stop`
- seek slider i licznik czasu
- `Cue A`, `Cue B`, `Skok A`, `Skok B`, `Loop A-B`, `Auto-cue`
- głośność i `Prev/Next` nie są obecnie zaimplementowane w UI, mimo wcześniejszych opisów
- multimedia są domyślnie wyłączone, gdy `LUMBAGO_DISABLE_MULTIMEDIA=1`

### Mocne strony

- dock player jest już wpięty w główne workflow
- cue/loop istnieją i działają na poziomie podstawowym
- timeline aktualizuje pozycję i czas
- player jest zintegrowany z wyborem tracka z tabeli

### Problemy

- `UX`: brak `Prev/Next`, brak volume slidera w aktualnym kodzie
- `UX`: brak hot cues 1-8, brak pozostałego czasu, brak wizualnego beat gridu
- `UX`: obecność `Stop` ma mniejszą wartość niż `Prev/Next` dla DJ-skiego workflow
- `Core`: player polega na `MainWindow` i wybranym wierszu, nie ma jasnej kolejki odtwarzania
- `Perf`: brak optymalizacji lub fallbacku dla długich plików / problemów z multimedia init
- `Arch`: cały player jest osadzony w `MainWindow`

### Co można usunąć

- `Stop` jako osobny priorytetowy przycisk, jeśli potrzeba miejsca na `Prev/Next` i hot cues
- `Loop A-B` z głównego rzędu, jeśli hot cues i waveform staną się ważniejsze

### Co można zmienić

- dodać `Prev/Next`
- dodać opcję czasu pozostałego
- lepiej połączyć cue points z detail panelem i waveformem
- jawnie pokazywać, czy multimedia są wyłączone

### Co można dodać

- hot cues 1-8
- pitch control i key lock
- waveform z kursorem w docku
- sync indicator BPM z poprzednim trackiem
- volume slider
- mini kolejkę

### Sugestie własne

- w obecnym stadium najpierw warto dowieźć `Prev/Next`, głośność i czytelny playback state
- dopiero potem przechodzić do hot cues, waveformu i funkcji bardziej DJ-performance

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie; zależność od `QtMultimedia` i środowiska użytkownika
- Zależności: `QMediaPlayer`, waveform, cue system, kolejkowanie

---

## 5. AI Tagger

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/ai_tagger_dialog.py`
- `lumbago_app/services/ai_tagger.py`
- `lumbago_app/core/services.py`

Aktualny stan:

- dialog otwiera się i od razu uruchamia `_analyze()`
- tryb lokalny używa `heuristic_analysis()`
- tryb cloud wspiera `openai`, `gemini`, `grok`, `deepseek`
- optional `AutoMetadataFiller` może wcześniej uzupełnić część braków przez AcoustID/MusicBrainz/Discogs
- wyniki są wyświetlane w tabeli i zapisywane do `tags` przez `replace_track_tags()`

### Mocne strony

- istnieje realne rozróżnienie local/cloud
- dialog jest batchowy i pokazuje progres
- jest walidacja wyniku AI przez `_sanitize_ai_result()`
- wyniki AI trafiają do tabeli tagów z `source` i `confidence`

### Problemy

- `UX`: dialog analizuje od razu po otwarciu, bez wyraźnego etapu decyzji użytkownika
- `UX`: auto-fetch z internetu jest trudny do zrozumienia dla mniej technicznych użytkowników
- `Core`: lokalna heurystyka oparta o BPM progi jest zbyt prymitywna
- `Core`: prompt cloud jest po polsku i zbyt wąski jak na różne modele
- `Core`: local confidence jest zabetonowane na `0.4`
- `Core`: w `AiTaggerDialog` jest realny błąd indeksu kolumny - combobox akcji jest tworzony w kolumnie 9, a `_apply_all()` i `_set_all_actions()` czytają kolumnę 6, więc Accept/Reject działa niezgodnie z intencją
- `Safety`: brak historii poprzednich wyników AI dla tracka
- `Arch`: część polityki walidacji siedzi w UI dialogu, a nie w warstwie serwisu

### Co można usunąć

- `_below_confidence()` jako logika w UI, jeśli decyzja o progach ma należeć do serwisu/policy layer
- `description` jako obowiązkowe pole promptu, jeśli nie daje użytecznej wartości użytkowej

### Co można zmienić

- przenieść analizę za kliknięcie `Analizuj`
- ujednolicić prompt na English i na JSON-only
- liczyć confidence lokalnie na podstawie liczby wiarygodnych przesłanek, nie tylko BPM
- przenieść politykę walidacji do warstwy `services/ai_tagger.py`
- naprawić obsługę kolumny akcji w dialogu

### Co można dodać

- tryb `fill missing only` vs `overwrite allowed`
- `auto-accept` dla wysokiej pewności
- porównanie providerów side-by-side
- historia wyników AI per utwór
- ETA batcha
- preview audio dla zaznaczonego wiersza

### Sugestie własne

- najpierw naprawić błąd kolumny i auto-start analizy; bez tego dialog sprawia wrażenie bardziej dojrzałego niż jest
- lokalny tagger warto przebudować na zestaw heurystyk oparty o `BPM`, `genre`, `year`, `format`, `existing tags`, a nie tylko BPM

### Priorytet, ryzyko, zależności

- Priorytet: `P0`
- Ryzyko: średnie; największe przy zmianie polityk merge/overwrite/confidence
- Zależności: `services/ai_tagger.py`, `core/services.py`, `metadata_enricher.py`, `data/repository.py`

---

## 6. Audio Recognizer i Metadata Enrichment

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/recognition_queue.py`
- `lumbago_app/services/recognizer.py`
- `lumbago_app/services/metadata_enricher.py`
- `lumbago_app/services/metadata_providers.py`

Aktualny stan:

- `RecognitionBatchWorker` batchowo uruchamia `MetadataEnricher.enrich_track()`
- `AcoustIdRecognizer` używa `fpcalc` i AcoustID API
- `MetadataEnricher.enrich_track()` robi ścieżkę: fingerprint -> AcoustID -> MusicBrainz -> cover art
- wyszukiwanie tekstowe MusicBrainz i Discogs istnieje, ale nie jest używane przez `RecognitionBatchWorker`
- cache metadanych jest w SQLite przez `MetadataCacheOrm`

### Mocne strony

- pipeline recognition oparty o fingerprint jest sensowny jako źródło prawdy
- jest cache z TTL
- cover art archive już działa
- jest walidacja kandydatów przez similarity policy

### Problemy

- `UX`: worker pokazuje tylko progres liczbowy; nie pokazuje "co jest teraz przetwarzane"
- `UX`: brak Accept/Reject przed zapisaniem wyników do bazy
- `Core`: `RecognitionBatchWorker` nie korzysta z fallback search/Discogs, mimo że taka logika istnieje w `AutoMetadataFiller`
- `Core`: timeouty providerów są krótkie i bez retry
- `Core`: brak jawnej polityki, kiedy Discogs ma wygrać nad MusicBrainz
- `Safety`: brak łatwego rollbacku błędnego enrichmentu partii
- `Arch`: mamy dwie pokrewne ścieżki enrichmentu - `RecognitionBatchWorker` i `AutoMetadataFiller` - które częściowo dublują odpowiedzialność

### Co można usunąć

- niepotrzebne dublowanie ścieżek enrichera, jeśli jedna polityka pipeline może obsłużyć zarówno recognition, jak i AI auto-fill

### Co można zmienić

- ujednolicić pipeline recognition i auto-fill
- dodać retry z exponential backoff
- zwiększyć timeouty do rozsądnego poziomu
- pokazywać bieżący track w progress dialogu
- jawnie rozdzielić `recognition result` od `applied metadata`

### Co można dodać

- panel Accept/Reject jak w AI Taggerze
- ręczne wyszukiwanie dla pojedynczego tracka
- Last.fm / Spotify jako dodatkowe źródła gatunku i popularności
- tryb offline z cache-only
- ranking źródeł i politykę merge

### Sugestie własne

- najważniejszy brak to brak etapu akceptacji wyniku przed zapisem
- warto zbudować jeden wspólny "metadata resolution pipeline", zamiast osobnych pół-równoległych ścieżek

### Priorytet, ryzyko, zależności

- Priorytet: `P0`
- Ryzyko: średnie do wysokiego; bezpośredni wpływ na poprawność biblioteki
- Zależności: `fpcalc`, AcoustID, MusicBrainz, Discogs, cache, change log

---

## 7. Wykrywanie duplikatów

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/duplicates_dialog.py`
- `lumbago_app/core/services.py`

Aktualny stan:

- dialog wspiera metody `Hash`, `Tagi`, `Fingerprint`, `Etapowo`
- staged scan robi: stat -> hash -> fingerprint
- można zaznaczać, przenosić, scalać metadane, usuwać, eksportować CSV
- merge uzupełnia brakujące pola z dzieci do pierwszego tracka w grupie

### Mocne strony

- jak na lokalną aplikację to bogaty zestaw metod
- staged scan ogranicza koszt fingerprintów
- jest eksport raportu i przenoszenie zamiast samego usuwania
- aktualizowane są `file_size`, `mtime`, `hash`, `fingerprint`

### Problemy

- `UX`: tree nie daje side-by-side porównania metadanych
- `UX`: brak odsłuchu i brakuje "smart keep"
- `UX`: zaznaczanie duplikatów zostawia pierwszy z grupy bez czytelnego uzasadnienia
- `Core`: metoda `Tagi` daje ryzyko false positives
- `Safety`: delete jest twardym usunięciem z dysku i bazy
- `Core`: merge działa tylko do pierwszego tracka i bez wyboru mastera
- `Arch`: część logiki selekcji i merge jest zaszyta w dialogu

### Co można usunąć

- metodę `Tagi` jako domyślnie promowaną
- `Zaznacz duplikaty` bez polityki `keep best`

### Co można zmienić

- dodać sortowanie grup i child rows
- dodać jawny wybór master tracka
- uczynić delete operacją soft lub co najmniej poprzedzać ją automatycznym backupem
- pokazać scoring i powód uznania za duplikat

### Co można dodać

- `Smart keep` z regułami: lepszy format, bitrate, tag completeness, artwork, play count
- odsłuch tracka z poziomu dialogu
- side-by-side metadata diff
- similarity threshold dla fingerprint
- auto-merge najlepszych tagów

### Sugestie własne

- `Smart keep + soft delete` to najważniejszy kierunek, bo radykalnie zmniejsza ryzyko przypadkowego uszkodzenia biblioteki
- staged scan warto zostawić jako domyślny, ale uprościć jego komunikację w UI

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: wysokie przy operacjach delete/move
- Zależności: backup, file operations, future undo/restore

---

## 8. Renamer

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/renamer_dialog.py`
- `lumbago_app/core/renamer.py`

Aktualny stan:

- wzorzec domyślny `{artist} - {title}`
- wspierane pola: `{artist}`, `{title}`, `{album}`, `{genre}`, `{bpm}`, `{key}`, `{index}`, `{index:03}`
- preview pokazuje starą nazwę, nową nazwę i status konfliktu
- apply wykonuje rename i zapisuje historię do `rename_history.json`
- undo cofa tylko ostatni batch

### Mocne strony

- logika planu rename jest oddzielona od UI
- są konflikty w planie i detekcja istniejących plików
- undo istnieje

### Problemy

- `UX`: brak live preview podczas pisania
- `UX`: brak presetów i buildera szablonów
- `UX`: brak ostrzeżenia o obcinaniu nazw do 180 znaków
- `Core`: jedno undo dla ostatniej operacji to za mało
- `Safety`: apply idzie od razu na realnych plikach, bez trybu copy/sandbox
- `Core`: brak `year` mimo że pole istnieje w modelu

### Co można usunąć

- `index/index:03` z głównej listy sugerowanych tokenów, jeśli mają niski realny użytek

### Co można zmienić

- dodać `year`, `format`, `bitrate`, `duration`
- dodać warning o truncation
- pokazać preview na żywo i status konfliktów w czasie wpisywania
- rozbudować historię rename do listy operacji, nie jednego snapshotu

### Co można dodać

- presety nazw
- `Copy instead of move`
- regex find/replace advanced
- case transform
- test pattern on selected file

### Sugestie własne

- szybkie zwycięstwo to: `{year}`, presety i live preview
- tryb `copy` jest ważny dla użytkowników, którzy nie ufają od razu masowemu rename

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie
- Zależności: file operations, backup, history/undo

---

## 9. XML Converter

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/xml_converter_dialog.py`
- `lumbago_app/ui/xml_import_dialog.py`
- `lumbago_app/services/xml_converter.py`
- `lumbago_app/ui/main_window.py` eksport playlisty do VirtualDJ

Aktualny stan:

- osobny dialog konwersji Rekordbox -> VirtualDJ
- osobny dialog importu Rekordbox lub VirtualDJ do bazy
- parser Rekordbox, parser VirtualDJ, eksport VirtualDJ
- eksport playlisty z `MainWindow` do VirtualDJ XML

### Mocne strony

- podstawowa ścieżka import/export działa
- logika parserów jest odseparowana od UI
- można użyć XML importu jako prostego bootstrapu metadanych

### Problemy

- `UX`: dwa osobne dialogi są mało spójne
- `UX`: brak preview mapowania i brak walidacji ścieżek przed importem
- `Core`: brak hot cues i cue points
- `Core`: brak Traktor NML mimo historycznych notatek
- `Core`: eksport jest w praktyce prostym mapowaniem metadanych, nie "DJ migration"
- `Safety`: brak dry-run z podsumowaniem zmian przed importem do bazy

### Co można usunąć

- rozdział na dwa dialogi, jeśli finalny workflow ma być jeden: `import / convert / preview`

### Co można zmienić

- scalić import i conversion preview w jedno narzędzie
- dodać podsumowanie liczby tracków, brakujących ścieżek, nieznanych pól
- doprecyzować mapowanie `Key` vs `Tonality`

### Co można dodać

- Traktor NML
- hot cues / `POSITION_MARK` / `Poi`
- eksport playlist, nie tylko collection
- walidację ścieżek
- preview XML przed eksportem/importem

### Sugestie własne

- bez hot cues i cue points narzędzie jest przydatne bardziej do katalogowania niż do realnej migracji DJ workflow
- połączenie obu dialogów w jedno narzędzie da znacznie lepszy UX

### Priorytet, ryzyko, zależności

- Priorytet: `P2`
- Ryzyko: średnie
- Zależności: playlisty, cue system, parsery XML

---

## 10. Playlisty

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/main_window.py`
- `lumbago_app/ui/playlist_dialog.py`
- `lumbago_app/ui/playlist_order_dialog.py`
- `lumbago_app/data/repository.py`

Aktualny stan:

- sidebar pokazuje playlisty i smart playlisty
- CRUD jest wspierany
- smart playlisty mają reguły `search`, `genre`, `key`, `bpm_min`, `bpm_max`
- drag & drop do playlist jest realizowany przez `eventFilter`
- reorder dialog istnieje dla zwykłych playlist
- `list_playlists()` zwraca fallbackowe nazwy, jeśli baza jest pusta

### Mocne strony

- playlisty są realną częścią głównego workflow
- reorder i smart rules już istnieją
- drag & drop działa

### Problemy

- `UX`: brak licznika tracków przy nazwie
- `UX`: smart rules są dość ubogie
- `UX`: brak statystyk playlisty i eksportu do M3U/PLS
- `Core`: fallbackowe playlisty istnieją tylko jako nazwy, a nie pełne rekordy z opisem i metadanymi
- `Core`: reguły są w JSON stringu, co utrudnia dalszą ewolucję
- `Arch`: filtracja smart playlist siedzi w `MainWindow._filter_tracks_by_rules()`

### Co można usunąć

- domyślną playlistę `Set Preparation`, jeśli nie ma faktycznego workflow ani onboardingowego znaczenia

### Co można zmienić

- dodać licznik utworów w sidebarze
- rozszerzyć reguły smart o `year`, `rating`, `energy`, `mood`, `date_added`
- przenieść logikę smart playlist z `MainWindow` do repo/service layer

### Co można dodać

- eksport do `M3U/PLS/txt`
- import `M3U`
- foldery playlist
- statystyki playlisty
- `Nowo dodane` jako auto-playlista
- kolory lub ikony playlist

### Sugestie własne

- najpierw warto dodać badge z liczbą tracków i eksport M3U
- smart playlisty mają potencjał na jedną z najlepszych funkcji produktu, ale potrzebują wydzielenia z `MainWindow`

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: niskie do średniego
- Zależności: repozytorium, filtracja, eksport

---

## 11. Analiza audio - LUFS, BPM grid, key, waveform

### Obecny stan i źródła

Źródła:

- `lumbago_app/services/loudness.py`
- `lumbago_app/services/beatgrid.py`
- `lumbago_app/services/key_detection.py`
- `lumbago_app/core/waveform.py`
- `lumbago_app/ui/main_window.py`

Aktualny stan:

- loudness analysis przez `ffmpeg loudnorm`
- normalizacja do nowego pliku
- beatgrid liczony jako równy interwał na podstawie znanego BPM
- auto-cue to `cue_in=0`, `cue_out=duration-10s`
- key detection przez `librosa chroma_cqt`, z opcją Camelot
- waveform PNG przez `ffmpeg showwavespic`, fallback do placeholdera

### Mocne strony

- cały pakiet analiz DJ-oriented już istnieje
- key detection i loudness są używalne jako v1
- cache analizy istnieje

### Problemy

- `UX`: waveform jest statyczny, bez interakcji i bez cue editing
- `UX`: beatgrid nie jest realnie wizualizowany w playerze
- `Core`: `compute_beatgrid()` nie wykrywa beatów, tylko rozkłada je równomiernie z istniejącego BPM
- `Core`: brak BPM detection dla plików bez metadanych
- `Core`: placeholder waveform jest mylący
- `Safety`: normalizacja tworzy nowy plik, ale UI nie prowadzi użytkownika przez konsekwencje takiej operacji

### Co można usunąć

- `generate_waveform_placeholder()` jako "neon waveform", jeśli ma udawać prawdziwą analizę
- udawanie beatgridu tam, gdzie BPM nie pochodzi z rzetelnego detektora

### Co można zmienić

- ograniczyć key detection do pierwszych 60 sekund lub wybranego okna analitycznego
- generować dane waveformu do dalszego renderu, nie tylko PNG
- odseparować "BPM z tagów" od "BPM wykryte"

### Co można dodać

- BPM detection przez `librosa`
- interaktywny waveform widget
- RMS / energy per segment
- spectral preview
- auto-scan BPM w tle po imporcie

### Sugestie własne

- najważniejsza jest uczciwość wobec użytkownika: waveform placeholder i pseudo-beatgrid trzeba wyraźnie odróżnić od realnej analizy
- pierwszym praktycznym krokiem powinno być wykrywanie BPM dla plików bez tagów

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie; zależności od `ffmpeg`, `librosa`, jakości plików
- Zależności: import, detail panel, player

---

## 12. Historia zmian (audit log)

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/change_history_dialog.py`
- `lumbago_app/data/repository.py`
- `lumbago_app/data/schema.py`

Aktualny stan:

- `ChangeLogOrm` przechowuje pole, starą wartość, nową wartość, źródło i datę
- `MainWindow._save_detail_changes()` loguje zmiany z detail panelu
- `ChangeHistoryDialog` pokazuje tabelę historii dla jednego tracka

### Mocne strony

- audit log istnieje naprawdę, a nie tylko jako plan
- źródło zmiany jest przechowywane
- historia jest zintegrowana z detail panelem

### Problemy

- `UX`: brak filtrowania i przywracania wartości
- `UX`: `source` jest surowym stringiem
- `Core`: nie wszystkie operacje masowe i automatyczne logują się równie bogato
- `Safety`: brak "restore this value" lub "restore snapshot"

### Co można usunąć

- nic krytycznego do usuwania

### Co można zmienić

- rozbudować logowanie zmian z bulk edit, AI, recognizer, rename, duplicates merge
- ładniej formatować źródła
- dodać filtr po polu, źródle i dacie

### Co można dodać

- `Przywróć tę wartość`
- globalny widok historii
- eksport CSV
- grupowanie po źródle
- diff view

### Sugestie własne

- audit log stanie się naprawdę użyteczny dopiero wtedy, gdy będzie dało się na jego podstawie cofać zmiany
- to jedna z najlepszych funkcji bezpieczeństwa produktu, warto ją rozbudować wcześniej niż później

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: niskie
- Zależności: wszystkie moduły modyfikujące dane

---

## 13. Ustawienia i API keys

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/settings_dialog.py`
- `lumbago_app/core/config.py`

Aktualny stan:

- `Settings` ładowane są z `settings.json`, env, Windows Registry i opcjonalnego `api_keys.json`
- dialog ma ponad 15 pól dla API, modeli, regexów i cache TTL
- klucze są zapisywane do `settings.json` jako plaintext
- `SettingsOrm` istnieje w bazie, ale `load_settings()` i `save_settings()` działają na pliku JSON, env i registry

### Mocne strony

- elastyczne źródła konfiguracji
- sensowne wartości domyślne dla providerów cloud
- fallback do `.lumbago_data`, gdy `APPDATA` nie jest zapisywalne

### Problemy

- `UX`: wszystko jest w jednym formularzu
- `UX`: brak testowania kluczy i diagnostyki
- `Safety`: plaintext JSON dla API keys
- `Core`: `SettingsOrm` dubluje koncepcję przechowywania ustawień, ale nie jest główną ścieżką
- `Arch`: model konfiguracji jest rozproszony między plik, env, registry i optional file, bez jasnego UI, które pokazuje faktyczne źródło wartości

### Co można usunąć

- pola `*_base_url` z głównego formularza i przenieść do `Advanced`
- tabelę `SettingsOrm`, jeśli projekt definitywnie zostaje przy pliku JSON

### Co można zmienić

- podzielić ustawienia na zakładki
- dodać przyciski `Test connection` / `Test key`
- wyświetlać źródło każdej wartości: `settings.json`, env, registry
- jasno określić jeden primary store ustawień

### Co można dodać

- DPAPI / `win32crypt` dla kluczy
- import/export ustawień
- profile ustawień
- sekcję diagnostyczną: `ffmpeg`, `fpcalc`, DB, cache, API reachability

### Sugestie własne

- największą wartość da `Test key` i uporządkowanie źródeł konfiguracji
- trzeba zdecydować, czy `SettingsOrm` zostaje, czy wypada; obecna hybryda komplikuje model mentalny

### Priorytet, ryzyko, zależności

- Priorytet: `P0`
- Ryzyko: średnie; dotyczy bezpieczeństwa i migracji ustawień
- Zależności: cloud AI, recognizer, metadata providers, przyszła diagnostyka

---

## 14. Baza danych

### Obecny stan i źródła

Źródła:

- `lumbago_app/data/db.py`
- `lumbago_app/data/schema.py`
- `lumbago_app/data/repository.py`

Aktualny stan:

- SQLite + SQLAlchemy ORM
- sensowne indeksy i check constraints
- repozytorium obejmuje tracki, tagi, playlisty, audit log i metadata cache
- `_ensure_track_columns()` nadal istnieje jako runtime migration helper

### Mocne strony

- model danych jest dość szeroki i już obejmuje rzeczy DJ-specyficzne
- mamy indeksy na podstawowych polach tracka
- check constraints na `rating`, `bpm`, `energy`

### Problemy

- `Core`: `list_tracks()` ładuje wszystko naraz
- `Perf`: brak FTS, brak paginacji, brak explicit eager loading dla relacji
- `Arch`: `repository.py` jest zbyt szerokie i skupia za dużo różnych odpowiedzialności
- `Arch`: `_ensure_track_columns()` to nadal techniczny dług mimo obecności Alembica w historii projektu
- `Core`: `SettingsOrm` nie jest spójny z realnym mechanizmem ustawień

### Co można usunąć

- `_ensure_track_columns()` po pełnej migracji danych
- `SettingsOrm`, jeśli konfiguracja ma zostać poza DB

### Co można zmienić

- podzielić repozytorium na mniejsze moduły
- dodać paginację lub przynajmniej fetch policy dla listowania tracków
- rozważyć `WAL mode`
- rozważyć `FTS5` dla search

### Co można dodać

- indeks na `date_added`
- statystyki biblioteki
- maintenance tasks: `VACUUM`, cleanup cache

### Sugestie własne

- przy tej skali funkcji największy zwrot da FTS5 oraz ograniczenie "load all tracks on startup"
- repozytorium warto podzielić funkcjonalnie: `tracks`, `playlists`, `audit`, `cache`

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie do wysokiego przy zmianach migracyjnych
- Zależności: search, library browser, settings, cache

---

## 15. Backup

### Obecny stan i źródła

Źródła:

- `lumbago_app/core/backup.py`
- `lumbago_app/ui/main_window.py`

Aktualny stan:

- backup kopiuje DB i `settings.json` do katalogu `backups/`
- wykonywany przy starcie i przy zamknięciu aplikacji
- limit backupów jest domyślnie `10`

### Mocne strony

- backup już istnieje i działa automatycznie
- implementacja jest prosta i przewidywalna

### Problemy

- `Safety`: backup nie jest powiązany z operacjami destrukcyjnymi typu delete duplicates / reset library / mass rename
- `UX`: brak UI restore
- `Core`: brak kompresji i brak konfigurowalnego limitu retencji

### Co można usunąć

- nic krytycznego do usuwania

### Co można zmienić

- dodać pre-operation backup dla operacji ryzykownych
- przenieść limit retencji do ustawień
- dodać metadane backupu i czytelną nazwę operacji

### Co można dodać

- restore dialog
- ZIP compression
- auto-backup wg harmonogramu
- backup verification / smoke restore

### Sugestie własne

- backup powinien być obowiązkowym guardrail przed `reset_library`, `delete selected duplicates`, `bulk destructive operations`

### Priorytet, ryzyko, zależności

- Priorytet: `P0`
- Ryzyko: niskie
- Zależności: delete/reset/rename/duplicates, settings

---

## 16. Tag Compare

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/tag_compare_dialog.py`

Aktualny stan:

- dialog działa na liście tracków, z nawigacją `Prev/Next`
- pokazuje stare i nowe tagi oraz tabelę z edytowalnym polem `Nowe`
- jest `Zapisz dla tego utworu`, `Zapisz wszystkie`, `Zastosuj tylko różnice`

### Mocne strony

- funkcja realnie istnieje i umożliwia pracę na wielu trackach
- preview `old/new` jest czytelne
- można zachować pending edits per track

### Problemy

- `UX`: etykieta kolumny `Użyj starego` nie zgadza się z faktycznym przyciskiem `Użyj`, który kopiuje starą wartość do nowej
- `UX`: brak filtra `pokaż tylko różnice`
- `UX`: brak wyróżnienia kolorami różnic
- `Core`: `_apply_diff_current()` jest mało czytelne z perspektywy użytkownika i utrudnia prosty model pracy
- `Safety`: zapis dzieje się od razu do pliku podczas `_apply_current()` / `_apply_all()`

### Co można usunąć

- `_apply_diff_current()` z głównego workflow, jeśli docelowo użytkownik i tak ma wybierać pola różniące się

### Co można zmienić

- poprawić etykietę i logikę przycisku w kolumnie 4
- pokazywać tylko tracki z różnicami
- dodać kolorystyczny diff

### Co można dodać

- batch rules typu "preferuj DB dla artist"
- apply all at end bez zapisu per track
- side-by-side większy cover/waveform

### Sugestie własne

- szybkie zwycięstwo to `show only differences + diff highlighting`
- długofalowo Tag Compare powinien być wspólnym patternem także dla recognition i AI tagger

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: niskie do średniego
- Zależności: audio tags I/O, history, compare workflows

---

## 17. Bulk Edit

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/bulk_edit_dialog.py`

Aktualny stan:

- checkbox + input dla `title`, `artist`, `album`, `genre`, `bpm`, `key`
- `Zastosuj` bez preview, bez diff, bez undo

### Mocne strony

- prosta i szybka operacja
- działa bezpośrednio na zaznaczonych trackach

### Problemy

- `UX`: brak preview i brak licznika zmian
- `UX`: brak trybu append/merge
- `Core`: `title` w bulk edit jest wysokiego ryzyka i niskiej praktycznej wartości
- `Safety`: brak undo i brak logu operacji masowej jako osobnego źródła

### Co można usunąć

- pole `title` z podstawowego bulk edit

### Co można zmienić

- dodać preview `before/after`
- logować `source=bulk_edit`
- pokazywać liczbę objętych tracków

### Co można dodać

- append mode
- autocomplete dla `genre` i `key`
- undo ostatniej operacji
- preset transformations

### Sugestie własne

- tu najwięcej daje preview przed apply oraz append mode dla `genre` i tagów opisowych

### Priorytet, ryzyko, zależności

- Priorytet: `P1`
- Ryzyko: średnie
- Zależności: change log, undo, selection model

---

## 18. Theme i UI

### Obecny stan i źródła

Źródła:

- `lumbago_app/ui/theme.py`
- `lumbago_app/ui/widgets.py`

Aktualny stan:

- `CYBER_QSS` jest rozbudowanym dark cyber stylem
- są gradienty, rounded corners, custom widgets, fade-in dialogów
- `AnimatedButton.enable_pulse()` jest używany dla wybranych CTA

### Mocne strony

- produkt ma własną tożsamość wizualną
- QSS jest spójne na poziomie kart, inputów, toolbarów i dialogów
- animacje dialogów i przycisków poprawiają perceived polish

### Problemy

- `UX`: pulse na ważnych przyciskach bywa rozpraszający
- `UX`: brak wariantów theme/density
- `Arch`: `theme.py` jest duże i ma sporo duplikacji/override'ów w arkuszu
- `Perf`: część efektów może być kosztowna na słabszych PC

### Co można usunąć

- pulse z przycisków produkcyjnych

### Co można zmienić

- uporządkować tokeny kolorystyczne i spacing
- dodać density settings
- dodać przynajmniej alternatywny wariant `Dark Minimal`

### Co można dodać

- light mode
- custom accent color
- globalny toggle animacji

### Sugestie własne

- theme jest już wystarczająco dobry jak na v1; większy zwrot da uporządkowanie interakcji niż całkowita przebudowa stylu

### Priorytet, ryzyko, zależności

- Priorytet: `P2`
- Ryzyko: niskie
- Zależności: settings, widgets, performance tuning

---

## Najważniejsze rozbieżności między opisami historycznymi a aktualnym kodem

- Player w kodzie ma `Play/Pause` i `Stop`, ale nie ma `Prev/Next` ani slidera głośności.
- Detail panel w kodzie nie ma pełnego zestawu pól z wcześniejszych opisów; ma głównie podstawowe pola plus `LUFS`.
- Recognition queue w aktualnym kodzie nie zapisuje ścieżki `AcoustID -> MusicBrainz -> Discogs`; batch worker używa tylko `enrich_track()` i nie daje etapu akceptacji.
- `reset_library()` w aktualnym kodzie nie usuwa `SettingsOrm`; czyści tracki, playlisty, tagi, change log i metadata cache.
- AI Tagger ma w aktualnym kodzie błąd logiczny w przypięciu kolumny akcji Accept/Reject.

---

## Top 10 priorytetów

1. `P0` Naprawić AI Tagger Accept/Reject i auto-start analizy.
2. `P0` Dodać pre-operation backup przed delete/reset/rename/duplicates.
3. `P0` Dodać testowanie kluczy API i uporządkować model źródeł ustawień.
4. `P0` Dodać etap akceptacji wyników Recognizera przed zapisem.
5. `P1` Uprościć import UX i dodać deduplikację już przy imporcie.
6. `P1` Ograniczyć domyślny widok tabeli i dodać presety kolumn.
7. `P1` Dodać eksport playlist do `M3U`.
8. `P1` Dodać `Prev/Next`, volume i lepszy playback state w playerze.
9. `P1` Dodać smart keep + soft delete w duplikatach.
10. `P1` Wydzielić krytyczną logikę z `ui/main_window.py` do warstw service/controller.

---

## Szybkie wygrane: duży efekt / niski koszt

- naprawa kolumny akcji w AI Taggerze
- badge z liczbą tracków przy playlistach
- `{year}` w Renamerze
- live preview wzorca rename
- `show only differences` i kolorowanie diffów w Tag Compare
- `Test API key` w ustawieniach
- eksport playlisty do `M3U`
- usunięcie lub oznaczenie pseudo-waveformów

## Większe refaktory: duży efekt / większe ryzyko

- rozbicie `ui/main_window.py`
- ujednolicenie pipeline recognition / auto metadata / AI enrichment
- FTS5 i polityka pobierania tracków zamiast `load all`
- refaktoryzacja ustawień do jednego modelu źródeł i storage
- interaktywny waveform i cue editing

## Długi ogon: nice-to-have

- light mode
- Traktor NML
- Spotify / Last.fm
- stem separation
- cloud backup
- pełny DJ-style player z hot cues 1-8, pitch i key lock

---

## Roadmapa wdrożeniowa

### Faza 1. Bezpieczeństwo i UX krytyczny

| Pozycja | Efekt dla użytkownika | Moduły zależne | Ryzyko | Minimalne kryterium akceptacji |
| --- | --- | --- | --- | --- |
| Naprawa AI Tagger Accept/Reject | AI nie zapisuje błędnych zmian mimo akceptacji/odrzucenia | `ui/ai_tagger_dialog.py`, `services/ai_tagger.py` | Średnie | Akceptacja zapisuje tylko wybrane tracki, odrzucenie nic nie zmienia |
| Pre-operation backup | Operacje destrukcyjne są odwracalne | `core/backup.py`, `ui/main_window.py`, `ui/duplicates_dialog.py`, `core/renamer.py` | Niskie | Przed reset/delete/rename powstaje backup i jest widoczny do restore |
| Test API key i diagnostyka | Użytkownik wie, czy klucz działa, zanim uruchomi kosztowną operację | `ui/settings_dialog.py`, `core/config.py`, provider services | Średnie | Każdy klucz można zweryfikować z wynikiem sukces/błąd |
| Accept/Reject dla Recognizera | Błędne dopasowania nie psują biblioteki | `ui/recognition_queue.py`, `services/metadata_enricher.py` | Średnie | Batch recognition zapisuje tylko potwierdzone wyniki |

### Faza 2. Workflow biblioteki i player

| Pozycja | Efekt dla użytkownika | Moduły zależne | Ryzyko | Minimalne kryterium akceptacji |
| --- | --- | --- | --- | --- |
| Presety kolumn i lepszy browser | Biblioteka staje się czytelna dla DJ-a | `ui/models.py`, `ui/main_window.py` | Niskie | Widoki `DJ`, `Metadata`, `Technical` działają i są trwałe |
| Import UX + dedupe | Mniej ręcznej pracy i mniej duplikatów | `ui/import_wizard.py`, `core/audio.py`, duplicates/repo | Średnie | Import pokazuje duplikaty i pozwala je pominąć lub zaktualizować |
| Player v2 | Odtwarzanie jest wygodniejsze i bliższe workflow DJ | `ui/main_window.py` | Średnie | `Prev/Next`, volume, czytelny playback state i stabilne multimedia |
| Playlist badges + M3U export | Playlisty stają się realnym narzędziem pracy | `data/repository.py`, `ui/main_window.py` | Niskie | Sidebar pokazuje liczbę tracków, export M3U działa |

### Faza 3. AI / recognizer / enrichment

| Pozycja | Efekt dla użytkownika | Moduły zależne | Ryzyko | Minimalne kryterium akceptacji |
| --- | --- | --- | --- | --- |
| Heurystyki local AI v2 | Lepsze wyniki bez chmury | `core/services.py` | Niskie | Local AI uwzględnia więcej niż BPM i daje lepszy confidence |
| Unified metadata pipeline | Jedna polityka merge/overwrite/confidence | `services/metadata_enricher.py`, `services/ai_tagger.py` | Wysokie | AI auto-fill i recognition używają wspólnej polityki |
| Historia wyników AI i recognition | Większe zaufanie do automatyki | audit log, tag storage | Średnie | Dla tracka widać ostatnie wyniki i źródło zmian |

### Faza 4. Wydajność, DB i architektura

| Pozycja | Efekt dla użytkownika | Moduły zależne | Ryzyko | Minimalne kryterium akceptacji |
| --- | --- | --- | --- | --- |
| Rozbicie `MainWindow` | Łatwiejszy rozwój i mniej regresji | `ui/main_window.py` i wszystkie dialogi | Wysokie | Player, detail panel, browser i actions są w osobnych klasach/modułach |
| FTS5 i lepsze listowanie tracków | Szybsza praca na dużych bibliotekach | `data/schema.py`, `data/repository.py`, browser | Wysokie | Search pozostaje płynny na bibliotece 10k+ |
| Polityka ustawień i storage | Mniej chaosu w konfiguracji | `core/config.py`, `ui/settings_dialog.py`, `SettingsOrm` | Średnie | Jeden primary store i jasne źródło każdej wartości |

### Faza 5. Rozszerzenia DJ-ekosystemu

| Pozycja | Efekt dla użytkownika | Moduły zależne | Ryzyko | Minimalne kryterium akceptacji |
| --- | --- | --- | --- | --- |
| Smart keep + soft delete w duplikatach | Bezpieczniejsze czyszczenie biblioteki | duplicates, backup, file ops | Średnie | Dialog sam proponuje najlepszy plik do zachowania |
| XML v2 z cue/hotcue | Realna użyteczność migracyjna | XML, player, cue system | Wysokie | Cue/hotcue przechodzą między formatami w podstawowym zakresie |
| BPM detection i waveform widget | Bardziej profesjonalna analiza audio | beatgrid, waveform, player | Wysokie | Track bez BPM może dostać BPM i interaktywny waveform |

---

## Rekomendacje już częściowo zaimplementowane

- backup istnieje, ale trzeba go związać z ryzykownymi operacjami
- audit log istnieje, ale brakuje restore
- playlisty i smart playlisty istnieją, ale są ograniczone
- loudness, key detection i waveform istnieją, ale są mało zintegrowane z workflowem
- recognition i AI tagging istnieją, ale brak im etapu bezpiecznej akceptacji

## Rekomendacje blokowane przez architekturę

- pełna wydajność browsera przy 10k+ bez zmian w `repository.py` i sposobie ładowania danych
- czytelny metadata pipeline bez ujednolicenia rozproszonych logik enrichmentu
- większa przebudowa playera bez wydzielenia go z `MainWindow`
- ustawienia per profil bez uproszczenia modelu storage

## Rekomendacje możliwe od ręki bez przebudowy systemu

- naprawa AI Tagger action column
- dodanie `{year}` do Renamera
- dodanie eksportu playlisty do `M3U`
- dodanie liczników playlist
- `Test API key`
- uproszczenie import preview
- `show only differences` w Tag Compare
- wyłączenie pulse w produkcyjnych CTA

---

## Scenariusze walidacyjne dla rekomendacji `P0/P1`

- import dużego folderu 5k+ plików z mieszanymi tagami
- import z uszkodzonymi plikami i błędnymi JSON sidecar
- AI tagging z ręcznym odrzuceniem części wyników
- recognition z błędnym dopasowaniem MusicBrainz
- duplikaty z kombinacją FLAC/MP3/WAV tego samego utworu
- reset biblioteki po automatycznym backupie i restore
- rename 500 plików z konfliktami nazw i cofnięciem operacji
- eksport playlisty do `M3U` i `VirtualDJ XML`
- biblioteka 10k+ rekordów z intensywnym filtrowaniem po `BPM/Key/Genre`

## Wniosek końcowy

`Lumbago Music AI` ma już zaskakująco szeroki zakres funkcji, ale dziś bardziej przypomina ambitne, rozwijane MVP niż stabilne narzędzie do codziennej pracy na dużej bibliotece DJ-skiej. Największa szansa na skok jakości nie leży w dopisywaniu kolejnych modułów, tylko w poprawie bezpieczeństwa zmian, spójności metadanych, ergonomii biblioteki i rozbiciu monolitycznej logiki `MainWindow`.

Jeśli kolejność wdrożeń będzie trzymała się powyższych faz, produkt może przejść od "bogatego prototypu" do naprawdę wiarygodnego desktopowego managera biblioteki dla DJ-a bez konieczności pełnego przepisywania systemu od zera.
