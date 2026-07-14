# Build portable Windows artifact for clean-machine smoke tests.
# Usage: .\scripts\build_portable_windows.ps1
#
# Per SZPIEG research 2026-06-15 Clean Windows P1 closure (full coverage of docs/clean_windows_test.md in portable smoke + scripts, note VM pending) + Duplicate Finder dopinanie to the absolute last detail (tests for staged/Etapowo/fp + match_method labels, merge on fp groups, any remaining UI/guards, no silent errors) + manual punkt 4 + full CHECKLIST closure with all auto-verifiable parts + status updates + Etap4 playback reliability + finalny efekt końcowy (VLC prio, visible '⚠ Audio niedostępne' + 'Pobierz VLC z videolan.org', diagnostics, targeted updates, file=load vs stream=transport, guards, EFFECT, booth-visible states, portable notes) - must document identical.
# Etap4 Build Spec step 8: include VLC guidance note for users (install or unpack portable VLC next to exe for full DJ features; otherwise Qt fallback for wave/cue/preview (FILE) but limited audio (STREAM)). Smoke will still pass (LUMBAGO_SAFE). Status + guidance shown in Odtwarzacz + Ustawienia > Audio tab. Per 'nie przestawaj'.

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
Write-Host "=== AUTO-COVERS: exe, resources(strict), backend_info, diagnostics, no-VLC states (per smoke/build + SZPIEG/ANALYZER/Plan 2026-06-25) ==="
Write-Host "Portable artifact for clean Windows P1 + Downloader (item 3 Nowa lista) (per docs/clean_windows_test.md + SZPIEG research 2026-07-14 plan rozbudowy Faza3 Packaging/CI + Faza4 Downloader/AI completion per \"chce dodać nowe, dosc skomplikowane.txt\" + 'dalej az do ukonczenia wszystkich faz' ... must document identical).
Dla Downloader na czystym Win: po unpack zainstaluj pip install yt-dlp i ffmpeg w PATH. UI pokazuje czytelne ostrzeżenia. Test detekcji + est + graceful bez narzędzi.
Full manual large playlists + clean-VM pending. Faza3-5 local gotowe per 'dalej az...'. Nie przestawaj."