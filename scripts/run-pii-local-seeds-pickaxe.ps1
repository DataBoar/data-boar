<#
.SYNOPSIS
  Runs git log --all pickaxe (-S) once per non-comment line in a local PII seeds file.

.DESCRIPTION
  Reads docs/private/security_audit/PII_LOCAL_SEEDS.txt by default (gitignored).
  Skips blank lines and lines starting with #. Uses one argv per seed so spaces work.

  This is a time/token saver versus typing dozens of git log -S commands by hand.
  It does NOT replace CI guards or pii_history_guard; it complements local literals.

.PARAMETER SeedsPath
  Path to the seeds file (default: docs/private/security_audit/PII_LOCAL_SEEDS.txt).

.PARAMETER Limit
  If set > 0, only process the first N non-comment seeds (smoke test).

.PARAMETER Quiet
  If set, only print seeds for which git log produced output.
#>
param(
    [string] $SeedsPath = "docs/private/security_audit/PII_LOCAL_SEEDS.txt",
    [int] $Limit = 0,
    [switch] $Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not [System.IO.Path]::IsPathRooted($SeedsPath)) {
    $SeedsPath = Join-Path $repoRoot $SeedsPath
}

if (-not (Test-Path -LiteralPath $SeedsPath)) {
    Write-Error "Seeds file not found: $SeedsPath. Copy from docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt"
    exit 1
}

$lines = Get-Content -LiteralPath $SeedsPath -Encoding UTF8
$processed = 0
foreach ($raw in $lines) {
    $line = $raw.Trim()
    if ($line.Length -eq 0) { continue }
    if ($line.StartsWith("#")) { continue }
    if ($Limit -gt 0 -and $processed -ge $Limit) { break }
    $processed++
    $idx = $processed

    if (-not $Quiet) {
        Write-Host ""
        Write-Host "=== seed #$idx (length $($line.Length)) ===" -ForegroundColor Cyan
    }

    $out = & git -C $repoRoot log --all --oneline -S $line 2>&1
    $text = if ($null -eq $out) { "" } else { ($out | Out-String).TrimEnd() }
    if ($Quiet) {
        if ($text.Length -gt 0) {
            Write-Host "=== HIT seed #$idx (length $($line.Length)) ===" -ForegroundColor Yellow
            Write-Host $text
        }
    } else {
        if ($text.Length -eq 0) {
            Write-Host "(no matches)"
        } else {
            Write-Host $text
        }
    }
}

Write-Host ""
Write-Host "Done. Processed $processed seed(s)." -ForegroundColor Green
