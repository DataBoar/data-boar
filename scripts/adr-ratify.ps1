#Requires -Version 5.1
<#
.SYNOPSIS
    Operator HITL stamp for ADR ratification rounds (INVENTORY RATIFIED_BY + signed commit).

.DESCRIPTION
    Thin wrapper over inv-adr.ps1 -RatifiedBy for numbered ratification rounds.
    Round 2 (ADR-0068) is not a gate-file ADR - no Gate-Change-Approved-By trailer.

.PARAMETER Round
    Ratification round: 1 = ADR-0060/0063/0071/0072; 2 = ADR-0068.

.PARAMETER RatifiedBy
    Operator GitHub handle. Default @FabioLeitao.

.EXAMPLE
    .\scripts\adr-ratify.ps1 -Round 2
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet(1, 2)]
    [int]$Round,
    [string]$RatifiedBy = '@FabioLeitao'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$roundAdrs = @{
    1 = @('0060', '0063', '0071', '0072')
    2 = @('0068')
}

$gateFileAdrs = @{
    1 = @('0071')
}

$numbers = $roundAdrs[$Round]
$invAdr = Join-Path $PSScriptRoot 'inv-adr.ps1'
& $invAdr -RatifiedBy $RatifiedBy -StampOnlyNumbers $numbers -Write
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$isGate = $false
if ($gateFileAdrs.ContainsKey($Round)) {
    foreach ($g in $gateFileAdrs[$Round]) {
        if ($numbers -contains $g) { $isGate = $true; break }
    }
}

Write-Host "Round $Round stamp: $($numbers -join ', ')"
Write-Host "gate: $(if ($isGate) { 'sim (Gate-Change-Approved-By se aplicavel)' } else { 'nao' })"
Write-Host "Next: git add docs/adr/INVENTORY.txt && git commit -S --trailer `"ADR-Ratified-By: $RatifiedBy - $(Get-Date -Format 'yyyy-MM-dd')`""
