#Requires -Version 5.1
<#
.SYNOPSIS
  Fail if the application CycloneDX is missing Cargo.lock crates (#1950).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$app = if ($args.Count -ge 1) { $args[0] } else { "sbom-python.cdx.json" }
$runtime = $null
if ($args.Count -ge 2) {
    $runtime = $args[1]
} elseif (Test-Path -LiteralPath "sbom-docker-image.cdx.json") {
    $runtime = "sbom-docker-image.cdx.json"
}

$cmd = @("python", "scripts/application_sbom.py", "check", "--application", $app)
if ($runtime) {
    $cmd += @("--runtime", $runtime)
}
uv run @cmd
