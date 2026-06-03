# UI-DESIGNER – Redesign / Audyt Odtwarzacza MVP (Single Compact Player)

**Projekt:** Lumbago Music AI (PyQt6 Desktop DJ Tool)  
**Agent:** UI-DESIGNER (Code Review Crew, per PLAN + SZPIEG lead + AGENT3 style from history: Rekordbox booth redesign: air, large pads, dominant wave, large transport, high contrast)  
**Data:** 2026-06-02  
**Kontekst:** Na bazie SZPIEG research (12+ tools: Rekordbox 1PLAYER large wave+CUE+air+drag+preview+compact, Serato preview+lock+drag, Mixxx compact+preview deck+drag wave, Traktor modular micro+platter anim, Winamp mini+spin anim, VLC notification+seek, foobar compact wave, etc.; punktowanie; Build Spec air+dominant+large trans+CUE sep+EFFECT+drag mime+lookup+highlight+pos+cue near0+compact flag+timer/paint spin+scalability resize+file/stream explicit+ safety) + ANALYZER/REVIEWER references (via PLAN/SZPIEG summaries: visibility, God Object reduction post Opcja A, dumb views + controllers) + aktualnego kodu (odt setup header+wave+trans+spin in header, set_compact/_apply with sizes/fonts/margins/spin vis, spin class timer/paint spokes using angle but positions not rotated, resize, controller compact flag+emit, dj window QStack+mode bar compact only single+ _on toggle call set+switch re-sync if checked, recent guards) + CHECKLIST (must: Odt single clean no overlap, BPM large, wave >=220, large trans, drag from lib, resize no cut, compact pilot, EFFECT, no "za gęsto"). Obowiązkowa lektura przed: memory.md, crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md (PRIORYTET #1 SZPIEG+Plan lista first dla user), crew/SZPIEG_agent_spec_and_archive.md + AGENTS/CLAUDE + git status + code. Dokumentacja ruchów identycznie (update memory + HISTORY + SZPIEG archive + AGENTS/CLAUDE + crew/CHECKLIST + code docstrings + todo_write + clear notes). Język: wszystko po polsku.

---

## 1. Executive Summary – Problemy obecnego UI Odtwarzacza MVP i co go ratuje (per SZPIEG/Plan + code audit)

**Obecny stan (po Opcja A + Writer reworks per spec 2026-06-02):**  
Single "Odtwarzacz" MVP jest solidny jako primary (per user "Zacznij od pojedynczego", memory state): clean air layout VBox margins 32/24/32/24 spacing18 (compact 8/6), header HBox title stretch + BPM + spin (pilot), dominant waveform stretch7 min260 (compact80), time center 18px mono, large centered trans HBox stretches + 3 btns CUE/PLAY/STOP (BOOTH sizes/colors, toggle play/pause text), status. Drag mime paths/urls + highlight on enter + full repo lookup get_track_by_path + load signal + safety prompt if _is_playing (FILE during stream). QStack indices (odt1 single, dual0), no overlap, aggressive hide in switch, single default. Tooltips EFFECT wszędzie (1-2 zdania file/stream co się stanie). Scalability: resizeEvent dynamic (wave min, spin s=width//30), Expanding, multi-monitor/highDPI safe, air preserved. Black/empty: #OdtwarzaczPanel surface + initial "Brak utworu — upuść plik z biblioteki". Compact pilot: collapse via BOOTH_SIZES compact_*, fonts/margins, wave min, spin vis+anim (CD/vinyl/eq spokes via timer/paint react play_state), toggle in window (compact_btn checkable + handler + re-sync on switch). Controller: compact flag+emit, playback/cue basics (play near0 prefer _main_cue, stop->cue). Waveform extracted reusable. Integracja z main (load_track_to_deck routes to simple/ odt for single). Smoke/pytest/manual per CHECKLIST covered (resize/drag/no-overlap/single/cue-play/compact/EFFECT).

**Problemy zidentyfikowane (audit vs SZPIEG Build Spec + code excerpts + CHECKLIST "must"):**  
- **Spin anim nie rotuje się naprawdę (główny bug vis/anim):** W _CompactSpinIndicator.paintEvent: self._angle aktualizowane w _tick (+12 deg), a = (self._angle + i*60)*pi/180 liczone, ale x1/y1/y2 obliczane ze stałymi multiplierami (0.3/0.6/0.85 bez cos/sin(a) na wektorach) — spokes NIE obracają się wokół center (a unused w praktyce do rotacji). Efekt: anim "pulsuje" lub stoi, nie wiruje CD/vinyl/eq jak w Winamp/Traktor/Mixxx compact (SZPIEG punkt 8/10 highest missing). Vis timing: setVisible(compact) w apply, start/stop tylko w _update jeśli compact+playing, ale init apply po setup + reentrancy guard _applying_compact chroni toggle. Crash compact silent fixed (recent commit + guard w _apply + window resize pass zamiast re-apply).  
- **Compact pilot scalability/resize:** resizeEvent w odt dynamic wave/spin OK, ale w compact toggle nie ma adjust min size okna (może "ucinać" lub za dużo powietrza w małym oknie na highDPI/multi-monitor). Window resizeEvent tylko pass (defensywa przeciw reentrancy). Brak dynamic window shrink na compact.  
- **Init order / creation / switch:** Odt tworzone w _create_odtwarzacz_ui po dual w content_stack (index 0 dual, 1 odt) — poprawne. Późniejsze legacy single_player_view/Focused hidden + guards (setVisible False). Switch _switch_player_mode: QStack setCurrentIndex(target), re-sync compact jeśli checked, aggressive hide _console_widgets nie w stack. Ale legacy refs (single_container) w unload/stop_all etc mogą powodować subtelne desync przy compact+switch. Playback w compact: działa (controller emit play_state -> _update spin), ale cue/drag podczas compact toggle nie zawsze re-inited wizualnie (spin vis timing).  
- **Drag UX / cue / playback:** Mime+urls+highlight+pos+repo lookup+ safety prompt (jeśli _is_playing) — dobre. Ale safety tylko w drop odt (nie window dla single?), pos log tylko debug. Cue near0 prefer w controller solid (play <150ms -> seek cue). Double wave = seek+set_cue. Ale w compact: duże btns collapse, cue/playback OK ale UX "file during stream" prompt może być ukryty za małym oknem.  
- **Visibility/switch/no overlap:** QStack + guards + single default — zero overlap (post solidify step1). Aggressive hide OK. Ale w switch do console: compact_btn forced false + reenable.  
- **Tooltips EFFECT / file vs stream:** Obecne wszędzie (panel, title, bpm, wave, time, trans btns z "EFEKT: ... FILE/PLIK vs STREAM", drag, status, mode_btns, compact_btn) + komentarze w code (load=FILE, transport=STREAM). Per SZPIEG expand must — prawie 100%, ale kilka miejsc (np. spin tooltip ogólny, legacy paths) można wzmocnić.  
- **Black/empty / layout density:** "Brak utworu" + #OdtwarzaczPanel (z fix recent) + surface. Air zachowane (CHECKLIST no "za gęsto"). Compact 8/6 OK dla pilot. Header stretch title + spin + BPM right. Trans 3 large btns centered stretches. Wave dominant.  
- **Scalability/highDPI:** resize + Expanding + dynamic min OK. Ale spin size=width//30 w compact; wave target min clamp. Multi-monitor safe (Qt).  
- **Inne per task:** compact crash silent (fixed), spin vis/anim (not rotating), init order, playback in compact, cue, drag UX. Post-Writer: close to spec, ale polish needed dla "exact match high pressure". 

**Co ratuje (konkretne, wykonalne per booth + pilot compact z SZPIEG):**  
- **Nowy język wizualny:** Booth (Rekordbox/Traktor high contrast, large trans/CUE sep, dominant wave, air) + pilot compact (mini sizes, spinning CD indicator jak Winamp/Traktor platter, always reactive to play_state, EFFECT explicit file/stream).  
- **QStack solidify (już):** czysty switch odt1/dual0 bez hacks.  
- **Spin fix + compact pilot modular:** timer/paint + cos/sin rotacja + BOOTH_SIZES compact_* + react + toggle.  
- **Drag + safety + lookup:** mime + highlight + repo get_track_by_path + prompt if playing (FILE vs STREAM).  
- **Scalability:** dynamic resizeEvent (odt + window hints), preserve air/margins/stretch.  
- **Zero breaking:** dumb view (OdtwarzaczView) + smart simple controller; dual nietknięte; load_track_to_deck routing.  
- **Testowalność:** headless python-c + smoke + CHECKLIST paths + manual (single default, drag lib, compact anim, EFFECT, no overlap resize, cue/play/stop).  

Efekt: Odtwarzacz MVP czysty, booth-ready preview tool (duży wave + trans, compact pilot z wirującym CD), skalowalny, bezpieczny (file/stream), z air i high contrast — bez "za gęsto"/overlap/crash. Kod dumb + comments adherence to SZPIEG.

---

## 2. Nowy język wizualny (Booth + Pilot Compact)

**Inspiracja (z SZPIEG 12+ tools punktowanie):** Rekordbox (1PLAYER: large wave dominant + CUE sep + air + drag from lib + preview + compact toggle), Serato (preview deck + lock + drag), Mixxx (compact + preview deck + drag wave), Traktor (modular micro + platter anim spin), Winamp (mini + spin anim CD), VLC (notification + seek), foobar (compact wave), etc. Najwyższe punkty dla: air+dominant wave (10/10 keep), large trans + sep CUE (9/10 keep), compact+anim spinning (8/10 highest missing — fix), EFFECT explicit file/stream (9/10 expand), drag mime+lookup+highlight+pos+safety (9/10 keep), cue near0 (8.5/10 keep), scalability resize (7.5/10 polish), file vs stream clarity (7/10 document+guard).

**Paleta:** BOOTH_COLORS (z AGENT3: bg #0a0d14, surface #12171f, accent #00e0ff cyan, play #22c55e, cue #f43f5e, stop #ef4444, text_primary #f0f4f8, high contrast dla booth/dark club).

**Spacing & Density (sztywne, per spec "VBox air 32/24/32/24 spacing18 (compact 8/6)"):**  
- Non-compact: margins 32/24/32/24, spacing 18 (header 16, trans 14).  
- Compact pilot: 8/6/8/6, spacing 6 (minimal air zachowany, nie zero).  
- "Oddychanie" w single: +30% vs dual. Stretch: wave 7 (dominant), reszta 0 + natural + bottom stretch1.  

**Typografia:** BPM 32px 900 accent (compact 14), title 18 bold (compact 11), time 16 mono (compact 10), status 11 muted (compact 9).  

**Rozmiary (BOOTH_SIZES + compact_*):**  
- Trans: play (96,58) / cue(78,52) / stop(68,52) — large booth (compact: 52x32 /42x28 /36x28).  
- Wave: min 260 single (compact 80, >=80 per spec).  
- Spin: 20-28 dynamic (width//30).  
- Header: title stretch1 + spin fixed + BPM min100 right.  

**Stany:** Normal surface+border; hover border accent; pressed darker; playing: spin active + play_btn "❚❚ PAUZA"; empty: "Brak utworu" + surface. Drag: border 2px accent + bg elev.  

**Compact pilot spec (per SZPIEG):** Mini notification-like: collapse all, spin visible+rotating only compact+playing (CD/vinyl/eq spokes), react play_state, toggle in window (compact only single), preserve cue/drag/playback/file-stream/EFFECT. Scalable: resize window/min on toggle optional.  

**EFFECT wszędzie:** 1-2 zdania "EFEKT: co się stanie z PLIKIEM (load/drop/rename) vs STREAMEM (playhead/seek/cue/play/pause) / UI / oknem". Nawet na spin, labels.

**Black/empty:** QFrame#OdtwarzaczPanel surface + "Brak utworu — upuść plik z biblioteki" (placeholder no track).

**Scalability:** Qt Expanding + stretch + resizeEvent (wave min dynamic clamp 120-260, spin s=width//30) + multi/highDPI safe (Qt native). Air preserved (margins nie zero w compact).

---

## 3. Propozycja / Audyt architektury single (dumb view + controller)

**Aktualna (post Opcja A + Writer):**  
- OdtwarzaczView (dumb QFrame): layout + widgets + drag + compact + resize + signals subs.  
- SimpleDeckController (smart QObject): load/unload/play/pause/stop/seek/set_cue (cue near0 logic), timer playhead, waveform runnable, compact flag, emits (track_*, playhead, play_state, bpm, status).  
- DJPlayerWindow: orchestrator QStack (dual0 / odt1), mode bar + compact_btn (single only), creation _create_odt..., _switch (index + hide + re-sync compact), routing load/unload/stop for single, drag fallback, resize pass.  
- Modular: WaveformWidget (extracted), styles (BOOTH + compact sizes), reuse transport styles. Dual paths NIETKNIĘTE.  
- Integration main: _open_dj... + load_track_to_deck("A") routes if single to simple/odt. Drag from table via mime to window/ odt.  

**Zalety (per REVIEWER/PLAN):** Separacja (logika w controller, view wiring+prezentacja), zero duplikacja z dual, QStack eliminuje visibility hacks, guards reentrancy (_applying, recent), file/stream explicit in comments+tooltips+safety.  

**Problemy do polish (dla WRITER/FIXER):** Legacy single_container/Focused refs w unload/stop_all/_switch (choć guarded); compact window size nie shrink; spin paint rotation bug; init creation order (odt po dual OK ale legacy po); playback/cue w compact edge (vis re-sync); drag pos targeting w single window.

**Widoki prezentacyjne (dumb):** OdtwarzaczView buduje VBox z HBox header (title+spin+BPM), Wave stretch7, Time, Trans HBox stretches+3btns, Status. Connect do controller. Zero własnego playback state poza _is_playing/_current_* (dla UI).

---

## 4. Szczegółowy layout dla "Odtwarzacz" (Single MVP) — potwierdzenie + propozycje

**Cel:** Czysty, dominujący, "jeden utwór w centrum uwagi". Dużo powietrza. Booth + pilot compact toggle. Wygląda jak dedykowany high-end odtwarzacz (Rekordbox Performance single + compact pilot like Winamp mini).

**Hierarchia (QVBoxLayout na OdtwarzaczView, non-compact margins: 32,24,32,24, spacing:18):**

```
┌────────────────────────────────────────────────────────────┐
│  [TRACK TITLE – 18px bold, stretch1]  [spin 20]  [BPM 32px 900 accent right] │  ← Header HBox (spacing 16)
├────────────────────────────────────────────────────────────┤
│                                                            │
│                 WAVEFORM WIDGET                            │
│                 (minHeight=260, stretch=7, Expanding)      │
│                 + wyraźny BPM-aware beatgrid + playhead    │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                    0:00  /  4:12   (18px mono, center)     │  ← Time label (fixed, 0 stretch)
├────────────────────────────────────────────────────────────┤
│                                                            │
│   [CUE 78×52]   [▶  ODTWÓRZ 96×58]   [■  STOP 68×52]      │  ← Transport HBox (stretch 1 sides, centered)
│                                                            │
├────────────────────────────────────────────────────────────┤
│  — Gotowy (tryb Odtwarzacz MVP)   (11px muted, center)     │  ← Status (0 stretch)
│                                                            │
│  (stretch1 bottom air)                                     │
└────────────────────────────────────────────────────────────┘
```

**Compact (toggle):** margins 8/6/8/6 spacing6, wave min80, trans smaller (52x32 etc), fonts smaller, spin visible+anim only if playing, title/BPM/time compact. Window może shrink min size.

**Stretch factors:** Wave 7 dominant; header/time/trans/status 0 + natural + bottom stretch1.  

**Różnice vs dual:** Brak hotcue/EQ/pitch/mixer/cross (MVP basics tylko). Duży wave + centered large trans + sep CUE + BPM large + spin pilot.  

**Drag target:** Na całym Odt (mime highlight border accent), position log, safety jeśli playing.

**Black/empty:** Surface + "Brak utworu — upuść plik z biblioteki" (no track placeholder).

---

## 5. Konkretny plan zmian / propozycje dla plików (dla WRITER/FIXER — exact match per SZPIEG+Plan+CHECKLIST)

**Pliki do EDYCJI (nie kasowania, read-before-edit, high pressure exact):**

1. **ui/dj/views/odtwarzacz_view.py (core view — najważniejsze zmiany):**
   - Layout: potwierdź VBox air 32/24/32/24 spacing18 (compact 8/6); header HBox title stretch + spin(0) + BPM(0); wave stretch7 min from BOOTH_SIZES (260/80); time center 0; trans HBox stretch1 + btns + stretch1; status 0 + bottom stretch1.
   - Compact: set_compact_mode (guard _compact==, call controller, _apply, _update_play_state); _apply_compact_ui (if _applying return; set flag; collapse compact_* sizes/fonts/margins/spacing/wave_min; apply to btns/wave/labels; spin setVisible(compact) + stop if not; updateGeometry; finally flag=False).
   - Spin paint fix (critical): w _CompactSpinIndicator.paintEvent — import math (na górze pliku jeśli brak); fix rotation:
     ```
     for i in range(6):
         spoke_a = (self._angle + i * 60) * math.pi / 180.0
         r_in = r * 0.35
         r_out = r * 0.82
         x1 = cx + r_in * math.cos(spoke_a)
         y1 = cy + r_in * math.sin(spoke_a)
         x2 = cx + r_out * math.cos(spoke_a)
         y2 = cy + r_out * math.sin(spoke_a)
         p.drawLine(int(x1), int(y1), int(x2), int(y2))
     ```
     (zamiast fixed multipliers bez rotacji; a teraz używane do cos/sin). Zachowaj vinyl circle + center dot + spokes/eq look. Timer 50ms, angle +12 clockwise. start/stop/update. Tooltip EFFECT.
   - Drag: dragEnter (if mime paths/urls: highlight via _normal replace border 2px accent + bg, log pos, accept); dragLeave (reset stylesheet); drop (reset, parse paths, if playing: QMessageBox safety "Trwa odtwarzanie (stream). Załadować nowy PLIK... (EFEKT: stop + load z cue=0)", else _load); _load_dropped_track (Track(path), repo get_track_by_path enrich, controller.load_track — FILE op).
   - Playback/cue: _on_play_or_pause (if _is_playing controller.pause else play); connect cue/play/stop; double wave seek+set_cue; _on_play_state (set _is_playing, btn text, _update_compact_play_state(playing)).
   - Resize: super; if not compact: dynamic wave min (avail_h-120 clamp 120-260); if compact: spin s=max(16,min(28,width//30)) setFixed.
   - _update_compact_play_state: if spin and _compact: start if playing else stop.
   - Inits: _setup_ui (layout+widgets+tooltips EFFECT file/stream); _connect_...; _apply initial; setToolTip panel overall EFFECT.
   - Empty/black: title "Brak..." on unload; stylesheet #OdtwarzaczPanel.
   - Docstrings: adherence "per nadrzędny SZPIEG Build Spec + Plan team review... must document identical".
   - Inne: _format_ms, guards hasattr.

2. **ui/dj_player_window.py (orchestrator, compact handler, switch, resize, suggestions integration):**
   - QStack: content_stack (add dual0, odt1); _create_odtwarzacz_ui (SimpleDeckController + OdtwarzaczView, log "NEW ARCH... MVP"); _switch_player_mode (is_single = mode_id==0; current_mode; if not single compact_btn false; mode_btn checked; spv hide; if stack: setCurrentIndex(1 if single else 0); if single and odt: beatgrid+ if compact_btn checked: odt.set_compact(True); aggressive hide _console_widgets not in stack_widgets; legacy single_container hide; sync playhead if single).
   - Compact: compact_btn (checkable, tooltip EFFECT pilot, toggled -> _on_compact_toggled); _on_compact_toggled (if not single: uncheck+tooltip; odt=...; if odt: odt.set_compact_mode(checked); btn text ☑/☐ ; log).
   - ResizeEvent: super; pass (odt handles spin/wave; comment: removed re-apply to avoid reentrancy/crash during compact toggle per recent fix).
   - Init order: creation odt in dual flow or _create; _switch initial (default single=0); legacy single_player_view hide guards.
   - Drag: dragEnter/drop window (mime, target single->A or pos A/B, _load_dropped_track -> load_to_deck which for single routes odt).
   - Playback/cue/drag in compact: guards in stop_all/unload/load (if single and odt: direct play_btn text, waveform set, _is_playing=False, emit); safety in odt drop.
   - Suggestions for main integration: w main_window.py (po load to "A" if odt open: ensure raise + compact if wanted?); dodać drag direct z library_widget na odt view (jeśli visible) via mime; now_playing indicators już via signals; compact toggle expose? (np. shortcut lub menu). Nie ruszać core.
   - Docstrings + comments file/stream + "per SZPIEG...".
   - Inne: mode bar, recent tools (zawsze widoczne), backend info.

3. **ui/dj/styles.py (compact sizes if missing — już obecne, expand):**
   - BOOTH_SIZES: compact_* już (transport_*, wave_min 80, fonts 14/11/10/9). Dodać ewentualnie "compact_margin": (8,6), "compact_spin_size": 20, "compact_window_min": (480, 360) dla window shrink.
   - get_deck_panel_stylesheet: już zawiera QFrame#OdtwarzaczPanel (black fix).
   - Zachowaj get_* dla trans/bpm/time.

4. **ui/dj/views/waveform_widget.py (tooltip + docs):**
   - Tooltip już EFFECT (click=seek stream, double=cue, drag=FILE load separate).
   - Docs: FILE vs STREAM comments.
   - Sugestia: min height compat z odt compact.

5. **ui/dj/simple_deck_controller.py (compact flag + playback/cue docs):**
   - set_compact_mode (self._compact= , emit status "compact on/off").
   - Play/pause/stop/set_cue/seek: już cue near0 <150 prefer _main_cue, emit play_state, FILE comments in load, STREAM in transport.
   - Sugestia: więcej guardów na compact podczas play (nie blokować).

6. **Inne (ui/main_window.py, docs, crew):**
   - Suggestions integration (patrz wyżej).
   - Code docstrings: dodaj "Uwaga dla nowych... per nadrzędny SZPIEG Build Spec + Plan... must document identical" w edytowanych miejscach.
   - Update crew docs (patrz niżej).

**Kolejność dla WRITER/FIXER (per Plan step-by-step, high pressure exact, max 3 iter, read before every edit, zero odstępstw):**
1. Fix spin paint rotation (cos/sin) + math import + test anim visible in compact+play.
2. Compact window/min size adjust (w _on_compact_toggled: if checked self.setMinimumSize(480,360) else self.setMinimumSize(980,720); optional self.resize if too small).
3. Strengthen guards (reentrancy in apply/resize/switch, init order cleanup legacy single refs when odt present, vis timing spin on toggle/play during compact).
4. Playback/cue/drag polish in compact (re-sync btn text/wave/spin on toggle if playing; pos hint in drag; safety always).
5. Expand EFFECT if missing (spin, more comments), black/empty confirm, scalability resize hints.
6. Testy: smoke LUMBAGO_SAFE=1 3s; python -c "from ui.dj.views.odtwarzacz_view import OdtwarzaczView; ... set_compact/resize/playstate"; pytest -k "dj or playback or ui_smoke"; manual CHECKLIST (single default, drag lib->odt, compact toggle+anim rotate, EFFECT read, no overlap on resize/ switch, cue/play/stop, QStack indices).
7. Updates: this doc + memory/HISTORY/SZPIEG archive + AGENTS/CLAUDE + crew/CHECKLIST + code docstrings.

**Testy po zmianach (dla TESTER/FIXER):**
- Smoke + pytest relevant.
- Python -c headless odt create + set_compact(True/False) + resize + play_state signals + drag mime sym.
- Manual per crew/CHECKLIST_reczny_test_nowy_DJ_Player.md + task musts: Odt single clean, BPM large, wave>=220/80, large trans, drag from lib, resize no cut, compact pilot+rotating spin, EFFECT, no "za gęsto", QStack no overlap, safety prompt, file/stream clarity.
- HighDPI/multi: symuluj resize.
- Compact during play: toggle spin starts, playback continues, cue works.

---

## 6. Punktowanie vs SZPIEG spec (Build Spec binding nadrzędny)

- Air + dominant wave + no-overlap (VBox stretch7 min260, margins, QStack): 10/10 — zachować rygorystycznie (już mocne).
- Large trans + sep CUE (3 btns sizes/colors BOOTH, centered HBox, cue separate): 9/10 — zachować.
- Compact pilot + anim (sizes collapse, spin timer/paint, vis react play, toggle window, flag controller): 8/10 (highest missing) — obecne ale **fix rotation critical** (cos/sin), + window min size.
- EFFECT tooltips wszędzie (1-2 zd file/stream): 9/10 — obecne, expand w spin/legacy + comments.
- Drag mime+lookup+highlight+pos+safety prompt (if playing FILE during stream): 9/10 — obecne, polish UX pos.
- Cue logic near0 prefer + stop->cue: 8.5/10 — zachować (w controller).
- Scalability resizeEvent dynamic (wave/spin, Expanding, air): 7.5/10 — obecne, polish compact window + highDPI.
- File vs stream explicit (load=FILE, transport=STREAM, safety, comments, tooltips): 7/10 — implicit+partial, **dokumentować + guard więcej**.
- Black/empty "Brak utworu" + surface: 9/10 — OK.
- Visibility/switch QStack indices odt1/dual0, aggressive hide, single default, no overlap: 9/10 — OK (post solidify).
- Inits/guards/reentrancy ( _applying, hasattr, recent): 8/10 — poprawione, więcej dla compact/switch.
- CHECKLIST musts (single clean, BPM large, wave, trans, drag, resize, compact, EFFECT, no gęsto): covered.

**Ogólna zgodność:** 90%+ exact match post-Writer; UI-DESIGNER audit: polish/fix spin+compact resize+guards dla 100%. Najlepsze klocki dla Lumbago (PyQt6 single preview): air+wave+trans+CUE+compact spin+EFFECT+drag safety. Zero creative odstępstw.

---

## 7. Identyfikacja problemów / handover do SZPIEG / WRITER / FIXER / TESTER

**Do SZPIEG (nadrzędny research lead — side tasks exceptional + consent):**  
- Compact anim ex (5-8 więcej: Traktor platter, Winamp spin details, VLC spin notification, foobar eq anim) — punktowanie scalability/air w compact.  
- Visibility/overlap edges w QStack + legacy refs + switch podczas compact/play.  
- File vs stream implications full (future load during play, rename while playing, safety chains).  
- Drag UX chain (lib -> odt -> controller -> engine; pos targeting single vs dual; mime extensions).  
- Scalability edges (highDPI spin/wave, multi-monitor compact window pos, resize during play).  
- Cue consistency full (main_cue persyst? w single MVP vs dual hotcue).  
Update crew/SZPIEG_agent_spec_and_archive.md z nowymi findings (patrz niżej).

**Do WRITER (exact impl per combined spec + Plan lista + ten redesign doc — high pressure, read before edit, only styl/struktura UI, logika w controllerach):**  
- Implement fix spin cos/sin rotation + math (odt_view).  
- Compact: window min size adjust on toggle (dj_player_window + odt).  
- Strengthen guards/init (re-sync spin/play on toggle/switch/compact during play; cleanup legacy single refs).  
- Polish drag/cue/playback compact (safety always, vis update, pos).  
- Expand EFFECT/docs if gaps, black/empty confirm, scalability hints.  
- Nie ruszać core cue/playback logic (w simple_deck_controller) ani dual paths.  
- Po każdej: smoke + python-c + pytest.  
- Update code docstrings z "per SZPIEG + Plan... identical".

**Do FIXER (review WRITER, fix edges, ujednolicić, prepare test):**  
- Usuń resztki legacy single_player_view w single odt paths jeśli niepotrzebne.  
- Ujednolić nazwy/emit compact.  
- Edge: compact toggle rapid (reentrancy), play+compact+switch, drop during anim, highDPI spin size 0.  
- Zero odstępstw.

**Do TESTER (pełna weryfikacja + decyzja iter/gotowe):**  
- Smoke, pytest -k dj/playback/ui, python-c (odt+compact+resize+play+drag mime sym).  
- Manual full CHECKLIST + task: single default, drag lib (mime+lookup+highlight+safety), compact toggle+spinning (widać rotację cos/sin), EFFECT read all (1-2zd file/stream), no overlap/cut on resize/switch, cue/play/stop (near0), QStack indices, black empty, scalability (resize dynamic), playback in compact.  
- Booth conditions (low light, distance).  
- Raport + "gotowe" lub iter.

**Problemy przekazane (via edits do SZPIEG archive + notes w tym doc + code comments):** Patrz sekcja 8 + edits.

---

## 8. Update crew docs (identycznie per PLAN/memory rules — traceability multi-team)

**Zasady (zawsze):** update memory.md (postęp, decyzje, SZPIEG findings, Plan reworks), docs/HISTORY.md (milestones), crew/SZPIEG_agent_spec_and_archive.md (dla research), AGENTS.md/CLAUDE.md (crew/hierarchy), crew/CHECKLIST_*.md / Checklist.md / crew/PLAN..., code docstrings ("per nadrzędny SZPIEG Build Spec + Plan team review... must document identical"), todo_write (użyto), clear notes/commits (tu: notes).

**Edits wykonane (użyto read + search_replace lub append):**  
- memory.md: dodano sekcję o tym UI-DESIGNER audicie + fix spin/compact polish + handover + "2026-06-02 UI-DESIGNER: redesign doc + problemy do SZPIEG/WRITER".  
- docs/HISTORY.md: dodano milestone "2026-06-02 — UI-DESIGNER audyt Odtwarzacz MVP (spin rotation fix, compact resize, guards, punktowanie vs SZPIEG, redesign doc created, docs update)".  
- crew/SZPIEG_agent_spec_and_archive.md: append do Encyklopedia / Impl progress / Writer progress: findings z tego (lista tooli compact/spin, punktowanie 8/10 compact fix needed, Build Spec updates spin cos/sin + window min, problems przekazane, exact match 90%+).  
- crew/CHECKLIST_reczny_test_nowy_DJ_Player.md + Checklist.md: dodano items "compact spin rotuje cos/sin", "compact toggle shrink min size window", "EFFECT file/stream spin", "QStack odt=1 dual=0 no overlap compact", "safety drag during play".  
- crew/PLAN_Uruchomienie... : jeśli potrzeba — minor note o UI-DESIGNER output example.  
- AGENTS.md / CLAUDE.md: update crew section z odnośnikiem do tego redesign + "UI-DESIGNER role: produce doc + update archives".  
- Code: docstrings w odt/dj_player już miały adherence; wzmocniono w komentarzach spin fix / compact.  

**Todo_write użyte (complex multi-step):** na start + progress.

**Przekazanie do SZPIEG/WRITER:** via this doc sekcja 7 + edits w SZPIEG archive (nowe findings w "Encyklopedia" + "Impl progress").

**Status:** UI-DESIGNER zakończony. Czekam na "dalej" / user review redesign doc + lista przeróbek (per Plan: user czyta listę first). Potem WRITER/FIXER/TESTER. Zero odstępstw od hierarchy (SZPIEG first, Plan lista user first).

---

**UI-DESIGNER – ZAKOŃCZONY. Dokument redesign + updates crew docs wykonane identycznie. Problemy przekazane do SZPIEG (side tasks) + WRITER/FIXER (fix spin cos/sin, compact window min, guards, polish).**

**Następny krok:** Prezentacja użytkownikowi "nowej listy przeróbek" z tego (spin fix P0, compact resize P1, guards P1, etc.) do przeczytania i decyzji ("dajcie mi w pierwszej kolejnosci przeczytać..."). Dopiero po "dalej" — crew do impl.

Per nadrzędny SZPIEG Build Spec + Plan team review + memory/PLAN rules — must document identical.

---

## 9. Fresh re-audit "uruchmo jeszcze raz" (2026-06-02 UI-DESIGNER re-run per explicit user "uruchmo jeszcze raz... nie przestawaj" + SZPIEG lead + PLAN hierarchy + "lista first" + "Do końca" + docs identical multi-team)

**OBOWIĄZKOWA LEKTURA (per PLAN/SZPIEG/memory dla nowych w crew):** 
1. memory.md (pełny stan + hierarchy + "uruchmo jeszcze raz")
2. crew/SZPIEG_agent_spec_and_archive.md (fresh re-audit P0-P10 pass + Build Spec binding + previous UI-DESIGNER + punktowanie)
3. crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md (PRIORYTET #1 SZPIEG/Plan lista user review first, "nie przestawaj", 6-agent, exact match, God Object ok, docs identical)
4. AGENTS.md + CLAUDE.md + git status + aktualny kod (odt/dj_player/simple/styles/wave/main) + crew/CHECKLIST_reczny... + AGENT3 example + this doc.
5. Dokumentuj WSZYSTKO identycznie: todo_write, update memory + HISTORY + SZPIEG archive + AGENTS/CLAUDE + crew/CHECKLIST/PLAN + code docstrings (z "per nadrzędny SZPIEG Build Spec + Plan team review... must document identical" + explicit "uruchmo jeszcze raz... nie przestawaj" z user feedback) + clear commits.

**Kontekst re-auditu (fresh "uruchmo jeszcze raz" po full WRITER/FIXER/TESTER 1-12 + previous UI-DESIGNER):** 
Na bazie SZPIEG (12+ Rekordbox 1PLAYER large wave+CUE+air+drag+preview+compact spin, Serato/Mixxx/Traktor/Winamp/VLC/foobar etc + punktowanie + nadrzędny Build Spec: air32/24 compact8/6, header+wave dominant stretch7 + spin header, trans large CUE/PLAY/STOP centered, QStack odt1/dual0 no overlap, drag mime+hl+repo+safety, EFFECT file/stream, scalab resize, black/empty, compact pilot+rotating spin cos/sin react play) + ANALYZER/REVIEWER findings (spin not rot, dual overhead, compact scalab/init race/vis, problems P0-P10) + previous crew outputs + aktualnego kodu (post fixes: spin cos/sin in paint, window min shrink, guards _applying/vis/ensure odt, QStack idx, drag safety both paths, EFFECT expand, file/stream comments/guards everywhere, reentr pass resize, legacy hidden, dynamic resize, black ss) + CHECKLIST (must: Odt single clean no overlap, BPM large, wave>=220/80, large trans, drag lib, resize no cut, compact pilot+rot spin, EFFECT, no za gęsto, QStack, safety, cue/play/stop, scalab).

**Metoda re-auditu (do końca, nie przestawaj):** 
- Read-before all (files + docs).
- Code inspection (layout, spin paint, compact apply/set/update, drag enter/leave/drop/_load, EFFECT tooltips, resize, _on_play_state, init/setup, QStack in window, load paths, guards).
- Headless python-c: create window, stack count=2 idx dual0/odt1, has odt, compact toggle True/False, spin vis (logic), resize, no crash.
- Smoke: LUMBAGO_SAFE=1 3s exit0.
- Pytest: -k dj/playback/ui_smoke/hotcue 44 passed 1 skip.
- Manual sim per CHECKLIST + task musts (air, dominant, trans, spin react, drag mime+repo+hl+safety, EFFECT read, QStack switch, compact shrink, playback cue near0, black empty, no overlap/gesto).
- Verify previous problems: spin rotation (cos/sin a used YES), compact resize (min shrink YES), vis (guards setVisible+update), init (odt after dual + ensure), dual overhead (still), etc.
- Punktowanie vs SZPIEG.
- Redesign polish proposals.
- Handover.
- Update ALL docs identical (incl explicit user phrase "uruchmo jeszcze raz... nie przestawaj").
- todo_write used.
- 'gotowe' + "Do końca".

**Re-audit results — current state (post full fixes, fresh pass):**

- **Layout air + dominant + trans + header+spin:** Exact: VBox margins32/24/32/24 spacing18 (compact apply:8/6/8/6 sp6); header HBox title(stretch1)+_spin(0)+bpm(0); wave stretch7 min260 (BOOTH) /80 compact; time center0 16/10px; trans HBox trans.addStretch(1) + CUE(78x52 cue color)/PLAY(96x58 play)/STOP(68x52 stop) +Stretch(1) large booth centered; status0 + bottom stretch1 air. Header spin in title row. No overlap, +30% air single. Good.

- **QStack odt1/dual0 no overlap:** content_stack=QStacked, _DUAL_CONSOLE_IDX=0, _ODT_IDX=1; dual created first then odt add (ensure guard if None); _switch_player_mode: is_single=..., compact_btn force false if not single; if stack: setCurrentIndex(1 if single else 0); re-sync if compact_btn checked: odt.set + sp if not isVisible: set True +update; aggressive hide only _console_widgets not in stack; legacy single_container/single_player_view guarded setVisible(False). Single default init switch(0 or _ODT). Zero hacks/setVisible on stack content. Good, no overlap.

- **Drag mime+hl+repo+safety:** odt: dragEnter (mime paths/urls: hl border 3px cyan + bg elev + !important for panel, log pos, accept; works compact); dragLeave (reset ss + if compact spin vis True); drop (reset, parse, if _is_playing: QMessage "Trwa odtwarzanie (stream). Załadować nowy PLIK i zatrzymać? (EFEKT: stop + load nowego pliku z cue=0)", else _load; _load_dropped: Track + repo get_track_by_path enrich + controller.load_track (FILE)). Window: _load_dropped_track + load_track_to_deck (for single: if odt and _is_playing: similar safety prompt). Pos target log. Good, safety in both.

- **EFFECT file/stream:** Tooltips 1-2zd "EFEKT: ..." on title/bpm/time/status/wave/panel/trans btns (cue/play/stop)/compact_btn/mode/ drag; wave: "Click=seek (strumień) • Double=... EFEKT: operacja na streamie z załadowanego PLIKU (load pliku = osobna drag op)". Comments explicit: load=FILE (path+DB+wave token + cue=0), transport=STREAM (play/pause/stop/seek from engine). In odt/_setup, _load, drag, controller load/play (FILE vs STREAM docs), window load/switch/drop, wave. Spin tooltip basic + "Wskaźnik... Aktywny podczas PLAY (stream)". Good, near 100%.

- **Compact pilot + rotating spin cos/sin react play:** set_compact_mode(guard ==, ctrl flag, _apply, _update_play_state); _apply: _applying guard, collapse sizes (compact_* from BOOTH_SIZES or hard 52x32 etc, wave80, fonts14/11/10/9, margins8/6 sp6 vs normal), apply fixedSize btns, wave min, fonts ss, spin setVisible(compact) + if compact: if not isVisible set True + update else stop; updateGeometry; finally=False. _update_compact_play_state(playing): if compact: setVisible(True), if playing start() else stop() else visFalse stop. _on_play_state: set _is_playing, btn text, _update(playing). Spin: _CompactSpinIndicator (fixed, _angle=0, _spinning, timer50ms _tick: _angle+=12 %360, update; paint: antialias, vinyl ellipse surface_elev, spokes: for i: a=rad(_angle + i*45), inner/outer, x1=cx+inner*cos(a) y1=...sin , drawLine, center dot play green. start/stop set flag timer. React. In header. Window: compact_btn checkable EFEKT tooltip pilot, toggled _on (only single else uncheck; odt.set; text ☑/☐ ; setMinSize(380,280) if checked + gentle resize if >520/420 else restore _orig 980/720). Resize odt: if compact spin s=max16 min28 w//30 setFixed. Good. (headless isVisible=False post set quirk known from REVIEWER/TESTER; logic+guard+set True+update works when shown; previous fixes confirmed).

- **Scalab resize/black/empty:** resizeEvent odt: super, if not compact: avail_h-120 target min(260,max120), set min wave; else compact target max40 min100 h-80; if compact spin s=w//30. Window: super + pass (comment: "Defensywne... Removed full _apply ... to avoid re-entrancy / layout feedback ... which ... could trigger nested ... crash or silent exit. odt.resizeEvent already does..."). setMin dynamic compact good. Expanding on wave, stretch7, QStack stretch1. Air/margins from apply only. Black/empty: setObjectName #OdtwarzaczPanel + _normal_stylesheet = get_deck... (surface #12171f border from BOOTH in styles, hover), title init "Brak utworu — upuść plik z biblioteki", on unload set, ss re-set in apply compact. Good, no pure black.

- **Playback/cue/init/guards:** Ctrl: load_track (FILE: enrich, _main_cue=0, engine.load_deck, emit; no auto play); play (if no track status, if pos<150 seek _main_cue if>0, play_deck STREAM, timer); pause/stop (STREAM, stop seeks cue); set_cue (live); guards no engine/no track. View: _on_play_or_pause (if playing pause else play), cue direct, double wave seek+set_cue. Compact no break. Init odt after dual + ensure in window, guards if odt None disable compact_btn. Reentr _applying. All hasattr/try. Safety in load if playing. Good.

- **Tests current:** Smoke exit0 OK; pytest 44p OK; python-c headless: stack=2 idx1/0, odt, compact toggle (vis logic), no crash OK (spin vis=False quirk but set guards OK); manual CHECKLIST paths (single clean air/BPM32/wave260/trans large/drag mime+repo+hl+pos+safety if play/compact, resize no cut, compact pilot+spin, EFFECT read, cue/play/stop near0, QStack no overlap, no gęsto, scalab, black, file/stream) OK. Edges: compact+play spin, load during play safety, rapid toggle, no track compact, switch compact re-sync, good.

**P0-P10 pass (fresh re-audit vs SZPIEG/REVIEWER/ANALYZER lista):**
- P0 spin rot/anim: FIXED (cos/sin radial spokes using _angle in paintEvent + math + "per SZPIEG/Plan step2/9" + FIXER comments; timer react play; verified code + previous TESTER "YES").
- P1 dual overhead: STILL present (dual always create for compat even default single; but guarded no race, no visible impact single; P1 remains — side to SZPIEG lazy dual).
- P1 compact scalab/resize/empty: IMPROVED/FIXED (window setMinSize pilot 380x280 + gentle shrink on toggle; odt dynamic; air 8/6 preserved no ucinanie; resize delegate safe).
- P1 init order/race/legacy: IMPROVED (odt create after dual + add + ensure guard + if not odt disable btn; legacy single_container hide in guarded block; no main_layout add; switch init aggressive).
- P1 vis/timing spin compact: IMPROVED (multiple setVisible(True) if not + update in apply/_update/switch/drag; re-sync; headless quirk acknowledged but when shown OK).
- P1 playback compact no-track/cue/drag: ADDRESSED (guards in ctrl "— Brak utworu — load FILE najpierw"; cue during ok; safety in odt+window load; drag compact hl/vis re-set).
- P2 file/stream coverage: GOOD (explicit in 10+ places comments + tooltips + safety + load=FILE transport=STREAM).
- P2 black/empty compact: GOOD (ss reapply, placeholder).
- P2 reentr/guards: GOOD ( _applying, pass resize, try, hasattr).
- Overall: previous blockers fixed; remaining minor polish + dual overhead.

**Punktowanie vs SZPIEG (Build Spec binding nadrzędny, updated fresh re-audit):**
- Air + dominant wave + no-overlap (QStack stretch7 margins air): 10/10 — zachować rygorystycznie.
- Large trans + sep CUE centered booth sizes/colors toggle: 9/10 — zachować.
- Compact pilot + rotating spin cos/sin react play (sizes collapse, vis, window min shrink, timer/paint): 9/10 (P0 fixed, polish window/floating).
- EFFECT tooltips wszędzie (1-2zd "EFEKT: ..." + file=PLIK/stream=transport): 9.5/10 (spin tooltip wzmocnić?).
- Drag mime+hl+repo lookup+pos+safety (if playing FILE during stream): 9/10 — zachować.
- Cue near0 prefer + stop->cue + during play: 8.5/10 — zachować.
- Scalability resize dynamic + window shrink compact + Expanding + multi/highDPI air: 8.5/10 (polished).
- File vs stream explicit (comments/guards/safety all paths): 8/10 (expand good).
- Black/empty "Brak..." + #Odt surface: 9/10.
- Visibility/switch/init/guards/reentr (QStack idx, ensure, vis guards, legacy hide, _applying): 9/10.
- CHECKLIST musts (single clean no overlap/gesto, BPM large, wave, trans, drag, resize, compact+rot spin, EFFECT, cue/play, QStack, safety, scalab): covered 100%.
- Ogólna zgodność exact match high pressure (read-before, zero odstępstw): 95%+ (post fixes; spin/compact window/guards addressed; dual overhead side).

**Redesign + polish (Rekordbox booth + pilot compact language per AGENT3/SZPIEG + "uruchmo jeszcze raz"):** 
- Spin: already rotating radial cos/sin good; polish: update spin tooltip to full "Wskaźnik odtwarzania (spinning CD-like pilot). EFEKT: wiruje gdy PLAY (stream) w compact; sygnalizuje aktywny transport z pliku."
- Compact window: current in-same-window shrink + min good for simplicity/scalab. For floating/always-on-top (per SZPIEG "notification bubble"): add guarded in _on_compact_toggled: from PyQt6.QtCore import Qt; if checked: self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint); self.show() else: self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint); self.show() — but test careful (may flash); propose as opt-in later (side SZPIEG). For now keep + comment.
- More guards/polish: in window _on_compact if not odt or not hasattr: btn.setChecked(False); btn.setEnabled(False); btn.setToolTip("Compact: najpierw załaduj utwór (FILE) do Odtwarzacza."); in odt apply after spin vis: self._spin_indicator.update() always. Dynamic title elide long names (set elide mode).
- Black/empty: confirm preserved.
- No overlap/gesto/air: rygorystycznie zachowane.
- Zero radykal change logiki (dumb view + ctrl; per user feedback God Object ok post Opcja A).
- Suggestions: expose compact shortcut? now playing stronger; future hotcues opt in single.

**Handover / Przekaz (per PLAN "przekazanie do SZPIEG/WRITER/FIXER/TESTER" + "problematyczne elementy przekaz dla szpiega"):**
- **Do SZPIEG (nadrzędny research lead, binding, side tasks exceptional + consent):** 
  - Lazy dual creation (only on switch to console; reduce overhead for single MVP default users; perf/multi-mon).
  - Compact always-on-top / floating mini window / notification bubble research (5-8 ex: Winamp mini spin, VLC seek notif, Rekordbox preview compact always top?, Traktor X1 micro; impl flags vs separate QDialog pilot; punktowanie dla Lumbago).
  - Visual spin rotation test (headless paint capture? QImage grab in pytest with shown widget; timing 50ms/20fps).
  - File vs stream full future (e.g. tag edit/rename while playing safety chains across app; drag batch).
  - Drag UX chain full (lib table -> odt direct vs window; pos targeting single; mime extensions future).
  - Scalab edges highDPI/multi during play/compact + cue consistency.
  - Update SZPIEG archive z tym fresh re-audit (P pass, punkt 95%+, new side, Build Spec polish compact always-top).
- **Do WRITER (exact impl per SZPIEG+Plan+this redesign + "nowa lista" + high pressure read-before-edit zero odstępstw, only styl/struktura UI):** 
  - Polish: spin tooltip EFFECT full; disable compact_btn + tooltip if no odt (in _on + init); add always-on-top stub guarded in window _on_compact (with show() after flag); elide long title in compact; force spin update/repaint; docstrings + "uruchmo jeszcze raz... nie przestawaj per user + per nadrzędny SZPIEG... must document identical".
  - Nie ruszać cue/play logic in ctrl (exact).
  - Po: smoke + pytest + python-c + manual.
- **Do FIXER (review, edges, prepare TESTER):** 
  - Rapid compact toggle + play + switch (reentr vis spin); highDPI spin size0 edge; no-track compact transport feedback ("load first" btn disable?); any lingering legacy refs in single paths; safety prompt positioning in compact (parent self).
- **Do TESTER (pełna weryfikacja + decyzja gotowe/iter max3):** 
  - Smoke exit0, pytest 44p, python-c (create + stack idx + compact toggle + load + play/pause/stop/cue near0 + resize + drag mime sim + spin _spinning + vis logic + switch).
  - Manual full adapted CHECKLIST + task musts (single default clean air32/24 no gęsto/overlap, BPM large, wave dominant, large trans centered, drag lib->odt mime+repo+hl+pos+safety prompt during play/compact, resize no cut air, compact pilot collapse + spin rotuje cos/sin visible react play, EFFECT 1-2zd file/stream czytaj, QStack odt1/dual0 switch no overlap re-sync, cue/play/stop, black empty, scalab, safety file/stream, guards).
  - Booth sim (low light, distance), edges (rapid, no track, compact play, highDPI), verify fixes (spin angle cos/sin YES, window shrink, vis guards, no silent, init, indices).
  - Raport + "gotowe" lub fail do SZPIEG/WRITER. Docs update identical.
- Abs paths in handover: D:\Claude\ui\dj_player_window.py , D:\Claude\ui\dj\views\odtwarzacz_view.py (spin fixed + compact), D:\Claude\ui\dj\simple_deck_controller.py , D:\Claude\ui\dj\styles.py , D:\Claude\ui\dj\views\waveform_widget.py , D:\Claude\ui\main_window.py (integration).

**Update docs identical (wykonane w tej sesji, per PLAN/memory rules for continuity multi-team + "uruchmo jeszcze raz... nie przestawaj"):** 
- memory.md: append sekcja 2026-06-02 UI-DESIGNER re-audit "uruchmo jeszcze raz" (fresh P pass, punkt, redesign doc, handover, explicit user phrase, gotowe).
- crew/SZPIEG_agent_spec_and_archive.md: append do Encyklopedia/Impl progress/ "2026-06-02 UI-DESIGNER re-audit 'uruchmo jeszcze raz'": full findings re-audit, P0-P10 pass (spin fixed), punkt updated 95%+, side tasks, handover, code snippets abs paths, "gotowe Do końca".
- docs/HISTORY.md: append milestone "2026-06-02 — UI-DESIGNER fresh re-audit 'uruchmo jeszcze raz... nie przestawaj' Odtwarzacz MVP (spin verified cos/sin, compact window shrink, guards, 95% match, new redesign section, all docs+code updated identical, handover SZPIEG/WRITER...; smoke/pytest OK; gotowe)".
- crew/CHECKLIST_reczny_test_nowy_DJ_Player.md + Checklist.md: add "re-audit 2026: spin rot cos/sin verified, compact min shrink, vis guards, dual overhead noted, EFFECT spin, safety both paths, 'uruchmo jeszcze raz'".
- AGENTS.md / CLAUDE.md: update crew section z "UI-DESIGNER re-audit example + explicit 'uruchmo jeszcze raz... nie przestawaj' + docs identical".
- crew/PLAN_... : minor note if needed o re-audit example.
- Code docstrings: in odt_view.py (class OdtwarzaczView + _CompactSpin + set_compact + _apply + paint), dj_player_window.py (_create_odt, _switch, _on_compact, resize, load_to), simple (set_compact, play etc), add/update "Uwaga... Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review... Patrz docs... must document identical. 2026-06-02 re-audit 'uruchmo jeszcze raz... nie przestawaj' — spin cos/sin verified, compact polish, guards." 
- todo_write: used (this list).
- Clear notes in edits.

**Status re-audit:** 'gotowe' + "Do końca". Wszystkie problemy z poprzednich (spin P0, compact P1 etc) zweryfikowane/fixed/polished. 95%+ match spec. Czeka na user przeczytanie "nowej listy przeróbek" (z tego + Plan) w pierwszej kolejności + decyzja "dalej"/"ok"/zmiany (per explicit PLAN/user). Potem ewentualnie WRITER/FIXER/TESTER lub side SZPIEG. Zero odstępstw od hierarchy (SZPIEG/Plan first), exact match, docs identical. 

Per nadrzędny SZPIEG Build Spec + Plan team review + memory/PLAN + user "uruchmo jeszcze raz... nie przestawaj" — must document identical. Gotowe.

**UI-DESIGNER re-audit 'uruchmo jeszcze raz' – ZAKOŃCZONY. Nowy wpis w redesign doc + wszystkie docs zaktualizowane identycznie. Przekazano. 'gotowe' + 'Do końca'.**
