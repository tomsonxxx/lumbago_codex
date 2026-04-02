# Przeniesione.md — Indeks migracji projektu Lumbago Music AI

**Data:** 2026-04-02
**Źródło:** `D:\Claude\Nowy folder\` (wersja nowsza, aktywna)
**Cel:** `D:\Claude\` (nowy katalog główny)
**Desktop:** `C:\Users\tomso\Desktop\Nowy folder\` (starsza kopia — usunięta)

---

## PLAN MIGRACJI

### FAZA 1: Przygotowanie D:\Claude
- [x] Usunąć pusty `.git` z `D:\Claude\` (pusty init, brak commitów)

### FAZA 2: Czyszczenie zbędnych plików w D:\Claude\Nowy folder (przed przeniesieniem)
- [x] `.venv/` (652 MB) — virtualenv, odtworzenie przez `python -m venv`
- [x] `.venv311_new/` (225 MB) — drugi virtualenv
- [x] `Lumbago_Music/` (484 KB) — stara wersja v1 (legacy)
- [x] `lumbago_codex/` (305 MB) — zagnieżdżona kopia repo (duplikat)
- [x] `.codex/` — środowiska Codex
- [x] `.pytest_cache/` — ⚠️ zablokowany (system permissions) — do ręcznego usunięcia
- [x] `web/node_modules/` (72 MB) — `npm install` odtworzy
- [x] `lumbago_app/__pycache__/` — skompilowane cache
- [x] `tests/__pycache__/` — skompilowane cache
- [x] `web/__pycache__/` — skompilowane cache
- [x] `.claude/worktrees/` — stare worktree'y Claude

### FAZA 3: Przeniesienie plików → D:\Claude\
- [x] `.git/` — repozytorium git (KRYTYCZNE)
- [x] `.claude/` — konfiguracja Claude (bez worktrees)
- [x] `.github/` — GitHub Actions workflows
- [x] `.gitignore` — reguły git ignore
- [x] `.env.example` — przykładowy plik env
- [x] `.lumbago_data/` — dane lokalne
- [x] `lumbago_app/` — KOD ŹRÓDŁOWY APLIKACJI (rdzeń)
- [x] `web/` — frontend + backend (bez node_modules)
- [x] `tests/` — testy pytest
- [x] `scripts/` — skrypty pomocnicze
- [x] `tools/` — narzędzia deweloperskie
- [x] `assets/` — zasoby (ikony, themes)
- [x] `docs/` — dokumentacja
- [x] `migrations/` — migracje Alembic
- [x] `pyproject.toml` — konfiguracja projektu
- [x] `requirements.txt` — zależności Python
- [x] `alembic.ini` — konfiguracja Alembic
- [x] `pyinstaller.spec` — build spec
- [x] `pytest.ini` — konfiguracja testów
- [x] `Build.md` — historia buildów
- [x] `Build2.md` — historia buildów (kontynuacja)
- [x] `Old.md` — notatki archiwalne
- [x] `README.md` — dokumentacja główna
- [x] `ToDo.md` — lista zadań
- [x] `ToDo2.md` — lista zadań (kontynuacja)

### FAZA 4: Usunięcie pustego Nowy folder
- [x] Usunąć `D:\Claude\Nowy folder\` — ⚠️ pozostał pusty folder z `.pytest_cache` (zablokowany)

### FAZA 5: Usunięcie Desktop
- [x] Usunąć `C:\Users\tomso\Desktop\Nowy folder\` (stara kopia) — USUNIĘTO

### FAZA 6: Aktualizacja konfiguracji
- [x] Zaktualizować MEMORY.md (nowa ścieżka: `D:\Claude`)
- [x] Dodać `safe.directory` do git config
- [x] Skopiować konfigurację projektu Claude do `~/.claude/projects/D--Claude/`
- [ ] Git remote — bez zmian (origin OK)

---

## PLIKI USUNIĘTE (LEGACY/ZBĘDNE)

| Plik/Folder | Lokalizacja | Rozmiar | Status |
|---|---|---|---|
| `.venv/` | D:\Claude\Nowy folder | 652 MB | ✅ usunięty |
| `.venv311_new/` | D:\Claude\Nowy folder | 225 MB | ✅ usunięty |
| `Lumbago_Music/` | D:\Claude\Nowy folder | 484 KB | ✅ usunięty |
| `lumbago_codex/` | D:\Claude\Nowy folder | 305 MB | ✅ usunięty |
| `.codex/` | D:\Claude\Nowy folder | — | ✅ usunięty |
| `web/node_modules/` | D:\Claude\Nowy folder | 72 MB | ✅ usunięty |
| `*/__pycache__/` | D:\Claude\Nowy folder | — | ✅ usunięty |
| `.claude/worktrees/` | D:\Claude\Nowy folder | — | ✅ usunięty |
| `Id3Tager/` | Desktop | 6.9 MB | ✅ usunięty (z Desktop) |
| `_archives/` | Desktop | 46 KB | ✅ usunięty (z Desktop) |
| `lumbagov3_extracted/` | Desktop | 19 KB | ✅ usunięty (z Desktop) |

**Oszczędności:** ~1.25 GB

---

## STRUKTURA DOCELOWA (D:\Claude\)

```
D:\Claude\
├── .claude/             # Konfiguracja Claude Code
├── .env.example         # Przykładowy plik env
├── .git/                # Repozytorium Git
├── .github/             # GitHub Actions
├── .gitignore           # Reguły ignorowania
├── .lumbago_data/       # Dane lokalne aplikacji
├── Build.md             # Historia buildów
├── Build2.md            # Historia buildów (kont.)
├── Old.md               # Archiwalne notatki
├── README.md            # Dokumentacja
├── ToDo.md              # Lista zadań
├── ToDo2.md             # Lista zadań (kont.)
├── alembic.ini          # Konfiguracja Alembic
├── assets/              # Zasoby (ikony, themes)
├── docs/                # Dokumentacja techniczna
├── lumbago_app/         # *** KOD ŹRÓDŁOWY ***
│   ├── core/            # Logika biznesowa
│   ├── data/            # ORM + SQLite
│   ├── services/        # AI, metadata, enrichment
│   └── ui/              # PyQt6 GUI
├── migrations/          # Migracje Alembic
├── przeniesione.md      # Ten plik
├── pyinstaller.spec     # Build spec
├── pyproject.toml       # Konfiguracja projektu
├── pytest.ini           # Konfiguracja testów
├── requirements.txt     # Zależności Python
├── scripts/             # Skrypty pomocnicze
├── tests/               # Testy pytest
├── tools/               # Narzędzia deweloperskie
└── web/                 # Frontend + Backend
    ├── backend/         # FastAPI
    ├── dist/            # Build frontend
    ├── src/             # Źródła frontend
    └── tests/           # Testy web
```

---

## LOG ZMIAN

| Czas | Akcja | Status |
|---|---|---|
| 03:22 | Utworzono przeniesione.md z planem migracji | ✅ |
| 03:23 | FAZA 1: Usunięto pusty .git z D:\Claude | ✅ |
| 03:23 | FAZA 2: Usunięto .venv (652MB), .venv311_new (225MB) | ✅ |
| 03:23 | FAZA 2: Usunięto Lumbago_Music, lumbago_codex (305MB), .codex | ✅ |
| 03:23 | FAZA 2: Usunięto node_modules (72MB), __pycache__, worktrees | ✅ |
| 03:24 | FAZA 3: Przeniesiono .git, .claude, .github, .gitignore, .env.example | ✅ |
| 03:24 | FAZA 3: Przeniesiono lumbago_app, web, tests, scripts, tools | ✅ |
| 03:24 | FAZA 3: Przeniesiono assets, docs, migrations | ✅ |
| 03:25 | FAZA 3: Przeniesiono 11 plików konfiguracyjnych | ✅ |
| 03:25 | Naprawiono git safe.directory dla D:\Claude | ✅ |
| 03:25 | FAZA 4: Nowy folder prawie usunięty (pozostał .pytest_cache) | ⚠️ |
| 03:26 | FAZA 5: Desktop\Nowy folder usunięty | ✅ |
| 03:27 | FAZA 6: MEMORY.md zaktualizowany na D:\Claude | ✅ |
| 03:27 | FAZA 6: Konfiguracja Claude skopiowana do D--Claude | ✅ |

---

## CZYNNOŚCI PO MIGRACJI

1. **Otwórz projekt w nowej lokalizacji:** `cd D:\Claude && claude`
2. **Utwórz virtualenv:** `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
3. **Zainstaluj node_modules:** `cd web && npm install`
4. **Usuń ręcznie** (jako Admin): `D:\Claude\Nowy folder\.pytest_cache`
5. **Uruchom testy:** `pytest`
