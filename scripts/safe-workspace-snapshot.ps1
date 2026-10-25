#!/usr/bin/env pwsh
# Read-only snapshot: git status at repo root (and optional nested docs/private/.git).
# Use before Preview/commit when the IDE shows noisy or ambiguous state (OOM reload, two Git roots).
# Does not replace check-all before merge.
#
# Usage (from repo root):
#   .\scripts\safe-workspace-snapshot.ps1
#   .\scripts\safe-workspace-snapshot.ps1 -SkipTests
#   .\scripts\safe-workspace-snapshot.ps1 -SkipPrivateGitStatus

param(
    [switch]$SkipTests,
    [switch]$SkipPrivateGitStatus
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

Write-Host "=== safe-workspace-snapshot (read-only) ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot" -ForegroundColor DarkGray
Write-Host ""

Write-Host "--- git status (repo root) ---" -ForegroundColor Yellow
git status
Write-Host ""

$privateGit = Join-Path $RepoRoot "docs\private\.git"
if (-not $SkipPrivateGitStatus -and (Test-Path -LiteralPath $privateGit)) {
    Write-Host "--- git status (docs/private nested repo) ---" -ForegroundColor Yellow
    git -C (Join-Path $RepoRoot "docs\private") status
    Write-Host ""
} elseif (-not $SkipPrivateGitStatus) {
    Write-Host "(no docs/private/.git - skipped nested status)" -ForegroundColor DarkGray
    Write-Host ""
}

if (-not $SkipTests) {
    Write-Host "--- quick guard tests ---" -ForegroundColor Yellow
    $guardTests = @(
        "tests/test_confidential_commercial_guard.py",
        "tests/test_talent_ps1_tracked_no_inline_pool.py"
    )
    $missing = $guardTests | Where-Object { -not (Test-Path -LiteralPath (Join-Path $RepoRoot $_)) }
    if ($missing) {
        Write-Warning "Missing test file(s): $($missing -join ', ') - skipping pytest."
    } else {
        uv run pytest @guardTests -q --tb=short
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            Write-Host "safe-workspace-snapshot: guard tests FAILED." -ForegroundColor Red
            exit $exitCode
        }
        Write-Host "guard tests: OK." -ForegroundColor Green
    }
    Write-Host ""
}

Write-Host "safe-workspace-snapshot: done (no commits, no staging)." -ForegroundColor Green
exit 0
