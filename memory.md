# Memory — Lumbago Music AI (DJ Player Project)

**Data ostatniej aktualizacji:** Czerwiec 2026 (po pełnej organizacji dokumentacji, impl single Odtwarzacz MVP per SZPIEG spec, team review, push; crew PLAN_Uruchomienie_... aktywowany z SZPIEG jako PRIORYTET #1 + user 'ok')

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