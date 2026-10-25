param(
    [Parameter(Mandatory = $true)]
    [string]$GitLabRepoUrl,
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "=== GitLab mirror health check ==="
Write-Host "Branch: $Branch"
Write-Host ""

$originSha = (git ls-remote origin "refs/heads/$Branch" | ForEach-Object { ($_ -split "`t")[0] } | Select-Object -First 1)
if (-not $originSha) {
    throw "Could not resolve origin branch SHA for $Branch."
}

$gitlabSha = (git ls-remote $GitLabRepoUrl "refs/heads/$Branch" | ForEach-Object { ($_ -split "`t")[0] } | Select-Object -First 1)
if (-not $gitlabSha) {
    throw "Could not resolve GitLab branch SHA for $Branch."
}

Write-Host "origin/$Branch : $originSha"
Write-Host "gitlab/$Branch : $gitlabSha"
Write-Host ""

if ($originSha -eq $gitlabSha) {
    Write-Host "Mirror status: OK (in sync)" -ForegroundColor Green
    exit 0
}

Write-Host "Mirror status: DRIFT (SHA mismatch)" -ForegroundColor Yellow
Write-Host "Action: check mirror settings and last sync run in GitLab."
exit 2
