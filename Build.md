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
