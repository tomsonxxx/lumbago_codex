# manual_win_dj_checklist_helper.ps1
# Helper do ręcznego testu DJ Player + clean Windows (per Szpieg research 2026-07-13 + Plan "nowa lista" + CHECKLIST)
# Uruchom na czystym Windows (fresh profile, portable ZIP rozpakowany lub dev).
# Per SZPIEG research 2026-07-13 co-dalej manual checklist + clean Win + "nie przestawaj" + must document identical.

param(
    [string]$ExePath = ".\LumbagoMusicAI.exe",
    [int]$SmokeSeconds = 3
)

Write-Host "=== LUMBAGO DJ PLAYER MANUAL CHECKLIST HELPER (2026-07-13) ===" -ForegroundColor Cyan
Write-Host "Per SZPIEG research 2026-07-13 + Plan + CHECKLIST + must document identical" 
Write-Host "Kroki: smoke -> DJ full flow (Single/Compact/Dual) -> sizes/visual -> fallback no-VLC -> booth sim -> raport"
Write-Host ""

# 1. Smoke / backend info
Write-Host "[1/10] Smoke + Backend Info (uruchom z LUMBAGO_SMOKE_DIAG jeśli python)" -ForegroundColor Yellow
if (Test-Path $ExePath) {
    Write-Host "Exe znaleziony: $ExePath"
    # Jeśli dev: python -c z engine (dla user z python)
    Write-Host "Zalecane: `$env:LUMBAGO_SMOKE_DIAG=1; & '$ExePath'  (lub python main.py)"
} else {
    Write-Host "UWAGA: exe nie znaleziony w $ExePath - użyj python lub podaj ścieżkę"
}
Write-Host "Sprawdź output: get_backend_info() → _NoopAudioBackend lub VLC"
Write-Host "Oczekiwany: prominent banner '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org'"
Write-Host ""

Read-Host "Naciśnij Enter po sprawdzeniu smoke + backend_info (zrób screenshot)"

# 2-4 Single
Write-Host "[2/10] Single Odtwarzacz - Waveform + BPM + transport" -ForegroundColor Yellow
Write-Host "Otwórz Single (domyślny). Załaduj utwór (drag lub Load)."
Write-Host "Wymagania (z CHECKLIST + Szpieg Build Spec):"
Write-Host "  - Waveform ≥220px wysokości (dużo air, brak zachodzenia)"
Write-Host "  - BPM duży ≥30px, gruby, czytelny"
Write-Host "  - Duży playhead + BPM-aware beatgrid"
Write-Host "  - Duże btn transport (PLAY/CUE/STOP)"
Write-Host "Sprawdź resize (dynamic, air zachowany)"
Read-Host "Enter po weryfikacji Single sizes + air + transport"

# 5 Compact advanced
Write-Host "[5/10] Compact pilot advanced (always-on-top + shrink + rapid)" -ForegroundColor Yellow
Write-Host "Toggle Compact. Sprawdź:"
Write-Host "  - minSize ~420x300, reduce empty bottom"
Write-Host "  - StaysOnTopHint (inne okna pod spodem, floating/pilot)"
Write-Host "  - Spin rotuje (cos/sin) tylko gdy playing"
Write-Host "  - Rapid toggle + play + drag + resize (bez crash/reentr)"
Write-Host "  - Test z innymi oknami + highDPI jeśli możliwe"
Read-Host "Enter po Compact always-on-top + rapid + spin + sizes"

# 6 EFFECT + drag + file/stream
Write-Host "[6/10] EFFECT tooltips + Drag safety + FILE vs STREAM" -ForegroundColor Yellow
Write-Host "Na każdym elemencie (wave, btn, status, compact): tooltip 'EFEKT: ...' (1-2 zd)"
Write-Host "Drag z biblioteki: highlight, load, safety prompt jeśli playing ('Trwa odtwarzanie (stream). Załaduj nowy PLIK?')"
Write-Host "FILE = load/preview ; STREAM = transport/play/cue/seek"
Read-Host "Enter po EFFECT + drag + file/stream clar"

# 7 Dual
Write-Host "[7/10] Dual Console" -ForegroundColor Yellow
Write-Host "Przełącz Dual. Sprawdź:"
Write-Host "  - Oba decki A/B"
Write-Host "  - Crossfader min 280px szeroki, wyraźny"
Write-Host "  - EQ/pitch czytelne"
Write-Host "  - 8 hotcue na deck"
Write-Host "  - Master/HP Cue/PFL + crossfader działa (audio + wizualnie)"
Read-Host "Enter po Dual cross + hotcues + EQ + PFL"

# 8 Hotcue / persist / shortcuts
Write-Host "[8/10] Hotcue (8/deck), Memory, SYNC, shortcuts, persist" -ForegroundColor Yellow
Write-Host "Set hotcue (Shift+click lub btn), jump, delete. Restart app → persist."
Write-Host "SYNC/Quantize/KEY/pitch nie psują wave/hotcue."
Write-Host "Skróty: Spacja=play/pause, Ctrl+1..8=hotcue"
Read-Host "Enter po hotcue + persist + skróty"

# 9 Booth sim + readability
Write-Host "[9/10] Booth symulacja (1m low light high-contrast air)" -ForegroundColor Yellow
Write-Host "Zmniejsz jasność ekranu. Oddal się ~1m."
Write-Host "Sprawdź: duże pady/BPM/wave/crossfader wyraźne, brak 'za gęsto'/zachodzenia, high-contrast air."
Write-Host "Test z/ bez VLC (odinstaluj → restart → visible exact '⚠ Audio niedostępne...' + diag btn)"
Read-Host "Enter po booth sim + no-VLC visible warning"

# 10 APPDATA + full flow + raport
Write-Host "[10/10] APPDATA + full clean flow + raport" -ForegroundColor Yellow
Write-Host "Sprawdź %APPDATA%\LumbagoMusicAI : lumbago.db + settings.json"
Write-Host "Import 1-3 plików, detail edit, DJ full flow."
Write-Host ""
Write-Host "=== RAPORT (skopiuj i uzupełnij) ==="
Write-Host "Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host "Env: clean Win / VM ?  VLC: tak/nie"
Write-Host "Single waveform/BPM/air: OK / issues"
Write-Host "Compact always-on-top/shrink/rapid/spin: OK / issues"
Write-Host "Dual cross >=280 / hotcues / EQ: OK / issues"
Write-Host "EFFECT tooltips + file/stream: OK / issues"
Write-Host "no-VLC banner visible (compact/highDPI/normal): OK / issues"
Write-Host "Booth 1m low-light readability: OK / issues"
Write-Host "APPDATA + import + detail + drag: OK / issues"
Write-Host "Backend: $(if (Test-Path $ExePath) { 'check get_backend_info' })"
Write-Host "Screenshots: [lista]"
Write-Host "Uwagi: "
Write-Host "Per SZPIEG research 2026-07-13 co-dalej manual checklist + clean Win... must document identical"
Write-Host "Zaktualizuj crew/CHECKLIST [x] + docs po teście."
Write-Host ""

Write-Host "=== KONIEC HELPERA - zamknij app, zrób raport, aktualizuj checklist/docs ===" -ForegroundColor Green
Write-Host "Następnie: 'dalej' lub raport do zespołu. Nie przestawaj."