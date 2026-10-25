# Remove local branches that are fully merged into main AND whose upstream was deleted ([gone]).
# Safe: does not delete branches with unique commits not in main.
# Usage: run from repo root: pwsh -File scripts/git-cleanup-merged-gone-branches.ps1

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

$current = git branch --show-current
if ($current -ne "main") {
    Write-Host "Checkout main first (current: $current)." -ForegroundColor Yellow
    exit 1
}

$merged = git branch --merged main --format="%(refname:short)" | Where-Object { $_ -ne "main" }
$set = [System.Collections.Generic.HashSet[string]]::new([string[]]$merged)

$deleted = @()
foreach ($line in (& git branch -vv)) {
    if ($line -notmatch ": gone\]") { continue }
    if ($line -match "^\*?\s+(\S+)\s+") {
        $name = $Matches[1]
        if ($set.Contains($name)) {
            Write-Host "Deleting merged+gone: $name" -ForegroundColor Cyan
            git branch -d $name
            if ($LASTEXITCODE -eq 0) { $deleted += $name }
        }
    }
}

Write-Host "Done. Removed $($deleted.Count) branch(es)." -ForegroundColor Green
