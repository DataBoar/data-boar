#Requires -Version 5.1
# Load KEY=VALUE env file and GET LAB-ROUTER-01 Network integration /sites (HTTP status only; no secret in output).
param(
    [string] $EnvFile = ""
)

$ErrorActionPreference = "Stop"

if (-not $EnvFile) {
    $repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
    $EnvFile = Join-Path $repoRoot "docs\private\homelab\.env.api.LAB-ROUTER-01-se.local"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Error "Env file not found: $EnvFile"
    exit 2
}

Get-Content -LiteralPath $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $k = $line.Substring(0, $idx).Trim()
    $v = $line.Substring($idx + 1).Trim()
    [Environment]::SetEnvironmentVariable($k, $v, "Process")
}

$base = ([Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_BASE_URL", "Process")).TrimEnd("/")
$pth = [Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_SITES_PATH", "Process")
$apiKey = [Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_KEY", "Process")
$accept = [Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_ACCEPT", "Process")

if (-not $base -or -not $pth -or -not $apiKey) {
    Write-Error "Missing LAB_LAB-ROUTER-01_API_BASE_URL, LAB_LAB-ROUTER-01_API_SITES_PATH, or LAB_LAB-ROUTER-01_API_KEY in env file."
    exit 2
}

$url = $base + $pth
$code = & curl.exe -s -o NUL -w "%{http_code}" -H "X-API-KEY: $apiKey" -H "Accept: $accept" $url
Write-Host "HTTP status: $code"

if ($code -ne "200") {
    exit 1
}
