# REMAINING DETAILED CHECKLIST — Lumbago Music AI (post konsolidacja masterPlan)

**Data:** 2026-07-14  
**Podstawa:** Porównanie aktualnego stanu (kod + testy + dokumentacja) z `docs/PLAN_MASTER_CONSOLIDATED_2026-07-14.md` (Verification Matrix, Faza0-5 opisy, "nowe listy", manual steps) + memory.md + TODO.md + crew/CHECKLIST* + clean_windows_test.md + code inspection (grep + read) + pytest run (79 passed relevant).

**Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + Downloader/AI per "chce dodać nowe, dosc skomplikowane.txt" + "dalej az do ukonczenia wszystkich faz" + consolidation using agents ... must document identical.**

**2026-07-14 NOWA_LISTA EXECUTION (bez zatrzymywania):** Local 79p GREEN + sims (wave/intel/DL) + sandbox timeout + Faza5 stub + wiring + artifacts + ident docs/fraza. Local closed A-Z. Real manual/700+/Win [~]. 'Gotowe' prep+verif. Nie przestawaj.

**Główne wnioski z porównania:**
- **Local / code / test "gotowe"** (silne dowody): Faza2 (waveform discrete tint, nested smart rules + live, intel camelot/energy), Faza4 core (downloader lazy+checkpoint+est+profiles MAX/bestaudio, AI registry+dispatch+some real wiring, 14p+ tests), smoke/portable/CI fixes, no-regresja (EFFECT, FILE/STREAM, guards).
- **Pytest:** 79 passed (playback + downloader + odt + dj + waveform + smart filter) — bardzo dobre pokrycie.
- **Główne braki:** **Prawdziwe wykonanie ręczne na czystym Windows/VM** (wszystkie wiersze matrix "Win/VM: Pending"). Brak pełnego E2E na real maszynie (import + DJ full flow + large DL + AI cmds). Niektóre szczegóły polish (exact sizes asserts, booth visual, pełne wiring AI). Faza5 tylko notatki.
- Wszystkie checklisty manualne mają otwarte [ ] na real testy.

---

## 1. Ogólne / Matrix Closure (wszystkie Fazy)

- [ ] **Win/VM real execution** dla każdej Fazy (zgodnie z Verification Matrix w master):
  - Czysty Windows (fresh profile, bez dev Python jeśli możliwe lub z minimalnym).
  - Z i bez VLC.
  - Pełny raport z helper/printable + screeny.
- [ ] E2E tests (pytest-qt lub manual + automated) dla kluczowych przepływów (import → library → DJ → DL → AI).
- [ ] Zaktualizować Verification Matrix w `PLAN_MASTER...` po real Win raportach.
- [ ] Pełne "gotowe" A-Z z frazą identyczną we wszystkich plikach.

---

## 2. Faza 0: Close current (manual + test gaps + sizes) – P0

Z master + clean_windows + CHECKLIST_reczny:

- [ ] Uruchomić `scripts/manual_win_dj_checklist_helper.ps1` + printable na **czystym Win** (z/ bez VLC).
- [ ] Zweryfikować exact rozmiary:
  - Waveform single ≥220px, compact ≥80px, dual booth ≥260px.
  - Crossfader ≥280px szeroki.
  - Compact pilot ~420x300 + StaysOnTopHint + shrink.
- [ ] Wzmocnić / uruchomić testy z dokładnymi assertami (test_odtwarzacz_load.py, test_deck_layout.py, test_booth_metrics_cue.py):
  - minHeight, exact fallback text "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org".
  - Compact metrics, EFFECT tooltips.
- [ ] Sync rozmiarów w kodzie vs TOKENS (styles.py) — potwierdzić w real highDPI + normal.
- [ ] Pełny flow na clean Win:
  - Import 1-3 audio.
  - Library appear + detail edit + save.
  - DJ Player: load (drag/button), play/seek/hotcue(8), loop, crossfader, waveform, status, no crash.
  - APPDATA %APPDATA%\LumbagoMusicAI (lumbago.db + settings.json).
  - Visible diagnostics + banner.
- [ ] Portable smoke na real extract (resources strict, DIAG, backend info).
- [ ] Booth 1m low-light high-contrast readability (duże elementy, brak gęstości, air).

**Status wg analizy:** Local code + sims + testy — done. Real manual — całkowicie otwarte.

---

## 3. Faza 1: Polish P2 (highDPI, pitch, diagnostics, headless)

- [ ] Real highDPI/extreme test na czystym Win (scale >1.04/1.55) + compact + diag visibility.
- [ ] Single pitch/TRIM stub — pełny manual test (set rate/pitch/keylock, tooltip "EFEKT: ...", compact hide, EFFECT).
- [ ] Diagnostics UI (get_backend_info / get_diagnostics) widoczne i poprawne w real run (Noop/Qt/VLC stany).
- [ ] Więcej headless testów + coverage (gaps z Analyzer 2026-07-13).
- [ ] Exact sizes vs base tokens — pełne asserty + dokumentacja.

**Status:** Local code + python-c/pytest done. Real highDPI + manual — pending.

---

## 4. Faza 2: Backlog features (waveform color, advanced Smart, playlist intelligence)

**Zaimplementowane (kod + testy potwierdzone):**
- Waveform discrete per-band tint + energy overlays (get_band_tint, classify).
- Advanced Smart: nested AND/OR + recursive build + live preview (repository.py).
- Playlist intel: camelot_distance, sort_harmonic, sort_energy.

**Pozostałe podpunkty:**

- [ ] Real manual w DJ Player:
  - Waveform pokazuje kolory kick (red), hi-hat (yellow), vocal (green), breakdown (blue) + energy overlay.
  - Test normal / compact / highDPI.
  - Smart builder: nested rules + live preview list + więcej pól.
  - Library smart tree dynamic update.
  - Order dialog: harmonic + energy sort buttons działają na real bibliotece.
- [ ] Pełne testy manualne na czystym Win (Faza2 additions w CHECKLIST).
- [ ] Python-c / pytest symulacje + real DB (już green local).
- [ ] No regression po Faza2 (EFFECT, air, QStack, drag, highDPI) — potwierdzić w real flow.
- [ ] Aktualizacja w master + checklists po manualu.

**Status wg master + kodu:** Local gotowe (TESTER closed). Real visualization + manual — pending.

---

## 5. Faza 3: Packaging/CI + Downloader notes (enhanced)

- [ ] Portable build + smoke na czystym Win (strict resources, DIAG, Noop/backend).
- [ ] yt-dlp + ffmpeg **w PATH** na clean maszynie — test warningów + graceful (Downloader UI).
- [ ] Pełne notki w clean_windows_test.md, user_guide.md, smoke/build ps1, pyinstaller.spec.
- [ ] CI runs (desktop-ci) zielone z nowymi notkami Downloader.
- [ ] Manual: po unpack — "Narzędzia gotowe" lub czytelne ostrzeżenie.

**Status:** Local scripts + notes — done. Real portable + external tools test — pending.

---

## 6. Faza 4: Downloader 700+ + AI Chat Panel (per "chce dodać nowe, dosc komplikowane.txt")

**Zaimplementowane (silne dowody):**
- Downloader: profiles (MAX/BALANCE/COMPACT), bestaudio priority, estimate, JSON checkpoints (.lumbago_dl_checkpoint), lazy extraction, UI (log, history, resume stub, prefill).
- AI: command_registry (pobierz, duplikaty, otaguj, status_biblioteki z EFFECT), dispatcher, sandbox, chat_widget integration, some real wiring (status_biblioteki real counts, prefill do DL).
- Tests: 14p+ (est, checkpoint, cancel, dispatch), python-c (registry, large est 700 warning, real repo counts).

**Pozostałe podpunkty (szczegółowa lista):**

### Downloader
- [ ] Na czystym Win: yt-dlp + ffmpeg w PATH (test detekcji + warning).
- [ ] Duża playlist (700+ items): 
  - Estymacja poprawna (rozmiar + czas).
  - Lazy extraction + progress.
  - Checkpoint creation/resume (JSON files).
  - MAX profile (bestaudio + jakość audible).
  - Throttle/fragments.
  - Cancel + continue.
  - Add to library po sukcesie.
- [ ] Error handling (brak narzędzi, network, duże pliki >5GB warning).
- [ ] UI polish: rich history z checkpoint details, resume last, log limit, komunikaty.
- [ ] Portable notes: UI pokazuje czytelne info gdy brak yt-dlp/ffmpeg.

### AI Chat Panel (złożony mechanizm)
- [ ] Pełne komendy z real actions:
  - "pobierz <url>" → prefill Downloader + auto_start jeśli podano.
  - "duplikaty" → otwiera DuplicatesDialog + skan (real).
  - "otaguj" → real autotag flow lub dialog.
  - "status_biblioteki" → real counts z repo (tracks/playlists).
- [ ] Ambiguity handling + "Myślę..." + multi-provider.
- [ ] Sandbox safety (registry-primary) + EFFECT descriptions na wszystkich komendach.
- [ ] Cross-wiring MainWindow ( _open_downloader, _scan... ) pełne i bezpieczne.
- [ ] Test na real bibliotece + large DL (end-to-end verbal command → result).

### Integracja + Testy
- [ ] Pełny E2E: AI command → Downloader → real download → library add → DJ load.
- [ ] 700+ playlist real run (nie tylko symulacja).
- [ ] Edge: cancel mid large PL, resume after restart, disk space check, no-silent errors.
- [ ] Aktualizacja checklisty Downloader (CHECKLIST_Downloader_AI_Panel.md) po real teście.
- [ ] Portable: notes + test na clean bez narzędzi.

**Status wg master:** Local gotowe (core + 14p + python-c). Real large PL + full AI verbal + clean Win — pending (gaps explicit w TODO/memory).

---

## 7. Faza 5: Long-term

- [ ] Crate digger / find similar (użycie audio_features).
- [ ] Full multi-monitor / booth advanced support.
- [ ] Advanced cue / memory DB (persist, recall).
- [ ] Performance (duże biblioteki, waveform, smart).
- [ ] Community feedback loop.
- [ ] Cross-platform notes (choć primary Windows).

**Status:** Tylko notatki w master/PLAN. Brak implementacji.

---

## 8. Manual Checklists — Wszystkie otwarte pozycje (z crew/ + clean_windows + printable)

**DJ Player (Single/Compact/Dual/Booth):**
- [ ] Otwórz Single → waveform + BPM + transport.
- [ ] Compact: always-on-top, shrink, rapid toggle, spin (cos/sin), min size.
- [ ] Dual: crossfader, 8 hotcue/deck, EQ, PFL.
- [ ] Hotcue set/jump/delete + persist po restart.
- [ ] EFFECT tooltip na każdym elemencie (wave, btn, status...).
- [ ] Drag z biblioteki → highlight + safety prompt + FILE vs STREAM.
- [ ] Booth 1m low light: czytelność (duże pady, brak zachodzenia, high-contrast).
- [ ] No-VLC: prominent banner + diagnostics link.
- [ ] Resize dynamic (air zachowany, highDPI).

**Clean Windows / Portable full flow:**
- [ ] Portable extract + exe start.
- [ ] Import audio + library + detail edit/save.
- [ ] DJ full (jak wyżej).
- [ ] APPDATA creation.
- [ ] Downloader na clean (PATH + large PL).
- [ ] VLC guidance widoczna gdy brak.

**Inne:**
- [ ] Wszystkie [ ] w `crew/CHECKLIST_reczny_test_nowy_DJ_Player.md` i printable.
- [ ] Wszystkie kroki w `docs/clean_windows_test.md` (import, DJ, DL, portable).
- [ ] Helper script run + raport.

---

## 9. Inne / Polish / Tech Debt

- [ ] Sandbox_runner.py: prawdziwy timeout (obecnie TODO).
- [ ] AI registry: pełne real wiring dla wszystkich komend (niektóre "stub + doc").
- [ ] Test sizes exact vs TOKENS (220/80 vs base).
- [ ] Pełne E2E (test_e2e_desktop.py — obecnie tylko mark).
- [ ] Coverage fail threshold / auto changelog (Faza3).
- [ ] Więcej real DB testów dla smart (stub vs integration).
- [ ] Dokumentacja w user_guide.md + dj_player_guide.md — pełne sekcje Downloader/AI + Faza2.
- [ ] Grep całego repo pod "stub", "TODO", "pending" i uporządkowanie.

---

## 10. Proces zamykania pozostałych

1. SZPIEG / Plan (jeśli potrzeba narrow research na manual lub large PL).
2. "Nowa lista" z tego checklistu → użytkownik (pierwsza kolejność).
3. Po "dalej": crew lub bezpośrednie wykonanie manual + fixes.
4. Real Win/VM raport + screeny.
5. Verifs (smoke + manual checklist + python-c + pytest).
6. Update master + memory + TODO + checklists z frazą identyczną.
7. todo_write + commit + push.

**Kryteria pełnego zamknięcia:** Wszystkie powyższe [ ] → [x] lub [~] z notką + real Win raport + master matrix updated + fraza we wszystkich plikach.

---

**Podsumowanie:**  
Kod i testy lokalne są w bardzo dobrym stanie (Faza0-4 largely done, 79p tests).  
**Główny pozostały work:** Real manual execution na czystym Windows/VM dla **wszystkich** manual flow (DJ + Downloader + AI + sizes + booth + portable) + Faza5 + drobne polish.

Ten checklist powinien być używany razem z `PLAN_MASTER_CONSOLIDATED_2026-07-14.md`.

**Nowa lista przeróbek (wyodrębniona w stylu Plan):** `docs/NOWA_LISTA_PRZEROBEK_2026-07-14.md`

**2026-07-14 PUSH:** git push origin main (e316b06d). Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + "dalej az do ukonczenia wszystkich faz" ... must document identical. 'Gotowe' push. Nie przestawaj.

Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + "dalej az do ukonczenia wszystkich faz" ... must document identical. 'Gotowe' analiza + checklist. Nie przestawaj.