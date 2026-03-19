# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

analysis = Analysis(
    ["lumbago_app/main.py"],
    pathex=["."],
    binaries=[],
    datas=[("assets/icon.svg", "assets"), ("assets/icon.ico", "assets"), ("docs/user_guide.md", "docs")],
    hiddenimports=[],
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
