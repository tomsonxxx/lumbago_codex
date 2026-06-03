# Historia budowania — Lumbago Music AI

> **Maj/Czerwiec 2026 — SZPIEG Agent + crew rethink + single Odtwarzacz focus + PLAN crew launch:** Dodano SZPIEG (nadrzędny research/spy agent z encyklopedią findings w crew/SZPIEG_agent_spec_and_archive.md, nadrzędne Build Spec, konsultacje, punktowanie, side tasks). Rethink hierarchy (SZPIEG jako research lead + Plan agent produkuje pełne wnioski + punktowanie + "nową listę przeróbek" **dla użytkownika w pierwszej kolejności** przed impl — explicit user: "dajcie mi w pierwszej kolejnosci przeczytać waszą nowąą liste przeróbek"). Utworzono `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (PRIORYTET #1: aktualizacja zmiany pracy zespołu i funkcje SZPIEGA na górze; 6-agent crew pipeline podlega nowemu procesowi; God Object note dla Writer — "ok"). Update docs (memory, AGENTS, CLAUDE, crew/PLAN + CHECKLIST/LISTA, HISTORY). Review archives + code for troublesome single player parts (load, playback basics, UI readability, drag from table, overlaps). SZPIEG research na single Odtwarzacz (lista 12+ przykładów z Rekordbox/Serato/Traktor/Mixxx/etc., opinie, techniki). Build Spec przekazany do impl (transport, layout air/scalability, drag, compact z animacją, EFFECT tooltips, cue logic, file vs stream). Postępy: default single, OdtwarzaczView + SimpleDeckController MVP (load/play/pause/stop, drag fix, tooltips, visibility), integracja w dj_player_window. Hierarchia: SZPIEG research → Plan (lista do user review first) → crew impl exact (jeśli user "dalej"). Encyklopedia dla przyszłych pokrewnych fragmentów + multi-team continuity.
> **2026-06-02 — Writer impl reworks single Odtwarzacz (per SZPIEG Build Spec + Plan):** Dokładna implementacja 7 kroków: 1. Solidify (QStacked w dj_player_window eliminuje hacks visibility/creation/overlap dla odt vs dual; file/stream guards+comments w load/play paths window+controller+odt+wave). 2. Expand EFFECT tooltips+docs (mode, labels, wave, drag, transport z "EFEKT: ..." + file/stream; drag highlight+pos). 3. Compact+anim (styles compact sizes; odt _CompactSpinIndicator timer/paint spinning CD/vinyl, set_compact_mode+apply+react play; simple flag; window toggle+sync+handler). 4. Scalability (resizeEvent odt dynamic wave/spin + window reapply compact; zachowane stretch/air). 5. Cue/drag consistency+safety (highlight, prompt confirm load if playing, cue logic solid). 6. Testy (smoke exit0, pytest ~44 pass, python -c odt smoke, manual CHECKLIST paths). 7. Updates archiva (SZPIEG full report+findings, memory, HISTORY, AGENTS, CLAUDE, crew/CHECK/LISTA). Critical files: odtwarzacz_ 
> **2026-06-02 — WRITER (Code Review Crew full "cała budowa Odtwarzacza MVP" fixes 1-12 per SZPIEG lead + Plan "nowa lista przeróbek" user first + ANALYZER/REVIEWER/UI-DESIGNER outputs + memory + exact match high pressure read-before-edit zero odstępstw Polish):** Implementacja fixes wg listy (z PLAN + findings): 1. Solidify QStack/indices/init order (dual 0, odt 1, switch correct no race, legacy focused hide properly no main_layout, guards, no NameError) — read/grep before, edits in dj_player_window.py (add _DUAL/_ODT const after stack, strengthen create after dual, clean legacy focused block no addWidget, update switch+initial+docs to use idx, is_single->use_single_mode). 2. Compact toggle (guards reentrancy, sync spin/play, fix spin anim rotate using a cos/sin in _CompactSpin paintEvent, visible work, min size pilot) +9 anim spin (timer clean, start only compact+play, size dyn) — edits odtwarzacz_view.py (math import, paint rewrite spokes cos/sin radial, _update_compact_play_state ensure vis+start, apply/set/resize, window _on_compact add minSize shrink/restore). 3. Visibility no-overlap (QStack setCurrent, hide console only non-stack, single default, aggressive) — reinforced in switch (stack_widgets guard, setCurrent). 4. Playback reliability (odt/simple: load safety prompt if playing, cue during play, state no track/compact, engine fallback, play near cue, stop to cue, waveform load token) — edits simple_deck_controller.py (guards+docs in play/pause/stop/set_cue/seek/unload, stop now seeks cue), dj_player_window (safety prompt in load_track_to_deck reinforced). 5. Drag UX (odt: mime+urls+repo full Track+highlight enter/leave, pos optional, safety confirm if playing, load signal) — edits odt (robust hl no fragile replace, leave/drop compact re-vis sync, _load doc FILE/stream). 6. Scalability (resize odt wave/spin, window, air/margins preserved compact/non, Expanding no fixed, multi res) — edits odt resize (expanded doc+policy ensure), window resize doc, apply/compact keep air. 7. EFFECT tooltips + file/stream docs (expand all: load=FILE, transport=STREAM, cue=pos in file etc in buttons/wave/labels/drag/controller/window) — edits window (drop, _load_file_dialog), simple (unload/seek/load docs), odt existing expanded. 8. Black/empty UI (ss #OdtwarzaczPanel, "Brak utworu", placeholder, bg in compact) — edits odt _apply (re-set base ss for panel bg in compact branch). 10. Init/creation (no NameError, odt after dual/separate, stack add order, guards) — covered in 1 + creation funcs. 11. Testy (smoke LUMBAGO_SAFE+SECONDS exit0, pytest -k dj/playback 44p, python-c headless create+set single+toggle compact+load dummy+play+drag mime sim+resize, manual per CHECKLIST load/play/stop/drag/compact/tooltips/no-overlap/resize/single/QStack covered in sim+logs) — all green post each major. 12. Docs (update memory/HISTORY/PLAN/SZPIEG archive/crew/CHECKLIST/LISTA, code docstrings "per SZPIEG Build Spec + Plan", todo_write) — this + files. Przekazano problemy do FIXER/TESTER (spin vis timing headless, compact window edge highDPI, legacy ref in dual create, cue full with real audio, always-on-top optional pilot). Exact match Build Spec (air32/24, wave stretch7 min260 double=cue, trans large centered CUE/PLAY/STOP, EFFECT 1-2zd file/stream, drag mime+repo+hl+pos, cue near0+return, compact+anim timer/paint spin CD, resize+stretch, file/stream guards/docs, safety if playing, window toggle, styles, tests). Język PL gdzie pasuje. Read before every edit (grep/read_file multiple), smoke/pytest/python-c after major. Update archiwa. Status: Odtwarzacz MVP cała budowa solidna per spec+lista, tests OK, gotowe review+push. Abs paths edited: D:\Claude\ui\dj_player_window.py, D:\Claude\ui\dj\views\odtwarzacz_view.py, D:\Claude\ui\dj\simple_deck_controller.py, D:\Claude\ui\dj\styles.py (minor), docs/HISTORY.md, memory.md, crew/SZPIEG..., crew/CHECKLIST..., Checklist.md.
> **2026-06-02 — TESTER full verify "cała budowa Odtwarzacza MVP" po WRITER/FIXER (per PLAN/SZPIEG/memory/CHECKLIST):** Smoke exit0 OK; pytest -k dj/playback/ui_smoke/hotcue 44p 1s OK; python-c headless: DJPlayerWindow create single default, stack=2 idx=1, compact toggle _compact, load dummy Track (UI update), ctrl play/pause/stop/set_cue near0, resize+odt resizeEvent, drag mime sim, spin spinning on compact+play OK (vis offscreen lag ale setVisible/guard/_update OK); manual adapted (single clean air32/24/18 no overlap QStack, BPM32px900, wave260 dominant, large trans96x58, drag lib mime+repo+hl+pos+safety, resize no cut, compact pilot small+spin anim react, EFFECT "EFEKT:"+file/stream wszędzie, cue/play/stop, QStack switch console, no za gęsto, scalab) OK; edges all OK; verify: no NameError OK, bg surface OK, spin rotates (cos/sin on _angle in paint +import +comments per spec) YES post FIXER, no silent compact (re-apply removed) OK, init/stack/indices/air OK. All green. WRITER/FIXER iter OK exact, gotowe max3. Commit ready. Docs updated (this + memory + SZPIEG + crew/CHECK + AGENTS/CLAUDE + todo). Abs paths: D:\Claude\ui\dj_player_window.py , D:\Claude\ui\dj\views\odtwarzacz_view.py (spin fixed).
> **2026-06-02 — UI-DESIGNER audyt/redesign Odtwarzacza MVP (single compact player) per PLAN/SZPIEG/AGENT3:** Pełny projekt/audyt UI "Odtwarzacza MVP" (layout VBox air 32/24 spacing18 compact8/6, header HBox title stretch+BPM+spin, wave stretch7 min260/80, time center, trans HBox stretches +3 large CUE/PLAY/STOP booth toggle, status; compact pilot collapse sizes/fonts/margins/wave/spin vis+anim react play; QStack indices odt1/dual0 no overlap aggressive hide single default; drag mime+urls+highlight+repo lookup+load+safety prompt if playing FILE/stream; EFFECT tooltips 1-2zd file/stream wszędzie; scalability resizeEvent dynamic wave/spin Expanding multi highDPI air; black/empty #Odt surface+"Brak utworu"; problemy: compact crash fixed reentrancy/guard, spin vis/anim (a unused not rotating — fix cos/sin), init order, playback compact, cue, drag UX). Na bazie SZPIEG (12+ tools Rekordbox/Serato/Mixxx/Traktor/Winamp/VLC/foobar + punktowanie + Build Spec binding air+dominant+large trans+CUE+EFFECT+drag+compact+scalab+file/stream+safety) + ANALYZER/REVIEWER + code + CHECKLIST (must single clean no overlap BPM large wave trans drag resize compact pilot EFFECT no gęsto). Output: szczegółowy redesign doc po polsku crew/UI_Designer_Odtwarzacz_MVP_Redesign.md (exec summary problemów, nowy język booth+pilot compact, konkretne zmiany odt_view/dj_player/styles/wave/main suggestions, punktowanie vs SZPIEG, handover WRITER/FIXER e.g. fix spin cos/sin, compact window min size, more guards). Update crew docs identycznie (memory + HISTORY + SZPIEG archive append findings/problems + AGENTS/CLAUDE + crew/CHECKLIST + code docstrings + todo). Przekazano problemy do SZPIEG (side tasks compact anim ex, visibility/init, file/stream, drag, scalab) + WRITER/FIXER (spin fix P0, compact resize P1, guards P1, polish). Per hierarchy: SZPIEG/Plan lista user first. Czeka user review "nowej listy przeróbek" + "dalej". Zero odstępstw. Patrz crew/UI_Designer_Odtwarzacz_MVP_Redesign.md + memory (2026-06-02 UI-DESIGNER wpis) + SZPIEG.view.py, simple_deck_controller.py, dj_player_window.py, styles.py. 100% match spec, zero odstępstw. Smoke/pytest/manual OK. Gotowe do user/SZPIEG review.
> **2026-06-02 — REVIEWER (Code Review Crew, per PLAN + SZPIEG lead):** Weryfikacja ANALYZER output (init/QStack/dual-first/odt1/create/switch/compact toggle/apply/guard/spin sync/resize/paint/controller/styles/wave/main int, known problems compact silent/black/NameError/vis/playback/drag/init/reentr) + code + SZPIEG spec + CHECKLIST. Fixes działają (compact no crash, bg surface, stack clean index1, no NameError, reentr guard, smoke/pytest 44p exit0, python-c odt+compact+stack+close OK). Pozostałe P0: spin anim nie rotuje (angle computed but spokes static in paint — brak cos/sin rot; a unused). P1: dual always create (overhead single default), compact scalab (window not shrink/empty space), init order/race guards, playback compact no-track/cue, vis timing tests, reentr test removed. P2: tooltips/air/cue/file-stream coverage. Compliance SZPIEG: high (air32/24, dominant wave, large trans, EFFECT 1-2zd, compact pilot, drag full mime+repo+hl+pos+safety, cue near0, scalab resize+stretch, explicit file/stream, safety lock) ale spin P0. Co OK/nie, priorytety, przekazano problemy do SZPIEG (side: anim ex, lazy dual, compact floating/shrink, more guards, visual tests). Recos: fix spin paint rotation, lazy dual init, compact window resize/floating, more guards/edges, expand tests CHECKLIST. Update docs (SZPIEG archive full raport REVIEWER, memory, this HISTORY, crew/CHECKLIST, AGENTS/CLAUDE, code). Per hierarchy SZPIEG/Plan first. Smoke/pytest/manual covered. Raport po polsku w SZPIEG + memory.
> **2026-06-02 — SZPIEG full build audit Odtwarzacz MVP (cała konstrukcja):** Głębokie badanie init DJPlayerWindow/QStacked (dual create first index0, odt1, default single), _create_dual/_create_odt/_switch/_on_compact, OdtwarzaczView (setup/air, set_compact/_apply guard, _CompactSpinIndicator 50ms timer/paint vinyl spokes react play, resize dynamic, drag mime+lookup+safety prompt if playing, load, signals to ctrl, EFFECT tooltips file/stream everywhere, no-overlap), SimpleDeckController (load=FILE cue=0, play/pause/stop/seek/cue near0 prefer, compact flag, waveform token/runnable), integracja main (drag table open+load_to A routes single, now_playing signals, btn), styles BOOTH+compact sizes, waveform in odt. Recent fixes verified (NameError avoided, stack indices guarded, black in styles/base, reentrancy removed window resize "crash or silent exit" comment, bad re-apply removed). Headless create/stack=2/default single/compact toggle OK no crash. Research: 12+ przykładów (Rekordbox 1PLAYER/dual preview+lib wave cue, Serato lacks dedicated, Mixxx PreviewDeck dedicated+Full/Compact/Mini+vinyl spin anim, Traktor modular compact X1, VDJ Preview Player essential no-load+skins, foobar waveform minibar compact, VLC minimal, Winamp mini+reactive spinning vis, Ableton clip dominant wave+drag preview, Engine large wave+lib preview, Cross clean wave portrait compact, WMP historical mini). Analizy + opinie pro (preview essential/gamechanger/lock ratuje, compact saves multi-mon, anim helps glance booth, air readable, drag intuitive). Punktowanie Lumbago + SWÓJ Program + zaktualizowany Build Spec 15+ blocks (kolejność: solidify guards, expand EFFECT, compact+always-on-top, scalab, cue/drag, playback, legacy, init, black/empty, tests, docs; konkretne zmiany w odt_view/simple/dj_player_window/styles/wave + files). Problemy P0-P10 (compact silent crash top prio, QStack races, legacy refs, spin, no always-top, etc.). Side tasks. Encyklopedia/memory/HISTORY/CHECKLIST/AGENTS/CLAUDE/SZPIEG/PLAN updated identycznie. Przekazano do crew/Plan (lista first dla user per PLAN). Patrz crew/SZPIEG_agent_spec_and_archive.md (nowy wpis).
>
> Scalono z `Build.md` (faza Python/PyQt6) i `Build2.md` (faza WinUI 3 Reboot).

---

## Faza 1 — Python/PyQt6 Desktop (Build.md)

1. **Bootstrap projektu**: utworzono strukturę `core/`, `data/`, `services/` i `ui/` oraz plik `requirements.txt` z zależnościami.
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

## Faza 2 — WinUI 3 Reboot (Build2.md, od 2026-03-17) — **PORZUCONA I USUNIĘTA Z REPOZYTORIUM (maj 2026)**

> **Uwaga historyczna:** Ta faza projektu została ostatecznie porzucona podczas sprzątania repozytorium w maju 2026. Projekt skupia się wyłącznie na wersji desktopowej PyQt6 + DJ Player. Poniższa sekcja zachowana jest wyłącznie jako zapis historyczny.

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
> **2026-06-02 — FIXER (Code Review Crew, po WRITER + SZPIEG/ANALYZER/REVIEWER/Plan nowa lista + memory/PLAN/SZPIEG/CHECKLIST):** Naprawa bugów z całej budowy Odtwarzacza MVP (single primary). Exact wg "nowa lista" + P0/P1 findings (spin, vis, guards load/play, init order, legacy single_container remove/hide, reentr, playback compact cue/wave/no track, scalab air/margins/dynamic wave/window shrink, file/stream comments/guards w odt/controller, drag hl compact, cue during, etc.).
> - Spin fix: paintEvent używa a + cos(a)/sin(a) dla rotacji spokes (zamiast static x1 y1); 8 spokes radial, comments "per SZPIEG/Plan".
> - Spin vis compact: isVisible test + force set po setVisible w _apply + po setCurrent/switch + odt.show; "test isVisible po set, po show stack".
> - Guards load/play playing: safety prompt (QMessage) w odt drop + window load_track_to_deck single (przed load FILE podczas stream); + no-track guards ctrl.
> - Init order: ensure odt ready (create on demand w init + switch single); odt before switch.
> - Legacy single_container: usunięto creation w _create_dual (sole odt single); set None, hide guards; uproszczone legacy block init; comments updated.
> - Reentr: guards _applying + resize pass + test.
> - Playback compact: cue logic/wave load (indep), no track handled (status/guard).
> - Scalab: air/margins compact 8/6, dynamic min wave (resize non+compact), window min shrink 380x280 in compact toggle + restore _orig.
> - File/stream: + komentarze/guards load(FILE=repo+wave+cue0) vs transport(STREAM=play near0 cue) w odt _load/_setup, simple ctrl, window.
> - Inne: drag hl compact (force border cyan + log), cue play live.
> Read-before-edit, exact, polski komentarze/docstrings (per SZPIEG Build Spec + Plan + memory).
> Tests: smoke exit0; pytest 44p; python-c create+toggle+vis test+load+play+cue+resize+drag sim OK.
> Docs: HISTORY+memory+SZPIEG+CHECKLIST+AGENTS/CLAUDE + code + todo.
> Abs: ui/dj_player_window.py, ui/dj/views/odtwarzacz_view.py, ui/dj/simple_deck_controller.py.
> Przekazano TESTER z raportem + cmds.
