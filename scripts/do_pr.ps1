# One-off: run commit-or-pr.ps1 with -Action PR and release description (avoids CLI escaping).
$Title = "Release 1.4.1: version bump, Docker image, SonarQube and docs alignment"
$Body = @"
Build 1.4.1: quality and docs alignment, Docker image published.

- Bump version to 1.4.1 (pyproject.toml, core/about.py, man pages, docs/deploy/DEPLOY.md, PLANS_TODO)
- Application and documentation aligned: operation, config, access (EN and pt-BR in sync)
- All 138 tests pass with no errors or warnings
- Docker image built and pushed: fabioleitao/data_boar:latest (and semver tags as released)
- SonarQube markdown fixes and automation (previous commits); commit-or-pr script used for this release
"@
& (Join-Path $PSScriptRoot "commit-or-pr.ps1") -Action PR -Title $Title -Body $Body
