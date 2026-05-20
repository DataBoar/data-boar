# Validate docs/hubs/INDEX.md and docs/plans/PRIMERS_HUB.md link targets.
# Linux/macOS twin: scripts/check-hubs.sh
$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot
& python "$repoRoot\scripts\check_hubs.py"
exit $LASTEXITCODE
