#!/usr/bin/env pwsh
# Token-aware tail: prefer Git for Windows tail.exe, else Get-Content -Tail.
# BareTail is a GUI log viewer; this script does not invoke it for automation (hints if found under Downloads).
#
# Usage:
#   .\scripts\repo-tail.ps1 -Path .\CHANGELOG.md -Lines 40
#   .\scripts\repo-tail.ps1 -Path .\logs\foo.log -Follow
#
# Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md

param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [ValidateRange(1, 100000)]
    [int]$Lines = 80,

    [switch]$Follow,

    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    @"
repo-tail.ps1 - last N lines of a file (Git tail.exe when available)

Usage:
  .\scripts\repo-tail.ps1 -Path <file> [-Lines N] [-Follow]

-Follow uses tail -f when Git tail exists; otherwise Get-Content -Wait -Tail.

Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md
"@
    exit 0
}

function Find-GitTailExe {
    $cmd = Get-Command tail -ErrorAction SilentlyContinue
    if ($cmd -and ($cmd.Source -match 'Git\\usr\\bin\\tail\.exe')) {
        return [string]$cmd.Source
    }
    $candidates = @(
        "C:\Program Files\Git\usr\bin\tail.exe",
        (Join-Path ${env:ProgramFiles(x86)} "Git\usr\bin\tail.exe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            return [string](Resolve-Path -LiteralPath $c).Path
        }
    }
    return $null
}

function Write-BareTailHintIfPresent {
    $downloads = Join-Path $env:USERPROFILE "Downloads"
    foreach ($leaf in @("baretail.exe", "BareTail.exe", "baretai.exe")) {
        $candidate = Join-Path $downloads $leaf
        if (Test-Path -LiteralPath $candidate) {
            Write-Host "repo-tail: found $leaf under Downloads (Bare Metal GUI). Automation stays on Git tail.exe or Get-Content; install Git for Windows for the fast tail path." -ForegroundColor DarkYellow
            return
        }
    }
}

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "repo-tail: file not found: $Path" -ForegroundColor Red
    exit 2
}

$fullPath = [string](Resolve-Path -LiteralPath $Path).Path
$tailExe = Find-GitTailExe

if (-not $tailExe) {
    Write-BareTailHintIfPresent
}

if ($tailExe) {
    if ($Follow) {
        & $tailExe @("-n", "$Lines", "-f", $fullPath)
        exit $LASTEXITCODE
    }
    & $tailExe @("-n", "$Lines", $fullPath)
    exit $LASTEXITCODE
}

if ($Follow) {
    Get-Content -LiteralPath $fullPath -Tail $Lines -Wait
    exit 0
}

Get-Content -LiteralPath $fullPath -Tail $Lines
exit 0
