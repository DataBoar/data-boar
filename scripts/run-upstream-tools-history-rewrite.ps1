<#
.SYNOPSIS
    Mirror backup, clone, rewrite Git history for one upstream tool repo using scripts/filter_repo_upstream_tools_replacements.txt.

.DESCRIPTION
    Same pattern as run-pii-history-rewrite.ps1: requires DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1.
    Do not use on the primary Windows dev workstation for canonical data-boar; use on a lab host or an isolated copy.
    Requires git-filter-repo on PATH. Working tree must be clean (commit or stash).
    If the clone is shallow (.git/shallow), fetch full history first: git fetch --unshallow

    Does NOT run data-boar pytest. After rewrite, optionally greps for a few known tokens (best-effort).

.PARAMETER RepoRoot
    Path to the .git repository to rewrite (e.g. ...\data-boar\_upstream_python_sgad).

.PARAMETER Push
    After successful rewrite, force-push all refs and tags to origin (URL taken from the original repo before rewrite).

.PARAMETER SkipMirrorBackup
    Skip mirror clone step (not recommended).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [switch]$Push,
    [switch]$SkipMirrorBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS -ne "1") {
    throw (
        "Refusing: set DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1 only when you intend history rewrite. " +
        "See docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md"
    )
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "Not a git repository: $RepoRoot"
}

$shallowMarker = Join-Path $RepoRoot ".git\shallow"
if (Test-Path -LiteralPath $shallowMarker) {
    Write-Warning "Shallow clone detected. Run: git -C `"$RepoRoot`" fetch --unshallow   then re-run."
}

$status = git -C $RepoRoot status --porcelain
if ($status) {
    throw "Working tree is not clean. Commit or stash before history rewrite.`n$status"
}

$filterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue
if (-not $filterRepo) {
    throw "git-filter-repo not found on PATH."
}

$exprFile = Join-Path $PSScriptRoot "filter_repo_upstream_tools_replacements.txt"
if (-not (Test-Path -LiteralPath $exprFile)) {
    throw "Missing $exprFile"
}

$originUrl = git -C $RepoRoot remote get-url origin 2>$null
if (-not $originUrl) {
    throw "No origin remote. Add origin before running, or push manually after rewrite."
}

$repoName = Split-Path $RepoRoot -Leaf
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$parent = Split-Path $RepoRoot -Parent
$mirrorPath = Join-Path $parent "${repoName}-mirror-backup-$ts.git"
$workPath = Join-Path $parent "${repoName}-history-rewrite-$ts"

if (-not $SkipMirrorBackup) {
    Write-Host "[1/4] Mirror backup -> $mirrorPath" -ForegroundColor Cyan
    if (Test-Path -LiteralPath $mirrorPath) {
        Remove-Item -Recurse -Force $mirrorPath
    }
    git clone --mirror $RepoRoot $mirrorPath
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Warning "Skipping mirror backup."
}

Write-Host "[2/4] Working clone -> $workPath" -ForegroundColor Cyan
if (Test-Path -LiteralPath $workPath) {
    Remove-Item -Recurse -Force $workPath
}
git clone $RepoRoot $workPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/4] git filter-repo (blobs + commit messages)" -ForegroundColor Cyan
Push-Location $workPath
try {
    git filter-repo --force --replace-text $exprFile --replace-message $exprFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "[4/4] Spot-check grep (best-effort)" -ForegroundColor Cyan
Push-Location $workPath
try {
    $patterns = @("glibra.corp", "telecom000", "corporate-entity-ario", "10.129.48.68")
    foreach ($p in $patterns) {
        $hit = git grep -n $p 2>$null
        if ($hit) {
            Write-Warning "Still found '$p' in history working tree - review and extend filter_repo_upstream_tools_replacements.txt"
            Write-Host $hit
        }
    }
} finally {
    Pop-Location
}

Write-Host "OK - rewritten repo at: $workPath" -ForegroundColor Green
if (-not $SkipMirrorBackup) {
    Write-Host "Mirror backup: $mirrorPath"
}

if ($Push) {
    Write-Host "Pushing to $originUrl (force)..." -ForegroundColor Yellow
    Push-Location $workPath
    try {
        git remote add origin $originUrl
        git push --force --all origin
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        git push --force --tags origin
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
    Write-Host "Force push done. In your dev clone: git fetch origin && git reset --hard origin/main" -ForegroundColor Green
} else {
    Write-Host "No push. Inspect $workPath then add remote and push, or re-run with -Push." -ForegroundColor Yellow
}
