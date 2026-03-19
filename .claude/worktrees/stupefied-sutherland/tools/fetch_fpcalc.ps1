$ErrorActionPreference = "Stop"

$tools = $PSScriptRoot
$dest = Join-Path $tools "fpcalc.exe"

if (Test-Path $dest) {
  Write-Host "fpcalc.exe już istnieje w tools/."
  exit 0
}

$api = "https://api.github.com/repos/acoustid/chromaprint/releases/latest"
$release = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "LumbagoMusicAI" }
$assets = $release.assets

$asset = $assets | Where-Object { $_.name -match "fpcalc" -and $_.name -match "win" } | Select-Object -First 1
if (-not $asset) {
  $asset = $assets | Where-Object { $_.name -match "win" -and $_.name -match "x64" } | Select-Object -First 1
}
if (-not $asset) {
  throw "Nie znaleziono paczki z fpcalc dla Windows w release."
}

$tempDir = Join-Path $env:TEMP "fpcalc_download"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
$zipPath = Join-Path $tempDir $asset.name

Write-Host "Pobieranie: $($asset.browser_download_url)"
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath

if ($zipPath -like "*.zip") {
  Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
}

$found = Get-ChildItem -Recurse -Path $tempDir -Filter fpcalc.exe | Select-Object -First 1
if (-not $found) {
  throw "fpcalc.exe nie znaleziony w pobranej paczce."
}

Copy-Item $found.FullName $dest -Force
Write-Host "Zapisano: $dest"
