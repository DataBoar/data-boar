#Requires -Version 5.1
<#
.SYNOPSIS
  Run snmp-LAB-ROUTER-01-lab-probe.ps1 and append output to a local log.
#>
param(
    [string] $RepoRoot = "",
    [string] $WslDistro = "",
    [string] $EnvFile = "",
    [string] $LogDir = "",
    [int] $MaxLines = 0
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}
if (-not $EnvFile) {
    $EnvFile = Join-Path $RepoRoot "docs\private\homelab\.env.snmp.local"
}
if (-not $LogDir) {
    $LogDir = Join-Path $RepoRoot "docs\private\homelab\reports"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (Test-Path -LiteralPath $EnvFile) {
    Get-Content -LiteralPath $EnvFile |
        Where-Object { $_ -and $_ -notmatch '^\s*#' } |
        ForEach-Object {
            $pair = $_ -split '=', 2
            if ($pair.Count -eq 2) {
                Set-Item -Path ("Env:{0}" -f $pair[0].Trim()) -Value $pair[1].Trim().Trim('"')
            }
        }
} else {
    $template = Join-Path $RepoRoot "docs\private.example\homelab\env.snmp.local.example"
    Write-Warning ("Env file not found: {0}. Create from template: {1}" -f $EnvFile, $template)
}

$required = @(
    "LAB_LAB-ROUTER-01_SNMP_HOST",
    "LAB_LAB-ROUTER-01_SNMP_V3_USER",
    "LAB_LAB-ROUTER-01_SNMP_AUTH_PASS",
    "LAB_LAB-ROUTER-01_SNMP_PRIV_PASS"
)

$missing = @()
foreach ($k in $required) {
    $v = [Environment]::GetEnvironmentVariable($k, "Process")
    if (-not $v) { $missing += $k }
}

if ($missing.Count -gt 0) {
    Write-Warning ("Missing env vars: {0}. Fix EnvFile: {1}" -f ($missing -join ", "), $EnvFile)
    exit 2
}

$logName = "snmp_LAB-ROUTER-01_probe_$(Get-Date -Format 'yyyyMMdd').log"
$logPath = Join-Path $LogDir $logName
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
$envLabel = if (Test-Path -LiteralPath $EnvFile) { Split-Path -Leaf $EnvFile } else { "(none)" }
$wslLabel = if ($WslDistro) { $WslDistro } else { "default" }

$header = @(
    ""
    "================================================================================"
    ("{0}  snmp-LAB-ROUTER-01-lab-probe  env={1}  WSL={2}" -f $stamp, $envLabel, $wslLabel)
    "================================================================================"
) -join [Environment]::NewLine

Add-Content -LiteralPath $logPath -Value $header -Encoding utf8

try {
    $probeParams = @{}
    if ($WslDistro) { $probeParams["WslDistro"] = $WslDistro }
    if (Test-Path -LiteralPath $EnvFile) { $probeParams["EnvFile"] = $EnvFile }
    $output = & "$PSScriptRoot\snmp-LAB-ROUTER-01-lab-probe.ps1" @probeParams 2>&1
    $exitCode = $LASTEXITCODE
} catch {
    Add-Content -LiteralPath $logPath -Value ("FATAL: {0}" -f $_.Exception.Message) -Encoding utf8
    exit 1
}

$lines = @($output | ForEach-Object { $_.ToString() })
if ($MaxLines -gt 0 -and $lines.Count -gt $MaxLines) {
    $lines[0..($MaxLines - 1)] | ForEach-Object { Add-Content -LiteralPath $logPath -Value $_ -Encoding utf8 }
    Add-Content -LiteralPath $logPath -Value "" -Encoding utf8
    Add-Content -LiteralPath $logPath -Value ("...(truncated: {0} lines total; increase -MaxLines or use 0 for full)..." -f $lines.Count) -Encoding utf8
} else {
    $lines | ForEach-Object { Add-Content -LiteralPath $logPath -Value $_ -Encoding utf8 }
}

Add-Content -LiteralPath $logPath -Value ("exit_code={0}" -f $exitCode) -Encoding utf8
Add-Content -LiteralPath $logPath -Value "" -Encoding utf8

Write-Host ("Wrote log: {0}  (exit={1})" -f $logPath, $exitCode)
exit $exitCode
