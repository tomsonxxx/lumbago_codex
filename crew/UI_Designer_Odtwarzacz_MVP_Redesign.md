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
