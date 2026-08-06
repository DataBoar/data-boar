#Requires -Version 5.1
<#
.SYNOPSIS
    Windows equivalent of clean-slate PII self-audit: fresh git clone + pii_history_guard + test_pii_guard.

.DESCRIPTION
    primary-dev-workstation-safe: only creates/removes a directory under %TEMP% (or -TempCloneName), never the canonical repo root.
    Clones the public repo into %TEMP%, runs uv sync, then:
      uv run python scripts/pii_history_guard.py --full-history
      uv run pytest tests/test_pii_guard.py -q
    Optional: talent placeholder guards from docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md section D.
    Does NOT rewrite Git history. For destructive reset of your main working tree on Linux, use
    docs/private/scripts/clean-slate.sh (from clean-slate.sh.example).

.PARAMETER RepoUrl
    HTTPS clone URL (default: public GitHub repo).

.PARAMETER TempCloneName
    Folder name under $env:TEMP (default: data-boar-pii-audit-timestamp).

.PARAMETER KeepClone
    Keep the temporary clone after run (for manual inspection).

.PARAMETER IncludeTalentGuards
    Also run tests/test_talent_public_script_placeholders.py and tests/test_talent_ps1_tracked_no_inline_pool.py.

.PARAMETER SkipUvSync
    Skip uv sync if you only need a quick re-run inside an existing kept clone.

.EXAMPLE
    .\scripts\pii-fresh-clone-audit.ps1

.EXAMPLE
    .\scripts\pii-fresh-clone-audit.ps1 -KeepClone -IncludeTalentGuards
#>
param(
    [string]$RepoUrl = "https://github.com/DataBoar/data-boar.git",
    [string]$TempCloneName = "",
    [switch]$KeepClone,
    [switch]$IncludeTalentGuards,
    [switch]$SkipUvSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $TempCloneName) {
    $ts = Get-Date -Format "yyyyMMdd-HHmmss"
    $TempCloneName = "data-boar-pii-audit-$ts"
}

$tempRoot = $env:TEMP
$clonePath = Join-Path $tempRoot $TempCloneName

Write-Host ""
Write-Host "=== PII fresh-clone audit (Windows) ===" -ForegroundColor Cyan
Write-Host "RepoUrl:    $RepoUrl"
Write-Host "ClonePath:  $clonePath"
Write-Host "KeepClone:  $KeepClone"
Write-Host ""

if (Test-Path -LiteralPath $clonePath) {
    Write-Host "Removing existing temp path..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $clonePath -Recurse -Force
}

Write-Host ">>> git clone" -ForegroundColor Yellow
git clone --branch main $RepoUrl $clonePath
if ($LASTEXITCODE -ne 0) {
    throw "git clone failed. Check network and URL."
}

Push-Location $clonePath
try {
    if (-not $SkipUvSync) {
        Write-Host ">>> uv sync" -ForegroundColor Yellow
        uv sync
        if ($LASTEXITCODE -ne 0) { throw "uv sync failed." }
    }

    Write-Host ">>> pii_history_guard.py --full-history" -ForegroundColor Yellow
    uv run python scripts/pii_history_guard.py --full-history
    if ($LASTEXITCODE -ne 0) { throw "pii_history_guard failed." }

    Write-Host ">>> pytest tests/test_pii_guard.py" -ForegroundColor Yellow
    uv run pytest tests/test_pii_guard.py -q
    if ($LASTEXITCODE -ne 0) { throw "test_pii_guard failed." }

    if ($IncludeTalentGuards) {
        Write-Host ">>> pytest talent placeholder guards" -ForegroundColor Yellow
        uv run pytest tests/test_talent_public_script_placeholders.py tests/test_talent_ps1_tracked_no_inline_pool.py -q
        if ($LASTEXITCODE -ne 0) { throw "talent guard tests failed." }
    }

    Write-Host ""
    Write-Host "PII fresh-clone audit: OK" -ForegroundColor Green
    exit 0
}
finally {
    Pop-Location
    if (-not $KeepClone -and (Test-Path -LiteralPath $clonePath)) {
        Remove-Item -LiteralPath $clonePath -Recurse -Force
        Write-Host "Removed temp clone: $clonePath" -ForegroundColor DarkGray
    } elseif ($KeepClone) {
        Write-Host "Kept temp clone: $clonePath" -ForegroundColor DarkGray
    }
}
