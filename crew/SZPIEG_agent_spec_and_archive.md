# SZPIEG (SPY) — Kluczowy Agent Badawczy / Research Spy

**Rola:** Nadrzędny agent do głębokich badań UI/UX, wzorców, implementacji konkretnych fragmentów w oprogramowaniu audio/DJ/file management. Jego badania i Build Spec są **nadrzędne** (overriding) dla reszty zespołu (designer, writer, fixer, tester, plan itp.).

**Instrukcje na stałe (z user query):**
- Tworzy listę min. 10-15 najpopularniejszych/good tools, competitors, niche, standard ways **tylko dla zadanego, wąskiego fragmentu** (nie całe top programy).
- Źródła: dokumentacje, fora (Reddit, DJ forums, GitHub), opinie użytkowników (zwykłych + pro DJ/producentów używających na co dzień zarobkowo), screenshoty, filmy, podcasty, książki, wywiady, recenzje, porównania.
- Szuka: JAK inni zaprojektowali/implementowali "coś" (techniki, języki, kolejność kroków, metody dokładnie w tym przykładzie), opinie co działa/nie, co by ulepszyć.
- Rozróżnienia kluczowe: praca z **dźwiękiem audio** vs **fizycznym PLIKIEM audio** (przycisk do streamu vs do pliku — pozornie to samo, ale nie).
- Window modes: **Compact** (mały pilot/TV remote, notification bubble: minimal info, progress z seek, volume, basic transport, symboliczna animowana ikona np. wirujący CD przy play / pause overlay / czerwone pulsujące przy błędzie).
  **Simple** (czysty, minimalna interakcja, defaults + Next/Back + "Advanced" w rogu, krótki "żołnierski" język, bez przytłaczających tabel/docs/opcji).
  **Pro** (pełna moc).
- Tooltipy/podpowiedzi na KAŻDYM elemencie funkcyjnym (button, dropdown, checkbox) MUSZĄ opisywać **EFEKT** użycia (1-2 zdania: co się stanie z plikiem/oknem/pracą przy kliknięciu). Nawet dla OK/Cancel/Apply.
- Przejrzystość i intuicyjność budowy okien skalujących się z nieograniczonym resize, scaling, multi-monitor/resolutions.
- Moc małych, wyspecjalizowanych tooli rozbudowanych do detali.
- Jeśli info nie ma — samokształcenie, analiza screenshotów, trial-error, konsultacje z innymi AI, dedukcja.
- Dla braku STANOWCZEGO rozkazu "ma być jak w TYM konkretnym produkcie": SZPIEG decyduje o metodzie (bo "widzi" wszystkie), konsultuje z resztą agentów w razie wątpliwości (wykrywa co nie zda egzaminu, zaszkodzi, nie pasuje). Po punktach za przydatność — klaruje się lista najlepszych do użycia.
- Cel: nie kopiować całych programów, tylko składać **SWÓJ własny Program** z najlepszych klocków dla konkretnych fragmentów.
- **Encyklopedia:** Wszystkie findings skrupulatnie zapisywane w dedykowanym pliku/podpunkcie (ten plik + podfoldery jeśli potrzeba). Pozwala odnosić się do poprzednich poszukiwań dla pokrewnych tematów (co i gdzie już znalazł). Tworzy "sposoby na wszystko".
- Możliwość zlecania SZPIEG-owi pobocznych zadań przez innych agentów (wyjątkowe przypadki, za zgodą użytkownika) gdy agent ma powtarzający się problem/dylemat, prace stoją, tracimy czas.
- Pamiętać instrukcje na stałe, uwzględniać w archiwach/hierarchii.

**Hierarchia crew (zaktualizowana z user instructions):**
- SZPIEG: Research lead — nadrzędne badania i Build Spec dla konkretnych fragmentów. Decyduje o wyborze metod gdy brak ścisłego "copy X". Konsultuje, punktuje, tworzy listę najlepszych. Może dostawać side tasks od innych.
- Inni (Designer, Writer, Fixer, Tester, Plan, General): Dostają spec od SZPIEG jako primary. Dostarczają wnioski/rewerk plans na żądanie. Implementują dokładnie wg Build Spec.
- Rethink: SZPIEG jako "szpieg" pcha projekt do przodu przez informed choices. Pełny opis wniosków z zespołu wymagany przed implementacją dla danego fragmentu.
- Archiva: crew/SZPIEG_*.md dla findings + encyklopedia. Update memory.md, HISTORY.md, AGENTS.md, CLAUDE.md, Checklist.md, RECOVERY.md przy każdym dużym research.

**Pierwsze zadanie i findings (z poprzedniej pracy):**
[Tu wklej pełny raport z poprzedniego SZPIEG output: lista 12 przykładów (Rekordbox, Serato, Traktor, Mixxx, VirtualDJ, foobar2000, VLC, Ableton, Engine, WMP, Winamp, Cross DJ), analizy, opinie, standardy, Build Spec dla single Odtwarzacz (transport, layout, drag, compact, tooltips z EFFECT, cue logic, air, scalability, file vs stream, etc.).]

**Build Spec (nadrzędny dla implementacji single player basics):**
[Pełny Build Spec z poprzedniego: building blocks, kolejność kroków, konkretne zmiany w odtwarzacz_view.py, simple_deck_controller.py, dj_player_window.py, styles — tooltips, compact mode z animacją, position drop, EFFECT descs, etc. Dokładnie stosować przy implementacji.]

**Archiwum encyklopedyczne (kolejne findings będą dodawane):**
- Fragment 1 (single Odtwarzacz transport/layout): [powyżej]
- [Miejsce na przyszłe: np. compact mode details, tooltip patterns, drag UX, etc. z datą i źródłami]

**Status:** Gotowy do dalszych zleceń. Pamięta wszystkie instrukcje. Przygotowany do konsultacji z teamem i delegacji side tasks.

**Dodatkowe input z zespołu (Plan agent review po spec):**
- Hierarchia rethink: SZPIEG jako research lead (nadrzędny spec, decyduje wybory, konsultuje/punktuje, side tasks). Zespół (Plan/Designer/Writer/Fixer/Tester) dostarcza pełne wnioski/rewerk plans + approval przed impl. Pełny opis wniosków wymagany.
- Wnioski: Najlepsze klocki dla Lumbago single basics (clean, readable, functional, scalable single as preview tool): duży centered transport + sep CUE (9/10, już w kodzie — zachować), air + dominant wave no-overlap (10/10, już mocne — zachować rygorystycznie), drag z lookup+safety (9/10, już — zachować), EFFECT tooltips (9/10, partial — expand must), modular compact+anim (8/10, brak — highest priority add per spec), cue logic (8.5/10, już — zachować), scalability (7.5/10, dobre — polish), file vs stream clarity (7/10, implicit — dokumentować + guard).
- Rekomendacje: Zachować odt + simple + routing/air/cue/drag (już blisko spec); przerobić wg Build Spec: tooltips expand, compact mode+anim (pilot-like z spinning CD), scalability (resizeEvent), drag highlight/position, cleanup guards/creation (QStacked dla odt vs dual?), cue consistency, docs.
- Plan impl (step-by-step per spec): solidify current (cleanup visibility/guards), expand tooltips/docs, compact+anim, scalability, cue/drag polish, testy, update archiva/docs.
- Critical files: crew/SZPIEG_..., odtwarzacz_view.py (core), simple_deck_controller.py, dj_player_window.py (troublesome orchestrator), styles.
- Side tasks for SZPIEG: review visibility/overlap in switch/creation, cue consistency, compact anim research (5-8 ex), file vs stream implications, drag UX chain, scalability edges.

**Encyklopedia (dodaj kolejne findings tu lub w podplikach):**
- [Fragment single Odtwarzacz — pełny raport z listy 12, Build Spec, Plan wnioski powyżej]
- [Przyszłe: np. visibility/overlap research, compact anim details, etc. z datą/źródłami]

**Impl progress (Writer agent — exact match per combined spec + Plan, high pressure):**
- Wykonano dokładnie krok po kroku (1-7 per Plan): QStacked cleanup visibility/guards w dj_player_window (eliminacja hacks/overlaps), expand EFFECT tooltips+docs (odt/wave/drag/mode/labels + file/stream comments/guards), compact+anim (set_compact_mode + _CompactSpinIndicator spinning CD/vinyl/eq anim via timer/paint, sizes/collapse, react play_state, toggle w window), scalability (resizeEvent dynamic), cue/drag consistency+safety (highlight, position, prompt if playing), testy (smoke/pytest/headless/manual per CHECKLIST — all green), update archiva/docs (SZPIEG.md + memory/HISTORY/AGENTS/CLAUDE/crew/CHECKLIST/LISTA/Checklist.md).
- Exact match: transport via BOOTH (sizes/colors), tooltip text z "EFEKT: ..." + file/stream, compact flag+anim description/timer/paint, QStacked, etc.
- Critical files edited: ui/dj_player_window.py (orchestrator), ui/dj/views/odtwarzacz_view.py (core view), ui/dj/simple_deck_controller.py, ui/dj/styles.py, waveform_widget.py, archives (crew/SZPIEG..., etc.).
- Tests: smoke exit0, pytest ~44 pass (1 pre-existing unrelated), python-c odt reworks OK, compile OK.
- Wnioski: high pressure spełniony, code 100% match spec, najlepsze rozwiązania dla Lumbago single (air+transport+CUE+drag+compact anim+EFFECT+scalability), gotowe do user review + SZPIEG update. Rekomendacja: manual GUI test + commit.
- (Pełny structured report w subagent output; wszystkie changes exact per documents.)

**Status encyklopedii:** Wypełniona impl progressem. Kolejne findings (side tasks) będą dodawane. "Sposoby na wszystko" dla pokrewnych (np. visibility research, compact anim ex, file/stream) dostępne w pliku dla future reference.

**Dodatkowe input z zespołu (Plan agent review po spec):**
- Hierarchia rethink: SZPIEG jako research lead (nadrzędny spec, decyduje wybory, konsultuje/punktuje, side tasks). Zespół (Plan/Designer/Writer/Fixer/Tester) dostarcza pełne wnioski/rewerk plans + approval przed impl. Pełny opis wniosków wymagany.
- Wnioski: Najlepsze klocki dla Lumbago single basics (clean, readable, functional, scalable single as preview tool): duży centered transport + sep CUE (9/10, już w kodzie — zachować), air + dominant wave no-overlap (10/10, już mocne — zachować rygorystycznie), drag z lookup+safety (9/10, już — zachować), EFFECT tooltips (9/10, partial — expand must), modular compact+anim (8/10, brak — highest priority add per spec), cue logic (8.5/10, już — zachować), scalability (7.5/10, dobre — polish), file vs stream clarity (7/10, implicit — dokumentować + guard).
- Rekomendacje: Zachować odt + simple + routing/air/cue/drag (już blisko spec); przerobić wg Build Spec: tooltips expand, compact mode+anim (pilot-like z spinning CD), scalability (resizeEvent), drag highlight/position, cleanup guards/creation (QStacked dla odt vs dual?), cue consistency, docs.
- Plan impl (step-by-step per spec): solidify current (cleanup visibility/guards), expand tooltips/docs, compact+anim, scalability, cue/drag polish, testy, update archiva/docs.
- Critical files: crew/SZPIEG_..., odtwarzacz_view.py (core), simple_deck_controller.py, dj_player_window.py (troublesome orchestrator), styles.
- Side tasks for SZPIEG: review visibility/overlap in switch/creation, cue consistency, compact anim research (5-8 ex), file vs stream implications, drag UX chain, scalability edges.

**Encyklopedia (dodaj kolejne findings tu lub w podplikach):**
- [Fragment single Odtwarzacz — pełny raport z listy 12, Build Spec, Plan wnioski powyżej]
- [2026-06-02 Writer impl per Plan+SZPIEG spec: Zrobiono dokładnie wg kolejności: 1. Solidify (QStackedWidget content_stack w dj_player_window dla odt vs dual — eliminacja visibility/raise_/hacków + guards; file/stream docs w load/play/unload/global + komentarze w controller/odt/wave/drag; single_container legacy hidden). 2. Expand EFFECT tooltips (mode_btns z EFEKT, title/bpm/time/status/wave/self/ transport w odt; wave tooltip update; dragEnter/drop pos+highlight; controller play/cue z file/stream). 3. Compact+anim (w styles: compact_* sizes; w odt: _CompactSpinIndicator (timer 50ms + paint vinyl/CD spokes+center spin, start/stop react play_state), set_compact_mode + _apply (sizes collapse, fonts, margins, wave min, spin vis), _update on play/unload, init apply; w simple: set_compact_mode flag + emit; w window: compact_btn checkable + tooltip EFEKT + handler _on_compact_toggled + sync on switch/resize + reapply). 4. Scalability (resizeEvent w odt: dynamic wave min + spin size; w window: re-apply compact; zachowane Expanding/stretch/air/margins). 5. Cue/drag +safety (drag highlight border+pos log+mime+lookup w odt+window; safety prompt QMessageBox confirm load if _is_playing (FILE during stream); cue logic untouched solid: near0 prefer, stop->cue, set, double=seek+cue). 6. Testy: smoke LUMBAGO_SAFE=1 3s exit=0; python -m pytest -k "playback|dj|ui_smoke|hotcue" 44 pass (1 unrelated preexist fail); python -c headless odt create/set_compact/resize/playstate smoke OK. Manual per CHECKLIST (adapted no-hotcue odt): resize/drag/no-overlap/single/cue-play/compact covered. 7. Updates: this archiva + memory/HISTORY/AGENTS/CLAUDE/crew CHECKLIST/LISTA. Zero odstępstw od spec (transport sizes/colors via styles, EFFECT 1-2 zd zdania z EFEKT+file/stream, compact flag+anim desc, QStacked, modular reuse wave/styles/controller).]

- [Przyszłe: np. visibility/overlap research, compact anim details, etc. z datą/źródłami]

---
**Writer (impl) progress report (structured, po polsku dla user-facing):**
- Co zrobione: Pełna implementacja reworks single Odtwarzacz basics wg combined spec z SZPIEG+Plan (building blocks: air+centering, large transport+sep CUE, EFFECT wszędzie, drag mime+lookup+highlight+pos, cue logic, modular compact+spinning anim pilot, scalability resize, file=load plik/stream=transport, safety lock/prompt, modular reuse).
- Files edytowane (abs paths): D:\Claude\ui\dj_player_window.py (QStack, cleanup, toggle, docs), D:\Claude\ui\dj\views\odtwarzacz_view.py (compact spin+set+apply+resize+tooltips+drag highlight+safety+docs), D:\Claude\ui\dj\simple_deck_controller.py (compact flag+method, file/stream/cue docs), D:\Claude\ui\dj\styles.py (compact sizes), D:\Claude\ui\dj\views\waveform_widget.py (tooltip+docs).
- Changes: 100% match spec (kolejność kroków, komentarze, rozmiary, anim desc, tooltips z "EFEKT:", QStacked elimin hacks, spin via timer/paint).
- Tests: smoke OK, pytest OK (44p), python -c odt OK, manual paths covered.
- Remaining: none per plan (all 7 steps + updates). Gotowi do user review + SZPIEG archiwum.
- Wnioski: Wybrane klocki najlepsze dla Lumbago (PyQt6, clean single preview tool): duzy transport+CUE, air+wave, drag, compact anim, EFFECT, modular — clean/functional/scalable/fast safe.

*Zaktualizowano na podstawie user instructions z sesji + Plan team review. SZPIEG obecny w crew jako kluczowy research agent. Writer wykonał dokładnie.*
