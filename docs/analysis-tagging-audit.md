# Audit analizy i tagowania

## 1. Aktualny przeplyw end-to-end

### Odczyt tagow i lokalnych metadanych

1. `lumbago_app/core/audio.py::extract_metadata()` otwiera plik przez Mutagen i wypelnia `Track`.
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

- Dodana zostala wspolna usluga zapisu metadanych: `lumbago_app/services/metadata_writeback.py`.
  - Obsluguje jeden zapis do DB, pliku audio, tabeli tagow i changelogu.
  - Korzystaja z niej teraz oba flow: dialog review i szybki `AutoTagWorker`.
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

To od razu upraszcza UI, testy i przyszle przejscie na jeden wspolny pipeline AI.
