# Local triage for maintenance rows -1 (Dependabot) and -1b (Docker Scout image).
# Does not modify the repo. Run from repo root after `gh auth login` and (for Scout) Docker Desktop.
# Usage: .\scripts\maintenance-check.ps1
# See SECURITY.md, docs/ops/COMMIT_AND_PR.md, and .cursor/rules/dependabot-hygiene.mdc.

$ErrorActionPreference = "Continue"
Write-Host "=== Maintenance check: Dependabot + Docker Scout ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "## Open Dependabot PRs (GitHub CLI)" -ForegroundColor Yellow
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh pr list --state open --author "dependabot[bot]" --limit 25 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "(gh pr list exited $LASTEXITCODE  - check auth: gh auth login)" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "GitHub CLI (gh) not found. Install: https://cli.github.com/" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "## Open Dependabot security alerts (GitHub API)" -ForegroundColor Yellow
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $repoJson = gh repo view --json nameWithOwner 2>$null
    if ($LASTEXITCODE -eq 0 -and $repoJson) {
        try {
            $nameWithOwner = ($repoJson | ConvertFrom-Json).nameWithOwner
            if ($nameWithOwner) {
                $alertsJson = gh api "repos/$nameWithOwner/dependabot/alerts?state=open&per_page=20" 2>$null
                if ($LASTEXITCODE -eq 0 -and $alertsJson) {
                    $parsed = $alertsJson | ConvertFrom-Json
                    if ($null -eq $parsed) {
                        $alerts = @()
                    } elseif ($parsed -is [System.Array]) {
                        $alerts = $parsed
                    } else {
                        $alerts = @($parsed)
                    }
                    if ($alerts.Count -gt 0) {
                        foreach ($a in $alerts) {
                            $pkg = $a.dependency.package.name
                            $sev = $a.security_advisory.severity
                            $num = $a.number
                            Write-Host "  - #$num  $sev  $pkg  $($a.security_advisory.summary)"
                        }
                        Write-Host "  Triage: docs/ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md (pyOpenSSL/Snowflake); docs/ops/DEPENDABOT_PYGMENTS_CVE.md (pygments)" -ForegroundColor DarkGray
                    } else {
                        Write-Host "  (none open)" -ForegroundColor DarkGray
                    }
                } else {
                    Write-Host "  (could not list alerts  - permissions or auth: gh auth login)" -ForegroundColor DarkYellow
                }
            }
        } catch {
            Write-Host "  (parse error; skip alerts section)" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "  (not a gh repo or gh repo view failed)" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  (skipped  - gh not installed)" -ForegroundColor DarkYellow
}
Write-Host ""

Write-Host "## Docker Scout quickview (published image)" -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker scout quickview fabioleitao/data_boar:latest 2>&1
} else {
    Write-Host "Docker not found; skip Scout (install Docker Desktop for local quickview)." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "## Next steps" -ForegroundColor Green
Write-Host "  1. Merge or apply Dependabot changes only after: .\scripts\check-all.ps1 (and CI green on PR)."
Write-Host "  2. For image CVEs: rebuild/push image after Dockerfile / deps fixes; re-run Scout on the new digest."
Write-Host "  3. Local Docker hygiene: .\scripts\docker-lab-build.ps1, .\scripts\docker-hub-pull.ps1, .\scripts\docker-prune-local.ps1 -WhatIf (see scripts\docker\README.md)."
Write-Host "  4. requirements.txt is uv-exported; wheel/pip are not direct app deps  - Dockerfile upgrades pip/wheel in build + runtime."
