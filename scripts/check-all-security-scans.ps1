#Requires -Version 5.1
<#
.SYNOPSIS
    Security scan tier for check-all (#1044) - Bandit + Zizmor; optional Semgrep with -Enforced.

.DESCRIPTION
    Fail-collect: runs every scan, reports all failures at the end (no fail-fast within tier).
    Commands mirror CI (.github/workflows/ci.yml bandit paths, semgrep.yml image tag via uvx semgrep@VER, zizmor CLI on workflows/).
#>
param(
    [switch]$Enforced = $false
)

$ErrorActionPreference = "Continue"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "check-all-security-scans: ABORTED: uv not on PATH." -ForegroundColor Red
    exit 2
}

$failures = [System.Collections.Generic.List[string]]::new()

function Invoke-SecurityScan {
    param(
        [string]$Name,
        [scriptblock]$Block
    )
    Write-Host "=== Security scan: $Name ===" -ForegroundColor Cyan
    & $Block
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "$Name... Failed (exit $code)" -ForegroundColor Red
        [void]$failures.Add("$Name (exit $code)")
    } else {
        Write-Host "$Name... Passed" -ForegroundColor Green
    }
}

Invoke-SecurityScan -Name "Bandit" -Block {
    uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q
}

# Local uvx zizmor is the PyPI CLI. CI (.github/workflows/zizmor.yml) runs
# zizmorcore/zizmor-action@<SHA> (SARIF upload, offline-audits). Those are
# different artifacts - do not invent CLI==action version parity (#1793).
Invoke-SecurityScan -Name "Zizmor" -Block {
    uvx zizmor .github/workflows/
}

if ($Enforced) {
    $wf = Join-Path $repoRoot ".github/workflows/semgrep.yml"
    $match = Select-String -Path $wf -Pattern "semgrep/semgrep:(\d+\.\d+\.\d+)" | Select-Object -First 1
    if ($null -eq $match) {
        Write-Host "check-all-security-scans: ABORTED: could not read Semgrep version from .github/workflows/semgrep.yml" -ForegroundColor Red
        exit 1
    }
    $script:SEMGREP_VER = $match.Matches[0].Groups[1].Value
    if ([string]::IsNullOrWhiteSpace($script:SEMGREP_VER)) {
        Write-Host "check-all-security-scans: ABORTED: could not read Semgrep version from .github/workflows/semgrep.yml" -ForegroundColor Red
        exit 1
    }
    Write-Host "Semgrep pin: $script:SEMGREP_VER (from .github/workflows/semgrep.yml image tag)." -ForegroundColor Cyan
    Invoke-SecurityScan -Name "Semgrep" -Block {
        uvx "semgrep@$script:SEMGREP_VER" scan --config p/python --metrics=off `
            --exclude-rule python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text `
            --error .
    }
}

if ($failures.Count -gt 0) {
    Write-Host "check-all-security-scans: FAILED ($($failures.Count) scan(s)):" -ForegroundColor Red
    foreach ($item in $failures) {
        Write-Host "  - $item" -ForegroundColor Red
    }
    exit 1
}

Write-Host "check-all-security-scans: OK (all security scans passed)." -ForegroundColor Green
exit 0
