#Requires -Version 5.1
<#
.SYNOPSIS
    Dispatch PyPI publish via GitHub Actions OIDC (zero local API token).

.DESCRIPTION
    Build and upload happen in CI (.github/workflows/publish-pypi.yml) using PyPI
    Trusted Publishing (OIDC). This wrapper does NOT run uv build or uv publish on
    the workstation. No UV_PUBLISH_TOKEN and no PyPI API token in operator env.

    Release ritual: after GitHub Release, dispatch TestPyPI first, verify install,
    then dispatch production PyPI. See .cursor/rules/release-publish-sequencing.mdc
    and docs/VERSIONING.md. Packaging: ADR-0031; workflow pins: ADR-0005.

.PARAMETER Target
    testpypi (default) or pypi. Production PyPI requires workflow_dispatch with
    environment protection on GitHub.

.PARAMETER Ref
    Git ref for workflow run (default main). Use the release branch or tag ref when
    publishing a specific line from non-main.

.EXAMPLE
    .\scripts\pypi-publish.ps1 -Target testpypi
    .\scripts\pypi-publish.ps1 -Target pypi -Ref main
#>
param(
    [ValidateSet("testpypi", "pypi")]
    [string]$Target = "testpypi",
    [string]$Ref = "main"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "gh: not found. Install GitHub CLI and run gh auth login." -ForegroundColor Red
    exit 1
}

Write-Host "=== PyPI publish dispatch (OIDC via CI) ===" -ForegroundColor Cyan
Write-Host "Target: $Target  Ref: $Ref"
Write-Host "Local uv build/publish: disabled (CI builds dist; OIDC uploads)." -ForegroundColor DarkGray

if ($Target -eq "pypi") {
    Write-Host "Production PyPI: confirm GitHub Release exists and TestPyPI was verified." -ForegroundColor Yellow
}

& gh workflow run publish-pypi.yml --ref $Ref -f "target=$Target"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[OK] Workflow dispatched. Monitor:" -ForegroundColor Green
Write-Host "  gh run list --workflow=publish-pypi.yml --limit 3"
Write-Host "  gh run watch   # use run id from list above"
Write-Host ""
if ($Target -eq "testpypi") {
    Write-Host "Verify package: https://test.pypi.org/project/data-boar/"
} else {
    Write-Host "Verify package: https://pypi.org/project/data-boar/"
    Write-Host "Install smoke:    pipx install data-boar==<version>   # after run succeeds"
}
