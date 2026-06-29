#Requires -Version 5.1
<#
.SYNOPSIS
    Gate trailer SSH ed25519 attestation wrapper (ADR-0056 file namespace + ADR-0071).

.DESCRIPTION
    Thin wrapper over scripts/gate_trailer_attest.py. Verifies or signs the decorative
    file-namespace SSH signature over a Gate-Change-Approved-By / Gate-Close-Approved-By line.

.EXAMPLE
    .\scripts\gate-trailer-attest.ps1 verify -Commit 888f175e
    .\scripts\gate-trailer-attest.ps1 sign -Text 'Gate-Change-Approved-By: @FabioLeitao | ...' -Key $env:USERPROFILE\.ssh\id_ed25519_attest
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
try {
    if (-not (Get-Command ssh-keygen -ErrorAction SilentlyContinue)) {
        Write-Error "gate-trailer-attest.ps1: ssh-keygen not on PATH."
        exit 2
    }
    $pyArgs = @("run", "python", "scripts/gate_trailer_attest.py") + $Args
    & uv @pyArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
