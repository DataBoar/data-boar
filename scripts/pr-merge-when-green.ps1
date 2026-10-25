#Requires -Version 5.1
<#
.SYNOPSIS
  Merge a GitHub PR after verifying it is open, mergeable, and (by default) CI checks pass.

.DESCRIPTION
  Use from the repo root with `gh` authenticated. Does not bypass branch protection unless you use -Admin.
  Escalate to the operator if merge fails, checks are red, or merge conflicts exist.

.EXAMPLE
  .\scripts\pr-merge-when-green.ps1 -PrNumber 42

.EXAMPLE
  .\scripts\pr-merge-when-green.ps1 -PrNumber 42 -Method squash -RunLocalCheckAll
#>
param(
    [Parameter(Mandatory = $true)]
    [int] $PrNumber,
    [ValidateSet("merge", "squash", "rebase")]
    [string] $Method = "merge",
    [switch] $RunLocalCheckAll,
    [switch] $SkipGhChecks,
    [switch] $Admin,
    [switch] $DeleteBranch
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "=== pr-merge-when-green: PR #$PrNumber ===" -ForegroundColor Cyan
git fetch origin 2>&1 | Write-Host

$viewJson = gh pr view $PrNumber --json state,mergeable,mergeStateStatus,title,url 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "gh pr view failed (auth, wrong number, or network)."
}
$pr = $viewJson | ConvertFrom-Json
if ($pr.state -ne "OPEN") {
    throw "PR #$PrNumber is not OPEN (state=$($pr.state))."
}
if ($pr.mergeable -eq "CONFLICTING") {
    throw "PR has merge conflicts - resolve on GitHub or locally, then retry."
}
if ($pr.mergeable -eq "UNKNOWN") {
    Write-Warning "mergeable=UNKNOWN - wait and re-run, or check GitHub UI."
}

if (-not $SkipGhChecks) {
    Write-Host "Running: gh pr checks $PrNumber" -ForegroundColor Yellow
    gh pr checks $PrNumber 2>&1 | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "gh pr checks failed or pending - fix CI or wait for green."
    }
}

if ($RunLocalCheckAll) {
    Write-Host "Running local .\scripts\check-all.ps1 ..." -ForegroundColor Yellow
    & "$repoRoot\scripts\check-all.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Local check-all failed - do not merge until fixed."
    }
}

$mergeArgs = @("pr", "merge", "$PrNumber")
switch ($Method) {
    "merge" { $mergeArgs += "--merge" }
    "squash" { $mergeArgs += "--squash" }
    "rebase" { $mergeArgs += "--rebase" }
}
if ($DeleteBranch) {
    $mergeArgs += "--delete-branch"
}
if ($Admin) {
    $mergeArgs += "--admin"
}

Write-Host "Running: gh $($mergeArgs -join ' ')" -ForegroundColor Green
& gh @mergeArgs
if ($LASTEXITCODE -ne 0) {
    throw "gh pr merge failed (branch protection, permissions, or GitHub lag). Check URL: $($pr.url)"
}

Write-Host "Merged PR #$PrNumber ($Method). Pull main: git checkout main && git pull origin main" -ForegroundColor Green
