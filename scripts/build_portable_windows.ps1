# Build portable Windows artifact for clean-machine smoke tests.
# Usage: .\scripts\build_portable_windows.ps1
#
# Per SZPIEG research 2026-06-15 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC videolan.org' + portable note, no silent, graceful FILE vs STREAM, diagnostics, EFFECT, booth) — must document identical.
# Etap4 Build Spec step 8: include VLC guidance note for users (install or unpack portable VLC next to exe for full DJ features; otherwise Qt fallback for wave/cue/preview (FILE) but limited audio (STREAM)). Smoke will still pass (LUMBAGO_SAFE). Status + guidance shown in Odtwarzacz + Ustawienia > Audio tab.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Building PyInstaller bundle..."
pyinstaller pyinstaller.spec --noconfirm

$distDir = Join-Path (Get-Location) "dist\LumbagoMusicAI"
if (-not (Test-Path $distDir)) {
    throw "Build output not found: $distDir"
}

$zipPath = Join-Path (Get-Location) "dist\LumbagoMusicAI-portable.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Write-Host "Creating portable zip: $zipPath"
Compress-Archive -Path (Join-Path $distDir "*") -DestinationPath $zipPath -Force

Write-Host "Done. Artifact: $zipPath"