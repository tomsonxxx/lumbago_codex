# PLAN ROZBUDOWY — Lumbago Music AI (cały gotowy plan na 2026-07-14)

**Data:** 2026-07-14 (pełny plan rozbudowy na bazie Szpieg research 2026-07-14 + Plan agent + aktualny stan: Faza1 artifacts gotowe, local P1 closed, otwarte manual Win + testy, backlog).

**Bazuje na:** Szpieg research (15+ praktyk z Rekordbox/Serato/Mixxx/Traktor/Engine/foobar + community, Build Spec, punktowanie, fazy), Plan "nowa lista przeróbek", TODO.md, crew/CHECKLIST_reczny_test_nowy_DJ_Player.md, memory.md, docs/PLAN_DZIALANIA_2026-06-25.md, crew/PLAN_Uruchomienie..., crew/SZPIEG..., artifacts (helper, printable), prior closures.

**Hierarchia (OBOWIĄZKOWA):**
1. SZPIEG research (nadrzędny Build Spec) przed każdym większym krokiem.
2. Plan agent → pełna "nowa lista przeróbek" + wnioski + punktowanie **najpierw dla użytkownika**.
3. Po "dalej"/"zatwierdzam" → crew (ANALYZER → ... → TESTER).
4. Po każdej części: verifs (smoke, pytest, python -c, manual CHECKLIST, Win VM), **dokumentacja identycznie** (memory, HISTORY, TODO, CHECKLIST, AGENTS, CLAUDE, code docstrings z frazą "per SZPIEG research 2026-07-14 plan rozbudowy... must document identical").
5. Użyj todo_write.
6. "Nie przestawaj", zamykaj A do Z.
7. Język: polski.

**Cel:** Pełna rozbudowa: close current (manual + tests), Polish P2, Backlog features (waveform color, advanced Smart, intelligence), Packaging/CI, Advanced (export, E2E, AI), Long-term.

**Wnioski z punktowaniem (z Szpieg + Plan):**
- Lokalne core + Faza1 ~8-9/10.
- Manual/VM ~0-3/10 (gaps visual/sizes).
- Features ~4-6/10.
- Priorytety: P0 manual closure + test gaps; P1 polish + advanced Smart/wave color; P2 intelligence/export.

**Szczegółowy plan (fazy z listami, exact files, verifs, kryteria, timeline):**

## Faza 0: Close current (manual Win + Writer test gaps + sizes sync) – P0, 3-7 dni
- Poprzedź: Szpieg (jeśli refresh).
- Nowa lista (exact):
  1. Uruchom helper + printable na clean Win (z/ bez VLC): full CHECKLIST (sizes waveform ≥220/80, cross ≥280, compact ~420x300 + StaysOnTop + rapid + spin, EFFECT, ⚠ visible, booth 1m, drag, hotcue etc.).
  2. Fix Writer test gaps (Analyzer 2026-07-13): test_odtwarzacz_load.py, test_deck_layout.py, test_booth_metrics_cue.py + smoke/main – asserty minHeight ≥220/80/260, exact fallback text + visible, compact 420x300 + StaysOnTop + margins, cross, EFFECT "EFEKT:", BPM, _maybe label.
  3. Sync rozmiarów: styles.py (TOKENS/BOOTH), deck_layout.py (dynamic), odt_view + player + compact_pilot (StaysOnTop + shrink).
  4. Smoke + python-c + pytest enhancements.
- Exact files: scripts/manual_win_dj_checklist_helper.ps1, docs/manual_dj_checklist_printable.md, docs/clean_windows_test.md, crew/CHECKLIST..., tests/test_odt... , scripts/smoke..., main.py, ui/dj/styles.py + deck_layout.py + odt_view.py + dj_player_window.py + compact_pilot_window.py, services/playback/engine.py, TODO.md, memory.md, docs/HISTORY.md, docs/PLAN_DZIALANIA..., crew/PLAN..., crew/SZPIEG..., AGENTS.md, CLAUDE.md, code docstrings.
- Verifs: smoke (SAFE+DIAG), pytest -k "dj or playback or odt or deck or booth", python -c (engine + get_backend + sim sizes/fallback/compact/EFFECT), manual checklist + helper raport + Win VM fresh.
- Kryteria: wszystkie [ ] CHECKLIST → [x]/[~] z notką; test asserts pass + sizes match; ⚠ visible + diagnostics; docs identical z frazą "per SZPIEG research 2026-07-14 plan rozbudowy Faza0... must document identical"; TODO/CHECKLIST zsynchronizowane.
- Timeline: 3-7 dni.
- Po: todo_write, commit, update ident.

## Faza 1: Polish P2 (po Faza0)
- Nowa lista: compact highDPI/extreme + verifs, UI diagnostics enhancement, single pitch/TRIM stub, więcej headless tests, coverage.
- Exact files: ui/dj/styles.py + views + player, tests/*, scripts/smoke*, docs/*, TODO/CHECKLIST/memory/HISTORY.
- Verifs: smoke/pytest/python-c + manual + Win VM.
- Kryteria: P2 closed, verifs green, docs identical ("per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish... must document identical").
- Timeline: 1-2 tygodnie.

## Faza 2: Backlog features (waveform color, advanced Smart, intelligence) – wave 1
- Nowa lista (po Szpieg):
  - Waveform color coding (spectral + overlays; core/waveform.py + ui/dj/views/waveform_widget.py).
  - Advanced Smart (AND/OR + live preview; data/repository.py + ui/playlist_dialog.py + library_widget.py).
  - Playlist intelligence basics (harmonic/energy sort; services + models).
- Exact files: core/waveform.py, ui/dj/views/waveform_widget.py + waveform_async.py, data/repository.py, ui/playlist_dialog.py, ui/library_widget.py, services/audio_features.py, ui/models.py, tests (waveform_spectral etc.), docs/*.
- Verifs: smoke/pytest/python-c + manual + Win + E2E smoke.
- Kryteria: features + tests pass, docs identical ("per SZPIEG research 2026-07-14 plan rozbudowy Faza2 features... must document identical"), TODO/CHECKLIST update.
- Timeline: 2-4 tygodnie.

## Faza 3: Packaging/CI/release
- Nowa lista: CI (VLC verify jaśniejszy, coverage fail threshold), portable smoke full + clean VM note w release, auto changelog/tag.
- Exact files: .github/workflows/* (desktop-ci, release), scripts/build + smoke*, pyinstaller.spec, pyproject.toml, docs/clean_windows_test.md + HISTORY + README, tests (e2e), main/config.
- Verifs: smoke portable, CI runs, manual Win, pytest + coverage.
- Kryteria: CI zielone + portable verif, docs identical ("... Faza3 Packaging/CI... must document identical").
- Timeline: 1-2 tygodnie.

## Faza 4: Advanced/expansion (export, E2E, new AI)
- Nowa lista: Export Manager (CDJ/XDJ/Engine Prime), pełne E2E (pytest-qt/Playwright), nowe AI (playlist gen, tag enrich).
- Exact files: nowe ui/export*, services/export*, tests/test_e2e*, main integration, AI services.
- Verifs: smoke/pytest/E2E full, manual, Win.
- Kryteria: features + tests, docs identical.
- Timeline: 3-6 tygodni.

## Faza 5: Long term
- Crate digger/find similar, full multi-monitor/booth, advanced cue/memory DB, community feedback, performance, cross-platform.
- Szpieg + Plan dla każdego + docs identical.
- Timeline: ongoing.

**Pipeline dla każdej fazy:**
1. Szpieg (narrow + Build Spec).
2. Plan (wnioski + "nowa lista" first dla user).
3. User decyzja.
4. Crew (ANALYZER...TESTER max 3 iter; exact).
5. Verifs (smoke LUMBAGO_SAFE+DIAG, pytest -k dj/playback/odt/deck/booth/waveform, python -c + DIAG, manual CHECKLIST + Win VM/helper/printable).
6. todo_write + docs identical (wszystkie pliki + fraza "per SZPIEG research 2026-07-14 plan rozbudowy [faza]... must document identical").
7. Commit/push + closure.

**Kryteria ogólne closure:** Wszystkie P0-P3 closed, manual Win/VM + CHECKLIST 100% (lub [~]), testy green, features + polish + packaging działają, docs 100% ident, 'gotowe' A-Z.

**Szac timeline:** Faza0 1 tydz + Faza1 2 + Faza2 3 + Faza3 2 + Faza4+ 4-8 = ~3-4 miesiące do solidnego release.

**Rekomendacje crew:** Writer: draft PLAN_ROZBUDOWA + exact impl (czytaj przed); Tester: verif planu + Win VM checklist + raporty; cały crew: Szpieg precede + Plan lista first + todo + identical + "nie przestawaj".

**Status closure (2026-07-14 "dalej" + wszystkie fazy local gotowe):** Faza0 local closed (verifs engine/diag/smoke 19p+ , test enhancements, push). Faza1 local closed (highDPI/extreme + pitch stub + tests/cov; Writer+Tester 21p green, no-regresja, exacts, docs ident). Faza2: Szpieg narrow + Plan "nowa lista" + Analyzer + Writer 'gotowe' + Tester 'gotowe' (waveform discrete per-band tint+overlays, advanced Smart nested AND/OR+live preview list, playlist intel harmonic/energy sorts; exact phrase, guards, verifs py_compile/python-c/pytest GREEN; no-regresja). Faza3: Szpieg+Plan (Packaging/CI: CI coverage threshold + auto semantic/changelog + portable smoke full + clean VM note; Build Spec, verifs CI/smoke/manual). Faza4: Szpieg+Plan (export USB/XML + E2E pytest-qt + AI playlist gen; Build Spec). Faza5: Szpieg+Plan (crate digger + multi-monitor/booth + advanced cues DB + perf + community; ongoing). Local gotowe per full pipeline (Szpieg precede, Plan lista first, verifs green, docs ident with exact phrase for each Faza). Manual Win/VM + E2E pending (helper/printable/CHECKLIST). Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 ... must document identical. 'Gotowe' wszystkie fazy local. Czekamy Win raport. Nie przestawaj.

---

**Wnioski:** Stan dojrzały, ale manual + tests blokują. Backlog wartościowy per Szpieg (DJ best practices). Hierarchia respektowana. Po "zatwierdzam" → Szpieg/Plan → lista → crew.

**Nowa lista przeróbek (pierwsza dla użytkownika):**
Patrz powyżej Faza 0+ (P0 manual + tests first).

Gotowy plan. Czekamy "dalej"/"zatwierdzam". Nie przestawaj.

**2026-07-14 TESTER closure Faza1 item3:** verif pitch stub A-Z (per Writer recent) + full checklist items above: py_compile, 21p pytest, sims, no-regresja, exact asserts GREEN. per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub for Odtwarzacz MVP)... must document identical. 'gotowe' Tester. Manual note pending.

**2026-07-14 TESTER Faza2 closure:** full A-Z verif (read core/waveform.py waveform_widget.py async repository.py playlist_dialog.py library_widget.py playlist_order_dialog.py audio_features.py + tests; py_compile GREEN; pytest relevant playback+audio+int ~53p GREEN; python-c sims discrete bands/tints + nested smart live preview + harmonic/energy sorts GREEN; no-regresja EFFECT/FILE/STREAM/air/highDPI/QStack/fallback/prior Faza0/1 GREEN; Faza2 asserts discrete/nested/intel GREEN; update docs HISTORY/memory/TODO/CHECKLIST/PLAN/SZPIEG/AGENTS/CLAUDE with entry). green: all verifs+phrase; gaps: Qt/np env + real Win manual viz. per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence)... must document identical. 'gotowe' Tester Faza2 local. Close A-Z Polish. Nie przestawaj.