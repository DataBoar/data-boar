#Requires -Version 5.1
<#
.SYNOPSIS
    Run zizmor on .github/workflows (local advisory by default).

.DESCRIPTION
    Scans GitHub Actions workflow YAML under .github/workflows. Default is warn-first
    (exit 0 when findings exist). Use -Enforce or env DATA_BOAR_ENFORCE_ZIZMOR=true to fail.

    Invokes zizmor from PATH when present; otherwise uses `uvx zizmor` (see docs.zizmor.sh).

    Not part of check-all.ps1. Optional pre-commit hook (manual stage): see .pre-commit-config.yaml.

.PARAMETER Enforce
    Exit non-zero when zizmor reports findings.

.PARAMETER SkipIfMissing
    Exit 0 when neither zizmor nor uvx is available (for optional hooks).

.EXAMPLE
    .\scripts\workflow-security-lint.ps1
    .\scripts\workflow-security-lint.ps1 -Enforce
    $env:DATA_BOAR_ENFORCE_ZIZMOR = 'true'; .\scripts\workflow-security-lint.ps1
#>
param(
    [switch]$Enforce,
    [switch]$SkipIfMissing
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$workflowsDir = Join-Path $repoRoot ".github\workflows"
if (-not (Test-Path -LiteralPath $workflowsDir)) {
    Write-Host "workflow-security-lint: SKIP (missing $workflowsDir)." -ForegroundColor Yellow
    exit 0
}

$enforceFindings = $Enforce.IsPresent
if (-not $enforceFindings -and $env:DATA_BOAR_ENFORCE_ZIZMOR -eq "true") {
    $enforceFindings = $true
}

function Get-ZizmorCommand {
    $zizmor = Get-Command zizmor -ErrorAction SilentlyContinue
    if ($zizmor) {
        return @{
            FilePath = $zizmor.Source
            ArgumentList = @()
        }
    }
    $uvx = Get-Command uvx -ErrorAction SilentlyContinue
    if ($uvx) {
        return @{
            FilePath = $uvx.Source
            ArgumentList = @("zizmor")
        }
    }
    return $null
}

$invoker = Get-ZizmorCommand
if (-not $invoker) {
    $msg = "workflow-security-lint: zizmor not found (install: uv tool install zizmor, or use uvx)."
    if ($SkipIfMissing) {
        Write-Host "$msg SKIP (-SkipIfMissing)." -ForegroundColor Yellow
        exit 0
    }
    Write-Host $msg -ForegroundColor Red
    exit 2
}

$argsList = @($invoker.ArgumentList + @($workflowsDir))
Write-Host "=== workflow-security-lint: zizmor on .github/workflows ===" -ForegroundColor Cyan
if ($enforceFindings) {
    Write-Host "  Mode: enforce (fail on findings)." -ForegroundColor Gray
} else {
    Write-Host "  Mode: advisory (warn on findings; use -Enforce to fail)." -ForegroundColor Gray
}

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $invoker.FilePath @argsList
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap

if ($null -eq $code) {
    $code = 0
}

if ($code -eq 0) {
    Write-Host "workflow-security-lint: OK (no findings)." -ForegroundColor Green
    exit 0
}

if ($enforceFindings) {
    Write-Host "workflow-security-lint: FAILED (zizmor exit $code, enforcement on)." -ForegroundColor Red
    exit $code
}

Write-Host "workflow-security-lint: WARN (zizmor exit $code, advisory mode)." -ForegroundColor Yellow
Write-Host "  Re-run with -Enforce or set DATA_BOAR_ENFORCE_ZIZMOR=true to fail on findings." -ForegroundColor DarkGray
exit 0
