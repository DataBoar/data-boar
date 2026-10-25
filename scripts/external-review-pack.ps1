param(
    [string]$DateStamp = "",
    [switch]$IncludePlans = $false,
    [switch]$IncludeCursor = $false
)

$ErrorActionPreference = "Stop"

function Assert-ExternalReviewDateStamp {
    <#
    .SYNOPSIS
      Reject DateStamp values that are not YYYY-MM-DD (#1192).
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )
    if ($Value -notmatch '^\d{4}-\d{2}-\d{2}$') {
        throw "Invalid -DateStamp '$Value' - expected YYYY-MM-DD."
    }
}

if ([string]::IsNullOrWhiteSpace($DateStamp)) {
    $DateStamp = (Get-Date).ToString("yyyy-MM-dd")
}

Assert-ExternalReviewDateStamp -Value $DateStamp

$bundlePath = "docs/private/gemini_bundles/public_bundle_$DateStamp.txt"

Write-Host "=== External review pack ==="
Write-Host "Bundle date: $DateStamp"
Write-Host ""

$argv = @(
    "run",
    "python",
    "scripts/export_public_gemini_bundle.py",
    "--output", $bundlePath,
    "--compliance-yaml",
    "--verify"
)

if ($IncludePlans) { $argv += "--plans" }
if ($IncludeCursor) { $argv += "--cursor" }

Write-Host "[1/3] Building Gemini bundle"
Write-Host "uv $($argv -join ' ')"
& uv @argv
if ($LASTEXITCODE -ne 0) {
    throw "Bundle generation/verification failed (exit code $LASTEXITCODE)."
}
Write-Host ""

Write-Host "[2/3] Corporate-Entity-C request source"
Write-Host "- Use: docs/ops/Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md"
Write-Host "- Keep 3 lenses explicit: cumulative / since last WRB / since last published release"
Write-Host ""

Write-Host "[3/3] Gemini prompt source"
Write-Host "- Use: docs/ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md"
Write-Host "- Triage findings in: docs/plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md"
Write-Host ""
Write-Host "Done. Bundle ready at: $bundlePath"
