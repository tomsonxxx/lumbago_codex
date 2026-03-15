# setup-ai-keys.ps1
# Interaktywny konfigurator kluczy + testy

function Read-Secret([string]$label) {
    Write-Host "`n$label" -ForegroundColor Cyan
    $secure = Read-Host -AsSecureString "Podaj klucz (wejście ukryte)"
    return $secure
}

function SecureToPlain([Security.SecureString]$secure) {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Set-EnvTemp([string]$name, [string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return }
    Set-Item -Path ("Env:{0}" -f $name) -Value $value
}

function Local-Validate([string]$label, [string]$value) {
    $issues = @()
    if ([string]::IsNullOrWhiteSpace($value)) { $issues += "pusty" }
    if ($value -match "\s") { $issues += "zawiera spacje" }
    if ($value.Length -lt 20) { $issues += "podejrzanie krótki" }
    $ok = $issues.Count -eq 0
    [pscustomobject]@{ Label = $label; Ok = $ok; Issues = ($issues -join ", ") }
}

function Prompt-Test([string]$label, [string]$key) {
    Write-Host "`nTest zdalny dla: $label" -ForegroundColor Yellow
    $url = Read-Host "URL testu (Enter = pomiń)"
    if ([string]::IsNullOrWhiteSpace($url)) {
        return [pscustomobject]@{ Label = $label; RemoteTest = "pominięty"; Status = "-" }
    }
    $headerName = Read-Host "Nazwa nagłówka (Enter = brak)"
    $headerValueTemplate = ""
    if (-not [string]::IsNullOrWhiteSpace($headerName)) {
        $headerValueTemplate = Read-Host "Wartość nagłówka (użyj {key})"
        if ([string]::IsNullOrWhiteSpace($headerValueTemplate)) { $headerValueTemplate = "{key}" }
    }
    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($headerName)) {
        $headers[$headerName] = $headerValueTemplate.Replace("{key}", $key)
    }

    try {
        $resp = Invoke-WebRequest -Uri $url -Method Get -Headers $headers -TimeoutSec 20 -ErrorAction Stop
        return [pscustomobject]@{ Label = $label; RemoteTest = "OK"; Status = $resp.StatusCode }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if (-not $code) { $code = "Błąd połączenia" }
        return [pscustomobject]@{ Label = $label; RemoteTest = "BŁĄD"; Status = $code }
    }
}

# --- Pobranie kluczy ---
$grokSecure = Read-Secret "GROK (xAI)"
$deepseekSecure = Read-Secret "DEEPSEEK"
$geminiSecure = Read-Secret "GEMINI"

$grok = SecureToPlain $grokSecure
$deepseek = SecureToPlain $deepseekSecure
$gemini = SecureToPlain $geminiSecure

# --- Ustawienie w bieżącej sesji ---
Set-EnvTemp -name "GROK_API_KEY" -value $grok
Set-EnvTemp -name "DEEPSEEK_API_KEY" -value $deepseek
Set-EnvTemp -name "GEMINI_API_KEY" -value $gemini

# --- Ustawienie na stałe (setx) ---
if (-not [string]::IsNullOrWhiteSpace($grok)) { setx GROK_API_KEY "$grok" | Out-Null }
if (-not [string]::IsNullOrWhiteSpace($deepseek)) { setx DEEPSEEK_API_KEY "$deepseek" | Out-Null }
if (-not [string]::IsNullOrWhiteSpace($gemini)) { setx GEMINI_API_KEY "$gemini" | Out-Null }

# --- Walidacja lokalna ---
$localChecks = @(
    Local-Validate "GROK" $grok
    Local-Validate "DEEPSEEK" $deepseek
    Local-Validate "GEMINI" $gemini
)

# --- Testy zdalne (opcjonalne) ---
$remoteChecks = @(
    Prompt-Test "GROK" $grok
    Prompt-Test "DEEPSEEK" $deepseek
    Prompt-Test "GEMINI" $gemini
)

# --- Raport ---
Write-Host "`n=== RAPORT ===" -ForegroundColor Green
Write-Host "Sesyjne zmienne środowiskowe ustawione: GROK_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY"
Write-Host "Stałe zmienne środowiskowe ustawione przez setx (wejdą w życie po nowym uruchomieniu terminala)." -ForegroundColor DarkYellow

Write-Host "`nWalidacja lokalna:" -ForegroundColor Cyan
$localChecks | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "Testy zdalne:" -ForegroundColor Cyan
$remoteChecks | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "Uwaga: setx zapisuje zmienne na stałe, ale nie aktualizuje już otwartych terminali." -ForegroundColor DarkYellow
