#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run recovery / forensic checks after a manual doc bundle mess (NOT a substitute for check-all.ps1).

.DESCRIPTION
    1) Pytest compile checks for: audit_concatenated_markdown.py, audit_concat_sliding_window.py,
       export_public_gemini_bundle.py, build_final_round_bucket_concat.py.
    2) Optionally runs sliding-window + H1 audits on a saved concatenated blob.

    Full operator narrative: docs/ops/DOC_BUNDLE_RECOVERY_PLAYBOOK.md

.PARAMETER BundlePath
    Optional path to a concatenated Markdown/text file (often under docs/private/...).

.PARAMETER SlidingWindow
    Line count for audit_concat_sliding_window.py (default 25).

.PARAMETER Headerless
    Pass --strip-bundle-markers to sliding-window (typical for blobs without --- FILE: --- markers).

.PARAMETER SkipPytest
    Skip step 1 (only run bundle forensics when BundlePath is set).

.PARAMETER IncludeH1Audit
    Also run audit_concatenated_markdown.py (verbose chunk output).

.PARAMETER DryRun
    Print commands that would run for the bundle steps without executing them.

.EXAMPLE
    .\scripts\recovery-doc-bundle-sanity.ps1

.EXAMPLE
    .\scripts\recovery-doc-bundle-sanity.ps1 -BundlePath "docs\private\mess_concatenated_gemini_sanity_check\sobre-data-boar.md" -Headerless
#>
param(
    [string]$BundlePath = "",
    [int]$SlidingWindow = 25,
    [switch]$Headerless,
    [switch]$SkipPytest,
    [switch]$IncludeH1Audit,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "=== recovery-doc-bundle-sanity (forensics helper, not check-all) ===" -ForegroundColor Cyan

if (-not $SkipPytest) {
    Write-Host "`n[1/2] pytest: compile checks for bundle recovery Python scripts..." -ForegroundColor Yellow
    $tests = @(
        "tests/test_scripts.py::test_audit_concatenated_markdown_py_compiles",
        "tests/test_scripts.py::test_audit_concat_sliding_window_py_compiles",
        "tests/test_scripts.py::test_export_public_gemini_bundle_py_compiles",
        "tests/test_scripts.py::test_build_final_round_bucket_concat_py_compiles"
    )
    if ($DryRun) {
        Write-Host "uv run pytest $($tests -join ' ') -q" -ForegroundColor Gray
    } else {
        & uv run pytest @tests -q
        if ($LASTEXITCODE -ne 0) {
            Write-Host "recovery-doc-bundle-sanity: pytest step FAILED." -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
} else {
    Write-Host "`n[1/2] skipped (-SkipPytest)" -ForegroundColor Yellow
}

if ([string]::IsNullOrWhiteSpace($BundlePath)) {
    Write-Host "`n[2/2] No -BundlePath; skipping sliding-window / H1 audits." -ForegroundColor Yellow
    Write-Host "Tip: pass -BundlePath and optionally -Headerless -IncludeH1Audit - see DOC_BUNDLE_RECOVERY_PLAYBOOK.md" -ForegroundColor Gray
    Write-Host "recovery-doc-bundle-sanity: OK (tooling step only)." -ForegroundColor Green
    exit 0
}

$resolved = Join-Path $repoRoot $BundlePath
if (-not (Test-Path -LiteralPath $resolved)) {
    Write-Host "ERROR: bundle not found: $resolved" -ForegroundColor Red
    exit 2
}

$slideArgs = @(
    "run", "python", "scripts/audit_concat_sliding_window.py",
    "-i", $resolved,
    "--repo-root", $repoRoot,
    "--window", $SlidingWindow.ToString(),
    "--show-sample-matches", "12",
    "--max-gaps", "12"
)
if ($Headerless) {
    $slideArgs += "--strip-bundle-markers"
}

Write-Host "`n[2/2] Sliding-window audit..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "uv $($slideArgs -join ' ')" -ForegroundColor Gray
} else {
    & uv @slideArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "recovery-doc-bundle-sanity: sliding-window script exited $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

if ($IncludeH1Audit) {
    Write-Host "`n[2b] H1-split audit (verbose)..." -ForegroundColor Yellow
    $h1Args = @("run", "python", "scripts/audit_concatenated_markdown.py", "-i", $resolved, "--repo-root", $repoRoot)
    if ($DryRun) {
        Write-Host "uv $($h1Args -join ' ')" -ForegroundColor Gray
    } else {
        & uv @h1Args
        if ($LASTEXITCODE -ne 0) {
            Write-Host "recovery-doc-bundle-sanity: H1 audit exited $LASTEXITCODE" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
}

Write-Host "`nrecovery-doc-bundle-sanity: OK." -ForegroundColor Green
exit 0
