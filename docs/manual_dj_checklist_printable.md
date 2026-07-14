# MANUAL DJ CHECKLIST PRINTABLE — Win + booth (Faza 1 prep)

**Wyodrębnione z crew/CHECKLIST_reczny_test_nowy_DJ_Player.md + expected sizes + screenshot placeholders + Build Spec excerpt z Szpieg + sekcja "Test bez VLC" + template raportu.**

Per SZPIEG research 2026-07-13 (Build Spec, 15 praktyk, luki, side recs: helper script + printable + template) + Plan "nowa lista" (Faza 1: prep artifacts helper + printable + update clean_windows) — must document identical.

**Użyj z:** scripts/manual_win_dj_checklist_helper.ps1 (uruchom helper przed/podczas)

**Jak drukować:** Drukuj na A4, landscape jeśli potrzeba, checkboxy do odhaczenia markerem.

---

## 0. Uruchomienie (z helperem)

```powershell
# W PowerShell (repo root)
.\scripts\manual_win_dj_checklist_helper.ps1
# lub z exe:
.\scripts\manual_win_dj_checklist_helper.ps1 -UseExe
```

Na starcie helper loguje get_backend_info() + diagnostics (dla python).

**Uruchom ponownie z VLC / bez VLC** — po teście.

---

## 1. Tryb Single ("Odtwarzacz") — MUST

- [ ] Otwórz w trybie Single
- [ ] Waveform ≥220px wysokości (compact ≥80), dużo wolnej przestrzeni, brak zachodzenia elementów
  - **Expected:** dominant wave stretch, min 220px non-compact (compact 80px), air 32/24px normal / 8/6 compact
  - ![screenshot placeholder: single_full.png — wave + BPM + transport]
- [ ] BPM duży i czytelny (≥30px non-compact / 14 compact, gruby accent)
  - **Expected sizes:** ≥30px font weight bold accent color
- [ ] Duży, wyraźny playhead + BPM-aware beatgrid
- [ ] Duże przyciski transport (PLAY/CUE/STOP booth sizes/colors, toggle play/pause)
- [ ] Compact pilot: toggle, collapse sizes/fonts/margins (8/6), wave min80, spin visible+rotuje (cos/sin angle CD/vinyl/eq) tylko gdy playing+compact, react play_state
- [ ] Compact pilot advanced (po lista 2+12 + SZPIEG pilot): always-on-top (StaysOnTopHint gdy compact, przydatne booth/multi-monitor), minSize shrink (~420x300), reduce empty bottom (tight margins bottom ~2px, mniej stretch push), floating/pilot feel, restore full air/minSize/normal na off. Test z innymi oknami + rapid toggle+play.
  - ![screenshot placeholder: compact_pilot.png — small always-on-top + spin]
- [ ] Drag z biblioteki: mime paths/urls, highlight border, repo lookup full Track, load, safety prompt jeśli playing (FILE during stream)
- [ ] EFFECT tooltips wszędzie (1-2 zdania "EFEKT: ..." file=PLIK load vs stream=transport play/cue/seek)
- [ ] Black/empty: #OdtwarzaczPanel surface + "Brak utworu — upuść plik z biblioteki"
- [ ] Resize: dynamic wave min/spin s=width//30, no cut, air preserved, multi/highDPI safe
- [ ] QStack: single default, odt index1 / dual0, no overlap, aggressive hide on switch, re-sync compact
- [ ] Cue/play/stop: near0 prefer cue, stop->cue, double wave seek+cue, playback in compact OK

---

## 2. Tryb Dual Console ("Konsola DJ")

- [ ] Przełącz na Dual Console
- [ ] Oba decki widoczne (A i B), crossfader duży i wyraźny (min 280px szerokości)
  - **Expected:** crossfader min 280px szeroki, czytelny
  - ![screenshot placeholder: dual_crossfader.png]
- [ ] EQ i pitch w pełni czytelne na każdym decku
- [ ] 8 hotcue padów na każdy deck
- [ ] Master Volume + HP Cue + PFL toggle działają
- [ ] Crossfader A↔B zmienia głośność decków poprawnie (słuchaj + wizualnie)

---

## 3. Podstawowa funkcjonalność + Integracja

- [x] Now playing indicators w bibliotece (▶A / ▶B) działają
- [x] Load z playlisty / szczegółów działa
- [x] Brak regresji w MainWindow
- [~] Smoke test przechodzi (auto)
- [ ] Hotcue: set, jump, delete – persystencja
- [ ] Memory S/R działa
- [ ] SYNC (BPM + faza) + Quantize + KEY + pitch — nie psują
- [ ] Drag & drop z głównej biblioteki do decków
- [ ] Resize okna – brak ucinania
- [ ] Skróty: Spacja=play/pause, Ctrl+1..8=hotcue

---

## 4. Testy w warunkach "booth" (symulacja) — LOW LIGHT INSTRUKCJA

- [ ] Zmniejsz jasność ekranu (niska jasność booth)
- [ ] Sprawdź czytelność z odległości ~1m (duże pady, BPM, waveform, crossfader powinny być wyraźne)
  - **Expected:** high-contrast air, brak "za gęsto"/zachodzenia, dominant elements
- [ ] Brak "za gęsto" / zachodzenia elementów
- [ ] Air zachowany, spin widoczny w compact+play

![screenshot placeholder: booth_lowlight_1m.png — symulacja odległość i jasność]

---

## 5. Test bez VLC (fallback) ⚠ 

**Uruchom helper ponownie bez VLC (odinstaluj lub zablokuj libvlc).**

- [ ] Widoczny prominent banner/status: **'⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org'**
  - W compact + normal + highDPI
  - Używa get_backend_info() (Noop/Qt fallback)
- [ ] Diagnostics: btn tools lub python call pokazuje backend info + get_diagnostics()
- [ ] Playback ograniczony (FILE load vs STREAM playback ograniczony) — safety + EFFECT tooltips nadal
- [ ] Po ponownym z VLC: warning znika, pełna jakość

**Expected:** warning widoczny nawet gdy status compact ukryty; exact text + link guidance.

---

## Build Spec excerpt (z Szpieg research 2026-07-13 + prior)

- Zachować: air + dominant wave (10/10), transport booth sizes + CUE sep, compact pilot (always-on-top + cos/sin spin 50ms), EFFECT 1-2zd na każdym (file=PLIK load vs stream=transport), drag safety + prompt + mime+repo+hl, scalability resize dynamic, single default QStack, FILE vs STREAM clarity + guards.
- Wzmocnić: visibility no-VLC (prominent banner w odt+window), compact extreme reduce empty/highDPI, diagnostics UI.
- 15+ praktyk z Szpieg: portable clean test, VLC guidance 'Pobierz VLC z videolan.org', graceful Noop/Qt, booth low light readable 1m, rapid toggle, safety FILE during stream.
- Luki z research: no-VLC vis w compact, smoke brak full DJ+diag exec, manual sizes/booth pending.

Per SZPIEG research 2026-07-13 co-dalej manual... must document identical.

---

## TEMPLATE RAPORTU (wypełnij po teście, skopiuj do issue/PR)

```
Data: 2026-07-13
Maszyna: [Win clean / VM / z VLC / bez VLC]
Helper: [użyty / manual]
Wyniki:
- Single sizes (wave ≥220px, BPM): [OK / FAIL - details]
- Compact advanced (always-on-top, shrink ~420x300, rapid+spin): [OK/FAIL]
- Dual cross (≥280px): [OK/FAIL]
- EFFECT tooltips: [OK/FAIL]
- no-VLC ⚠ visible (compact/normal): [OK/FAIL]
- drag safety: [OK/FAIL]
- booth sim (low light ~1m, no gęsto): [OK/FAIL]
- Test bez VLC: [OK/FAIL - warning visible? backend?]
- Inne issues: ...
Screenshoty: [lista z placeholderów]
Podsumowanie: [GREEN / issues]
Per SZPIEG research 2026-07-13 co-dalej manual... must document identical
```

---

**Po teście:** 
- Odhacz w crew/CHECKLIST
- Update docs/clean_windows_test.md + memory + TODO + HISTORY + PLAN + CHECKLIST (notka)
- Verif: cat docs/manual_dj_checklist_printable.md | head -5
- Przekaz Tester + "Uruchom ponownie z VLC / bez VLC"

Per PLAN Faza 1 + "nie przestawaj". Exact match. 'Gotowe' printable.