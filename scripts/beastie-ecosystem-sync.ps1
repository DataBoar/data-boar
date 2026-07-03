#!/usr/bin/env pwsh
# Beastie ecosystem - local clone sync / status (DataBoar org).
# Windows twin of scripts/beastie-ecosystem-sync.sh - delegates to bash when available.
#
# Usage (from data-boar repo root):
#   .\scripts\beastie-ecosystem-sync.ps1 status
#   .\scripts\beastie-ecosystem-sync.ps1 status homing-robin quirky-quati
#   .\scripts\beastie-ecosystem-sync.ps1 fetch | clone-missing | pull-ff

param(
    [Parameter(Position = 0)]
    [ValidateSet('status', 'fetch', 'clone-missing', 'pull-ff', 'set-remote')]
    [string]$Mode = 'status',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Repos
)

$ErrorActionPreference = 'Stop'
$sh = Join-Path $PSScriptRoot 'beastie-ecosystem-sync.sh'
if (-not (Test-Path -LiteralPath $sh)) {
    Write-Error "Missing bash twin: $sh"
    exit 2
}

$bash = Get-Command bash -ErrorAction SilentlyContinue
if (-not $bash) {
    Write-Host 'beastie-ecosystem-sync.ps1: bash not on PATH (install Git for Windows or use WSL).' -ForegroundColor Red
    exit 2
}

$argsList = @($Mode) + $Repos
& $bash.Source $sh @argsList
exit $LASTEXITCODE
