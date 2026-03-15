# Build Log (Lumbago Music AI - Python/Windows)

1. **Bootstrap projektu**: utworzono strukturę `lumbago_app/` (core, data, services, ui) i plik `requirements.txt` z zależnościami.
2. **Konfiguracja środowiska**: dodano `core/config.py` z katalogami `%APPDATA%` i cache.
3. **Modele domenowe**: dodano `core/models.py` (Track, Playlist, Tag, AnalysisResult, itp.).
4. **Audio core**: dodano `core/audio.py` (scan folderów, mutagen, hash).
5. **Heurystyki AI i duplikaty**: dodano `core/services.py`.
6. **SQLite**: dodano `data/db.py`, `data/schema.py`, `data/repository.py` (init, upsert, list).
7. **Integracje zewnętrzne**: dodano `services/metadata_providers.py` (MusicBrainz/Discogs) i `services/recognizer.py` (AcoustID).
8. **AI tagger**: dodano `services/ai_tagger.py` (local + cloud placeholder).
9. **UI Theme**: dodano `ui/theme.py` (cyber theme).
10. **UI Model**: dodano `ui/models.py` (TrackTableModel).
11. **Główne okno**: dodano `ui/main_window.py` (sidebar, header, list/grid, detail, player).
12. **Entry point**: dodano `main.py` i README.
13. **API Keys UI**: dodano `ui/settings_dialog.py` + zapis do `settings.json` i obsługę Grok/DeepSeek/OpenAI.
14. **Import Wizard**: dodano `ui/import_wizard.py` i podpięto w UI.
15. **Tabela UI**: włączono sortowanie i resize kolumn w `QTableView`.
16. **Grid UI**: dodano okładki, tytuł/artist, placeholder, kontekstowe menu.
17. **Animowane przyciski**: dodano `ui/widgets.py` (AnimatedButton) i podpięto w UI.
18. **Zaokrąglony UI**: poprawiono style i wygładzone kontury w `theme.py`.
19. **Detail Panel edycja**: dodano pola edycji tagów i zapis do SQLite.
20. **Waveform placeholder**: dodano `core/waveform.py` + podgląd w detail panel.
21. **Playlisty**: dodano `playlist_tracks` w schema, listowanie i dodawanie tracków do playlist przez drag&drop.
22. **Cover edit**: dodano podgląd okładki w detail panel + zmiana okładki i zapis w DB.
23. **List context menu**: dodano menu PPM dla listy (play, details, add to playlist).
24. **AI Tagger UI**: dodano dialog Smart Tagger (Local) z podglądem wyników i Apply All.
25. **Multi-select + bulk**: dodano Select All/Clear Selection + Bulk Edit dialog dla wielu plików.
26. **Tagi plików**: dodano odczyt/zapis/usuwanie tagów w plikach audio (mutagen) + akcje w UI.
27. **Test tagów**: wykonano test odczytu/zapisu/usuwania na kopii pliku audio (`_tag_test.mp3`).
28. **Tag Compare UI**: dodano okno porównania tagów z nawigacją i przyciskami szybkiej zamiany.
29. **Auto-detekcja kluczy**: dodano skan registry + plik `api_keys.json` i automatyczne użycie znalezionych kluczy.
30. **AI Tagger start**: podpięto wybór providera (local/cloud) w dialogu tagowania.
31. **UI PL + tooltips**: spolszczono interfejs i dodano dymki podpowiedzi.
32. **Tag compare upgrade**: dodano nawigację, zapisywanie zmian i przyciski akcji w porównaniu tagów.
33. **Tag compare UX**: dodano podgląd okładki, podgląd tagów, zapis przy następnym i tryb „tylko różnice”.
34. **AI Tagger Accept/Reject**: dodano akcje Akceptuj/Odrzuć na wierszach oraz przyciski zbiorcze.
35. **AI Tagger DB**: zapis wyników AI do tabeli `tags` z oznaczeniem źródła.
36. **Cloud AI realne wywołania**: dodano obsługę OpenAI (Responses API) oraz kompatybilnych endpointów Grok/DeepSeek.
37. **Ustawienia AI**: dodano pola base URL + model dla OpenAI/Grok/DeepSeek w ustawieniach.
38. **Kolejka rozpoznawania**: dodano worker rozpoznawania i postęp w UI.
39. **Batch metadata**: dodano uzupełnianie metadanych przez AcoustID + MusicBrainz.
40. **Okładki z MusicBrainz**: dodano pobieranie okładek z Cover Art Archive.
41. **Duplikaty (fingerprint)**: dodano wykrywanie duplikatów po fingerprintach.
42. **Duplikaty UI**: dodano widok grup, akcje przenieś/usuń i eksport raportu CSV.
43. **Renamer**: dodano wzorce, podgląd, wykrywanie konfliktów i undo.
44. **XML Converter**: dodano parser Rekordbox i eksport VirtualDJ.
45. **Cache hash/fingerprint**: dodano zapisywanie hashy i fingerprintów w DB.
46. **Duplikaty etapowo**: dodano wykrywanie etapowe (rozmiar/mtime → hash → fingerprint).
47. **Batch DB updates**: dodano zbiorcze aktualizacje ścieżek i metadanych plików.
48. **Fingerprint bez blokowania UI**: skan w tle z ograniczeniem obciążenia.
49. **Auto‑kolumny DB**: automatyczne dodawanie brakujących kolumn w tabeli tracks.
50. **Import batch**: dodano batch commit oraz anulowanie importu.
51. **Import raport**: dodano raport błędów importu i zapis do pliku.
52. **Player timeline**: dodano suwak pozycji i licznik czasu.
53. **Hotcues + loop**: dodano Cue A/B, skok i pętlę A-B.
54. **Animacje widoków**: dodano przejścia między listą i siatką.
55. **Ikony i skróty**: dodano ikony przycisków i skróty klawiszowe.
56. **Sprint 0 uzupełnienia**: dodano `.env.example`, `pyproject.toml` i ikonę aplikacji.
57. **Playlisty CRUD**: dodano tworzenie/edycję/usuwanie playlist.
58. **Playlisty smart**: dodano reguły i filtrowanie smart playlist.
59. **Reorder playlist**: dodano ręczną zmianę kolejności utworów.
60. **Metadane lokalne**: dodano odczyt z nazw plików, folderów oraz plików JSON.
61. **AI w menu**: podpięto analizę AI w menu listy i siatki.
62. **Metadane .cue**: dodano odczyt tagów z plików CUE.
63. **Wzorce nazw**: dodano konfigurowalne regexy nazw plików w ustawieniach.
64. **AI auto‑metadata**: dodano opcję pobierania braków z internetu w taggerze AI.
65. **Naprawa Tag Compare**: poprawiono flagi edycji w tabeli tagów.
66. **Alembic**: dodano konfigurację migracji i pierwszą migrację.
67. **Indeksy i constraints**: dodano indeksy i ograniczenia w schemacie DB.
68. **Tabela settings**: dodano tabelę ustawień i API do odczytu/zapisu.
69. **Historia zmian**: dodano log zmian i okno historii w detail panel.
70. **Import XML**: dodano import z Rekordbox/VirtualDJ.
71. **Waveform real**: dodano generowanie waveform przez ffmpeg.
72. **PyInstaller**: dodano spec i skrypt budowania portable ZIP.
73. **Instrukcja**: dodano `docs/user_guide.md`.
74. **Tagi (Top 20)**: rozszerzono listę tagów w oknie porównania do 20 najczęściej używanych pól.
75. **Fallback danych**: dodano bezpieczny fallback do `.lumbago_data` przy braku uprawnieĹ„ w `%APPDATA%` (ustawienia, cache, DB).
76. **Logi startu**: dodano `startup.log` oraz `app.log` do diagnozowania zamkniÄ™cia okna.
77. **ObsĹ‚uga bĹ‚Ä™dĂłw**: dodano crash log oraz handler komunikatĂłw Qt do `qt.log`.
78. **Tryb bezpieczny**: dodano `LUMBAGO_SAFE_MODE=1` do uruchamiania minimalnego okna bez peĹ‚nej logiki.
79. **Multimedia toggle**: dodano `LUMBAGO_DISABLE_MULTIMEDIA=1` do wyĹ‚Ä…czania inicjalizacji odtwarzacza.
80. **ToDo: metody tagów**: dodano listę metod analizy, wyszukiwania i walidacji tagów do ToDo.md.
80. **Pipeline metadanych**: dodano tryb auto z priorytetami (AcoustID -> MusicBrainz -> Discogs) oraz walidację kandydatów.
81. **AI minimalny prompt**: skrócono prompt AI do brakujących pól.
82. **Walidacja (balanced)**: obniżono rygor walidacji kandydatów do trybu zbalansowanego i ustawiono progi dopasowania.
83. **Testy**: próba uruchomienia pytest zakończona brakiem modułu w środowisku.
84. **Pytest**: dodano pytest do zależności oraz pierwsze testy walidacji metadanych.
85. **Pytest config**: dodano pytest.ini, aby izolować testy tylko do katalogu tests.
86. **Testy OK**: uruchomiono pytest, 3 testy przeszły.
87. **Cache metadanych**: dodano tabelę cache w SQLite oraz TTL dla zapytań MusicBrainz/Discogs.
88. **Walidacja lenient**: dodano tryb lenient i testy dla wszystkich trybów walidacji.
89. **Ustawienia cache**: dodano TTL cache metadanych w ustawieniach UI.
90. **AI minimalne wywołania**: pomijanie chmury, gdy brakujących pól nie ma.
91. **Cache online**: cache zapytań MusicBrainz/Discogs z TTL w SQLite.
92. **Walidacja lenient**: dostrojono próg (0.4) i testy przeszły.
93. **Filtr kompilacji**: odrzucanie albumów typu "Greatest Hits" przy uzupełnianiu.
94. **Testy OK**: uruchomiono pytest, 5 testów przeszło.
95. **Walidacja AI**: dodano filtr BPM/Key/energy oraz progi confidence w AI Taggerze.
96. **Rok wydania**: dodano pole year w modelu, DB i UI oraz walidację zakresu.
97. **Testy OK**: uruchomiono pytest, 6 testów przeszło.
98. **Test renamera**: dodano unit test dla konfliktów w planie rename.
99. **Testy OK**: uruchomiono pytest, 7 testów przeszło.
100. **Testy parserów**: dodano unit testy dla XML (Rekordbox/VDJ) i duplikatów.
101. **Testy OK**: uruchomiono pytest, 10 testów przeszło.
87. **Walidacja w UI**: dodano wybór trybu walidacji (strict/balanced/lenient) w ustawieniach.
102. **Test integracyjny DB**: dodano reset silnika po teście i uruchomiono pytest (11 testów OK).
103. **Smoke mode**: dodano `LUMBAGO_SMOKE_SECONDS` do automatycznego zamykania aplikacji podczas testów.
104. **UI smoke test**: dodano test uruchomieniowy UI w trybie safe i uruchomiono pytest (12 testów OK).
105. **Bundlowanie fpcalc**: build.ps1 wykrywa `fpcalc` z `tools/` lub `PATH`, dodano instrukcję w `tools/README.md`.
106. **Pobieranie fpcalc**: dodano `tools/fetch_fpcalc.ps1` i pobrano `fpcalc.exe` do `tools/`.
107. **PyInstaller**: dodano zależność i zainstalowano PyInstaller 6.19.0 w venv.
108. **Ikona ICO**: wygenerowano `assets/icon.ico` i ustawiono w spec, dodano `COLLECT` dla trybu onedir.
109. **Build portable**: zbudowano `dist/LumbagoMusicAI` oraz `dist/LumbagoMusicAI-portable.zip`.
110. **Smoke test EXE**: uruchomiono `dist/LumbagoMusicAI/LumbagoMusicAI.exe` w trybie safe z auto‑zamknięciem.
111. **Checklist clean Windows**: dodano `docs/clean_windows_test.md`.
112. **Test clean Windows**: odłożony na później (na prośbę użytkownika).
113. **Loudness (LUFS)**: dodano analizę głośności i normalizację do nowego pliku.
114. **Beatgrid + auto‑cue**: dodano wyliczanie siatki beatów i automatyczne cue (intro/outro) z cache.
115. **Auto‑key**: dodano wykrywanie tonacji z mapowaniem Camelot.
116. **Backup**: dodano automatyczny backup bazy i ustawień (start/wyjście).
117. **Eksport setów**: dodano eksport playlisty do VirtualDJ XML.
118. **Track fields**: dodano `loudness_lufs` i `cue_in_ms/cue_out_ms` do modeli i DB.
119. **Testy audio/UX**: dodano testy beatgrid/auto‑cue i zmieniono smoke test na subprocess.
120. **Testy OK**: uruchomiono pytest, 15 testów przeszło.
121. **Zależności**: dodano `numpy` i `librosa` do analizy tonacji.
