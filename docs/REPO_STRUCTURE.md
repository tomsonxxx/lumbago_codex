# REPO STRUCTURE - Lumbago Music AI (Desktop Windows Python only)

**Główny folder domowy: D:\Claude**

Projekt jest **wyłącznie** wersją desktopową na Windows w Pythonie (PyQt6).
Zero web, zero innych wersji w głównym drzewie.

## Struktura (zgodna z najlepszymi praktykami)

D:\Claude\
├── .claude\                          # Global agent config
├── LumbagoMusicAI\                   # Główny projekt
│   ├── .github\                      # Tylko desktop CI
│   │   └── workflows\
│   │       └── desktop-ci.yml
│   ├── .claude\                      # Per-project agents
│   ├── assets\
│   ├── core\                         # Logika
│   ├── data\                         # DB/repository
│   ├── services\                     # AI, metadata, playback, DJ
│   ├── ui\                           # PyQt6
│   ├── docs\                         # Living docs (desktop only)
│   ├── MEMORY\                       # Agent memory
│   ├── crew\                         # SZPIEG, PLAN, CHECKLIST
│   ├── tests\
│   ├── scripts\                      # Windows build/smoke
│   ├── main.py
│   ├── pyproject.toml
│   ├── README.md
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── ...
├── archives\                         # Stare/web remnants
└── ...

## Kluczowe zasady
- Tylko desktop Windows Python.
- Agenci zaczynają od README + memory + docs + crew specs.
- Living documentation + " must document identical\.
- Src-like layout (core/data/services/ui).
- D:\Claude jako canonical home.

Szczegóły w SZPIEG research + proposal.
