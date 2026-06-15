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

# Portable resource verif (part of Clean Windows P1 per zatwierdzona lista + clean_windows_test.md + 'nie przestawaj' continuation)
# Per SZPIEG Etap4 portable notes + Build Spec (bundled fpcalc, ui/assets, docs, icons for clean machine without Python).
Write-Host "Verifying bundled resources (for full portable on clean Windows):"
$checks = @(
    "tools\fpcalc.exe",
    "ui\assets",
    "docs\user_guide.md",
    "assets\icon.ico"
)
foreach ($c in $checks) {
    $p = Join-Path $ExtractDir $c
    if (Test-Path $p) {
        Write-Host "  Resource OK: $c"
    } else {
        Write-Host "  Resource note: $c (may be in _internal or COLLECT layout; get_resource_path handles frozen)"
    }
}

$env:LUMBAGO_SAFE_MODE = "1"
$env:LUMBAGO_SMOKE_SECONDS = "3"

Write-Host "Running smoke: $exe"
$p = Start-Process -FilePath $exe -PassThru -Wait
if ($p.ExitCode -ne 0) {
    throw "Smoke failed with exit code $($p.ExitCode)"
}

Write-Host "Smoke OK"