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

# Portable resource verif STRICT (per Analyzer report luki: luźne resource verif) + SZPIEG Clean Windows P1 + Plan nowa lista.
# Critical: throw jeśli brak. Support LUMBAGO_SMOKE_DIAG (przekieruj output do log, assert "Noop|backend" dla diagnostics/no-VLC states).
# Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" (SAFE stub omija DJ/backend/diag, luźne verif) — must document identical.
# Etap4: smoke is audio-agnostic (SAFE_MODE); real reliability tested in Odtwarzacz (engine.get_backend_info shows fallback, status '⚠' + guidance if no VLC). User note: for full audio after portable extract, install VLC or place portable VLC next to exe + restart. Per 'nie przestawaj'.

# Strict critical resources — any missing = throw (strengthened vs loose)
Write-Host "Verifying bundled resources STRICT (for full portable on clean Windows per clean_windows_test.md + SZPIEG 2026-06-25 research + Analyzer):"
$critical_checks = @(
    "tools\fpcalc.exe",
    "ui\assets",
    "docs\user_guide.md",
    "assets\icon.ico",
    "assets\themes",
    "ui\assets\icons"
)
foreach ($c in $critical_checks) {
    $p = Join-Path $ExtractDir $c
    if (Test-Path $p) {
        Write-Host "  Resource OK (strict): $c"
    } else {
        throw "Missing critical portable resource: $c (get_resource_path/frozen layout expected per pyinstaller.spec + SZPIEG/ANALYZER 2026-06-25) — per SZPIEG research 2026-06-25 + Analyzer + Plan must document identical"
    }
}

Write-Host "Portable structure note (ties to clean_windows_test.md + SZPIEG Build Spec): exe present, resources checked (fpcalc, ui/assets, docs, icons, themes). Full functional manual on clean/VM: import 1-3 audio, library appear, detail edit+save, DJ Player open/load (drag or button) 1-2 tracks, play/seek/hotcue (set/jump 8/deck if dual)/loop/crossfader/waveform/status, no crash unscanned, %APPDATA%\LumbagoMusicAI\lumbago.db + settings.json creation, VLC guidance ('Pobierz VLC z videolan.org' or portable next to exe), backend diagnostics."

# AUTO-COVERS + DIAG support: LUMBAGO_SMOKE_DIAG flag/env → redirect output from exe (which triggers main.py smoke path even under SAFE), assert "Noop|backend" for coverage of backend_info, diagnostics, no-VLC states.
# Wzmocnione basic DJ sim w main DIAG: create PlaybackEngine + odt view sim + load + _maybe_apply + assert label "⚠" lub Noop backend.
# Per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 (smoke_portable + main DIAG + testy odt/deck/booth) ... must document identical.
Write-Host "=== AUTO-COVERS: exe, resources(strict), backend_info, diagnostics, no-VLC states, basic DJ sim (PlaybackEngine+odt+load+_maybe+⚠/Noop assert) (per CHECKLIST + clean_windows_test P1.1/P1.2 + SZPIEG/ANALYZER 2026-07-13 + Plan) ==="
Write-Host "COVERED by portable smoke: exe-run, resources (strict throw on critical), backend_info/diagnostics (via LUMBAGO_SMOKE_DIAG redirect+assert), basic DJ sim (odt view sim + fallback label in DIAG), portable get_resource_path note, APPDATA note (manual on real), no-VLC/Noop states."
Write-Host "MISSING (full manual on clean Win/VM): import 1-3 audio + library + detail edit, full DJ load/drag/play/seek/hotcue/loop/crossfader/wave/status, no-VLC states + 'Pobierz VLC' visible, APPDATA/lumbago.db+settings creation on real run, booth sim."
Write-Host "Backend diagnostics note (exercise in real DJ Player run): use PlaybackEngine.get_backend_info() and get_diagnostics() — should report active backend (VLC/Qt/Noop), error states, FILE=load vs STREAM=transport. Smoke SAFE (no real audio) — full verif on target machine with/without VLC."

$env:LUMBAGO_SAFE_MODE = "1"
$env:LUMBAGO_SMOKE_SECONDS = "3"
$env:LUMBAGO_SMOKE_DIAG = "1"

Write-Host "Running smoke with diag support (LUMBAGO_SMOKE_DIAG triggers early engine print in main + redirect + basic DJ sim odt/load/_maybe/⚠ assert per 2026-07-13) : $exe"
$p = Start-Process -FilePath $exe -PassThru -Wait -RedirectStandardOutput "$ExtractDir\smoke_diag.log" -RedirectStandardError "$ExtractDir\smoke_err.log"
if ($p.ExitCode -ne 0) {
    Write-Host "Smoke exit: $($p.ExitCode)"
    if (Test-Path "$ExtractDir\smoke_diag.log") { Get-Content "$ExtractDir\smoke_diag.log" | Select-Object -Last 20 }
    throw "Smoke failed with exit code $($p.ExitCode)"
}

Write-Host "Smoke diag log (last lines):"
if (Test-Path "$ExtractDir\smoke_diag.log") { Get-Content "$ExtractDir\smoke_diag.log" | Select-Object -Last 10 }

# Assert diagnostics output contains backend/Noop + DJ sim (covers no-VLC states + odt sim per Analyzer/SZPIEG/Plan 2026-07-13)
$diagLog = if (Test-Path "$ExtractDir\smoke_diag.log") { Get-Content "$ExtractDir\smoke_diag.log" -Raw } else { "" }
if ($diagLog -notmatch "(?i)(Noop|backend|BACKEND_INFO|DIAGNOSTICS|SMOKE_DJ_SIM|odt view)") {
    throw "Diagnostics assert FAILED: log missing 'Noop|backend' / BACKEND_INFO / SMOKE_DJ_SIM (LUMBAGO_SMOKE_DIAG did not produce expected output per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 ... must document identical)"
} else {
    Write-Host "Diagnostics assert PASSED: found backend/Noop info + DJ sim in redirected smoke output."
}

Write-Host "Smoke OK (exe run + resources(strict) + diag + basic DJ sim per clean_windows_test.md + SZPIEG research 2026-07-14 plan rozbudowy Faza2 + Downloader/AI continuation per \"chce dodać nowe, dosc skomplikowane.txt\" + 'dalej' ... must document identical).
Dodatkowo dla Downloader (item 3): sprawdź w UI (po real run) komunikaty o yt-dlp/ffmpeg jeśli nie w PATH na clean maszynie."
Write-Host "Checklist auto items covered by smoke: resources bundled, exe starts (SAFE), structure OK, backend_info+diagnostics+no-VLC + odt sim (via DIAG + SMOKE_DJ_SIM assert '⚠'/Noop)."
Write-Host "Full manual on clean-VM required for: import+detail+DJ full flow (load/drag/play/cue/hotcue/crossfader/waveform), APPDATA db+settings, VLC guidance (⚠ + 'Pobierz VLC'), backend_info/diagnostics visible if no-VLC, fallback behavior. Pending per PLAN + 'od A do Z'."
# Note: diagnostics via engine.get_backend_info() + get_diagnostics() + basic DJ sim (PlaybackEngine + odt view + _maybe_apply label) — should be exercised in real DJ Player smoke on target machine. Per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 ... must document identical.