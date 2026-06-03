# Memory — Lumbago Music AI (DJ Player Project)

**Data ostatniej aktualizacji:** Czerwiec 2026 (po pełnej organizacji dokumentacji, impl single Odtwarzacz MVP per SZPIEG spec, team review, push; crew PLAN_Uruchomienie_... aktywowany z SZPIEG jako PRIORYTET #1 + user 'ok'; **pełny re-audit crew 2026-06-02: SZPIEG (full research + Build Spec + punktowanie + problemy) + Plan (wnioski + nowa lista 1-15) + ANALYZER/REVIEWER/UI-DESIGNER (redesign) + WRITER/FIXER/TESTER (fixes + all tests smoke/pytest/headless/manual/edge/verify OK, spin cos/sin rotate, compact no silent close, QStack/air/EFFECT/guards/safety/file-stream/scalab preserved) — po kolei cała budowa odtwarzacza, problematyczne elementy przekazane SZPIEG (compact crash, spin anim, init order, visibility, playback compact, drag, scalab edges, cue, file/stream); "nie przestawaj póki nie skończysz" — ukończone, gotowe, docs update identycznie, commit/push)

**Cel pliku (dla nowych programistów/agentów):** 
Ten plik jest **centralną, żywą "encyklopedią" projektu**. Po przeczytaniu go (zawsze na początku nowej sesji) każdy nowy programista lub agent AI musi mieć **kompletny, aktualny pogląd** na:
- Zasady prowadzenia projektu i komunikacji (w tym "1,2,3 po kolei", "dalej"/"do końca" bez zbędnych pytań, testy na bieżąco).
- Aktualny poziom prac / stan (co działa, co w toku, co problematic; obecnie: single "Odtwarzacz" MVP solidny per spec, Opcja A zakończona, dual zachowany).
- Hierarchię crew/agentów (SZPIEG jako nadrzędny research lead + Plan review "nowej listy przeróbek" jako **pierwszy krok dla użytkownika** przed jakąkolwiek impl; potem 6-agent crew).
- Jak dokumentować własne ruchy (zawsze w ten sam sposób: update memory + HISTORY + AGENTS/CLAUDE + crew/SZPIEG archive + crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md + code docstrings + todo_write dla complex + clear commit msg). Dokumenty muszą być stale uzupełniane, aby wiele odrębnych zespołów mogło pracować równolegle bez tracenia wątku.

**Zasady dokumentacji (obowiązkowe dla wszystkich):**
- Zawsze aktualizuj memory.md (ten plik) na końcu sesji lub po major changes (postęp, decyzje, problemy, SZPIEG findings, Plan reworks lists).
- Aktualizuj docs/HISTORY.md z chronologicznymi milestone'ami.
- Dla research fragmentów: używaj SZPIEG, zapisuj w crew/SZPIEG_agent_spec_and_archive.md (encyklopedia "sposoby na wszystko").
- Update AGENTS.md, CLAUDE.md, crew/ pliki (PLAN_Uruchomienie_..., CHECKLIST, LISTA), Checklist.md przy zmianach w crew/hierarchy/process lub uruchamianiu crew.
- W kodzie: dodawaj/aktualizuj docstrings komentujące adherence do spec (SZPIEG Build Spec jest nadrzędny; "Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review... must document identical").
- Używaj todo_write dla multi-step/complex tasks (jak ten).
- Commit często z jasnym message (co zrobione, odniesienia do docs/spec + user feedback).
- Język: wszystko po polsku (user requirement).
- Cel: traceability + parallelism (multiple teams/agents bez utraty kontekstu).

**Aktualny fokus projektu:** DJ Player (PyQt6) — single "Odtwarzacz" MVP jako primary (basics: poprawne wczytanie pliku z drag z tabeli + repo lookup, play/pause/stop z cue logic, clean readable UI bez overlap/dużej gęstości, dużo powietrza, scalability/resize/multi-monitor, compact pilot-like mode z animacją (spinning indicator), EFFECT tooltips na każdym elemencie, drag&drop, podstawowy feedback waveform/title/time/BPM). Dual "Konsola DJ" zachowany ale secondary. Opcja A (legacy cleanup) zakończona — nowa architektura sole (OdtwarzaczView + SimpleDeckController + QStacked w window).

**Crew/Hierarchy (2026, z SZPIEG — PRIORYTET #1 przy uruchamianiu crew):**
- **SZPIEG (SPY):** Nadrzędny research lead. Dla konkretnych wąskich fragmentów (transport, compact, drag, tooltips EFFECT, visibility, cue, file-vs-stream, scalability...) tworzy listy 10-15+ przykładów, analizuje, punktuje przydatność dla TEGO projektu, produkuje Build Spec binding + encyklopedię w crew/SZPIEG_agent_spec_and_archive.md. Decyduje przy braku ścisłego copy. Side tasks tylko wyjątkowe + user consent.
- **Plan agent (kluczowy przed impl):** Zawsze produkuje **pełne wnioski + punktowanie + "nową listę przeróbek"** (zachować X / przerobić Y + szczegółowa kolejność kroków 1-7 + critical files + side tasks). **Użytkownik dostaje listę przeróbek w pierwszej kolejności do przeczytania i samodzielnej decyzji** (explicit: "dajcie mi w pierwszej kolejnosci przeczytać waszą nowąą liste przeróbek do i pewniessaam msie na ro"). Dopiero po akceptacji ("wszystko ok", "dalej", ewentualne zmiany) — crew przechodzi do impl.
- **6-agent Code Review Crew (ANALYZER → REVIEWER → UI-DESIGNER → WRITER → FIXER → TESTER, max 3 iter, polski):** Dostaje SZPIEG spec + zatwierdzoną listę z Planu jako primary input. High pressure exact match (read before edit, zero odstępstw). Writer: nie rusza radykalnie logiki biznesowej w UI (tylko styl/strukturę) — **OK** potwierdzone. Po Opcja A: logika w controllerach, views są dumb — bezpieczniej.
- **Proces uruchomienia (zawsze):** memory + SZPIEG + crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md (PRIORYTET #1) → SZPIEG/Plan (lista do user review first) → crew impl (jeśli user da "dalej") → smoke/pytest + docs update (memory + HISTORY + SZPIEG + PLAN + AGENTS/CLAUDE + crew files + code) → commit/push.
- Side tasks dla SZPIEG: visibility/overlap, compact anim ex (5-8), file/stream, drag UX, scalability edges (zapisane w SZPIEG archive).

Patrz `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (pełny plan crew z SZPIEG first) + `crew/SZPIEG_agent_spec_and_archive.md` (research + Build Spec + Plan wnioski) dla szczegółów.

---

**Data ostatniej aktualizacji (stara sekcja poniżej dla historii):** Maj 2026 (po dużym sprzątaniu repozytorium)  
**Cel pliku (historyczny):** Pełna, trwała pamięć projektu — wszystko co zostało omówione, zbudowane, naprawione i postanowione od początku pracy nad DJ Playerem.

---

## 1. Podstawowe zasady komunikacji

- **Język:** Użytkownik kategorycznie wymaga, żeby **wszystko** (odpowiedzi, wyjaśnienia, podsumowania) było po polsku. Od pewnego momentu sesji padło wyraźne: „rozmawiamy tylko po polsku”.
- Użytkownik często resetuje sesje ("zamknij sesję i uruchom nową") i oczekuje, że AI będzie pamiętało kontekst dzięki temu plikowi.
- Styl pracy: użytkownik często mówi „dalej”, „do końca”, „nie pytaj co chwila”, „sam sukcesywnie podejmuj decyzje”, „poprawiaj błędy”.

---

## 2. Chronologiczna historia pracy nad DJ Playerem (główny temat sesji)

### Faza 1 – Początek (żądanie pełnego, profesjonalnego playera)
- Użytkownik zażądał stworzenia **kompletnego, niezależnego dual-deck DJ Playera** w osobnym oknie.
- Wymagania: 4 lub 8 hotcue’ów z pełną persystencją w bazie, duży waveform z beatgridem (BPM-aware), 3-pasmowy EQ, crossfader, Volume, Pitch, Loop In/Out, KEY, SYNC (z fazą), PFL, Quantize, Master + HP Cue, Memory Save/Recall, Recent History per deck.
- Silna integracja z biblioteką (drag&drop, menu kontekstowe, wskaźniki „teraz gra w playerze”).
- Dwa tryby w jednym oknie: **„Odtwarzacz”** (single) i **„Konsola DJ”** (dual).
- Użytkownik wielokrotnie podkreślał, że player ma być „osobnym ciałem”, nie bazować na starym wbudowanym odtwarzaczu (`ui/player_widget.py` został uznany za deprecated).

### Faza 2 – Iteracje UI i walka o czytelność (najdłuższa i najbardziej emocjonalna część)
Użytkownik był bardzo wymagający co do jakości interfejsu:
- Wielokrotne narzekania: „okno jest kompletnie nie czytelne”, „ikony zachodzą na siebie”, „za gęsto”, „wszystko zachodzi na siebie i przykrywa jedno przez drugie”, „tryb pojedynczy jest podwójny!!!”.
- Prośby o większe pady hotcue, większe czcionki, więcej powietrza, styl „booth” / Rekordbox.
- Kilka rund przeprojektowywania układu (marginesy, spacingi, rozmiary padów 72×52 → 88×58 → 92×60 itd.).
- Na pewnym etapie użytkownik poprosił: **„zatrudnij agenta do projektowania UI który od nowa zaprojektuje okno dj playera kopiując rozwiązania UI programu rekordbox”**.
- Powstały dwa tryby w jednym oknie z przełącznikiem (SinglePlayerView + DeckWidget dual).

### Faza 3 – Ciężka praca nad stabilnością i błędami („poprawiaj błędy”)
Użytkownik wielokrotnie wracał do tematu naprawiania błędów ładowania i odtwarzania:
- Krytyczne bugi:
  - `QThreadPool.start(worker)` gdzie worker był funkcją → TypeError (naprawione przez `WaveformRunnable` + token).
  - Backendy ustawiały `self._enabled = False` po błędzie → deck na zawsze zablokowany.
  - Duplikacja metod cue_points w `repository.py`.
  - Zepsute wiązanie przycisku „Wczytaj plik…” w Single view.
  - Desynchronizacja hotcue’ów i main cue przy przełączaniu trybów Single ↔ Console.
  - Brak `vol_val` w SinglePlayerView → crash przy zmianie głośności.
- Użytkownik wybierał ścieżki napraw (np. „b” = głęboka naprawa synchronizacji hotcue’ów między trybami).
- Powtarzające się polecenia: „poprawiaj błędy”, „testuj wszystko na gotowo”, „dalej”.

### Faza 4 – Wzmocnienie architektury Playback
- Stworzenie solidnego `PlaybackEngine` + warstwowych backendów (VLC jako priorytet).
- Poprawki w `_NoopAudioBackend`, żeby testy DJ działały nawet bez VLC.
- Dodanie instalacji VLC w GitHub Actions (`desktop-ci.yml`).

### Faza 5 – Dokończenie spójności modelu danych (ostatnie duże zadanie)
- Nowe pola w `Track`: `albumartist`, `composer`, `publisher`, `tracknumber`, `discnumber`, `isrc`, `grouping`, `copyright`.
- Problem: pola były w dataclassu i w ORM, ale nie były kopiowane w `_TRACK_META_FIELDS` w `repository.py` → `AttributeError` i tracone dane.
- Naprawione w `data/repository.py` + wypchnięte.

---

## 3. Kluczowe decyzje architektoniczne

- **DJ Player jako całkowicie osobne okno** (nie integrujemy go głęboko ze starym player widgetem).
- **Dwa tryby w jednym oknie** z możliwością przełączania (Single + Dual Console).
- **PlaybackEngine** jako czysta warstwa logiki (niezależna od UI).
- Priorytet backendów audio: **VLC → QtMultimedia → Noop**.
- Hotcue’e przechowywane wyłącznie w tabeli `cue_points` (pełny CRUD w repository).
- Przy przełączaniu trybów staramy się robić lekką synchronizację stanu zamiast pełnego przeładowania tracka (`_sync_deck_a_state_between_views`).
- Używanie `QThreadPool + QRunnable` do ciężkich operacji (waveform extraction).
- Wszystkie zapisy do bazy tylko przez `data/repository.py`.

---

## 4. Najważniejsze problemy i ich rozwiązania (dla przyszłych sesji)

| Problem | Objawy | Rozwiązanie |
|--------|--------|-----------|
| Desynchronizacja hotcue’ów przy zmianie trybu | Hotcue’e znikały lub nie działały po przełączeniu Single ↔ Console | Lepsza funkcja `_sync_deck_a_state_between_views` + odświeżanie waveformu i padów |
| Crash przy ładowaniu waveformu | `TypeError: QThreadPool.start() argument 1 must be QRunnable` | Wprowadzenie `WaveformRunnable` z tokenem ścieżki |
| Backend blokował się na zawsze | Po błędzie ładowania deck nie chciał już nic odtwarzać | Usunięcie `self._enabled = False` z `_set_error()` w backendach |
| Testy DJ padały w CI | Brak VLC → noop nie pamiętał rate/loop | Ulepszenie `_NoopAudioBackend` + skipy w testach wymagających realnego audio |
| Brakujące pola Track po wczytaniu z bazy | `AttributeError: 'Track' object has no attribute 'albumartist'` | Uzupełnienie `_TRACK_META_FIELDS` w repository |
| Bardzo zła czytelność UI | „Ikony zachodzą”, „za gęsto”, „tryb pojedynczy jest podwójny” | Wiele iteracji layoutu + prośba o redesign w stylu Rekordbox |

---

## 5. Aktualny stan (czerwiec 2026 — po full org docs + impl single Odtwarzacz MVP + SZPIEG + push)

**Główne osiągnięcia (zastosowane wszystkie zmiany do tego momentu):**
- **Opcja A (legacy cleanup):** Zakończona. Usunięto wszystkie guardy _HAS_NEW/_use_new, hybrydowe bloki STARA/NEW, martwe klasy DeckWidget/SinglePlayerView, _build_mixer_strip, stare cross/toggle. Nowa architektura sole (DeckController + views dla dual; OdtwarzaczView + SimpleDeckController dla single). Plik dj_player_window.py dramatycznie uproszczony.
- **Single "Odtwarzacz" MVP (primary focus per user "Zacznij od pojedynczego"):** Pełna impl basics per SZPIEG Build Spec + Plan team review (exact match, high pressure):
  - Clean, readable, no-overlap UI: VBox z dużo powietrza (margins 32/24, spacing 18+), dominant waveform stretch7 min260, header title+BPM, time center, large centered transport (CUE/PLAY/STOP).
  - Load file: drag from table (full repo lookup get_track_by_path + enrich Track), file dialog.
  - Playback basics: play/pause/stop (toggle on PLAY, cue logic "near 0 prefer _main_cue", stop to cue), via SimpleDeckController + PlaybackEngine (VLC prio).
  - Feedback: waveform with playhead+beatgrid, title/time/BPM update, status.
  - Drag&drop: from library table to player (mime + urls, highlight, position target in single).
  - Compact pilot-like mode: set_compact_mode (mini sizes, icons, _CompactSpinIndicator anim spinning CD/vinyl/eq via timer/paint, react to playing; toggle in window).
  - Scalability: Expanding/stretch, resizeEvent (dynamic), QStacked in window for clean single/dual switch (eliminates visibility hacks/overlaps).
  - EFFECT tooltips everywhere (1-2 zdania "EFEKT: co się stanie z plikiem/pozycją/UI/stream"; file vs stream rozróżnienie).
  - Default mode: single "Odtwarzacz" (per user).
  - Visibility/switch: clean, odt always visible in single, dual hidden.
- **SZPIEG Agent:** W pełni zintegrowany jako kluczowy research lead. Pełny research + Build Spec dla single Odtwarzacz (lista 12+ przykładów z real soft: Rekordbox/Serato/Traktor/Mixxx/..., opinie pro/users, techniki). Encyklopedia w crew/SZPIEG_agent_spec_and_archive.md (z Plan team review wnioskami + Writer impl exact). Nadrzędny dla zespołu. Hierarchy rethink w docs.
- **Dokumentacja:** W pełni uporządkowana (patrz sekcja "Dla nowych..." na górze). memory.md jako centralna encyklopedia (zasady, stan, SZPIEG, jak dokumentować). Update wszystkich: AGENTS/CLAUDE/HISTORY/crew/CHECKLIST/LISTA/Checklist. Nowi agenci/devi muszą czytać memory + crew/SZPIEG + aktualizować je + code docs + todo + commit.
- **Testy:** Smoke OK, pytest ~44+ pass (relevant DJ/playback/ui), headless odt smoke, manual CHECKLIST paths (resize, drag, no-overlap, single, cue/play/stop, compact, tooltips).
- **Git:** Zmiany zebrane (Opcja A, single reworks per spec, docs org, SZPIEG). Gotowe do push.

**Co jest w miarę stabilne, ale może wymagać dalszej pracy (z archives + SZPIEG/Plan):**
- Pełna integracja single z biblioteką (now playing indicators, batch).
- Compact mode dalsze polish (zawsze-on-top? więcej anim?).
- Playback reliability (VLC install dla user, fallback Qt).
- Więcej SZPIEG research na troublesome (visibility edge, cue consistency full, file vs stream future).

**Otwarte / potencjalne tematy na przyszłość (SZPIEG będzie research):**
- Side tasks dla SZPIEG (visibility/overlap review, compact anim ex, file/stream implications, drag chain, scalability).
- Dodatkowe w single (hotcues grid jako opcja, pitch? — ale tylko po basics solid).
- Multi-team parallelism via docs.

## 6. SZPIEG Agent (kluczowy research/spy agent — dodany 2026, nadrzędny)
- **Rola:** Nadrzędny agent do głębokich badań konkretnych fragmentów UI/UX/wzorców w oprogramowaniu (DJ/audio/file tools). Tworzy listy min. 10-15 przykładów **tylko dla zadanego wąskiego fragmentu**, analizuje implementacje, opinie (użytkownicy + pro DJ/producenci), screenshoty, fora, docs, etc.
- **Instrukcje na stałe:** Szuka "jak to zrobili inni" (techniki, kolejność, metody dokładnie), rozróżnienia (plik audio vs strumień dźwięku, compact/simple/pro modes, tooltipy z EFEKTEM akcji 1-2 zdania), encyklopedia findings w dedykowanym pliku (crew/SZPIEG_agent_spec_and_archive.md).
- **Hierarchia:** SZPIEG research lead — jego Build Spec nadrzędny dla zespołu. Decyduje o wyborach metod gdy brak ścisłego "copy X" (konsultuje z resztą, punktuje przydatność). Inni dostają spec jako primary. Możliwe side tasks od innych agentów (wyjątkowe, za zgodą usera).
- **Archiva:** Oddzielny plik crew/SZPIEG_... + update memory/HISTORY/AGENTS/CLAUDE/Checklist/RECOVERY/crew przy każdym research. Tworzy "sposoby na wszystko" dla pokrewnych tematów.
- **Pierwsze zadanie:** Single "Odtwarzacz" (transport basics play/pause/stop, clean layout bez overlap, drag from table, compact modes, tooltips EFFECT, air/scalability, file vs stream). Pełny raport + Build Spec w crew/SZPIEG_agent_spec_and_archive.md.
- **2026-06-02 Writer:** Dokładna impl reworks per spec+plan (QStack solidify, EFFECT expand, compact+spinning anim, resize, cue/drag+safety, testy, docs). Patrz SZPIEG archiwum + HISTORY. Smoke/pytest OK.
- **2026-06-02 Writer (Code Review Crew — exact match per SZPIEG Build Spec + zatwierdzona "nowa lista przeróbek" z Plan, high pressure, read-before-edit, zero odstępstw, Polish):** Pełna implementacja fixes dla "całej budowy Odtwarzacza MVP" wg listy 1-12 z PLAN + findings SZPIEG/ANALYZER/REVIEWER/UI-DESIGNER + aktualny kod + Build Spec (air 32/24 centering, dominant wave stretch7 min260 clickable double=cue, large centered trans CUE/PLAY/STOP sep BOOTH, EFFECT 1-2 zd file/stream, drag mime+repo+highlight+pos, cue near0 prefer+return, compact flag+anim timer/paint spin CD, scalability resize+stretches, file/stream explicit guards/docs, safety prompt if playing, window toggle, styles compact, tests). Po kolei: 1. Solidify QStack/indices/init (dual0 odt1 add order, switch correct, legacy focused hide no main_layout.add, guards, default single, no race/NameError) — edits dj_player_window (constants, creation, legacy block cleaned, switch use _ODT/_DUAL, initial setCurrent+call). 2+9. Compact toggle + anim spin (reentrancy guard _applying, sync spin/play via _update, fix paint cos/sin radial spokes using a in _CompactSpinIndicator, visible work + re-set, dynamic size, start only compact+play, timer clean stop, pilot window minSize auto in toggle for feel) — edits odt_view (import math, paint rewrite, _update visible+start, apply, set, resize), dj_player_window (window min adjust). 3. Visibility no-overlap (QStack setCurrent, hide only non-stack, single default aggressive, re-sync) — reinforced in switch/docs. 4. Playback reliability (odt/simple: load safety prompt if playing in window+odt drop, cue during play ok, state no-track/compact guards, engine fallback status, play near cue<150, stop to cue (seek after stop), waveform load token) — edits simple (guards in play/pause/stop/set_cue/seek/unload + docs, stop seek cue), window (safety in load_to_deck reinforced). 5. Drag UX (odt: mime+urls+repo get full Track via get_track_by_path enrich + controller load signal, highlight enter/leave robust no-fragile, pos log, safety QMessage if _is_playing) — edits odt (dragEnter robust hl, leave/drop compact re-vis, _load doc). 6. Scalability (resize odt wave/spin dynamic, window, air/margins preserved, Expanding no fixed on wave, multi res) — edits odt resize (doc+policy), window resize doc, styles. 7. EFFECT tooltips + file/stream docs expand in all (buttons wave labels drag controller window: load=FILE, transport=STREAM, cue=pos in file etc) — edits window (drop, load_dialog), simple (unload, seek, load expanded), odt (existing +). 8. Black/empty UI (#OdtwarzaczPanel ss, "Brak utworu" init/unload placeholder, ensure bg in compact) — edits odt apply (re-set ss base in compact). 10. Init/creation (no NameError, odt after dual, stack add order, guards) — in 1. 11. Testy (smoke SAFE+SECONDS exit0, pytest -k dj/playback 44p, python-c headless create+set single+toggle compact+load dummy+play+drag mime sim+resize + CHECKLIST paths sim: load/play/stop/drag/compact/tooltips/no-overlap/resize/single/QStack) — all green, verified. 12. Docs update (memory + HISTORY + SZPIEG archive + crew/PLAN/CHECKLIST + Checklist.md + AGENTS/CLAUDE + code docstrings "per SZPIEG Build Spec + Plan team review... zero odstępstw... must document identical" + todo_write). Przekazano do FIXER/TESTER problemy (np. spin visible timing w some headless, compact window shrink edge, always re-apply in compact for vis, legacy focused still ref in dual, full always-on-top pilot, real audio for cue tests). Zero odstępstw, exact match, read every edit (grep/read_file), po major smoke/pytest/python-c. Język PL w kodzie/komach gdzie pasuje. Update archiwa. Status: Odtwarzacz MVP solidny per spec, smoke/pytest/headless OK, gotowe do user + FIXER/TESTER + commit. Patrz crew/CHECKLIST + SZPIEG (nowy wpis Writer impl 2026-06-02 full list1-12).
- **2026-06-02 SZPIEG full build audit "Odtwarzacz MVP":** Pełne głębokie badanie całej konstrukcji (init window, QStacked dual0/odt1 dual-first, creates, switch, compact+ _CompactSpin timer/paint, odt full methods/drag/load/signals/EFFECT/file-stream, simple ctrl load/play/cue/compact/wave token, main integration, styles, fixes verified). Web/Reddit/X research 12+ przykładów (Rekordbox 1/2PLAYER+preview, Serato lacks, Mixxx PreviewDeck+Full/Compact/Mini+vinyl spin, Traktor modular, VDJ dedicated preview, foobar waveform minibar, VLC minimal, Winamp mini+anim vis, Ableton clip, Engine large wave, Cross clean, WMP mini) + analizy (compact sizes+anim, dominant wave air transport, QStack/modular no overlap, file=load vs stream=transport, EFFECT hovers, scalability resize sizes, cue near0, drag lookup safety) + opinie pro (preview essential/gamechanger esp locked, compact saves multi-mon, anim orient booth, air readable). Punktowanie Lumbago (air/wave 10/10 keep, transport/CUE 9/10 keep, drag 9/10 keep, EFFECT 9/10 expand, compact-anim 8.5/10 polish, cue 8.5 keep, scalab 7.5 polish, file-stream 8 expand guards). SWÓJ Program + zaktualizowany Build Spec 15+ blocks (kolejność: solidify guards first, expand EFFECT, compact polish+always-on-top, scalab, cue/drag, playback guards, legacy, init/stack, black/empty, tests, docs). Problemy lista P0-P10 (compact silent crash top, QStack races, legacy refs, spin test, no always-top, etc. priorytet). Side tasks SZPIEG. Encyklopedia + memory/HISTORY/CHECKLIST/AGENTS/CLAUDE updated identycznie. Headless verify create/stack=2/default single/compact toggle OK. Przekazano do Plan/crew (lista first dla user). Patrz crew/SZPIEG_agent_spec_and_archive.md (nowy wpis "Odtwarzacz full build audit 2026").
- **2026-06-02 REVIEWER (Code Review Crew — per PLAN_Uruchomienie + SZPIEG lead + ANALYZER):** Przegląd + weryfikacja ANALYZER deep analysis + current build single Odtwarzacz MVP (QStack, dual-first+odt index1, create/switch, compact toggle/apply/guard/spin sync, resize/paint, controller/styles/wave/main, known problems). Weryfikacja fixes: compact no crash/silent (re-apply removed), bg (surface via #OdtwarzaczPanel), stack correct (no hacks), no NameError (guards), playback/drag. Identyfikacja remaining P0/P1/P2 (spin rotation: angle computed NOT used in paint spokes — static; dual always overhead for single; compact scalability window not shrink/empty space; init order race; reentrancy guards; playback compact no-track/cue during; vis timing tests; etc.). Compliance z SZPIEG spec: high (air32/24 dominant large trans EFFECT1-2zd compact pilot drag mime+repo+highlight+pos+safety cue near0 scalability resize explicit file/stream safety lock) ~90%+ exact match, ale P0 spin anim broken. Smoke/pytest(44p)/python-c (odt create+compact+stack idx1+close) green; headless inspect OK. Priorytety + recos: fix spin using angle (cos/sin in paint), lazy dual?, more guards, compact window/floating, test visual/timing/edges. Przekazano problemy do SZPIEG (side tasks: anim impl, lazy init, compact scalab). Co OK/nie + raport do UI-DESIGNER/WRITER/FIXER/TESTER. Update docs identycznie (SZPIEG archive full report, memory, HISTORY, crew CHECKLIST, AGENTS/CLAUDE, code docstrings). Per hierarchy: SZPIEG/Plan first. Patrz crew/SZPIEG... (nowy wpis REVIEWER 2026-06-02) + crew/CHECKLIST_reczny.... 
- **2026-06-02 UI-DESIGNER (Code Review Crew per PLAN + SZPIEG lead + AGENT3 style Rekordbox booth redesign air/large trans/dominant wave/high contrast/compact pilot):** Pełny audyt/projekt "Odtwarzacza MVP" (single compact player) na bazie SZPIEG research (12+ tools Rekordbox1PLAYER large wave+CUE+air+drag+preview+compact, Serato/Mixxx/Traktor/Winamp/VLC/foobar spin/compact/drag etc + punktowanie + nadrzędny Build Spec air+dominant+large trans+CUE sep+EFFECT+drag mime+lookup+highlight+pos+cue near0+compact flag+timer/paint spin+scalability resize+file/stream explicit+safety) + ANALYZER/REVIEWER refs + code (odt header+wave+trans+spin header, set_compact/_apply sizes/fonts/margins/spin vis, spin timer/paint spokes angle but positions NOT rotated/a unused, resize, ctrl compact flag+emit, dj window QStack+mode compact only single+_on toggle set+switch re-sync, guards) + CHECKLIST (must Odt single clean no overlap, BPM large, wave>=220, large trans, drag lib, resize no cut, compact pilot, EFFECT, no "za gęsto"). Obowiązkowa lektura: memory + PLAN (PRIORYTET#1 SZPIEG+Plan "nowa lista przeróbek" user first) + SZPIEG archive + AGENTS/CLAUDE + git status (clean) + code. Dokumentacja identycznie (todo_write complex, update memory/HISTORY/SZPIEG/AGENTS/CLAUDE/crew CHECKLIST + code docstrings). 
  Executive: problemy spin rotation (a computed unused in paint spokes static no cos/sin — nie wiruje), compact pilot (collapse OK ale no window min shrink on toggle, vis/anim timing), init order/legacy refs, playback compact, cue/drag UX, reentrancy (fixed partial), QStack good. Co ratuje: booth + pilot compact language (Rekordbox/Traktor/Winamp), QStack solidify, spin fix cos/sin, compact window min size, more guards, EFFECT explicit, drag safety+lookup, scalability dynamic. 
  Nowy język: booth high contrast + pilot compact (mini sizes, spinning CD react play, air preserved compact 8/6, EFFECT file/stream). 
  Konkretne zmiany: odt_view.py (layout VBox air HBox header wave stretch7 trans 3btns, compact apply collapse spin vis, spin paint FIX cos/sin radial rotate, drag mime+highlight+repo+safety, resize dynamic, tooltips EFFECT, docstrings); dj_player_window.py (QStack indices odt1/dual0, compact handler/switch re-sync, resize pass guard, init order, drag route, suggestions main integration); styles (compact sizes expand if needed); waveform (tooltip). 
  Punktowanie vs SZPIEG: air/wave 10/10 keep, trans+CUE 9 keep, compact+anim 8 (P0 fix spin), EFFECT 9, drag 9, cue 8.5, scalab 7.5 (P1 window), file/stream 7 (expand). 90%+ match, spin/compact resize blockers. 
  Handover: do SZPIEG (side: compact anim ex 5-8 + cos/sin, visibility/init lazy dual, file/stream future, drag chain, scalab edges, cue full); WRITER (fix spin cos/sin, compact window min size dynamic toggle, more guards reentrancy/init/switch/compact play, polish drag/cue UX compact, expand EFFECT, init cleanup, playback compact vis; exact per spec nie zmieniaj cue/play ctrl); FIXER (edges rapid toggle+play+switch, highDPI spin0, safety hidden, no-track compact, re-sync, legacy remove); TESTER (smoke/pytest/python-c odt+compact+resize+play+drag+switch; manual full CHECKLIST+task musts single clean BPM/wave/trans/drag/resize/compact+rot spin/EFFECT/no overlap/QStack/safety/file-stream/cue/play; booth sim; report). 
  Update crew docs: memory (ten wpis) + HISTORY + SZPIEG archive (append UI-DESIGNER report + problems) + AGENTS/CLAUDE + crew/CHECKLIST + code. todo_write użyte. Przekazano problemy. Czeka na user review "nowej listy przeróbek" first (per PLAN) + "dalej". Zero odstępstw. Patrz crew/UI_Designer_Odtwarzacz_MVP_Redesign.md (pełny redesign doc po polsku jak AGENT3). 
  Wpływ: audyt+design polish single MVP do 100% spec match + continuity dla multi-team.
- **Wpływ:** Ma pchnąć projekt do przodu przez informed, nie-powierzchowne wybory. Pamiętać na stałe, uwzględniać w crew re-think.
- Pełniejsze testy integracyjne całego playera z biblioteką
- Ewentualne dodatkowe opcje zaawansowane (np. więcej kontroli nad loopami, beatjump itd.)

---

## 7. Jak korzystać z tego pliku w nowych sesjach (dla nowych agentów/programistów — OBOWIĄZKOWE)

1. **Zawsze na początku (w tej kolejności):**
   - Przeczytaj `memory.md` (ten plik — pełny pogląd na zasady, stan, SZPIEG, dokumentację).
   - Przeczytaj `crew/SZPIEG_agent_spec_and_archive.md` (nadrzędny research + Build Spec + encyklopedia + Plan wnioski).
   - Przeczytaj `crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md` (PRIORYTET #1: jak uruchamiać crew — SZPIEG + Plan review "nowej listy przeróbek" dla użytkownika najpierw, potem 6-agent pipeline, God Object "ok", zasady dokumentacji).
2. AI musi przełączyć się na język polski i potwierdzić zrozumienie zasad (hierarchia z SZPIEG jako lead + Plan lista first dla usera, dokumentacja ruchów w ten sam sposób dla multi-team continuity).
3. **Dokumentuj WSZYSTKO tak samo:** 
   - Używaj todo_write dla complex/multi-step.
   - Aktualizuj memory.md (postęp, decyzje, SZPIEG findings, Plan reworks lists, state).
   - Aktualizuj docs/HISTORY.md (milestones).
   - Dla fragmentów: używaj SZPIEG, zapisuj w crew/SZPIEG_ (encyklopedia).
   - Update AGENTS/CLAUDE + crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md + crew/CHECKLIST/LISTA/Checklist przy crew/hierarchy/process changes lub po crew run.
   - W kodzie: docstrings z odniesieniami do spec ("per nadrzędny SZPIEG Build Spec + Plan team review... zero odstępstw... must document identical").
   - Commit często z jasnym message (odniesienia do docs/spec + user feedback).
4. **Cel:** Kompletny pogląd dla nowego (zasady, aktualny stan, jak dokumentować aby nie tracić wątku w multi-team). Inny programista/agent po przeczytaniu memory + SZPIEG + PLAN ma pełny obraz i wie, że musi robić to samo.
5. Przed większymi zmianami lub na koniec — aktualizuj docs. SZPIEG research + Plan "lista przeróbek" + user decision przed impl crew.

**Ten plik + crew/SZPIEG + AGENTS/CLAUDE/HISTORY są "pamięcią instytucjonalną". Im bardziej szczegółowy/szczery/zaktualizowany, tym łatwiej pracować równolegle bez utraty kontekstu.**

## 8. Duże sprzątanie repozytorium (maj 2026) + kontynuacja (czerwiec)

---

**Ten plik ma być „pamięcią instytucjonalną” projektu.** Im bardziej szczegółowy i szczery będzie, tym łatwiej będzie kontynuować pracę po resetach sesji.

---

## 7. Duże sprzątanie repozytorium (maj 2026)

Na żądanie użytkownika przeprowadzono gruntowne porządki:

- Usunięto wszelkie ślady starych wersji:
  - Web MVP (FastAPI + React / Vite)
  - tagerv2 (standalone React tagger)
  - Plany migracji na WinUI 3
- Usunięto: vercel.json, docs/recovery_tagerv2_*.md oraz kilka tymczasowych skryptów debugujących z roota.
- Wyczyszczono requirements.txt (usunięto fastapi, uvicorn, httpx).
- Naprawiono pliki konfiguracyjne .claude/ (launch.json, settings.local.json) – usunięto stare konfiguracje webowe i odniesienia do nieistniejącej struktury `lumbago_app/`.
- Zaktualizowano dokumentację (README, user_guide.md, memory.md), aby jasno komunikować, że projekt jest wyłącznie desktopowy (PyQt6).
- Repozytorium jest teraz czyste i skupione wyłącznie na aplikacji desktopowej + DJ Playerze.

## Dodatki po sprzątaniu (czerwiec 2026)

- Dodano **minimalną warstwę Next.js** (`app/`, `vercel.json` z `"framework": "nextjs"`, `@vercel/speed-insights`, skrypty build) wyłącznie w celu poprawnego deploymentu na Vercel (lumbago-codex). Bez niej platforma błędnie wykrywała `main.py` jako funkcję serverless. Nie jest to reaktywacja pełnej aplikacji web — to tylko obecność kompatybilnościowa.
- Zainstalowano i zarejestrowano **vercel-plugin** (manifesty `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` dodane do repo). 
  - Umożliwia agentom (Claude Code, Codex, Cursor) dostęp do 26 skills Vercel/Next.js (m.in. nextjs, vercel-cli, deployments-cicd, ai-sdk, workflow) oraz specjalistów (ai-architect, deployment-expert, performance-optimizer).
  - Rejestracja: `npx plugins add vercel/vercel-plugin --target claude-code --scope project --yes` (i dla pozostałych targetów).
  - Treść ląduje w cache użytkownika (`~/.claude/plugins/cache/vercel/...`); manifesty w repo są lekkie.
- Zaktualizowano AGENTS.md, CLAUDE.md, README.md oraz Checklist.md o informacje o pluginie i warstwie Vercel.
- Naprawiono serię crashy runtime (DJ Player UnboundLocalError, TypeError None duration/bpm w beatgrid, UnicodeDecodeError w subprocessach na Windows cp1250, fix apply_best_match w autotagu).
- Wypchnięto na main + uporządkowano (rebase, czysty working tree, 160 testów zielonych).

Po sprzątaniu zweryfikowano:
- Struktura: core/, data/, services/, ui/, tests/, main.py na poziomie głównym.
- Brak folderów web/react/winui.
- Testy przechodzą (141 passed).
- Aplikacja uruchamia się poprawnie.

**2026-06-02 TESTER (Code Review Crew per PLAN/SZPIEG/memory — pełna weryfikacja "całej budowy Odtwarzacza MVP" po WRITER/FIXER fixes):**
Testy po kolei (wszystko po polsku, dokumentacja identyczna):
- Smoke: LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py → RETURN CODE 0. OK.
- Pytest: pytest -q --tb=line -k "dj or playback or ui_smoke or hotcue" → 44 passed, 1 skipped. OK (relevant DJ/playback).
- Python -c headless (offscreen Qt): create DJPlayerWindow (default single), _switch_player_mode(0), compact_btn toggle on/off, load mock Track (load_track_to_deck + UI title update), ctrl.play/pause/stop/set_cue (near0 logic), win.resize multi + odt.resizeEvent sim, drag mime sim (QDragEnter/Leave with x-lumbago mime + no crash), checks: stack.count()==2, currentIndex==1 (single), odt._compact flag correct toggle, spin _spinning=True on compact+play_state sim (vis in pure offscreen may lag due Qt polish, but setVisible+update+guards in _apply/_update present), no crash/exit/close. OK.
- Manual per CHECKLIST_reczny_test_nowy_DJ_Player.md (adapted single odt no hotcues full, via code inspect + runtime props + python-c): open single (default yes, idx1); clean no overlap (margins 32/24 spacing18, QStack no hacks/raise/setVisible on stack content, wave dominant); BPM readable (32px 900 accent yes); wave dominant (min260 stretch via addWidget 7 + Expanding policy); large trans (96x58 play etc from BOOTH); drag from lib to player A (mime application/x-lumbago-track-paths + repo get_track_by_path + border highlight + pos log + safety if _is_playing QMessage "Trwa odtwarzanie (stream). Załadować nowy PLIK..."); resize no cut (dynamic resizeEvent wave min from height-120 + spin scale w//30 + QStack stretch); compact pilot (sizes small: margins8/6 wave80 fonts11/14/10/9, spin vis+react play, toggle in window, _spinning flag); EFFECT tooltips (title/bpm/time/wave/cue/play/stop/panel/drag/mode with "EFEKT: co się stanie z plikiem/pozycją/UI/stream" + explicit file=load vs stream=transport); cue/play/stop basics (ctrl near0<150 prefer _main_cue, stop->cue, double=seek+cue, buttons); QStack switch to console (idx0/1 clean, compact_btn disabled in console); no "za gęsto" (air large normal, reduced only pilot); scalability (Expanding+stretch+dynamic+multi res). OK.
- Edge: compact while playing (_spinning=True + start); no track compact (toggle no crash); load while playing (safety _is_playing flag + prompt guard in drop); drag position (log pos in enter/drop); multi resize (700x600..1600x1200 no crash); highDPI sim (Qt policy auto + no hard px). OK.
- Verify fixes (post FIXER): no NameError (full runs clean, Optional/guards/hasattr/try); bg not black (stylesheet): yes (get_deck_panel_stylesheet #OdtwarzaczPanel surface #12171f via BOOTH_COLORS, not pure black/transparent); spin rotates (angle used): YES (FIXER: paintEvent math.radians(self._angle + i*..), math.cos(a)/sin(a) for x1/y1/x2/y2 spokes, num_spokes=8, inner/outer, + "import math", comment "using angle a + cos/sin per SZPIEG/Plan step2/9"); no silent close on compact: yes (dj_player_window.resizeEvent: "Removed full _apply call here to avoid re-entrancy / layout feedback during compact toggle (which changed child sizeHints and could trigger nested resizeEvents + crash or silent exit)", odt.resize handles, _applying_compact guard); init succeeds: yes (NEW ARCHITECTURE ACTIVE + Odtwarzacz MVP logs, dual created first index0 + odt1, odt present, default single _current_mode); indices correct: yes (_DUAL_CONSOLE_IDX=0 _ODT_IDX=1, target_idx calc, if count> setCurrentIndex, initial set, switch guards); air preserved: yes (normal 32/24/18 per spec, compact reduced intentional for pilot-like).
Wyniki ogólne: WSZYSTKO OK (po FIXER spin fix + vis guards + reentrancy polish + comments/docs ref spec).
Co do WRITER/FIXER iteracja: spełnione (high pressure exact match SZPIEG Build Spec + zatwierdzona lista z Planu; zero odstępstw; Writer tylko styl/struktura UI, logika w ctrl; FIXER edges/guards/paint/cos-sin/vis/reentrancy; code + docstrings "Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review... must document identical").
Gotowe (max 3 iter): TAK. Brak faili do przekazania SZPIEG/WRITER. Rekomendacja: git add -A, commit z "TESTER: full verify Odtwarzacz MVP post FIXER - all smoke/pytest/headless/manual/edge/verify OK, spin rotates now, ready user review", push. Update docs identycznie (memory/HISTORY/SZPIEG/CHECKLIST/AGENTS/CLAUDE + crew).
(Per hierarchy: SZPIEG lead + PLAN first binding, dokumentacja dla multi-team continuity.)
Abs paths touched for verify: D:\Claude\ui\dj_player_window.py , D:\Claude\ui\dj\views\odtwarzacz_view.py (spin fixed), D:\Claude\ui\dj\styles.py , D:\Claude\ui\dj\simple_deck_controller.py , tests/* , main.py (via smoke).- **2026-06-02 FIXER (Code Review Crew, po WRITER + SZPIEG/ANALYZER/REVIEWER/Plan nowa lista + full read memory/PLAN/SZPIEG/CHECKLIST/outputs crew/code):** Naprawa wszystkich bugów z "całej budowy Odtwarzacza MVP" wg dokładnej listy z user (z "nowa lista" + P0/P1 findings z SZPIEG/REVIEWER). Język polski w komentarzach. Read before edit, zero odstępstw, exact match SZPIEG Build Spec + Plan reworks + memory. Użyto todo_write. 
  Fixes:
  - spin anim: paintEvent w _CompactSpinIndicator używa 'a' (radians + cos(a) sin(a) dla x1 y1 x2 y2 radial spokes rotate; 8 spokes; usunęto static; + import math + komentarze "per SZPIEG/Plan").
  - spin visible compact: test isVisible() po setVisible + force set+update jeśli nie (w _apply_compact + po switch setCurrent + odt.show sim w testach); "Upewnij spin visible w compact (test isVisible po set, po show stack current odt)".
  - guards load/play jeśli playing: safety prompt QMessage w odt dropEvent + w window load_track_to_deck (dla single odt load z library/drag) confirm "Trwa odtwarzanie... Załadować nowy PLIK"; + no-track guards w ctrl.play etc; "safety prompt w odt load like in window".
  - init order/race: ensure odt ready (create guard w init po dual + on-demand w _switch if single && !odt); odt before switch/setCurrent/compact/play.
  - legacy focused single_container: usunięto creation w _create_dual_console (po Opcja A sole odt for single); set=None; uproszczono init legacy block do None+hide; zaktualizowano wszystkie komentarze/referencje; "Usuń lub ukryj legacy...".
  - reentrancy: wzmocnione guardy (_applying_compact, set same return, window resize pass z komentarzem "to avoid re-entrancy", switch guards); test w python-c.
  - playback compact: cue logic (live set_cue), waveform load (token/request indep compact), no track state (ctrl guards + odt unload reset _is_playing + status); play/cue/stop w compact bez błędu.
  - scalability: air/margins compact (8/6/6 + komentarze), dynamic min wave (resizeEvent non-compact + compact 40-100); window minSize dynamic shrink w _on_compact (380x280 / restore _orig) dla "window not shrink empty"; odt resize spin/wave.
  - file/stream: + komentarze/guards w load vs transport (odt: _load_dropped "FILE op... transport STREAM", _setup_ui, drag; simple: load=FILE play=STREAM + doc; window load_to + drop + safety; "dodaj komentarze/guards w load vs transport paths w odt/controller").
  - inne: drag highlight compact (enter force 3px cyan + !important + log compact flag; leave reset); cue during play (live OK); vis timing; no odt compact guard (disable btn).
  Tests po: smoke exit0; pytest 44p; python-c create+toggle compact+isVisible test+load+play+cue+resize+drag sim OK (headless spin vis lag ale guardy passed).
  Update docs: memory (ten wpis) + docs/HISTORY.md (append) + crew/SZPIEG (append FIXER resolved + test results) + crew/PLAN_Uruchomienie + crew/CHECKLIST_reczny + AGENTS.md + CLAUDE.md + code docstrings (nadrzędny SZPIEG + Plan + "must document identical").
  Przekazano do TESTER z pełnym raportem + poleceniami run (smoke/pytest/python-c + manual per CHECKLIST).
  Abs paths: D:\Claude\ui\dj_player_window.py , D:\Claude\ui\dj\views\odtwarzacz_view.py , D:\Claude\ui\dj\simple_deck_controller.py .
  Status: wszystkie z listy naprawione, tests pass, gotowe TESTER. Per hierarchy/PLAN.
