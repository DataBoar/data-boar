# Audit scripts/*.ps1 vs .sh twins and SCRIPTS_CROSS_PLATFORM_PAIRING.md
# Linux/macOS twin: scripts/check-cross-platform-gaps.sh
param(
    [switch]$MissingOnly
)
$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot
$pyArgs = @("$repoRoot\scripts\check_cross_platform_gaps.py")
if ($MissingOnly) {
    $pyArgs += "--missing-only"
}
& python @pyArgs
exit $LASTEXITCODE
