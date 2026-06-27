#!/usr/bin/env pwsh
# Post-build smoke for hardened release image (#1028 PR-A). Linux twin: docker-image-smoke.sh
# Usage: .\scripts\docker\docker-image-smoke.ps1 -Image data_boar:lab [-Version 1.7.4]

param(
    [Parameter(Mandatory = $true)]
    [string]$Image,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$python = "/usr/local/bin/python3.13"

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "podman not in PATH"
}

Write-Host "=== docker-image-smoke: $Image ===" -ForegroundColor Cyan

$out = podman run --rm $Image $python -c "from core.about import _package_version; print(_package_version())"
Write-Host "public version -> $out"

if ($Version) {
    if ($out -notmatch "\b$([regex]::Escape($Version))\b") {
        throw "FAIL: expected public version token $Version"
    }
    if ($out -match "$([regex]::Escape($Version))\.\d+") {
        throw "FAIL: maturity octet leaked in public version string"
    }
}

podman run --rm $Image $python -c "import boar_fast_filter; print('boar_fast_filter:', boar_fast_filter.__name__)"

$tls = @'
import httpx
resp = httpx.get("https://example.com", timeout=20.0, follow_redirects=True)
resp.raise_for_status()
assert resp.status_code == 200, resp.status_code
print("tls_probe: ok status=", resp.status_code)
'@
podman run --rm $Image $python -c $tls

Write-Host "=== docker-image-smoke: PASS ===" -ForegroundColor Green
