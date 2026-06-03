# Audit analizy i tagowania

## 1. Aktualny przeplyw end-to-end

### Odczyt tagow i lokalnych metadanych

1. `core/audio.py::extract_metadata()` otwiera plik przez Mutagen i wypelnia `Track`.
2. Dla MP3/FLAC/OGG czyta bezposrednie tagi, a dla MP4/M4A dodatkowo przechodzi przez `read_tags()`.
3. Na koncu `apply_local_metadata()` dokleja dane z:
   - sidecar JSON,
   - `folder.json` / `metadata.json`,
   - nazwy pliku,
   - regexow z ustawien,
   - plikow CUE,
   - struktury katalogow.

### Analiza audio

1. W dialogu `AiTaggerDialog` pipeline worker decyduje, czy plik potrzebuje cech audio.
2. Gdy tak, `AudioFeatureExtractor` zapisuje tempo i cechy widmowe do cache.
3. `detect_key()` uzupelnia tonacje tylko wtedy, gdy pole `key` jest puste.
4. `enrich_track_with_analysis()` sklada wynik audio z prostymi heurystykami (`mood`, `energy`).

### Autotagowanie / AI

1. `DatabaseTagger` probuje rozpoznac plik przez AcoustID + MusicBrainz albo fallback text search.
2. `CloudAiTagger` pyta wybrane API tylko o pola brakujace lub wygladajace na szum.
3. `MultiAiTagger` skleja odpowiedzi providerow po najwyzszym `confidence`.
4. `_merge_analysis_into_track()` nadpisuje pola w `Track`.

### Wzbogacanie metadanych

1. `AutoMetadataFiller` / `MetadataEnricher` probuje dopelnic puste pola z lokalnej biblioteki i zrodel zewnetrznych.
2. Wynik wraca jako `MetadataFillReport`, ale jest uzywany glownie do auto-akceptacji i logu.

### Zapis nowych metadanych

1. W `AiTaggerDialog._apply_accepted()` decyzje uzytkownika sa zamieniane na:
   - update obiektu `Track`,
   - wpisy `TagOrm` przez `replace_track_tags()`,
   - zapis tagow do pliku przez `write_tags()`,
   - update rekordu DB przez `update_tracks()`.
2. W `MainWindow.AutoTagWorker` istnieje drugi, niezalezny przeplyw zapisu dla trybu "Autotagowanie (natychmiast)".

## 2. Glówne problemy

- Logika jest rozproszona miedzy `core/audio.py`, `services/ai_tagger.py`, `services/analysis_engine.py`, `services/autotag_rewrite.py`, `ui/ai_tagger_dialog.py` i `ui/main_window.py`.
- Sa dwa rownolegle silniki AI:
  - stary `services/ai_tagger.py`,
  - nowszy `services/analysis_engine.py`.
- Sa dwa osobne flow autotagowania:
  - dialog review (`AiTaggerDialog`),
  - szybki worker w `MainWindow`.
- Warstwa UI zawiera logike domenowa i zapis do pliku/DB, zamiast delegowac to do jednej uslugi.
- `AiTaggerDialog` mial zduplikowane metody cache AI; to utrudnialo utrzymanie i maskowalo realny kod aktywny w runtime.

## 3. Co warto uproscic lub zoptymalizowac

### Najwyzszy priorytet

- Wyciagnac zapis zmian z `AiTaggerDialog` i `AutoTagWorker` do jednej uslugi typu `metadata_writeback.py`.
- Wybrac jeden silnik AI:
  - albo utrzymac `ai_tagger.py`,
  - albo przeniesc calosc na `analysis_engine.py`.
- Ujednolicic cache:
  - jeden format klucza,
  - jeden format payloadu,
  - jeden podpis pliku.

### Sredni priorytet

- Rozbic `extract_metadata()` na male czytelne etapy:
  - read raw tags,
  - normalize canonical tags,
  - apply local metadata overlays.
- Zastapic listy typu `FIELDS`, `AI_FIELDS`, `FIELD_LABELS` jednym kontraktem pola z metadanymi:
  - nazwa,
  - label,
  - typ,
  - zrodla,
  - czy zapisujemy do pliku,
  - czy pole jest audio-derived.
- Ujednolicic walidacje wartosci:
  - rok,
  - BPM,
  - ISRC,
  - rating,
  - key.

### Nizszy priorytet

- Przeniesc logike "local metadata overlay" do osobnej klasy strategii.
- Dodac telemetryczny raport pola:
  - skad przyszla wartosc,
  - co nadpisala,
  - dlaczego zostala zaakceptowana.

## 4. Zmiany wykonane teraz

- Dodana zostala wspolna usluga zapisu metadanych: `services/metadata_writeback.py`.
  - Obsluguje jeden zapis do DB, pliku audio, tabeli tagow i changelogu.
  - Korzystaja z niej teraz oba flow: dialog review i szybki `AutoTagWorker`.
- Background enrichment zostal dopiety do tej samej sciezki writebacku.
  - `BackgroundAutotagWorker` i `BackgroundEnrichmentService` nie pisza juz lokalnie w roznych stylach.
  - Wspolny helper dostaje `PendingTrackWrite`, wiec DB, changelog i plik tagow ida jednym kontraktem.
- Usuniety zostal martwy kod z `AiTaggerDialog`:
  - nieuzywane panele audio i zrodel metadanych,
  - zduplikowane metody cache AI,
  - pomocnicza metoda `_analyze()`.
- Usunieta zostala opcja zmiany nazw plikow bezposrednio z dialogu autotagowania.
  - Powod: to dublowalo osobny renamer i mieszalo zapis tagow z operacja na nazwach plikow.
- Odchudzony zostal boczny panel w `MainWindow`.
  - Zostawione zostaly glowne akcje zwiazane z biblioteka i tagowaniem.
  - Usuniete z sidebara zostaly mniej centralne narzedzia: batch recognition, XML import/export i health report.

## 5. Rekomendowany nastepny krok

Najbardziej oplacalna zmiana architektoniczna to stworzenie jednej uslugi:

- wejscie:
  - `Track before`,
  - `Track proposed`,
  - lista zaakceptowanych pol,
  - `source`,
  - `confidence`;
- wyjscie:
  - update DB,
  - update file tags,
  - change log,
  - opcjonalny raport bledow.

W praktyce nastepny etap to doprowadzenie do tego samego wzorca rowniez dla wszystkich pozostalych background flow rozpoznania i zapisow, z jednym jawnie nazwanym miejscem odpowiedzialnosci.

To od razu upraszcza UI, testy i przyszle przejscie na jeden wspolny pipeline AI.

## 6. Macierz zrodel: tolerowane zapytania i pewnosc wyniku

To jest roboczy, trwały kontrakt dla pipeline rozpoznawania. W praktyce:
- im bardziej strukturalne zapytanie, tym mniej szumu,
- im bardziej wynik jest listą kandydatów, tym bardziej trzeba go walidowac drugim zrodlem,
- fingerprint nie jest jedynym punktem prawdy, tylko mocnym sygnalem pomocniczym.

| Zrodlo | Tolerowana forma zapytania | Typ wyniku | Ocena pewnosci |
|---|---|---|---|
| AcoustID | fingerprint audio / track id | lista trafien z score | bardzo mocny sygnal, ale nadal probabilistyczny |
| MusicBrainz | tekst z polami `recording`, `artist`, `title`, quotes, AND/field query | lista kandydatow rankingowanych | srednia do wysokiej, zalezy od precyzji query |
| ListenBrainz | strukturalne `artist_name` + `recording_name` (+ opcjonalnie `release_name`) | zwykle pojedynczy mapping / obiekt | wysoka, ale do potwierdzenia z drugim zrodlem |
| TheAudioDB | `s=artist&t=track` albo samo `t` / `s` | lista trackow, code bierze pierwszy hit | srednia |
| Discogs | `q` release-oriented, najlepiej `artist title` | lista rezultatow | srednia, lepsze dla label/year/style niz samej tozsamosci |
| iTunes | `term`, `entity=song`, limit 1 | pojedynczy hit z rankingu | srednia |
| Deezer | `artist:"X" track:"Y"` albo prosty `q` | lista wynikow | srednia do niskiej |
| Musixmatch | `q_track` + opcjonalnie `q_artist` | lista trackow | srednia do niskiej |
| Genius | `q` | lista hitow | srednia do niskiej |
| LRCLIB | `track_name` + `artist_name` (+ opcjonalnie `album_name`), lub `q` | lista rekordow z lyrics | srednia dla lyrics, niska dla tozsamosci utworu |
| Lyrics.ovh | dokładne `artist/title` w URL | pojedynczy tekst lyrics albo brak | niska dla identyfikacji, wysoka tylko dla lyrics |
| YouTube / SoundCloud / Bandcamp / Audius / Archive / JioSaavn | swobodny query tekstowy | zwykle 1 wynik lub wynik wytypowany przez scoring | niska do sredniej, rescue only |
| AI | cala paczka evidence, nie jedno pole | wynik scalony z confidence | zalezy od jakosci wejsciowych danych, nie traktowac jako absolut |

## 7. Zasada kolejności

Po tej analizie najlepiej utrzymac nastepujaca kolejnosc logiczna:
1. nazwa pliku po oczyszczeniu i prostym tasowaniu slownym,
2. w tym samym pierwszym przebiegu szybki test YouTube + SoundCloud na samej oczyszczonej nazwie pliku, bez wymagania tasowania,
3. lokalne metadane tylko jako sygnaly o wadze, nie jako "twarda prawda",
4. zewnetrzne tekstowe/metadata lookupi,
5. fingerprint jako mocne potwierdzenie albo korekta,
6. AI jako scalacz i fallback, gdy kilka zrodel nie daje zgodnego wyniku.

## 8. Uwaga o YouTube i SoundCloud

W pierwszym, najprostszym kroku rozpoznawania warto zawsze odpytac przynajmniej:
- YouTube,
- SoundCloud.

Powod:
- bardzo czesto znajduja wynik nawet po samym oczyszczeniu nazwy pliku,
- dobrze toleruja prosty query typu `title-artist`,
- ich odpowiedz bywa wystarczajaco bliska temu, co jest na pliku, zeby wczesnie zbudowac sensowna hipoteze,
- nadaja sie do szybkiego odfiltrowania plikow, ktore juz na starcie da sie sensownie przypisac.

To nie znaczy, ze ich wynik jest automatycznie pewny. To znaczy, ze:
- powinny byc czescia pierwszego passu,
- powinny dostac niski koszt wejscia,
- i moga podniesc pewnosc gdy zgadzaja sie z innym zrodlem lub z lokalnym sygnalem pliku.

## 9. Tryb awaryjny dla starszych zrodel

Stare lub mniej trafne ścieżki nie są usuwane, tylko przeniesione na koniec kolejki:
- AcoustID,
- MusicBrainz fallbacki,
- portal rescue z `Bandcamp` / `Audius` / `Archive` / `JioSaavn`,
- `LRCLIB`,
- `Lyrics.ovh`.

Ich rola:
- uruchamiają się dopiero wtedy, gdy nowy first-pass nie dał sensownej odpowiedzi,
- mogą ratować trudne pliki,
- ale nie blokują ani nie dominują pierwszej decyzji.
