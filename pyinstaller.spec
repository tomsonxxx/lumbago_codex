# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for LumbagoMusicAI (PyQt6 desktop, onedir + portable ZIP).

Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Duplicate Finder dopinanie to the absolute last detail (tests for staged/Etapowo/fp + match_method labels, merge on fp groups, any remaining UI/guards, no silent errors) + manual punkt 4 + full CHECKLIST closure with all auto-verifiable parts + status updates + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical.

Per "Test na czystym Windows (PyInstaller build)" P1 (root Checklist.md) + Plan "nowa lista" step 3:
- Bundle all runtime resources so EXE works on fresh Windows (no Python, no dev deps).
- fpcalc for AcoustID/recognition.
- ui/assets for dialog icons etc.
- docs for user_guide.
- Safe hiddenimports for deps that may not be auto-detected (SQLAlchemy, mutagen, rapidfuzz, PyQt6 plugins, analysis libs).
- onedir preferred (large deps like librosa/numpy/PyQt6).

After build: dist/LumbagoMusicAI/ contains exe + all datas next to it.
Use with scripts/make_portable.ps1 or CI to create -portable.zip for clean test per docs/clean_windows_test.md.

Frozen path resolution is now handled via core.config.get_resource_path (step 2 fix).
Per 'nie przestawaj'.
"""

block_cipher = None

analysis = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[("tools/fpcalc.exe", "tools")],
    datas=[
        ("assets/icon.svg", "assets"),
        ("assets/icon.ico", "assets"),
        ("assets/themes", "assets/themes"),
        ("docs/user_guide.md", "docs"),
        ("ui/assets", "ui/assets"),
        ("tools/fpcalc.exe", "tools"),
    ],
    hiddenimports=[
        "sqlalchemy.dialects.sqlite",
        "mutagen",
        "mutagen.*",
        "rapidfuzz",
        "librosa",
        "numpy",
        "scipy",
        "soundfile",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimedia.*",
        "vlc",  # optional, graceful fallback
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="LumbagoMusicAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    name="LumbagoMusicAI",
)
