# Commit locally or create a PR (Agent Review Panel-style workflow).
# Usage:
#   .\scripts\commit-or-pr.ps1 -Action Preview
#   .\scripts\commit-or-pr.ps1 -Action Commit -Title "Short description" -Body "Bullet1`nBullet2"
#   .\scripts\commit-or-pr.ps1 -Action PR    -Title "Short description" -Body "Bullet1`nBullet2"
#   .\scripts\commit-or-pr.ps1 -Action PR    -Branch "feature/my-pr" -Title "..." -Body "..."
#   .\scripts\commit-or-pr.ps1 -Action PR    -IncludeFiles "README.md","api/routes.py" -Title "..." -Body "..."
# Run from repo root. Respects .gitignore: only non-ignored paths are staged (no audit_results.db, .env, etc.).
# Preview: show what would be committed (files + proposed message); no commit.
# -IncludeFiles: optional; only these paths are included (enables file selection). Comma-separated or array.
# PR: fetch + rebase if behind origin (keeps workflow clean), then push to origin and open PR in browser.
# PR always pushes the current branch to origin so the central repo (data-boar) reflects full progress and history.
# If the branch is already pushed (no unpushed commits), PR still runs gh pr create when no open PR exists for the head branch.
# -RunTests: when creating a PR, run the test suite before pushing; exit without pushing if tests fail.

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Preview','Commit','PR')]
    [string]$Action,

    # Empty defaults: Preview lists files only; Commit/PR require -Title (see docs/ops/COMMIT_AND_PR.md).
    [string]$Title = "",

    [string]$Body = "",

    [string]$Branch = "",

    [string[]]$IncludeFiles = @(),

    [switch]$RunTests = $false,

    [switch]$RunVersionSmoke = $false,

    # Safety guard: require Preview before Commit/PR unless explicitly bypassed.
    [switch]$SkipPreviewGuard = $false
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot
$previewStampPath = Join-Path $repoRoot ".git\commit-or-pr.preview.json"

function Invoke-RepoTestSuite {
    param(
        [string]$Context = "tests"
    )

    Write-Host "Running tests before push ($Context)..."
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) {
        & uv run pytest -v -W error
    } else {
        Write-Host "uv not found; falling back to system python pytest." -ForegroundColor Yellow
        & python -m pytest -v -W error
    }
    return $LASTEXITCODE
}

function Invoke-VersionReadinessSmoke {
    $smokeScript = Join-Path $repoRoot "scripts\version-readiness-smoke.ps1"
    if (-not (Test-Path -LiteralPath $smokeScript)) {
        Write-Host "Version readiness smoke script not found; skipping." -ForegroundColor Yellow
        return 0
    }
    Write-Host "Running version readiness smoke..."
    & $smokeScript
    return $LASTEXITCODE
}

# Allow -IncludeFiles "path1,path2" as single string
if ($IncludeFiles.Count -eq 1 -and $IncludeFiles[0] -match ',') {
    $IncludeFiles = $IncludeFiles[0] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

function Set-GhDefaultRepo {
    param(
        [switch]$Quiet
    )

    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        return $false
    }

    $currentDefault = & gh repo view --json nameWithOwner -q ".nameWithOwner" 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($currentDefault)) {
        if (-not $Quiet) {
            Write-Host "gh default repository already configured: $currentDefault"
        }
        return $true
    }

    $remoteUrl = git remote get-url origin 2>$null
    if (-not $remoteUrl) {
        if (-not $Quiet) {
            Write-Host "Could not read 'origin' URL; skipping gh default repository setup." -ForegroundColor Yellow
        }
        return $false
    }

    if ($remoteUrl -notmatch 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
        if (-not $Quiet) {
            Write-Host "Origin is not a GitHub remote; skipping gh default repository setup." -ForegroundColor Yellow
        }
        return $false
    }

    $owner = $Matches[1]
    $repo = ($Matches[2] -replace '\.git$', '')
    $repoSlug = "$owner/$repo"
    if (-not $Quiet) {
        Write-Host "Configuring gh default repository from origin: $repoSlug"
    }
    & gh repo set-default $repoSlug
    if ($LASTEXITCODE -ne 0) {
        if (-not $Quiet) {
            Write-Host "Failed to configure gh default repository '$repoSlug'." -ForegroundColor Yellow
        }
        return $false
    }

    $verifiedDefault = & gh repo view --json nameWithOwner -q ".nameWithOwner" 2>$null
    if ($LASTEXITCODE -eq 0 -and $verifiedDefault -eq $repoSlug) {
        if (-not $Quiet) {
            Write-Host "gh default repository set to: $verifiedDefault"
        }
        return $true
    }

    if (-not $Quiet) {
        Write-Host "gh default repository was set, but verification failed. You can run: gh repo set-default $repoSlug" -ForegroundColor Yellow
    }
    return $false
}

# Changed + untracked files; only include paths not ignored by .gitignore
$changed = @()
$changed += git diff --name-only
$changed += git diff --name-only --cached
$changed += git ls-files --others --exclude-standard
$changed = $changed | Sort-Object -Unique
$toAdd = @()
foreach ($p in $changed) {
    if (-not $p) { continue }
    git check-ignore -q $p 2>$null
    if ($LASTEXITCODE -ne 0) { $toAdd += $p }
}

# Optional: restrict to selected files only (file selection)
if ($IncludeFiles.Count -gt 0) {
    $toAdd = @($toAdd | Where-Object { $f = $_; $IncludeFiles | Where-Object { $f -eq $_ -or $f -like "$_*" -or $f -replace '\\','/' -like "$($_ -replace '\\','/')*" } })
}

function Get-ScopeFingerprint([string[]]$paths) {
    if (-not $paths) { return "" }
    $sorted = @($paths | Sort-Object -Unique)
    return [string]::Join("|", $sorted)
}

if ($Action -eq 'PR' -and (Get-Command gh -ErrorAction SilentlyContinue)) {
    [void](Set-GhDefaultRepo -Quiet)
}

# Preview and Commit require something to commit
if (-not $toAdd.Count -and $Action -in 'Preview','Commit') {
    Write-Host "No files to commit (or all changes are ignored by .gitignore)."
    exit 0
}

# PR with nothing to commit: push any existing local commits and open PR (central repo gets full history).
if (-not $toAdd.Count -and $Action -eq 'PR') {
    $branchName = (git rev-parse --abbrev-ref HEAD)
    # Parse ahead count explicitly: git prints "0" when in sync; do not use `-and $countOut` - in PowerShell the
    # integer 0 is falsy and string "0" is truthy; mixed behavior caused false "1 ahead" and wrong branches.
    $ahead = 0
    $countOut = git rev-list --count "origin/$branchName..HEAD" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $parsedAhead = 0
        if ($null -ne $countOut -and [int]::TryParse($countOut.Trim(), [ref]$parsedAhead)) {
            $ahead = $parsedAhead
        }
    } else {
        # No origin/<branch> or rev-list failed (e.g. first push): assume local commits may need pushing.
        $ahead = 1
    }
    if ($ahead -gt 0) {
        if ($RunTests) {
            $testExit = Invoke-RepoTestSuite -Context "-RunTests"
            if ($testExit -ne 0) { Write-Host "Tests failed. Fix failures before pushing. No push performed." -ForegroundColor Red; exit 1 }
        }
        if ($RunVersionSmoke) {
            $smokeExit = Invoke-VersionReadinessSmoke
            if ($smokeExit -ne 0) { Write-Host "Version readiness smoke failed. No push performed." -ForegroundColor Red; exit 1 }
        }
        Write-Host "No new changes to commit; pushing $ahead existing local commit(s) and opening PR..."
        git fetch origin 2>$null
        $behind = git rev-list --count "HEAD..origin/$branchName" 2>$null
        if ($LASTEXITCODE -eq 0 -and $behind -and [int]$behind -gt 0) {
            Write-Host "Branch is behind origin/$branchName by $behind commit(s). Pulling with rebase..."
            git pull --rebase origin $branchName
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Rebase failed (e.g. conflicts). Resolve and run 'git rebase --continue', or 'git rebase --abort' to cancel."
                exit 1
            }
        }
        git push -u origin $branchName
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $Title = (git log -1 --format=%s)
        $Body = (git log -1 --format=%b)
        if (-not $Body) { $Body = "See commits for details." }
        $prOpened = $false
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            $bodyFile = [System.IO.Path]::GetTempFileName()
            $Body | Set-Content -Path $bodyFile -Encoding utf8
            try {
                $baseBranch = "main"
                $ref = gh repo view --json defaultBranchRef -q ".defaultBranchRef.name" 2>$null
                if ($ref) { $baseBranch = $ref }
                & gh pr create --title $Title --body-file $bodyFile --base $baseBranch --web
                if ($LASTEXITCODE -eq 0) { $prOpened = $true; Write-Host "Browser opened. Review and click 'Create pull request'." }
            } finally { Remove-Item -LiteralPath $bodyFile -ErrorAction SilentlyContinue }
        }
        if (-not $prOpened) {
            $remoteUrl = git remote get-url origin 2>$null
            if ($remoteUrl -match 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
                $defaultBranch = "main"
                if (Get-Command gh -ErrorAction SilentlyContinue) {
                    $ref = gh repo view --json defaultBranchRef -q ".defaultBranchRef.name" 2>$null
                    if ($ref) { $defaultBranch = $ref }
                } else {
                    $sym = git symbolic-ref refs/remotes/origin/HEAD 2>$null
                    if ($sym) { $defaultBranch = $sym -replace '^refs/remotes/origin/', '' }
                }
                $compareUrl = "https://github.com/$($Matches[1])/$($Matches[2].TrimEnd('.git'))/compare/$defaultBranch...$branchName"
                Write-Host "On GitHub, set base repository to $($Matches[1])/$($Matches[2].TrimEnd('.git')) and base branch to $defaultBranch (same repo = no fork)."
                Start-Process $compareUrl
            }
        }
        exit 0
    }
    # Already synced with origin: open a PR if GitHub has none for this branch (avoids silent skip after manual push).
    Write-Host "No unpushed commits on '$branchName'. Checking for an existing PR..."
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $prJson = gh pr list --head $branchName --json number 2>$null
        $hasPr = $false
        if ($prJson) {
            try {
                $arr = $prJson | ConvertFrom-Json
                if ($arr -and @($arr).Count -gt 0) { $hasPr = $true }
            } catch { }
        }
        if ($hasPr) {
            Write-Host "A pull request already exists for '$branchName'. Nothing to do."
            exit 0
        }
        if ([string]::IsNullOrWhiteSpace($Title)) {
            Write-Host "commit-or-pr: Branch is already pushed; -Title is required for gh pr create." -ForegroundColor Red
            Write-Host "Example: .\scripts\commit-or-pr.ps1 -Action PR -Title `"feat: my change`" -Body `"`"- detail`"`n- detail`"`""
            exit 1
        }
        $bodyFile = [System.IO.Path]::GetTempFileName()
        $prBodySynced = if (-not [string]::IsNullOrWhiteSpace($Body)) { $Body } else { "See commits on branch '$branchName'." }
        $prBodySynced | Set-Content -Path $bodyFile -Encoding utf8
        try {
            $baseBranch = "main"
            $ref = gh repo view --json defaultBranchRef -q ".defaultBranchRef.name" 2>$null
            if ($ref) { $baseBranch = $ref }
            & gh pr create --title $Title --body-file $bodyFile --base $baseBranch --head $branchName
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Created pull request for '$branchName' (was already pushed)."
                exit 0
            }
        } finally {
            Remove-Item -LiteralPath $bodyFile -ErrorAction SilentlyContinue
        }
        Write-Host "gh pr create failed (auth, fork, or branch). Open the compare URL from your repo or fix gh."
        exit $LASTEXITCODE
    }
    Write-Host "Nothing to commit, branch is up to date, and 'gh' is not available. Install GitHub CLI or create the PR in the browser."
    exit 0
}

if ($Action -eq 'Preview') {
    Write-Host "=== Preview (no commit) ===" -ForegroundColor Cyan
    Write-Host "Files that would be included (use -IncludeFiles to select only some):"
    $toAdd | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
    Write-Host "Summary (diff --stat):"
    $untracked = $toAdd | Where-Object { -not (git ls-files --error-unmatch $_ 2>$null) }
    $untracked = @($untracked)
    if ($untracked.Count -gt 0) {
        git add -N $untracked 2>$null
        git diff --cached --stat -- $untracked
        git reset $untracked 2>$null
    }
    git diff --stat -- $toAdd
    git diff --cached --stat -- $toAdd
    Write-Host ""
    if ([string]::IsNullOrWhiteSpace($Title)) {
        Write-Host "NOTE: You did not pass -Title / -Body. There is no auto-generated commit message." -ForegroundColor Yellow
        Write-Host "      For -Action Commit or -Action PR you must supply -Title and usually -Body (see docs/ops/COMMIT_AND_PR.md)." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Proposed commit title: (not set - pass -Title)"
        Write-Host "Proposed body: (not set - pass -Body, e.g. bullet lines separated by ``n)"
    } else {
        Write-Host "Proposed commit title: $Title"
        Write-Host "Proposed body (will appear in PR description):"
        if (-not [string]::IsNullOrWhiteSpace($Body)) {
            $Body -split "`n" | ForEach-Object { Write-Host "  $_" }
        } else {
            Write-Host "  (empty - optional)"
        }
    }
    Write-Host ""
    $branchName = (git rev-parse --abbrev-ref HEAD)
    $stamp = @{
        branch = $branchName
        created_at_utc = [DateTime]::UtcNow.ToString("o")
        file_count = @($toAdd).Count
        scope_fingerprint = (Get-ScopeFingerprint $toAdd)
    }
    $stamp | ConvertTo-Json -Depth 3 | Set-Content -Path $previewStampPath -Encoding utf8
    Write-Host "Preview stamp saved to .git/commit-or-pr.preview.json"
    Write-Host ""
    Write-Host "To include only specific files, run with -IncludeFiles ""path1"",""path2""."
    Write-Host "Run with -Action Commit to commit locally, or -Action PR to push and open PR in browser."
    exit 0
}

# Optional: switch to or create PR branch before committing
if ($Action -eq 'PR' -and $Branch) {
    $currentBranch = (git rev-parse --abbrev-ref HEAD)
    if ($currentBranch -ne $Branch) {
        # Check if branch exists (we only use $LASTEXITCODE; discard output)
        $null = git rev-parse --verify "refs/heads/$Branch" 2>$null
        if ($LASTEXITCODE -eq 0) {
            git checkout $Branch
        } else {
            git checkout -b $Branch
        }
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Host "Switched from '$currentBranch' to branch '$Branch'."
    }
}

if ([string]::IsNullOrWhiteSpace($Title)) {
    Write-Host "commit-or-pr: -Title is required for Commit/PR when there are changes to commit." -ForegroundColor Red
    Write-Host "Example: .\scripts\commit-or-pr.ps1 -Action Commit -Title `"feat: FN reduction slice`" -Body `"`"- MEDIUM threshold config`"`n- Suggested review sheet`"`""
    exit 1
}

if (-not $SkipPreviewGuard) {
    if (-not (Test-Path -LiteralPath $previewStampPath)) {
        Write-Host "commit-or-pr safety guard: no Preview stamp found." -ForegroundColor Yellow
        Write-Host "Run: .\scripts\commit-or-pr.ps1 -Action Preview"
        Write-Host "Or bypass once with -SkipPreviewGuard."
        exit 1
    }
    $stampRaw = Get-Content -LiteralPath $previewStampPath -Raw -ErrorAction SilentlyContinue
    $stamp = $null
    try { $stamp = $stampRaw | ConvertFrom-Json } catch { $stamp = $null }
    if (-not $stamp) {
        Write-Host "commit-or-pr safety guard: invalid Preview stamp. Re-run Preview." -ForegroundColor Yellow
        exit 1
    }
    $currentBranch = (git rev-parse --abbrev-ref HEAD)
    $currentFp = Get-ScopeFingerprint $toAdd
    if (($stamp.branch -ne $currentBranch) -or ($stamp.scope_fingerprint -ne $currentFp)) {
        Write-Host "commit-or-pr safety guard: scope changed since Preview (branch or file set differs)." -ForegroundColor Yellow
        Write-Host "Run Preview again to confirm scope, then Commit/PR."
        Write-Host "Current branch: $currentBranch | Stamped branch: $($stamp.branch)"
        exit 1
    }
}

foreach ($f in $toAdd) { git add -- $f }
git status -sb

# Use separate -m for title and body so both are passed as single arguments (no word-split)
$bodyForCommit = if (-not [string]::IsNullOrWhiteSpace($Body)) { $Body } else { "See diff for details." }
git commit -m "$Title" -m "$bodyForCommit"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Committed: $Title"

if ($Action -eq 'PR') {
    $branchName = (git rev-parse --abbrev-ref HEAD)
    if ($RunTests) {
        $testExit = Invoke-RepoTestSuite -Context "-RunTests"
        if ($testExit -ne 0) { Write-Host "Tests failed. Fix failures before pushing. No push performed." -ForegroundColor Red; exit 1 }
    }
    if ($RunVersionSmoke) {
        $smokeExit = Invoke-VersionReadinessSmoke
        if ($smokeExit -ne 0) { Write-Host "Version readiness smoke failed. No push performed." -ForegroundColor Red; exit 1 }
    }
    git fetch origin 2>$null
    $behind = git rev-list --count "HEAD..origin/$branchName" 2>$null
    if ($LASTEXITCODE -eq 0 -and $behind -and [int]$behind -gt 0) {
        Write-Host "Branch is behind origin/$branchName by $behind commit(s). Pulling with rebase..."
        git pull --rebase origin $branchName
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Rebase failed (e.g. conflicts). Resolve and run 'git rebase --continue', or 'git rebase --abort' to cancel."
            exit 1
        }
    }
    git push -u origin $branchName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Pushed branch '$branchName'. Opening PR in browser (form pre-filled)..."

    $prOpened = $false
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $bodyFile = [System.IO.Path]::GetTempFileName()
        $bodyForCommit | Set-Content -Path $bodyFile -Encoding utf8
        try {
            $baseBranch = "main"
            $ref = gh repo view --json defaultBranchRef -q ".defaultBranchRef.name" 2>$null
            if ($ref) { $baseBranch = $ref }
            & gh pr create --title $Title --body-file $bodyFile --base $baseBranch --web
            if ($LASTEXITCODE -eq 0) {
                $prOpened = $true
                Write-Host "Browser opened. Review the pre-filled title and description, then click 'Create pull request'."
            }
        } finally {
            Remove-Item -LiteralPath $bodyFile -ErrorAction SilentlyContinue
        }
    }

    if (-not $prOpened) {
        $remoteUrl = git remote get-url origin 2>$null
        if ($remoteUrl -match 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
            $owner = $Matches[1]
            $repo = $Matches[2].TrimEnd('.git')
            $defaultBranch = "main"
            if (Get-Command gh -ErrorAction SilentlyContinue) {
                $ref = gh repo view --json defaultBranchRef -q ".defaultBranchRef.name" 2>$null
                if ($ref) { $defaultBranch = $ref }
            } else {
                $sym = git symbolic-ref refs/remotes/origin/HEAD 2>$null
                if ($sym) { $defaultBranch = $sym -replace '^refs/remotes/origin/', '' }
            }
            $compareUrl = "https://github.com/$owner/$repo/compare/${defaultBranch}...${branchName}"
            Write-Host "Opening compare page in browser (create PR there): $compareUrl"
            Write-Host "On GitHub, set base repository to $owner/$repo and base branch to $defaultBranch (same repo = no fork)."
            Start-Process $compareUrl
        } else {
            Write-Host "Push succeeded. Open GitHub, go to your repo, and create a PR from branch '$branchName'."
        }
    }
}
