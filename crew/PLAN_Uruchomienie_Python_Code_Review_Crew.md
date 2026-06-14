# Plan: Uruchomienie Python Code Review Crew (6-agentów) na projekcie Lumbago Music AI

**Data utworzenia / aktualizacji:** 2026-06 (po feedbacku użytkownika na proposed plan)

**Status:** Obowiązujący. SZPIEG + zmiany w pracy zespołu — **PRIORYTET #1 (w pierwszej kolejności)**. Ten dokument jest "planem uruchomienia" crew i musi być czytany przez wszystkich agentów/subagentów przed startem pracy crew.

**Feedback użytkownika (akceptacja):** "ok" — plan przyjęty w wersji z SZPIEG i aktualizacją zmiany pracy zespołu na pierwszym miejscu. God Object note potwierdzone jako "ok". Dokument aktywowany.

---

## PRIORYTET #1: Aktualizacja zmiany pracy zespołu i funkcje SZPIEGA (zawsze na górze, binding)

Użytkownik potwierdził (feedback na proposed plan):

> plan jest ok tylko trzeba w nim wziąść pod uwagę aktualizację zmiany pracy zespołu i funkcje SZPIEGA. W pierwszej kolejnosci

Dlatego **wszystkie uruchomienia Code Review Crew (i wszelkie prace na fragmentach)** **zaczynają się od** tego rozdziału. Żadne działanie crew nie może ruszyć bez explicit uwzględnienia poniższego.

### Nowa hierarchia crew (Rethink 2026 — SZPIEG jako research lead)
1. **SZPIEG (SPY)** — Nadrzędny agent badawczy / research lead dla **wąskich fragmentów** (nie całe produkty).
   - Dla zadanego fragmentu (np. single Odtwarzacz transport, compact pilot, EFFECT tooltips, drag UX z tabeli do playera, visibility w switchu, cue consistency, file vs stream ops, scalability) tworzy listę >=10-15 popularnych/good tools + konkurentów + lubianych standardów + praktyk pro DJ/producentów (zarobkowo).
   - Źródła: dokumentacje, Reddit/fora/DJ communities, opinie użytkowników + pro, screenshoty, YouTube, podcasty, wywiady, trial-error + self-educate + konsultacje.
   - Kluczowe rozróżnienia: praca z **fizycznym PLIKIEM audio** (load, rename, move, tag writeback) vs **strumieniem dźwięku** (playhead, seek, cue, pause, transport) — pozornie to samo, ale inne operacje i ryzyko.
   - Window modes: **Compact** (pilot-like / notification bubble: minimal info, progress/seek, volume, basic transport, symboliczna animowana ikona wirującego CD przy play / pause / error overlay; zawsze-on-top opcja), **Simple** (czysty, bez przytłaczania, "ZA A WANSOWANE" w rogu, krótki żołnierski język, minimal interakcji), **Pro**.
   - **Tooltipy/podpowiedzi na KAŻDYM elemencie funkcyjnym** MUSZĄ opisywać **EFEKT** użycia (1-2 zdania: co się stanie z plikiem / oknem / pracą / streamem przy kliknięciu). Nawet OK/Cancel.
   - Przejrzystość: okna skalujące się bez ograniczeń (resize, multi-monitor, high DPI), dużo powietrza, dominant elementy (waveform).
   - **Encyklopedia:** Wszystkie findings skrupulatnie w `crew/SZPIEG_agent_spec_and_archive.md` (datowane, z punktami). Pozwala na "sposoby na wszystko" dla pokrewnych tematów w przyszłości.
   - Gdy brak STANOWCZEGO "ma być jak w TYM konkretnym produkcie" — SZPIEG decyduje o metodzie (konsultuje z resztą, punktuje przydatność **dla TEGO projektu**). Build Spec SZPIEG jest **nadrzędny / binding** dla reszty zespołu (Designer, Writer, Fixer, Tester, Plan).
   - Side tasks dla SZPIEG: tylko w wyjątkowych przypadkach (agent utknął, powtarzający się problem), za zgodą użytkownika.

2. **Plan agent** — Dostarcza **pełne wnioski + rewerk plans + punktowanie + "nową listę przeróbek"** na żądanie (przed jakąkolwiek implementacją).
   - Po SZPIEG research (lub z archiwum) — Plan produkuje:
     - Wnioski z punktowaniem (np. air+wave 10/10, transport+CUE 9/10, compact+anim 8/10 highest missing, EFFECT 9/10, drag+safety 9/10, cue 8.5/10, scalability 7.5/10, file/stream 7/10).
     - Rekomendacje: co zachować, co przerobić (z uzasadnieniem dla Lumbago).
     - Szczegółowa lista przeróbek / kolejność kroków (np. 1. Solidify QStacked/visibility, 2. Expand EFFECT tooltips+docs, 3. Compact+anim spinning, 4. Scalability resize, 5. Cue/drag+safety, 6. Testy, 7. Updates archiva).
     - Critical files, side tasks dla SZPIEG, Build Spec highlights.
   - **Użytkownik musi mieć w pierwszej kolejności możliwość przeczytania "waszą nową listę przeróbek" i samodzielnej decyzji** (explicit user instruction: "dajcie mi w pierwszej kolejnosci przeczytać waszą nowąą liste przeróbek do i pewniessaam msie na ro").
   - Plan nie startuje impl — tylko raport + rekomendacje + lista do review użytkownika.
   - Po decyzji użytkownika ("dalej", "ok", "zmień X") — dopiero wtedy crew przechodzi do impl.

3. **Reszta zespołu (6-agent Code Review Crew + General)**: Dostaje **combined spec od SZPIEG + zatwierdzoną listę przeróbek z Planu** jako primary input.
   - Implementują **dokładnie wg spec** (high pressure: read before every edit, zero odstępstw, "exact match").
   - Writer: nie może zmieniać radykalnie logiki biznesowej w UI (tylko styl i strukturę) — **potwierdzone "ok" przez użytkownika**.
   - Po każdej fazie/iteracji: **obowiązkowa aktualizacja dokumentacji w identyczny sposób** (patrz niżej "Zasady dokumentacji dla multi-team").
   - Użycie: `spawn_subagent` tool z pełnym kontekstem (memory + SZPIEG archive + ten PLAN + aktualny stan z code/docs).

### Zaktualizowany pipeline uruchomienia crew (dla każdego większego zadania / fragmentu)
1. **Zawsze najpierw (SZPIEG + Plan — PRIORYTET #1)**:
   - Jeśli fragment wymaga researchu (UI/UX, compact, drag, tooltips, visibility, cue, file/stream, scalability itp.): odwołać się do `crew/SZPIEG_agent_spec_and_archive.md` (lub zlecić SZPIEG side task).
   - Uruchomić Plan subagenta z promptem zawierającym SZPIEG findings + zadanie → Plan zwraca pełne wnioski + punktowanie + nową listę przeróbek.
   - **Prezentacja użytkownikowi** listy przeróbek jako pierwszej rzeczy do przeczytania i decyzji.
   - Czekać na explicit "dalej" / akceptację / zmiany od użytkownika.

2. **Potem klasyczny 6-agent Code Review Crew** (jeśli użytkownik zatwierdzi):
   - ANALYZER → REVIEWER → UI-DESIGNER (dla UI) → WRITER → FIXER → TESTER.
   - Max 3 iteracje.
   - Język: **wszystko po polsku**.
   - Każdy agent dostaje prompt z: full memory + SZPIEG spec (binding) + zatwierdzona lista przeróbek z Planu + aktualny kod + "exact match required, read before edit".
   - Po każdej roli: smoke + pytest + python -c imports + headless creation + manual checklist paths (jeśli UI).
   - Writer/Fixer/Tester: high pressure exact implementation per spec (zero creative odstępstw).

3. **Zasady dokumentacji (obowiązkowe dla wszystkich — continuity dla odrębnych zespołów)**:
   - Zawsze aktualizuj: `memory.md` (centralna żywa encyklopedia), `docs/HISTORY.md`, `crew/SZPIEG_agent_spec_and_archive.md` (dla research), `AGENTS.md`, `CLAUDE.md`, `crew/CHECKLIST_*.md`, `crew/LISTA_*.md`, `Checklist.md`, `RECOVERY.md`.
   - W kodzie: docstrings z "Uwaga dla nowych agentów/programistów: Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review... Patrz docs... must document identical".
   - Używaj `todo_write` dla complex/multi-step.
   - Commit często z jasnym message (odniesienia do docs/spec + co zrobione).
   - Cel: każdy nowy programista lub agent po przeczytaniu memory + SZPIEG + tego PLAN + AGENTS/CLAUDE ma **kompletny pogląd** na zasady, aktualny poziom prac, hierarchy, i wie, że musi dokumentować dokładnie tak samo — bez tracenia wątku nawet przy wielu odrębnych zespołach.

4. **Narzędzia uruchomienia**:
   - Głównie `spawn_subagent` (z `subagent_type`: general-purpose / explore / plan / reviewer itp., prompt zawierający pełny kontekst + "follow SZPIEG spec first + Plan reworks list + user decision").
   - Dla research fragmentów: prompt z "You are SZPIEG..." + instrukcje z SZPIEG archive.
   - Dla Plan: prompt "You are the Plan agent. Produce full wnioski + punktowanie + lista przeróbek for user review first. No impl yet."
   - Po zakończeniu: zawsze `git add -A`, commit, push (standing auth).

### Akceptacja uwag z feedbacku
- Proposed plan line 61 (God Object): "Dużo logiki biznesowej siedzi w UI (antypattern God Object) — Writer nie może tego zmieniać radykalnie (tylko styl i strukturę)." → **OK** (potwierdzone przez użytkownika).
  - Uwaga: Po Opcja A (pełny legacy cleanup) + nowa architektura sole (DeckController / SimpleDeckController + dumb views OdtwarzaczView/ConsoleDeckView + QStacked) — God Object w `ui/dj_player_window.py` jest dramatycznie zredukowany. Logika playback/cue/waveform/hotcue jest w controllerach. Writer może bezpiecznie pracować na views + wiring, o ile trzyma się spec (nie rusza core business w controllerach/repo bez uzasadnienia w zatwierdzonej liście).

---

## Oryginalny / bazowy opis 6-agent Code Review Crew (zachowany, ale podległy nowemu priorytetowi #1)

### Cele crew
- Systematyczna, wieloetapowa recenzja i poprawa kodu Python (głównie UI + logika DJ Playera).
- Unikanie "God Object", duplikacji, złych wzorców (szczególnie w `ui/dj_player_window.py` i widokach).
- Wysoka jakość + czytelność + testowalność.
- Pełna dokumentacja procesu (dla continuity).

### Role (pipeline — sekwencyjny, z możliwością iteracji max 3x)
1. **ANALYZER** — Głęboka analiza wskazanego pliku/plików lub obszaru. Identyfikuje problemy: duplikacja, God Object, brak separacji (logika w UI), złe nazewnictwo, brak testów, problemy z drag&drop, visibility, compact, cue, playback, etc. Produkuje raport z punktami.
2. **REVIEWER** — Przegląd raportu ANALYZERA. Weryfikuje, priorytetyzuje (P0/P1/P2), sugeruje architekturę (np. DeckController + dumb views). Dodaje rekomendacje UX (booth, air, Rekordbox-like). Raport końcowy do UI-DESIGNER/WRITER.
3. **UI-DESIGNER** (tylko dla UI fragmentów) — Projektuje nowe rozwiązania UI (layout, spacing, rozmiary padów 82x62, BOOTH_COLORS, dominant waveform, centered transport, compact mode, drag&drop z mime+repo lookup, EFFECT tooltips, QStacked dla switcha). Produkuje szczegółowy redesign doc (np. AGENT3_UI_Designer_Rekordbox_Redo.md) z konkretnymi zmianami w plikach.
4. **WRITER** — Implementuje zmiany **dokładnie wg** zatwierdzonej listy przeróbek z Planu + SZPIEG Build Spec + raportu UI-DESIGNER/REVIEWER. Tylko styl/strukturę w UI (logika biznesowa — patrz akceptacja powyżej). Wysoka presja exact match. Po każdej większej zmianie: smoke + pytest + headless.
5. **FIXER** — Przegląda kod WRITERA. Naprawia błędy, poprawia edge cases, ujednolica, usuwa pozostałości. Przygotowuje do testów.
6. **TESTER** — Pełna weryfikacja: smoke (LUMBAGO_SAFE_MODE=1), pytest (relevant DJ/playback/ui), python -c (imports, headless creation views/controllers), manual paths z CHECKLIST (drag, compact toggle, play/pause/stop/cue, resize no-overlap, tooltips EFFECT, single default, QStack visibility). Raport + decyzja o kolejnej iteracji lub "gotowe".

### Zasady działania crew (pod SZPIEG/Plan)
- **Język:** Wszystko po polsku (user requirement).
- **Max 3 iteracje** pełnego cyklu na dany obszar.
- **Testy na bieżąco:** Po każdej roli/kluczowej zmianie — smoke + pytest + weryfikacja.
- **Dokumentacja:** Każdy agent aktualizuje odpowiednie pliki (patrz PRIORYTET #1).
- **Prompty:** Muszą zawierać odniesienie do `memory.md` + `crew/SZPIEG_agent_spec_and_archive.md` + ten PLAN + "follow hierarchy, SZPIEG binding, user-reviewed reworks list first".
- **Narzędzia:** `spawn_subagent` (z odpowiednim `subagent_type` i bogatym promptem). Możliwe równoległe dla nieblokujących części (np. Plan + side research), ale weryfikacja sekwencyjna.
- **Nie przerywać bez powodu:** "dalej", "do końca", "równolegle działaj aż do końca bez przerw".

### Kiedy uruchamiać crew
- Duże refaktoryzacje (Opcja A, redesign playera).
- Wprowadzanie nowych wzorców (compact, drag, menu kontekstowe per widget).
- Po SZPIEG research + Plan review listy i decyzji użytkownika.
- Gdy użytkownik prosi o "Code Review Crew" lub konkretny obszar (np. "zatrudnij agenta do projektowania UI").

### Przykładowa sekwencja uruchomienia (po user review listy)
1. Przygotuj prompt z pełnym kontekstem (memory + SZPIEG + PLAN + kod + zatwierdzona lista).
2. Spawn ANALYZER (jeśli potrzeba świeżej analizy).
3. Spawn REVIEWER na output ANALYZERA.
4. Spawn UI-DESIGNER (dla UI) lub bezpośrednio WRITER (z full spec).
5. WRITER → FIXER → TESTER.
6. Po TESTER: aktualizacja docs + commit/push + prezentacja użytkownikowi.

### Ograniczenia Writer (akceptowane)
- Dużo logiki biznesowej siedzi w UI (antypattern God Object) — Writer nie może tego zmieniać radykalnie (tylko styl i strukturę). **OK** (per user feedback).
- Po Opcja A: preferuj pracę przez controllery + dumb views. Logika cue/playback/waveform — w `SimpleDeckController` / `DeckController`. UI tylko wiring + prezentacja.

### Pliki referencyjne (dołączane do promptów crew)
- `memory.md` (dla nowych: zasady, stan, SZPIEG, jak dokumentować).
- `crew/SZPIEG_agent_spec_and_archive.md` (nadrzędny research + Build Spec + encyklopedia + Plan wnioski).
- Ten plik (`crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md`).
- `AGENTS.md`, `CLAUDE.md`.
- `crew/AGENT3_UI_Designer_Rekordbox_Redo.md` (przykład output UI-DESIGNER).
- `crew/CHECKLIST_reczny_test_nowy_DJ_Player.md`, `crew/LISTA_POPRAWEK_*.md`.
- `docs/HISTORY.md`.
- Aktualny kod + git status.

### Weryfikacja po crew
- Smoke: `LUMBAGO_SAFE_MODE=1 LUMBAGO_SMOKE_SECONDS=3 python main.py`
- Pytest: `pytest -q --tb=line -k "dj or playback or hotcue or ui_smoke"`
- Python -c: headless creation OdtwarzaczView, SimpleDeckController, switch modes, set_compact, drag mime symulacja.
- Ręczny: per CHECKLIST (single default, drag z library, compact anim, EFFECT tooltips, no overlap on resize, cue/play basics, QStack clean switch).
- Docs: sprawdź czy memory/HISTORY/SZPIEG/AGENTS/CLAUDE/crew zaktualizowane identycznie.

---

## Jak aktualizować ten Plan
- Po każdym większym researchu SZPIEG lub decyzji użytkownika dotyczącej crew — dodaj sekcję "Aktualizacja z [data]".
- Zawsze po zmianach w hierarchii: propaguj do memory.md, AGENTS.md, CLAUDE.md, HISTORY.md, crew files.
- Ten dokument + SZPIEG + memory są "pamięcią instytucjonalną" dla multi-team.

**Koniec planu.** 

Po przeczytaniu tego (i memory + SZPIEG) każdy agent ma pełny obraz: SZPIEG + Plan review listy **zawsze pierwsze**, potem crew 6-agentów z exact match i identyczną dokumentacją.

Przygotowane na podstawie feedbacku użytkownika + aktualnego stanu projektu (czerwiec 2026, single Odtwarzacz MVP solidny per spec, Opcja A zakończona, docs zorganizowane dla continuity).

**2026-06-02 aktualizacja po uruchomieniu:** REVIEWER (jako część crew) wykonał weryfikację (na bazie ANALYZER + SZPIEG + code + CHECKLIST). Raport + problemy P0 (spin) /P1 (dual overhead, compact scalab, init) przekazane do SZPIEG w crew/SZPIEG_agent_spec_and_archive.md + memory/HISTORY/CHECKLIST/AGENTS/CLAUDE zaktualizowane identycznie (per zasady). Smoke/pytest/python-c/manual OK dla fixes. Użyto todo_write. Zgodne z PRIORYTET#1 (SZPIEG/Plan first, choć tu review po Writer). Następne kroki: fixy przez WRITER/FIXER po ewentualnej decyzji user/Plan. Dokumentacja multi-team continuity zachowana.**2026-06-02 update (po FIXER):** FIXER zakończył fixes z "nowa lista" (spin anim fix cos/sin, spin vis, load guards safety, init order, legacy single_container remove/hide, reentr test, compact playback cue/wave, scalab air/margins/dynamic + window shrink, file/stream comments/guards odt/ctrl, drag hl compact, cue play etc). Smoke/pytest/python-c green. Docs (memory/HISTORY/SZPIEG/CHECKLIST/AGENTS/CLAUDE) + code updated identycznie. Przekazano TESTER. Per PLAN: SZPIEG/Plan lista first, exact, docs continuity.
**2026-06-14 — FIXER polish edges po "dalej" + SZPIEG/Plan nowa lista 1-15 (per hierarchy "nie przestawaj"):** Polish edges (fokus 2,5,7,12,14,9,10 + compact prompt UX, highDPI/empty, vis timing, guards, legacy, black/empty, file/stream): compact prompt UX (MOM parent top window for floating pilot); highDPI/empty+vis (force update in apply); legacy+guard re-sync. Read-before exact. Verifs smoke0/pytest44p/python-c (create/stack/compact/load/cue/resize/drag) + manual CHECKLIST all green. 'gotowe' pass TESTER. Docs identical (memory/HISTORY/this/CHECKLIST/SZPIEG/AGENTS/CLAUDE/code + "per nowa lista... must document identical"). Abs D:\Claude\ui\dj_player_window.py + odt (prompt+highDPI+legacy polish) + crew/* . Ukończone. Do końca.
**2026-06-02 WRITER full 1-12 (per PLAN lista + SZPIEG binding):** Zrobiono po kolei 1-12 (QStack solidify+init, compact+spin cos/sin+toggle+pilot, vis no-overlap, playback rel, drag UX, scalab, EFFECT+docs, black/empty, anim, init, testy smoke/pytest/python-c+CHECKLIST, docs update all+code). Exact match, read before, zero odst, tests green. Przekazano FIXER/TESTER problemy. Docs (memory/HISTORY/this PLAN note + SZPIEG/crew CHECK + Checklist + AGENTS/CLAUDE) updated identically per multi-team. Status: gotowe.

**2026-06-14 — WRITER (nowa lista 1-15 po "dalej" user):** OBOWIĄZKOWA first (memory+SZPIEG+PLAN+CHECK+UI_Designer+code). High pressure read-before-edit, exact per lista 1-15 + SZPIEG spec (grupy 1+8 QStack/init/on-demand/legacy/guards, 2+12 compact+always-on-top/floating, 3+10 EFFECT/file/stream, 5+9 scalab/black, 4+6+7+14 drag/cue/legacy/moreguards). Verifs (smoke0/pytest44p/python-c odt ready/stack/compact/load/cue/resize/switch + CHECKLIST+edges) green. 'gotowe' + pass FIXER/TESTER. Docs identical (memory/SZPIEG/this PLAN/CHECKLIST/HISTORY/AGENTS/CLAUDE/code "per SZPIEG Build Spec + Plan nowa lista po 'dalej' user... must document identical"). Abs: D:\Claude\ui\dj_player_window.py + odtwarzacz_view.py . Ukończone. Do końca.
**2026-06-02 SZPIEG re-audit "uruchmo jeszcze raz zespouł... nie przestawaj puki nie skonczysz":** Pełny re-audit po kolei całej budowy odtwarzacza (single primary) + research/punktowanie/Build Spec/P0-P10 przekaz/side + 'gotowe' pass Plan/crew (lista first). Docs updated identycznie (SZPIEG new entry, memory, HISTORY, this PLAN note, CHECKLIST, AGENTS/CLAUDE, code). Per PRIORYTET#1. Status: ukończone do końca.
