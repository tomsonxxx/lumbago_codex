$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Build: PyInstaller"
& .\.venv\Scripts\python -m PyInstaller .\pyinstaller.spec

$dist = Join-Path $root "dist\LumbagoMusicAI"
if (-not (Test-Path $dist)) {
  throw "Brak katalogu dist. Sprawdź wynik PyInstaller."
}

Write-Host "Bundle: fpcalc"
$fpcalc = Join-Path $root "tools\fpcalc.exe"
if (Test-Path $fpcalc) {
  Copy-Item $fpcalc $dist -Force
} else {
  Write-Host "Uwaga: fpcalc.exe nie znaleziony w tools/"
}

Write-Host "Portable ZIP"
$zipPath = Join-Path $root "dist\LumbagoMusicAI-portable.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$dist\*" -DestinationPath $zipPath

Write-Host "Gotowe: $zipPath"
