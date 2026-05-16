# Historia budowania — Lumbago Music AI

> Scalono z `Build.md` (faza Python/PyQt6) i `Build2.md` (faza WinUI 3 Reboot).

---

## Faza 1 — Python/PyQt6 Desktop (Build.md)

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
33. **Tag compare UX**: dodano podgląd okładki, podgląd tagów, zapis przy następnym i tryb „tylko różnice".
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
75. **Fallback danych**: dodano bezpieczny fallback do `.lumbago_data` przy braku uprawnień w `%APPDATA%`.
76. **Logi startu**: dodano `startup.log` oraz `app.log` do diagnozowania zamknięcia okna.
77. **Obsługa błędów**: dodano crash log oraz handler komunikatów Qt do `qt.log`.
78. **Tryb bezpieczny**: dodano `LUMBAGO_SAFE_MODE=1` do uruchamiania minimalnego okna bez pełnej logiki.
79. **Multimedia toggle**: dodano `LUMBAGO_DISABLE_MULTIMEDIA=1` do wyłączania inicjalizacji odtwarzacza.
80. **Pipeline metadanych**: dodano tryb auto z priorytetami (AcoustID → MusicBrainz → Discogs) oraz walidację kandydatów.
81. **AI minimalny prompt**: skrócono prompt AI do brakujących pól.
82. **Walidacja (balanced)**: obniżono rygor walidacji kandydatów do trybu zbalansowanego i ustawiono progi dopasowania.
83. **Pytest**: dodano pytest do zależności oraz pierwsze testy walidacji metadanych.
84. **Pytest config**: dodano pytest.ini, aby izolować testy tylko do katalogu tests.
85. **Cache metadanych**: dodano tabelę cache w SQLite oraz TTL dla zapytań MusicBrainz/Discogs.
86. **Walidacja lenient**: dodano tryb lenient i testy dla wszystkich trybów walidacji.
87. **Ustawienia cache**: dodano TTL cache metadanych w ustawieniach UI.
88. **AI minimalne wywołania**: pomijanie chmury, gdy brakujących pól nie ma.
89. **Cache online**: cache zapytań MusicBrainz/Discogs z TTL w SQLite.
90. **Filtr kompilacji**: odrzucanie albumów typu "Greatest Hits" przy uzupełnianiu.
91. **Walidacja AI**: dodano filtr BPM/Key/energy oraz progi confidence w AI Taggerze.
92. **Rok wydania**: dodano pole year w modelu, DB i UI oraz walidację zakresu.
93. **Test renamera**: dodano unit test dla konfliktów w planie rename.
94. **Testy parserów**: dodano unit testy dla XML (Rekordbox/VDJ) i duplikatów.
95. **Walidacja w UI**: dodano wybór trybu walidacji (strict/balanced/lenient) w ustawieniach.
96. **Test integracyjny DB**: dodano reset silnika po teście i uruchomiono pytest (11 testów OK).
97. **Smoke mode**: dodano `LUMBAGO_SMOKE_SECONDS` do automatycznego zamykania aplikacji podczas testów.
98. **UI smoke test**: dodano test uruchomieniowy UI w trybie safe i uruchomiono pytest (12 testów OK).
99. **Bundlowanie fpcalc**: build.ps1 wykrywa `fpcalc` z `tools/` lub `PATH`, dodano instrukcję w `tools/README.md`.
100. **Pobieranie fpcalc**: dodano `tools/fetch_fpcalc.ps1` i pobrano `fpcalc.exe` do `tools/`.
101. **PyInstaller v2**: dodano zależność i zainstalowano PyInstaller 6.19.0 w venv.
102. **Ikona ICO**: wygenerowano `assets/icon.ico` i ustawiono w spec, dodano `COLLECT` dla trybu onedir.
103. **Build portable**: zbudowano `dist/LumbagoMusicAI` oraz `dist/LumbagoMusicAI-portable.zip`.
104. **Smoke test EXE**: uruchomiono `dist/LumbagoMusicAI/LumbagoMusicAI.exe` w trybie safe z auto‑zamknięciem.
105. **Checklist clean Windows**: dodano `docs/clean_windows_test.md`.
106. **Loudness (LUFS)**: dodano analizę głośności i normalizację do nowego pliku.
107. **Beatgrid + auto‑cue**: dodano wyliczanie siatki beatów i automatyczne cue (intro/outro) z cache.
108. **Auto‑key**: dodano wykrywanie tonacji z mapowaniem Camelot.
109. **Backup**: dodano automatyczny backup bazy i ustawień (start/wyjście).
110. **Eksport setów**: dodano eksport playlisty do VirtualDJ XML.
111. **Track fields**: dodano `loudness_lufs` i `cue_in_ms/cue_out_ms` do modeli i DB.
112. **Testy audio/UX**: dodano testy beatgrid/auto‑cue i zmieniono smoke test na subprocess.
113. **Zależności**: dodano `numpy` i `librosa` do analizy tonacji.
114. **WinUI 3 shell**: dodano szkice XAML (shell + strony + dialog) i theme w `docs/winui3`.

---

## Faza 2 — WinUI 3 Reboot (Build2.md, od 2026-03-17)

1. 2026-03-17 — Utworzono Build2.md i ToDo2.md, wykonano audyt dokumentacji oraz przegląd podglądów UI.
2. 2026-03-17 — Rozpoczęto benchmarking wzorców UI z aplikacji DJ i menedżerów biblioteki.
3. 2026-03-17 — Dodano wstępne wzorce UI do ToDo2.md.
4. 2026-03-17 — Potwierdzono WinUI 3 i styl „neon glass", dodano plan projektowania UI we współpracy.
5. 2026-03-17 — Utworzono `docs/winui3/ui_plan.md` (styl v1, mapa widoków, makieta Biblioteki v1).
6. 2026-03-17 — Dodano makiety Importu i Duplikatów (v1) do `docs/winui3/ui_plan.md`.
7. 2026-03-17 — Dodano makiety Odtwarzacza, Tag Compare, Smart Tagger oraz Start/Dashboard (v1).
8. 2026-03-17 — Dodano makiety Playlist, Konwertera XML i Ustawień (v1).
9. 2026-03-17 — Ustalono strukturę nawigacji, stany globalne i komponenty bazowe (v1).
10. 2026-03-17 — Dodano style listy/siatki, zasady dostępności i must‑have interakcje (v1).
11. 2026-03-17 — Wygenerowano przykładowe screeny UI (v1) w `output/imagegen/ui_v1_2026-03-17`.
12. 2026-03-17 — Dopracowano screeny (v2) i przeniesiono do `docs/winui3/previews` jako `*_v2.png`.
13. 2026-03-17 — Zaktualizowano `Theme.xaml` pod styl neon glass (kolory, Acrylic, NeonCardBorder).
14. 2026-03-17 — Podmieniono karty stron na NeonCardBorder w Start/Library/Import/Duplicates/Settings/Converter.
15. 2026-03-17 — Ujednolicono polskie etykiety i teksty w stronach WinUI 3.
16. 2026-05-16 — Dodano SmartTaggerPage: kolejka AI (POST /analysis/jobs), polling co 2s, podgląd decyzji per pole z CheckBox Accept/Reject, zbiorowe zatwierdzanie i zapis (apply endpoint).
17. 2026-05-16 — Dodano AnalysisModels.cs + AnalysisViewModels.cs (INotifyPropertyChanged DecisionViewModel) oraz metody API w ApiClient: CreateAnalysisJobAsync, GetAnalysisJobAsync, ApplyAnalysisJobAsync.
18. 2026-05-16 — Podpięto odtwarzacz audio (Windows.Media.Playback.MediaPlayer) w MainWindow: play/pause/seek/prev/next, DispatcherTimer pozycji, autoplay kolejki, double-click w LibraryPage uruchamia odtwarzanie.
19. 2026-05-16 — Dodano Smart Tagger do nawigacji NavView (między Import a Duplikaty).
20. 2026-05-16 — Dodano BulkEditDialog: multi-select (Ctrl+klik) w LibraryPage, dialog z checkboxami per pole (Genre/Year/Key/Mood/Energy/BPM/Comment), batch PUT /tracks dla każdego zaznaczonego tracka.
