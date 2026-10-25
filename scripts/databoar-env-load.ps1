#Requires -Version 5.1
<#
.SYNOPSIS
    Load Data Boar runtime secrets from XDG-style config env files into the session.

.DESCRIPTION
    Product contract (stable): YAML *_from_env -> OS environment at process start.
    Vaults (Bitwarden CLI today; Phase B @vault: / enterprise vaults later) inject
    into that same env layer - they do not replace *_from_env in tracked YAML.

    Canonical dir (override with $env:DATA_BOAR_ENV_DIR):
      $env:USERPROFILE\.config\databoar\   (Windows)
      or $XDG_CONFIG_HOME/databoar when set

    Dot-source so exports persist:
      . .\scripts\databoar-env-load.ps1
      . .\scripts\databoar-env-load.ps1 -Name hubspot

    Prefer vault -> env when available; on-disk *.env is an optional bridge.
    Docs: docs/ops/OPERATOR_CREDENTIALS_FROM_ENV.md

.PARAMETER Name
    Stem of a single file (hubspot -> hubspot.env). Omit to load all *.env.

.PARAMETER List
    List matching files; do not export.
#>
param(
    [string]$Name = "",
    [switch]$List
)

$ErrorActionPreference = "Stop"

function Get-DataBoarEnvDir {
    if ($env:DATA_BOAR_ENV_DIR) { return $env:DATA_BOAR_ENV_DIR }
    if ($env:XDG_CONFIG_HOME) { return (Join-Path $env:XDG_CONFIG_HOME "databoar") }
    # Prefer Windows-friendly path under USERPROFILE\.config (mirrors Linux XDG)
    return (Join-Path $env:USERPROFILE ".config\databoar")
}

function Import-DataBoarEnvFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "databoar-env-load: not found: $Path"
    }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        if ($line -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { return }
        $key = $Matches[1]
        $val = $Matches[2].Trim()
        if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        Set-Item -Path "env:$key" -Value $val
    }
    Write-Host "databoar-env-load: loaded $(Split-Path -Leaf $Path)" -ForegroundColor Gray
}

$dir = Get-DataBoarEnvDir
if (-not (Test-Path -LiteralPath $dir)) {
    Write-Host "databoar-env-load: directory missing: $dir" -ForegroundColor Yellow
    Write-Host "  New-Item -ItemType Directory -Path `"$dir`" -Force; icacls `"$dir`" /inheritance:r /grant:r `"$($env:USERNAME):(OI)(CI)F`"" -ForegroundColor Gray
    throw "databoar-env-load: create the directory first"
}

if ($List) {
    $files = Get-ChildItem -LiteralPath $dir -Filter "*.env" -File -ErrorAction SilentlyContinue
    if (-not $files) {
        Write-Host "databoar-env-load: no *.env under $dir" -ForegroundColor Yellow
        return
    }
    $files | Format-Table Name, Length, LastWriteTime -AutoSize
    return
}

if ($Name) {
    $stem = $Name -replace '\.env$', ''
    Import-DataBoarEnvFile -Path (Join-Path $dir "$stem.env")
    return
}

$loaded = 0
Get-ChildItem -LiteralPath $dir -Filter "*.env" -File -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match '\.example\.env$' -or $_.Name -eq 'example.env') { return }
    Import-DataBoarEnvFile -Path $_.FullName
    $loaded++
}
if ($loaded -eq 0) {
    Write-Host "databoar-env-load: no *.env under $dir" -ForegroundColor Yellow
    throw "databoar-env-load: nothing to load"
}
