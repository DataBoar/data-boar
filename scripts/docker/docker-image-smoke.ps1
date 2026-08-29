#!/usr/bin/env pwsh
# Post-build smoke for hardened release image (#1028 PR-A). Linux twin: docker-image-smoke.sh
# Usage: .\scripts\docker\docker-image-smoke.ps1 -Image data_boar:lab [-Version 1.7.4]

param(
    [Parameter(Mandatory = $true)]
    [string]$Image,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
# Skip license ENTRYPOINT so smoke measures the interpreter (cp314t), not PYTHON_GIL=1.
$python = "/usr/local/bin/python3.14t"

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "podman not in PATH"
}

function Invoke-ImagePy {
    param([string]$Code)
    podman run --rm --entrypoint $python $Image -c $Code
}

Write-Host "=== docker-image-smoke: $Image ===" -ForegroundColor Cyan

$out = Invoke-ImagePy "from core.about import _package_version; print(_package_version())"
Write-Host "public version -> $out"

if ($Version) {
    if ($out -notmatch "\b$([regex]::Escape($Version))\b") {
        throw "FAIL: expected public version token $Version"
    }
    if ($out -match "$([regex]::Escape($Version))\.\d+") {
        throw "FAIL: maturity octet leaked in public version string"
    }
}

Invoke-ImagePy "import boar_fast_filter; print('boar_fast_filter:', boar_fast_filter.__name__)"

# #1401: in_artifact extras must import
$extras = @'
from core.extras_manifest import assert_in_artifact_imports, load_manifest
m = load_manifest()
assert_in_artifact_imports(m)
print("extras_manifest: ok in_artifact=", sum(1 for e in m.get("extras", {}).values() if e.get("in_artifact")))
'@
Invoke-ImagePy $extras

$tls = @'
import httpx
resp = httpx.get("https://example.com", timeout=20.0, follow_redirects=True)
resp.raise_for_status()
assert resp.status_code == 200, resp.status_code
print("tls_probe: ok status=", resp.status_code)
'@
Invoke-ImagePy $tls

Write-Host "=== docker-image-smoke: PASS ===" -ForegroundColor Green
