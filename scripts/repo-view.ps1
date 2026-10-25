#!/usr/bin/env pwsh
# Token-aware file preview: prefer bat (batcat) with pager off and line cap, else Get-Content.
#
# Usage:
#   .\scripts\repo-view.ps1 -Path .\README.md -MaxLines 120
#
# Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md

param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [ValidateRange(1, 50000)]
    [int]$MaxLines = 200,

    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    @"
repo-view.ps1 - print start of a text file (bat with line cap when available)

Usage:
  .\scripts\repo-view.ps1 -Path <file> [-MaxLines N]

Uses bat -pp --line-range when bat or batcat is on PATH; otherwise Get-Content -TotalCount.

Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md
"@
    exit 0
}

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "repo-view: file not found: $Path" -ForegroundColor Red
    exit 2
}

$fullPath = [string](Resolve-Path -LiteralPath $Path).Path

function Find-BatExe {
    foreach ($name in @("bat", "batcat")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
            return [string]$cmd.Source
        }
    }
    $downloads = Join-Path $env:USERPROFILE "Downloads"
    $candidates = @(
        (Join-Path $downloads "bat.exe"),
        (Join-Path $downloads "batcat.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\bat.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\bat.exe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            return [string](Resolve-Path -LiteralPath $c).Path
        }
    }
    return $null
}

$bat = Find-BatExe
if ($bat) {
    $range = ":$MaxLines"
    & $bat @("-pp", "--line-range", $range, $fullPath)
    exit $LASTEXITCODE
}

Get-Content -LiteralPath $fullPath -TotalCount $MaxLines
exit 0
