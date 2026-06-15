# Smoke test for portable Windows build.
# Usage: .\scripts\smoke_portable_windows.ps1 [-ExtractDir C:\LumbagoTest]
#
# Per SZPIEG research 2026-06-15 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC videolan.org' + portable note, no silent, graceful FILE vs STREAM, diagnostics, EFFECT, booth) — must document identical.
# Etap4: smoke is audio-agnostic (SAFE_MODE); real reliability tested in Odtwarzacz (engine.get_backend_info shows fallback, status '⚠' + guidance if no VLC). User note: for full audio after portable extract, install VLC or place portable next to exe + restart.

param(
    [string]$ExtractDir = (Join-Path $env:TEMP "LumbagoSmokeTest")
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$zipPath = Join-Path $repoRoot "dist\LumbagoMusicAI-portable.zip"

if (-not (Test-Path $zipPath)) {
    throw "Missing artifact. Run scripts\build_portable_windows.ps1 first."
}

if (Test-Path $ExtractDir) {
    Remove-Item $ExtractDir -Recurse -Force
}
New-Item -ItemType Directory -Path $ExtractDir | Out-Null

Write-Host "Extracting to $ExtractDir"
Expand-Archive -Path $zipPath -DestinationPath $ExtractDir -Force

$exe = Join-Path $ExtractDir "LumbagoMusicAI.exe"
if (-not (Test-Path $exe)) {
    throw "Executable not found: $exe"
}

$env:LUMBAGO_SAFE_MODE = "1"
$env:LUMBAGO_SMOKE_SECONDS = "3"

Write-Host "Running smoke: $exe"
$p = Start-Process -FilePath $exe -PassThru -Wait
if ($p.ExitCode -ne 0) {
    throw "Smoke failed with exit code $($p.ExitCode)"
}

Write-Host "Smoke OK"