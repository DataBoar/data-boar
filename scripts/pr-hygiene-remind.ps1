#!/usr/bin/env pwsh
# PR hygiene reminders + optional quick PR checks.
# Usage (from repo root): .\scripts\pr-hygiene-remind.ps1
#        (optional checks): .\scripts\pr-hygiene-remind.ps1 -RunQuickChecks
# See: docs/ops/README.md S. "Before you open a PR", CONTRIBUTING.md, AGENTS.md, docs/plans/TOKEN_AWARE_USAGE.md

param(
    [switch]$RunQuickChecks = $false
)

Write-Host "=== PR hygiene (reminders only) ===" -ForegroundColor Cyan
Write-Host "1. Full gate:  .\scripts\check-all.ps1   (or: plans-stats --write, pre-commit, pytest -W error)"
Write-Host "2. Never commit:  docs/private/   (real inventory  - gitignored)"
Write-Host "3. Never:  git add -f config.yaml   (secrets / LAN paths)"
Write-Host "4. Template:  docs/private.example/  -> copy to docs/private/  (policy: PRIVATE_OPERATOR_NOTES.md)"
Write-Host "5. Agents: no real hostnames, RFC1918 IPs, serials, or home paths in tracked Markdown/code comments."
Write-Host "6. Commit subjects: type(scope): ...  - e.g. chore(deps):, docs(homelab):, docs(workflow):  - see AGENTS.md table."
Write-Host "7. gh preflight:  .\scripts\gh-ensure-default.ps1   (avoid 'No default remote repository' errors)"
Write-Host "8. Stop conditions: failing checks, mergeable != MERGEABLE, or conflicts -> do not merge; fix first."
Write-Host "9. Slack (AFK): repo secret SLACK_WEBHOOK_URL -> Actions -> Slack operator ping (manual); CI failure -> Slack notify workflow (see OPERATOR_NOTIFICATION_CHANNELS.md)."
Write-Host "=== end ===" -ForegroundColor Cyan

if (-not $RunQuickChecks) {
    exit 0
}

Write-Host ""
Write-Host "=== PR quick checks ===" -ForegroundColor Cyan
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "gh not found in PATH. Install/auth gh or run checks in GitHub UI." -ForegroundColor Yellow
    exit 0
}

& (Join-Path $PSScriptRoot "gh-ensure-default.ps1") -Quiet

$prsJson = gh pr list --state open --json number,title,headRefName,url 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($prsJson)) {
    Write-Host "Could not list open PRs (gh auth/repo context)."
    exit 0
}

try {
    $prs = $prsJson | ConvertFrom-Json
} catch {
    Write-Host "Could not parse open PR list."
    exit 0
}

if (-not $prs -or @($prs).Count -eq 0) {
    Write-Host "No open PRs found."
    exit 0
}

foreach ($pr in @($prs)) {
    Write-Host ""
    Write-Host ("PR #{0} [{1}] - {2}" -f $pr.number, $pr.headRefName, $pr.title)
    Write-Host ("URL: {0}" -f $pr.url)
    gh pr checks $pr.number 2>$null
}

Write-Host "=== end PR quick checks ===" -ForegroundColor Cyan
