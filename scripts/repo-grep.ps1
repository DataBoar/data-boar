#!/usr/bin/env pwsh
# Token-aware repo content search: prefer ripgrep (rg), then optional baregrep.exe (GUI), else Select-String.
# Default caps output lines for transcript safety. Try answer first; fix tool wiring later under pressure.
#
# Usage:
#   .\scripts\repo-grep.ps1 -Pattern "TODO" -Path .
#   .\scripts\repo-grep.ps1 -Pattern "class Foo" -Glob "*.py" -SimpleMatch
#   .\scripts\repo-grep.ps1 -Pattern "bar" -PreferBareGrep
#
# Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md

param(
    [Parameter(Mandatory = $true)]
    [string]$Pattern,

    [string]$Path = "",

    [ValidateRange(1, 100000)]
    [int]$MaxOutputLines = 400,

    [switch]$SimpleMatch,

    [string]$Glob = "",

    [switch]$PreferBareGrep,

    [switch]$ShowCommand,

    [switch]$Help
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName

if ($Help) {
    @"
repo-grep.ps1 - fast content search with fallbacks (token-aware line cap)

Order:
  1) baregrep.exe first only when -PreferBareGrep (may open a GUI window / splash)
  2) ripgrep (rg) when found on PATH or common install locations
  3) Select-String over files (slower; capped file scan)

Usage:
  .\scripts\repo-grep.ps1 -Pattern "<regex or literal>" [-Path <dirOrFile>] [-MaxOutputLines N] [-SimpleMatch] [-Glob "*.md"]
  .\scripts\repo-grep.ps1 -Pattern "x" -PreferBareGrep

Notes:
  - GNU grep from unrelated installs (e.g. FPC toolchain) is skipped for recursion safety; use rg or Select-String.
  - If rg is missing: winget install BurntSushi.ripgrep.MSVC (or install rg and ensure PATH).
  - baregrep.exe: often under %USERPROFILE%\\Downloads; use -PreferBareGrep (may show GUI / splash).

Docs: docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md
"@
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) {
    $Path = $repoRoot
}

$resolvedPath = [string](Resolve-Path -LiteralPath $Path).Path

function Find-RgExe {
    $cmd = Get-Command rg -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
        return [string]$cmd.Source
    }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\rg.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\rg.exe"),
        "C:\Program Files\Git\usr\bin\rg.exe",
        (Join-Path ${env:ProgramFiles(x86)} "Git\usr\bin\rg.exe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) {
            return [string](Resolve-Path -LiteralPath $c).Path
        }
    }
    return $null
}

function Find-BareGrepExe {
    $cmd = Get-Command baregrep -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
        return [string]$cmd.Source
    }
    # Portable copies (not winget-installable): common under the operator profile Downloads.
    $downloads = Join-Path $env:USERPROFILE "Downloads"
    foreach ($leaf in @("baregrep.exe", "BareGrep.exe")) {
        $candidate = Join-Path $downloads $leaf
        if (Test-Path -LiteralPath $candidate) {
            return [string](Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Invoke-SelectStringFallback {
    param(
        [string]$Root,
        [string]$Pat,
        [bool]$Simple,
        [string]$GlobPat,
        [int]$MaxLines,
        [int]$MaxFiles
    )
    Write-Host "repo-grep: using Select-String fallback (install rg for speed). Scan cap: $MaxFiles files." -ForegroundColor Yellow
    $lineCount = 0
    if (Test-Path -LiteralPath $Root -PathType Leaf) {
        Select-String -LiteralPath $Root -Pattern $Pat -SimpleMatch:$Simple -ErrorAction SilentlyContinue |
            ForEach-Object {
                if ($lineCount -ge $MaxLines) {
                    return
                }
                $lineCount++
                "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line
            }
        return
    }
    $files = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue
    if ($GlobPat -ne "") {
        $files = $files | Where-Object { $_.Name -like $GlobPat }
    }
    $files |
        Select-Object -First $MaxFiles |
        ForEach-Object {
            if ($lineCount -ge $MaxLines) {
                return
            }
            Select-String -LiteralPath $_.FullName -Pattern $Pat -SimpleMatch:$Simple -ErrorAction SilentlyContinue |
                ForEach-Object {
                    if ($lineCount -ge $MaxLines) {
                        return
                    }
                    $lineCount++
                    "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line
                }
        }
}

if ($PreferBareGrep) {
    $bare = Find-BareGrepExe
    if ($bare) {
        Write-Host "repo-grep: invoking baregrep (may show GUI / splash)." -ForegroundColor Yellow
        $bareArgs = @("-r", $Pattern, $resolvedPath)
        if ($ShowCommand) {
            Write-Host ("& `"$bare`" " + ($bareArgs -join " "))
        }
        & $bare @bareArgs
        exit $LASTEXITCODE
    }
    Write-Host "repo-grep: -PreferBareGrep set but baregrep.exe not found on PATH or in Downloads." -ForegroundColor Yellow
}

$rg = Find-RgExe
if ($rg) {
    $cmdArgs = [System.Collections.Generic.List[string]]::new()
    [void]$cmdArgs.Add("-n")
    [void]$cmdArgs.Add("--no-heading")
    [void]$cmdArgs.Add("--max-columns")
    [void]$cmdArgs.Add("400")
    if ($SimpleMatch) {
        [void]$cmdArgs.Add("-F")
    }
    if ($Glob -ne "") {
        [void]$cmdArgs.Add("--glob")
        [void]$cmdArgs.Add($Glob)
    }
    [void]$cmdArgs.Add($Pattern)
    [void]$cmdArgs.Add($resolvedPath)
    if ($ShowCommand) {
        $quoted = ($cmdArgs | ForEach-Object {
                if ($_ -match '[\s"]') {
                    '"' + ($_ -replace '"', '\"') + '"'
                } else {
                    $_
                }
            }) -join " "
        Write-Host ("& `"$rg`" $quoted")
    }
    & $rg @($cmdArgs.ToArray()) 2>&1 | Select-Object -First $MaxOutputLines
    exit 0
}

Invoke-SelectStringFallback -Root $resolvedPath -Pat $Pattern -Simple:$SimpleMatch -GlobPat $Glob -MaxLines $MaxOutputLines -MaxFiles 3000
exit 0
