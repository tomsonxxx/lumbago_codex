# GUARDIAN SAFETY REVIEW REQUEST — Full Repo Consolidation 2026-06-16 (Archivist/Cleaner)

**Date:** 2026-06-16
**Agent:** Archivist / Cleaner
**Task origin:** User request + SZPIEG plan for full consolidation (create root MEMORY/, logical sub structure, move historical/unnecessary/historical files (md, old artifacts), trim live docs to bare min, update memory.md, identical note phrase in all edited, only docs/md/old remnants — NEVER touch active .py, tests, scripts, requirements, pyproject, source code etc.)

## Proposed Final MEMORY/ Structure (per explicit spec)
- MEMORY/full_agent_instructions/  — full pre-trim copies of AGENTS.md, CLAUDE.md, crew/PLAN_*.md, crew/SZPIEG_*.md, crew/CHECKLIST_*.md (with clear dated names e.g. *_2026-06-16_full_pre-trim.md), + old crew md if needed
- MEMORY/historical_checklists/ — root Checklist.md + any old CHECKLIST*.md (dated)
- MEMORY/history/ — consolidated previous runs excerpts, HISTORY excerpts, Archiwum content summaries/index
- MEMORY/old_docs/ — unused md like analysis-tagging-audit.md, Lumbago_Blueprint_Extracted.txt, other remnants (dated names)
- MEMORY/previous_archive/ — integrate/move entire contents of docs/archive/ (build-artifacts/, crew/ old md, mockups pngs, old-docs/, web-remnants/) here for single MEMORY home (preserve subdirs or flat integrate)

## Exact Targets Identified (from list_dir + grep + terminal inventory of *.md/*.txt excluding node/venv/build/dist/pycache; only project historical/unnecessary)
**To COPY first (full pre-trim for preservation in full_agent_instructions/):**
- D:\Claude\AGENTS.md → MEMORY/full_agent_instructions/AGENTS.md_2026-06-16_full_pre-trim.md
- D:\Claude\CLAUDE.md → MEMORY/full_agent_instructions/CLAUDE.md_2026-06-16_full_pre-trim.md
- D:\Claude\crew\PLAN_Uruchomienie_Python_Code_Review_Crew.md → MEMORY/full_agent_instructions/PLAN_Uruchomienie_Python_Code_Review_Crew.md_2026-06-16_full_pre-trim.md
- D:\Claude\crew\SZPIEG_agent_spec_and_archive.md → MEMORY/full_agent_instructions/SZPIEG_agent_spec_and_archive.md_2026-06-16_full_pre-trim.md
- D:\Claude\crew\CHECKLIST_reczny_test_nowy_DJ_Player.md → MEMORY/full_agent_instructions/CHECKLIST_reczny_test_nowy_DJ_Player.md_2026-06-16_full_pre-trim.md

**To MOVE (historical/unnecessary — after safe copy where applicable):**
- D:\Claude\Checklist.md → MEMORY/historical_checklists/Checklist.md_2026-06-16.md
- D:\Claude\docs\analysis-tagging-audit.md → MEMORY/old_docs/analysis-tagging-audit.md_2026-06-16.md
- D:\Claude\docs\Lumbago_Blueprint_Extracted.txt → MEMORY/old_docs/Lumbago_Blueprint_Extracted.txt_2026-06-16.txt
- Entire docs/archive/ content → MEMORY/previous_archive/ (Move contents or structure: build-artifacts/ (txts), crew/ (4 old md: AGENT3_*, LISTA_*, SZPIEG_DJ_*, UI_Designer_*), mockups/ (4 pngs), old-docs/ (3 md), web-remnants/ (next/web remnants) — for single home; keep original sub structure under previous_archive/ if possible or integrate)

**Files to LEAVE in place (active / current docs, not historical remnants):**
- memory.md (will be UPDATED with top MEMORY Archive section + note phrase)
- docs/clean_windows_test.md, docs/dj_player_guide.md, docs/HISTORY.md, docs/user_guide.md (active guides)
- README.md, RECOVERY.md, SECURITY.md, tools/README.md (standard project)
- services/playback/DESIGN.md (active in services/)
- All .py, tests/, scripts/, pyproject, requirements, core/data/ui/services/ etc — **STRICTLY NEVER TOUCH**
- .claude/worktrees/* and venv/site-packages etc (external, not project historical docs per task scope)

**No other loose project md identified in core tree for move.**

## Safety Measures (built-in, per task "Coordinate with Guardian for safety review before any delete/move")
- **Copies FIRST for anything trimmed (full pre-trim dated copies to MEMORY/full... before any edit/trim of live AGENTS/CLAUDE/crew files).** Originals only trimmed in place AFTER copy.
- **Moves only for clearly historical/unnecessary (per prior 2026-06-15 "uporzadkuj" which moved to docs/archive, now deeper single MEMORY home per new request).** Active docs stay.
- Use terminal Copy-Item / Move-Item (powershell native, atomic where possible, Force for safety).
- After any move of archive dir content, docs/archive/ will be emptied then removed only if confirmed empty.
- No data loss: full copies of verbose historical in MEMORY/; trimmed live retain essential for work + pointer to full in MEMORY/.
- Git will track all (renames + new dir) — commit after.
- Only md, txt, png artifacts in archive context. No binaries exec, no source.
- Read_file + list_dir + grep used before any edit/move planning.
- todo_write used for tracking.
- After groups: verifs (git status, list MEMORY -Recurse, read key trimmed + new archived files).
- Identical note phrase added to EVERY live edited file (AGENTS, CLAUDE, 3x crew, memory.md): "Per 2026-06-16 full repo consolidation and cleanup: all prior documentation, full agent instructions, checklists, history, and context memories safely archived in root MEMORY/ directory (with subdirs) and consolidated/summarized in this memory.md. Live files trimmed to essential minimum for ongoing work but complete for continuity. All information from the project up to this point is preserved and accessible in MEMORY/."
- Prominent header in trimmed live points to MEMORY/ for full.
- For previous_archive: integrates the 2026-06-15 docs/archive (old crew redesigns, mockups, web, etc.) under one roof.

**Risks & Mitigations:** Low — only docs. If git worktree or .claude ignored (not touched). Reversible via git. No impact on run/build/test (scripts/docs only).

**Proposed Sequence (after Guardian OK):**
1. Write this review file + read it back (self-coord + audit).
2. todo update.
3. run mkdir -Force for MEMORY + 5 subdirs.
4. Copy-Item the 5 full pre-trim (dated).
5. Move-Item Checklist, analysis, blueprint txt (dated names).
6. mkdir MEMORY/previous_archive if needed; Move-Item docs/archive/* → MEMORY/previous_archive/ (recurse for subs); then if empty rmdir docs/archive.
7. Trim 5 live files via targeted search_replace (read-before done; insert note + reduce to min keeping "Dla nowych", hierarchy, current status summary, commands, pointers).
8. Update memory.md (top MEMORY Archive section with index + summary "all prior preserved safely" + note phrase).
9. Verif groups: terminal git status, Get-ChildItem MEMORY -Recurse | select FullName, list_dir MEMORY, read_file key trimmed + archived.
10. Update todo, final report with progress list, actions, final structure.
11. (Later) git add MEMORY/ trimmed files + commit (but task not require push here).

**Guardian review checklist (for you):**
- [ ] Only docs/md/old artifacts touched? Yes.
- [ ] Copies before trim/rm? Yes planned.
- [ ] No source/py touched? Yes.
- [ ] Structure matches user/SZPIEG spec? Yes.
- [ ] Note phrase + pointers added? Yes.
- [ ] Safe, reversible, momentum kept? Yes.
- [ ] Read memory recent + docs/archive first? Yes (tool calls done).
- [ ] Work folder by folder? Yes.

**Requested action from Guardian:** Review above, approve or flag changes. Once approved in response (or by reading this + todo), Archivist will execute exactly. No moves/deletes until this step.

All prior info (full verbose history, crew outputs, SZPIEG research, plans, checklists, old docs) will be safely in MEMORY/ + summarized in memory.md. Live continuity preserved.

END OF REQUEST — ready for review/execute. Per "uporzadkuj cala dokumentacje" + current task + PLAN. "Nie przestawaj".