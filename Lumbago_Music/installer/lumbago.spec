# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec dla Lumbago Music AI
Uruchom: pyinstaller installer/lumbago.spec
"""

import sys
from pathlib import Path

project_root = Path(SPECPATH).parent

block_cipher = None

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[
        # ffmpeg
        (str(project_root / 'bundled' / 'ffmpeg' / 'ffmpeg.exe'), 'bundled/ffmpeg'),
        (str(project_root / 'bundled' / 'ffmpeg' / 'ffprobe.exe'), 'bundled/ffmpeg'),
        # fpcalc
        (str(project_root / 'bundled' / 'fpcalc' / 'fpcalc.exe'), 'bundled/fpcalc'),
    ],
    datas=[
        (str(project_root / 'assets'), 'assets'),
        (str(project_root / '.env.example'), '.'),
    ],
    hiddenimports=[
        'lumbago_app',
        'lumbago_app.ui.themes.cyber_neon',
        'lumbago_app.ui.themes.fluent_dark',
        'lumbago_app.services.ai.providers.openai_provider',
        'lumbago_app.services.ai.providers.claude_provider',
        'lumbago_app.services.ai.providers.gemini_provider',
        'lumbago_app.services.ai.providers.grok_provider',
        'lumbago_app.services.ai.providers.deepseek_provider',
        'sqlalchemy.dialects.sqlite',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'notebook', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LumbagoMusic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app — bez konsoli
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icons' / 'lumbago.ico'),
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LumbagoMusic',
)
