#!/usr/bin/env pwsh
# Run pinned Pester suite (PowerShell script LOGIC - #984).
# Linux/macOS: invoked from check-all.sh when pwsh is on PATH.
# Usage: .\scripts\run-pester.ps1

#Requires -Version 7.0

$ErrorActionPreference = 'Stop'

# Pin - keep in sync with tests/test_pester_harness.py::PESTER_REQUIRED_VERSION
$PesterRequiredVersion = '5.6.1'

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$pesterRoot = Join-Path $repoRoot 'tests/pester'

if (-not (Test-Path -LiteralPath $pesterRoot)) {
    Write-Error "run-pester: missing directory $pesterRoot"
    exit 2
}

$pesterModule = Get-Module -ListAvailable -Name Pester |
    Where-Object { $_.Version -eq [version]$PesterRequiredVersion } |
    Select-Object -First 1

if (-not $pesterModule) {
    Write-Host "Installing Pester $PesterRequiredVersion (CurrentUser)..." -ForegroundColor Yellow
    $prev = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'
    try {
        Install-Module -Name Pester -RequiredVersion $PesterRequiredVersion `
            -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
    } finally {
        $ProgressPreference = $prev
    }
}

Import-Module Pester -RequiredVersion $PesterRequiredVersion -Force

$config = New-PesterConfiguration
$config.Run.Path = $pesterRoot
$config.Run.Exit = $true
$config.Output.Verbosity = 'Detailed'
$config.TestResult.Enabled = $false

Write-Host "=== run-pester: Pester $PesterRequiredVersion ($pesterRoot) ===" -ForegroundColor Cyan
Invoke-Pester -Configuration $config
exit $LASTEXITCODE
