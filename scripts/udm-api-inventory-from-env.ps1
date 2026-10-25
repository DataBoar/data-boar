#Requires -Version 5.1
# Read-only inventory via Network Integration API: sites + devices (+ clients if available).
# Loads secrets from docs/private/homelab/.env.api.LAB-ROUTER-01-se.local  - does not echo API key.
# Output: summary to stdout; optional JSON under docs/private/homelab/reports/ (gitignored).
param(
    [string] $EnvFile = "",
    [switch] $SaveJson
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
$apiKey = [Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_KEY", "Process")
$accept = [Environment]::GetEnvironmentVariable("LAB_LAB-ROUTER-01_API_ACCEPT", "Process")

if (-not $base -or -not $apiKey) {
    Write-Error "Missing LAB_LAB-ROUTER-01_API_BASE_URL or LAB_LAB-ROUTER-01_API_KEY in env file."
    exit 2
}

$headers = @{
    "X-API-KEY" = $apiKey
    "Accept"    = $accept
}

function Invoke-LAB-ROUTER-01Get([string] $RelativePath) {
    $uri = $base + $RelativePath
    try {
        return Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
    } catch {
        Write-Host ("GET failed: {0} -> {1}" -f $RelativePath, $_.Exception.Message) -ForegroundColor Yellow
        return $null
    }
}

Write-Host "=== LAB-ROUTER-01 API inventory (read-only) ===" -ForegroundColor Cyan

$sitesResp = Invoke-LAB-ROUTER-01Get "/proxy/network/integration/v1/sites"
if (-not $sitesResp -or -not $sitesResp.data) {
    Write-Error "Could not read sites."
    exit 1
}

$siteCount = @($sitesResp.data).Count
Write-Host ("Sites: {0}" -f $siteCount)

$firstSite = $sitesResp.data[0]
$siteId = $firstSite.id
$siteName = $firstSite.name
Write-Host ("Using site: {0} ({1})" -f $siteName, $siteId)

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "docs\private\homelab\reports"
if ($SaveJson) {
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}

$devicesPath = "/proxy/network/integration/v1/sites/$siteId/devices"
$devResp = Invoke-LAB-ROUTER-01Get $devicesPath

if ($devResp -and $devResp.data) {
    $rows = @($devResp.data)
    Write-Host ("Devices: {0}" -f $rows.Count)
    $byModel = @{}
    $byFw = @{}
    foreach ($d in $rows) {
        $m = $d.model
        if (-not $m) { $m = "(unknown)" }
        if (-not $byModel.ContainsKey($m)) { $byModel[$m] = 0 }
        $byModel[$m]++
        $fw = $d.firmwareVersion
        if (-not $fw) { $fw = $d.version; if (-not $fw) { $fw = "(unknown)" } }
        if (-not $byFw.ContainsKey($fw)) { $byFw[$fw] = 0 }
        $byFw[$fw]++
    }
    Write-Host "Models (count):" -ForegroundColor Gray
    $byModel.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Key, $_.Value) }
    Write-Host "Firmware versions (count):" -ForegroundColor Gray
    $byFw.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Key, $_.Value) }
    if ($SaveJson) {
        $out = Join-Path $reportDir "LAB-ROUTER-01_api_devices_$stamp.json"
        $devResp | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $out -Encoding utf8
        Write-Host ("Wrote: {0}" -f $out) -ForegroundColor Green
    }
} else {
    Write-Host "No device list or endpoint not available (check Network API / firmware)." -ForegroundColor Yellow
}

$clientsPath = "/proxy/network/integration/v1/sites/$siteId/clients"
$cliResp = Invoke-LAB-ROUTER-01Get $clientsPath

if ($cliResp -and $cliResp.data) {
    $c = @($cliResp.data).Count
    Write-Host ("Clients (current list): {0}" -f $c)
    if ($SaveJson) {
        $out = Join-Path $reportDir "LAB-ROUTER-01_api_clients_$stamp.json"
        $cliResp | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $out -Encoding utf8
        Write-Host ("Wrote: {0}" -f $out) -ForegroundColor Green
    }
} else {
    Write-Host "Clients endpoint not available or empty (normal on some versions)." -ForegroundColor DarkGray
}

Write-Host "Done." -ForegroundColor Cyan
