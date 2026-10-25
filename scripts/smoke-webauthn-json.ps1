# Runs pytest subset for WebAuthn JSON RP (Phase 1a). ASCII-only for PowerShell 5.1.
# Full gate: .\scripts\check-all.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

uv run pytest tests/test_webauthn_rp.py tests/test_webauthn_session_cookie.py -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "smoke-webauthn-json: OK"
