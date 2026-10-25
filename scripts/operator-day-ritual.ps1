#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Morning or end-of-day operator ritual helpers (carryover + sync close).

.DESCRIPTION
    English session tokens (see .cursor/rules/session-mode-keywords.mdc):
    - carryover-sweep  ->  -Mode Morning
    - eod-sync         ->  -Mode Eod

    Morning Mode runs Tier A readiness by default: git fetch, status, open PRs,
    latest main CI runs, today-mode file existence; then reminders for trust cadence
    (-1 / -1b / -1L). See docs/ops/today-mode/README.md "Morning readiness".

    Does not post to Slack or GitHub; runs local git/gh read-only steps and prints
    paths. Secrets stay in Actions / env per OPERATOR_NOTIFICATION_CHANNELS.

.PARAMETER Mode
    Morning: surface prior today-mode files + private carryover note.
    Eod: git fetch, short log of origin/main since local midnight (progress), status,
    open PRs list, tomorrow today-mode path hint.

.PARAMETER SkipReadiness
    Morning only: skip the daily Tier A block (git fetch, status, gh PRs/CI, today-mode file check).
    Use when you only want the file list + social hints.

.EXAMPLE
    .\scripts\operator-day-ritual.ps1 -Mode Morning

.EXAMPLE
    .\scripts\operator-day-ritual.ps1 -Mode Morning -SkipReadiness

.EXAMPLE
    .\scripts\operator-day-ritual.ps1 -Mode Eod
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Morning", "Eod")]
    [string]$Mode
,

    [Parameter(Mandatory = $false)]
    [int]$Days = 0
,
    [Parameter(Mandatory = $false)]
    [switch]$SkipReadiness
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

function Invoke-GhOptional {
    param([string[]]$GhArgs)
    try {
        & gh @GhArgs 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

if ($Mode -eq "Morning") {
    Write-Host "=== carryover-sweep (Morning) ===" -ForegroundColor Cyan
    $today = [DateTime]::Today.ToString("yyyy-MM-dd")
    $yesterday = [DateTime]::Today.AddDays(-1).ToString("yyyy-MM-dd")
    Write-Host "Calendar yesterday: $yesterday  |  today: $today"
    Write-Host ""

    if (-not $SkipReadiness) {
        Write-Host "=== Readiness Tier A (daily, ~2 min) ===" -ForegroundColor Cyan
        Write-Host "Full ladder: docs/ops/today-mode/README.md (Morning readiness)"
        $prevEap = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        git fetch origin 2>$null | Out-Null
        $ErrorActionPreference = $prevEap
        Write-Host ""
        Write-Host "git status -sb:" -ForegroundColor Yellow
        git status -sb
        Write-Host ""
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            Write-Host "Open PRs (gh):" -ForegroundColor Yellow
            gh pr list --state open --limit 8 2>$null
            Write-Host ""
            Write-Host "Latest CI on main (ci.yml, max 3):" -ForegroundColor Yellow
            gh run list -L 3 --workflow ci.yml --branch main 2>$null
        } else {
            Write-Host "gh not in PATH; skip PR list and CI run list." -ForegroundColor DarkYellow
        }
        Write-Host ""
        $todayModePath = Join-Path $repoRoot ("docs/ops/today-mode/OPERATOR_TODAY_MODE_{0}.md" -f $today)
        if (Test-Path -LiteralPath $todayModePath) {
            Write-Host "Today-mode file: OK  $todayModePath" -ForegroundColor Green
        } else {
            Write-Host "Today-mode file: MISSING for today. Copy template:" -ForegroundColor Yellow
            Write-Host "  docs/ops/today-mode/OPERATOR_TODAY_MODE_TEMPLATE.md -> OPERATOR_TODAY_MODE_$today.md"
        }
        Write-Host ""
    }

    Write-Host "Private rhythm note (gitignored):" -ForegroundColor Yellow
    $carry = Join-Path $repoRoot "docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md"
    if (Test-Path -LiteralPath $carry) {
        Write-Host "  $carry"
    } else {
        Write-Host "  (create from template in session docs if missing) $carry"
    }
    Write-Host ""
    Write-Host "Recent OPERATOR_TODAY_MODE_*.md (open today's first, then yesterday's):" -ForegroundColor Yellow
    Get-ChildItem -Path (Join-Path $repoRoot "docs/ops/today-mode") -Filter "OPERATOR_TODAY_MODE_*.md" -File |
        Where-Object { $_.Name -notlike "*.pt_BR.md" } |
        Sort-Object Name -Descending |
        Select-Object -First 6 |
        ForEach-Object { Write-Host "  $($_.FullName)" }
    Write-Host ""
    Write-Host "Social (private gitignored) - planned posts / hub:" -ForegroundColor Yellow
    $hubSocial = Join-Path $repoRoot "docs\private\social_drafts\editorial\SOCIAL_HUB.md"
    $edSocial = Join-Path $repoRoot "docs\private\social_drafts\editorial"
    if (Test-Path -LiteralPath $hubSocial) {
        Write-Host "  Hub: $hubSocial"
    } else {
        Write-Host "  (no hub file yet) $hubSocial"
    }
    if (Test-Path -LiteralPath $edSocial) {
        Get-ChildItem -Path $edSocial -Filter "EDITORIAL_MASTER_CALENDAR_*.pt_BR.md" -File -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Host "  Calendar: $($_.FullName)" }
    }
    $tomorrowAm = [DateTime]::Today.AddDays(1).ToString("yyyy-MM-dd")
    Write-Host "  Skim Alvo for today ($today) / tomorrow ($tomorrowAm) + draft rows. Doc: docs/ops/today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.md"
    Write-Host ""
    if ($env:DATA_BOAR_VERACRYPT_REMIND -eq "1" -and $env:DATA_BOAR_VERACRYPT_DRIVE) {
        $vl = $env:DATA_BOAR_VERACRYPT_DRIVE.TrimEnd(":").Substring(0, 1).ToUpperInvariant()
        $mountPath = "${vl}:\"
        if (-not (Test-Path -LiteralPath $mountPath)) {
            Write-Host "VeraCrypt: ${vl}: nao montado. Opcional: .\scripts\mount-secure-vault.ps1 -VaultPath `$env:DATA_BOAR_VERACRYPT_CONTAINER -DriveLetter $vl" -ForegroundColor DarkYellow
        }
    }
    Write-Host ""
    Write-Host "=== Trust / prod cadence (B-D: NOT every day; see PLANS_TODO -1 / -1b / -1L) ===" -ForegroundColor Cyan
    Write-Host "  Tier B (-1):  uvx pip-audit -r requirements.txt   (weekly, before release, or after deps work)"
    Write-Host "  Tier C (-1b): docker scout quickview fabioleitao/data_boar:latest   (after Dockerfile/lock/image change)"
    Write-Host "  Tier D (-1L): docs/ops/HOMELAB_VALIDATION.md + optional scripts/lab-op-sync-and-collect.ps1 (second env proof)"
    Write-Host ""
    Write-Host "Optional: uv run pytest tests/test_operator_help_sync.py -v" -ForegroundColor Gray
    exit 0
}

# Eod
Write-Host "=== eod-sync (Eod) ===" -ForegroundColor Cyan
Write-Host "git fetch origin..."
git fetch origin 2>&1 | ForEach-Object { Write-Host $_ }
Write-Host ""

if ($Days -gt 0) {
    $sinceDate  = [DateTime]::Today.AddDays(-$Days).ToString("yyyy-MM-dd")
    $sinceLabel = "last $Days days (since $sinceDate)"
    $sinceArg   = $sinceDate
} else {
    $sinceLabel = "today since midnight"
    $sinceArg   = "midnight"
}
Write-Host "Progress ($sinceLabel, origin/main, max 30):" -ForegroundColor Yellow
$progressLines = @(git -C $repoRoot log origin/main --oneline --since=$sinceArg --format="%ad %s" --date=short -30 2>$null)
if ($progressLines.Count -eq 0 -or ($progressLines.Count -eq 1 -and [string]::IsNullOrWhiteSpace($progressLines[0]))) {
    Write-Host "  (no new commits on origin/main since midnight - or detached/fresh clone)" -ForegroundColor DarkGray
} else {
    foreach ($ln in $progressLines) {
        Write-Host "  $ln"
    }
}
Write-Host ""

Write-Host "Working tree:" -ForegroundColor Yellow
git status -sb
Write-Host ""

if (Invoke-GhOptional @("pr", "list", "--state", "open", "--limit", "15")) {
    Write-Host "Open PRs (gh):" -ForegroundColor Yellow
    gh pr list --state open --limit 15
} else {
    Write-Host "gh not available or failed; skip PR list." -ForegroundColor DarkYellow
}

$tomorrow = [DateTime]::Today.AddDays(1).ToString("yyyy-MM-dd")
$modeEn = Join-Path $repoRoot "docs/ops/today-mode/OPERATOR_TODAY_MODE_$tomorrow.md"
$modePt = Join-Path $repoRoot "docs/ops/today-mode/OPERATOR_TODAY_MODE_$tomorrow.pt_BR.md"
Write-Host ""
Write-Host "Tomorrow today-mode paths (create if missing):" -ForegroundColor Yellow
Write-Host "  $modeEn"
Write-Host "  $modePt"
Write-Host ""
Write-Host "Social (private) - before closing: update SOCIAL_HUB if you published today; skim tomorrow Alvo in editorial/SOCIAL_HUB.md. See docs/ops/today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.md" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Next: merge open PRs when green (.\scripts\pr-merge-when-green.ps1); then git checkout main, git pull, rest." -ForegroundColor Gray
Write-Host ""
Write-Host "Private repo sync (stacked private git):" -ForegroundColor Yellow
Write-Host "  .\scripts\private-git-sync.ps1          # sync feedbacks + commit pending private files"
Write-Host "  .\scripts\private-git-sync.ps1 -Push    # + push stacked private repo remote"
Write-Host "  Chat keyword: private-stack-sync        # see docs/ops/PRIVATE_STACK_SYNC_RITUAL.md"
$privateStatus = git -C (Join-Path $repoRoot "docs/private") status --short 2>$null
if ($privateStatus) {
    Write-Host "  AVISO: Private repo tem arquivos pendentes ($($privateStatus.Count) linhas de status)." -ForegroundColor Yellow
} else {
    Write-Host "  Private repo esta em dia." -ForegroundColor Green
}
exit 0
