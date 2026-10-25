# Verify release manifest JSON: each file path must exist and SHA-256 must match.
# Usage: .\scripts\release-integrity-check.ps1 -ManifestPath path\to\manifest.json
# Run from repo root. Exits 0 if OK, 1 on mismatch or error.

param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

$ErrorActionPreference = "Stop"
$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Write-Error "Manifest not found: $ManifestPath"
    exit 1
}

$json = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$files = $json.files
if (-not $files) {
    Write-Error "Manifest has no 'files' array."
    exit 1
}

foreach ($item in $files) {
    $rel = $item.path
    $want = ($item.sha256).ToLower()
    if (-not $rel -or -not $want) { continue }
    $fp = Join-Path $root $rel
    if (-not (Test-Path -LiteralPath $fp)) {
        Write-Error "Missing file: $fp"
        exit 1
    }
    $hash = Get-FileHash -LiteralPath $fp -Algorithm SHA256
    $got = $hash.Hash.ToLower()
    if ($got -ne $want) {
        Write-Error "SHA-256 mismatch for ${rel}: expected $want got $got"
        exit 1
    }
}

Write-Host "release-integrity-check: OK ($($files.Count) file(s))."
exit 0
