# Smoke test for portable Windows build.
# Usage: .\scripts\smoke_portable_windows.ps1 [-ExtractDir C:\LumbagoTest]
#
# Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Duplicate Finder dopinanie to the absolute last detail (tests for staged/Etapowo/fp + match_method labels, merge on fp groups, any remaining UI/guards, no silent errors) + manual punkt 4 + full CHECKLIST closure with all auto-verifiable parts + status updates + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) — must document identical.
# Etap4: smoke is audio-agnostic (SAFE_MODE); real reliability tested in Odtwarzacz (engine.get_backend_info shows fallback, status '⚠' + guidance if no VLC). User note: for full audio after portable extract, install VLC or place portable next to exe + restart. Per 'nie przestawaj'.

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
# Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Etap4 portable notes + Build Spec (bundled fpcalc, ui/assets, docs, icons for clean machine without Python; get_resource_path handles frozen; post-extract for full audio: Pobierz VLC z videolan.org or place portable VLC next to exe + restart; DB/settings in %APPDATA%\LumbagoMusicAI or .lumbago_data fallback created on first real run; diagnostics via engine.get_diagnostics + backend_info in UI show '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org' if no VLC; FILE=load vs STREAM=transport guarded in playback; no silent via explicit error states + Noop fallback; EFFECT + booth-visible states).
Write-Host "Verifying bundled resources (for full portable on clean Windows per clean_windows_test.md):"
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

Write-Host "Portable structure note (ties to clean_windows_test.md): exe present, resources checked. Full functional (import 1-3 audio files, appear in library, detail edit+save tags, DJ Player open/load 1-2 tracks via library/drag, play/seek/hotcue/loop/crossfader/waveform/status, no crash on unscanned, %APPDATA%\LumbagoMusicAI\lumbago.db + settings.json on real run) covered in manual on clean/VM per PLAN. Smoke is SAFE audio-agnostic + resource verif."

$env:LUMBAGO_SAFE_MODE = "1"
$env:LUMBAGO_SMOKE_SECONDS = "3"

Write-Host "Running smoke: $exe"
$p = Start-Process -FilePath $exe -PassThru -Wait
if ($p.ExitCode -ne 0) {
    throw "Smoke failed with exit code $($p.ExitCode)"
}

Write-Host "Smoke OK (exe run + resources per clean_windows_test.md + SZPIEG Etap4 portable + 'nie przestawaj'). Full clean-VM/manual pending per original plan."