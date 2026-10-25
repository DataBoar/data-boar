<#
.SYNOPSIS
  Lab A/B harness: two timed lab-completao-orchestrate rounds (different -LabGitRef) plus optional SQLite/report capture.

.DESCRIPTION
  Wrapper around scripts/lab-completao-orchestrate.ps1 (not a fork of its internals). Keeps the
  orchestrator contract intact; this script only sequences runs, measures wall time, copies
  artifacts you point at, and writes bench/COMPARISON.log.

  For git checkout A/B on the canonical clone (legacy tag vs restored branch) plus benchmark_runs/times.txt,
  use scripts/benchmark-ab.ps1 instead.

  The orchestrator does not emit a scan SQLite by itself (host smoke + optional GRC JSON). Pass
  -SqlitePath to copy the same file after each round if you run a separate main.py scan, or
  copy from a fixed lab path.

  Round 1 default ref: v1.7.3 (use -SkipGitPullOnInventoryRefresh when pinning tags).
  Round 2 default ref: origin/main (LAB clone tip).

.PARAMETER SqlitePath
  Optional path to audit SQLite to copy into bench/v1.7.3/results.db and bench/v1.7.4/results.db.

.PARAMETER ReportConfigYaml
  Path to YAML for data-boar-report (after round 2 only).

.PARAMETER ReportSessionId
  Session UUID for data-boar-report (after round 2 only).

.NOTES
  ASCII-only for Windows PowerShell 5.1. Requires manifest and SSH per LAB_COMPLETAO_RUNBOOK.md.
#>
[CmdletBinding()]
param(
    [string] $RepoRoot = "",
    [string] $BenchRoot = "bench",
    [string] $Round1Ref = "v1.7.3",
    [string] $Round2Ref = "origin/main",
    [string] $SqlitePath = "",
    [string] $ReportConfigYaml = "",
    [string] $ReportSessionId = "",
    [switch] $Privileged,
    [switch] $SkipGitPullOnInventoryRefresh,
    [switch] $WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string] $Root)
    if ([string]::IsNullOrWhiteSpace($Root)) {
        $here = Split-Path -Parent $MyInvocation.MyCommand.Path
        return (Resolve-Path (Join-Path $here "..")).Path
    }
    return (Resolve-Path $Root).Path
}

$r = Resolve-RepoRoot -Root $RepoRoot
$bench = Join-Path $r $BenchRoot
$dA = Join-Path $bench "v1.7.3"
$dB = Join-Path $bench "v1.7.4"
$logPath = Join-Path $bench "COMPARISON.log"

if ($WhatIf) {
    Write-Host "WhatIf: would reset $dA , $dB and run two orchestrate passes."
    exit 0
}

foreach ($p in @($dA, $dB)) {
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p
    }
    New-Item -ItemType Directory -Path $p | Out-Null
}

$orch = Join-Path $r "scripts\lab-completao-orchestrate.ps1"
if (-not (Test-Path $orch)) {
    throw "missing orchestrator: $orch"
}

function Invoke-CompletaoTimed {
    param(
        [string] $LabGitRef,
        [string] $Label,
        [switch] $RoundUsesTagPin
    )
    $argList = @("-NoProfile", "-File", $orch, "-LabGitRef", $LabGitRef)
    if ($Privileged) { $argList += "-Privileged" }
    if ($SkipGitPullOnInventoryRefresh -or $RoundUsesTagPin) { $argList += "-SkipGitPullOnInventoryRefresh" }
    Write-Host "[benchmark] starting completao: $Label ref=$LabGitRef"
    $sw = Measure-Command {
        Push-Location $r
        try {
            & powershell.exe @argList
            if ($LASTEXITCODE -ne 0) {
                throw "completao exit $LASTEXITCODE for $Label"
            }
        } finally {
            Pop-Location
        }
    }
    return $sw
}

$round1TagPin = $Round1Ref -match '^v[0-9]'
$t1 = Invoke-CompletaoTimed -LabGitRef $Round1Ref -Label "round1" -RoundUsesTagPin:$round1TagPin
if (-not [string]::IsNullOrWhiteSpace($SqlitePath)) {
    $src = Resolve-Path $SqlitePath
    Copy-Item -LiteralPath $src -Destination (Join-Path $dA "results.db") -Force
}

$t2 = Invoke-CompletaoTimed -LabGitRef $Round2Ref -Label "round2" -RoundUsesTagPin:$false
if (-not [string]::IsNullOrWhiteSpace($SqlitePath)) {
    $src = Resolve-Path $SqlitePath
    Copy-Item -LiteralPath $src -Destination (Join-Path $dB "results.db") -Force
}

$mdOut = Join-Path $dB "executive_report_benchmark.md"
$reportRc = 0
$reportOk = $false
if (-not [string]::IsNullOrWhiteSpace($ReportConfigYaml) -and -not [string]::IsNullOrWhiteSpace($ReportSessionId)) {
    $cfgR = Resolve-Path $ReportConfigYaml
    $argsUv = @(
        "run", "python", "-m", "cli.reporter",
        "--config", $cfgR.Path,
        "--session-id", $ReportSessionId,
        "-o", $mdOut
    )
    Push-Location $r
    try {
        & uv @argsUv
        $reportRc = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($reportRc -eq 0 -and (Test-Path $mdOut)) {
        $body = Get-Content -LiteralPath $mdOut -Raw -ErrorAction SilentlyContinue
        if ($body -and ($body.Length -gt 0)) {
            if ($body -match "Recomenda") { $reportOk = $true }
        }
    }
}

$lines = @()
$lines += "data_boar_lab_benchmark $(Get-Date -Format o)"
$lines += "repo=$r"
$lines += "round1_ref=$Round1Ref total_seconds=$([math]::Round($t1.TotalSeconds, 3))"
$lines += "round2_ref=$Round2Ref total_seconds=$([math]::Round($t2.TotalSeconds, 3))"
$lines += "data_boar_report_exit=$reportRc markdown_action_plan_pt=$reportOk"

$dbA = Join-Path $dA "results.db"
$dbB = Join-Path $dB "results.db"
if ((Test-Path $dbA) -and (Test-Path $dbB)) {
    Push-Location $r
    try {
        $diffText = & uv run python (Join-Path $r "scripts\benchmark_sqlite_diff.py") $dbA $dbB 2>&1
        $lines += "sqlite_diff:"
        $lines += $diffText
    } finally {
        Pop-Location
    }
} else {
    $lines += "sqlite_diff: skipped (need results.db in both dirs; pass -SqlitePath or copy files)"
}

Set-Content -LiteralPath $logPath -Value ($lines -join "`n") -Encoding ascii
Write-Host "[benchmark] wrote $logPath"
