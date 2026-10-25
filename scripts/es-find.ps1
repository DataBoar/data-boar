#!/usr/bin/env pwsh
# Token-aware wrapper for voidtools Everything CLI (es.exe).
# Requires the Everything service running and volumes indexed.
# Default scope is this Git repo root; use -Global for the full index (still capped by -MaxCount).
# If you see "Everything IPC not found", start the Everything GUI/service so es.exe can connect.
#
# Usage:
#   .\scripts\es-find.ps1 -Query "*.md"
#   .\scripts\es-find.ps1 -Query "foo" -Global -MaxCount 30
#   .\scripts\es-find.ps1 -Query "bar" -SearchRoot "D:\work" -Regex

param(
    [Parameter(Position = 0)]
    [string]$Query = "",

    [string]$SearchRoot = "",

    [switch]$Global,

    [ValidateRange(1, 100000)]
    [int]$MaxCount = 50,

    [string]$EsExePath = "",

    [switch]$Regex,

    [switch]$MatchCase,

    [switch]$FilesOnly,

    [switch]$FoldersOnly,

    [switch]$GetResultCount,

    [switch]$ShowCommand,

    [switch]$Help,

    # If es.exe is missing (exit 127 path), run a capped PowerShell -Recurse name search instead (slower, more I/O).
    # Ignored when -Regex is set (regex search requires es). Ignored when -Global is set (full-volume index requires es).
    [switch]$FallbackPowerShell
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName

function Invoke-PowerShellFilenameSearch {
    param(
        [string]$Root,
        [string]$Pattern,
        [int]$MaxCount
    )
    if (-not (Test-Path -LiteralPath $Root)) {
        Write-Host "Fallback: root not found: $Root" -ForegroundColor Red
        return
    }
    $like = $Pattern
    if ($like -notmatch '[*?\[]') {
        $like = "*$like*"
    }
    Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like $like } |
        Select-Object -First $MaxCount |
        ForEach-Object { $_.FullName }
}

if ($Help) {
    @"
es-find.ps1 - voidtools Everything CLI wrapper (read-only, token-aware default cap)

Usage:
  .\scripts\es-find.ps1 -Query "<pattern>" [-MaxCount N] [-Global] [-SearchRoot path]
  .\scripts\es-find.ps1 -Query "*.md" -Regex
  .\scripts\es-find.ps1 -Query "foo" -ShowCommand

Docs: docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md
Rule: .cursor/rules/everything-es-cli.mdc
Fallback: -FallbackPowerShell when es.exe is absent (not with -Regex or -Global).
"@
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Query)) {
    Write-Host "es-find: missing -Query. Use -Help for usage." -ForegroundColor Yellow
    exit 2
}

function Resolve-EsExe {
    param([string]$Override)
    if ($Override -and (Test-Path -LiteralPath $Override)) {
        return [string](Resolve-Path -LiteralPath $Override).Path
    }
    $cmd = Get-Command es -ErrorAction SilentlyContinue
    if ($cmd) {
        return [string]$cmd.Source
    }
    $wingetLink = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\es.exe"
    if (Test-Path -LiteralPath $wingetLink) {
        return [string](Resolve-Path -LiteralPath $wingetLink).Path
    }
    return $null
}

$effectiveRoot = $SearchRoot
if ([string]::IsNullOrWhiteSpace($effectiveRoot)) {
    $effectiveRoot = $repoRoot
}

$esExe = Resolve-EsExe -Override $EsExePath
if (-not $esExe) {
    if ($FallbackPowerShell -and -not $Regex -and -not $Global) {
        Write-Host "es.exe not found; using PowerShell filename search under: $effectiveRoot (slower)." -ForegroundColor Yellow
        Invoke-PowerShellFilenameSearch -Root $effectiveRoot -Pattern $Query -MaxCount $MaxCount
        exit 0
    }
    Write-Host "es.exe not found. Install voidtools Everything CLI (e.g. winget install voidtools.Everything.Cli) and ensure Everything is running. Or re-run with -FallbackPowerShell (scoped tree, not -Global/-Regex)." -ForegroundColor Yellow
    exit 127
}

$cmdArgs = [System.Collections.Generic.List[string]]::new()
[void]$cmdArgs.Add("-n")
[void]$cmdArgs.Add("$MaxCount")

if (-not $Global) {
    [void]$cmdArgs.Add("-path")
    [void]$cmdArgs.Add($effectiveRoot)
}

if ($MatchCase) {
    [void]$cmdArgs.Add("-case")
}
if ($FilesOnly) {
    [void]$cmdArgs.Add("/a-d")
}
if ($FoldersOnly) {
    [void]$cmdArgs.Add("/ad")
}
if ($GetResultCount) {
    [void]$cmdArgs.Add("-get-result-count")
}

if ($Regex) {
    [void]$cmdArgs.Add("-regex")
    [void]$cmdArgs.Add($Query)
} else {
    [void]$cmdArgs.Add($Query)
}

if ($ShowCommand) {
    $quoted = ($cmdArgs | ForEach-Object {
            if ($_ -match '[\s"]') {
                '"' + ($_ -replace '"', '\"') + '"'
            } else {
                $_
            }
        }) -join " "
    Write-Host ("& `"$esExe`" $quoted")
}

& $esExe @cmdArgs
exit $LASTEXITCODE
