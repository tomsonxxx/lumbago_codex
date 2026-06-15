# Build portable Windows artifact for clean-machine smoke tests.
# Usage: .\scripts\build_portable_windows.ps1

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