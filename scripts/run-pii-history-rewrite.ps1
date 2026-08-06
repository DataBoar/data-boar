<#
.SYNOPSIS
    Backup, clone, rewrite Git history with scripts/filter_repo_pii_replacements.txt, run tests.

.DESCRIPTION
    BLOCKED unless environment variable DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS is set to 1.
    Never enable on primary Windows dev PC (primary dev workstation); use only on a designated lab host with operator intent.
    Does NOT push by default. Use -Push after reviewing test output.
    Requires git-filter-repo on PATH and a clean working tree (commit or stash first).

.PARAMETER Push
    After successful pytest + pii_history_guard, set origin to GitHub and force-push all refs.

.PARAMETER RepoRoot
    Default: parent of scripts/ (repository root).
#>
[CmdletBinding()]
param(
    [switch]$Push,
    [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS -ne "1") {
    throw (
        "Refusing: set DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1 only on a non-primary-workstation lab host when you intend history rewrite. " +
        "See docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md"
    )
}

if (-not $RepoRoot) {
    $RepoRoot = Split-Path $PSScriptRoot -Parent
    if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
        Write-Error "Could not find .git above scripts/."
    }
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

$status = git -C $RepoRoot status --porcelain
if ($status) {
    Write-Error "Working tree is not clean. Commit or stash before history rewrite. git status:`n$status"
}

$filterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue
if (-not $filterRepo) {
    Write-Error "git-filter-repo not found on PATH."
}

$exprFile = Join-Path $RepoRoot "scripts\filter_repo_pii_replacements.txt"
if (-not (Test-Path -LiteralPath $exprFile)) {
    Write-Error "Missing $exprFile"
}

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$parent = Split-Path $RepoRoot -Parent
$mirrorPath = Join-Path $parent "data-boar-mirror-backup-$ts.git"
$workPath = Join-Path $parent "data-boar-history-rewrite-$ts"

Write-Host "[1/5] Mirror backup -> $mirrorPath" -ForegroundColor Cyan
git clone --mirror $RepoRoot $mirrorPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/5] Working clone -> $workPath" -ForegroundColor Cyan
if (Test-Path -LiteralPath $workPath) {
    Remove-Item -Recurse -Force $workPath
}
git clone $RepoRoot $workPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/5] git filter-repo (blobs + commit messages)" -ForegroundColor Cyan
Push-Location $workPath
try {
    git filter-repo --force --replace-text $exprFile --replace-message $exprFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "[4/5] pytest + pii_history_guard (full history)" -ForegroundColor Cyan
Push-Location $workPath
try {
    uv run pytest -q -W error
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pytest failed. Restore from mirror: git clone $mirrorPath <newdir>"
    }
    uv run python scripts/pii_history_guard.py --full-history
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pii_history_guard failed. Restore from mirror: git clone $mirrorPath <newdir>"
    }
} finally {
    Pop-Location
}

Write-Host "[5/5] OK - rewritten repo at: $workPath" -ForegroundColor Green
Write-Host "Mirror backup: $mirrorPath"

# After a public rewrite, any remote branch that still pointed at pre-rewrite SHAs will
# keep old blobs reachable for git log --all (and pii_history_guard --full-history).
# Prune or delete those branches on GitHub, then git fetch --prune locally.

if ($Push) {
    $originUrl = "https://github.com/DataBoar/data-boar.git"
    Write-Host "Pushing to $originUrl (force)..." -ForegroundColor Yellow
    Push-Location $workPath
    try {
        git remote add origin $originUrl 2>$null
        git remote set-url origin $originUrl
        git push --force --all origin
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        git push --force --tags origin
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
    Write-Host "Force push done. In your dev clone run: git fetch origin && git reset --hard origin/main" -ForegroundColor Green
} else {
    Write-Host "No push (omit -Push). Inspect $workPath then re-run with -Push or push manually." -ForegroundColor Yellow
}
