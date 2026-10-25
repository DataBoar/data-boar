#Requires -Version 7.0
<#
.NAME
 scripts/Resolve-MaestroRoot.ps1

.SYNOPSIS
 Resolve the DataBoar/maestro clone root for consumer wrappers (spinout #8).

.DESCRIPTION
 Fail-closed: never falls back to the removed data-boar/scripts/maestro/ tree.
 Order: -Hint, MAESTRO_ROOT, sibling ../maestro or ../Maestro next to this repo.

.EXAMPLE
 . ./scripts/Resolve-MaestroRoot.ps1
 $root = Resolve-MaestroRoot -ConsumerRoot (Resolve-Path ..).Path
#>

Set-StrictMode -Version 2

function Test-MaestroRootCandidate {
    param([Parameter(Mandatory = $true)][string]$Candidate)
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $false }
    if (-not (Test-Path -LiteralPath $Candidate)) { return $false }
    return (Test-Path -LiteralPath (Join-Path $Candidate 'core/Maestro.ps1'))
}

function Resolve-MaestroRoot {
    param(
        [string]$Hint = '',
        [string]$ConsumerRoot = ''
    )

    if (-not [string]::IsNullOrWhiteSpace($Hint)) {
        $resolved = (Resolve-Path -LiteralPath $Hint).Path
        if (Test-MaestroRootCandidate -Candidate $resolved) {
            return $resolved
        }
        throw "MAESTRO_ROOT hint is not a Maestro clone (missing core/Maestro.ps1): $resolved"
    }

    $envRoot = [Environment]::GetEnvironmentVariable('MAESTRO_ROOT')
    if (-not [string]::IsNullOrWhiteSpace($envRoot) -and (Test-MaestroRootCandidate -Candidate $envRoot)) {
        return (Resolve-Path -LiteralPath $envRoot).Path
    }

    $consumer = $ConsumerRoot
    if ([string]::IsNullOrWhiteSpace($consumer)) {
        if ($PSScriptRoot) {
            $consumer = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
        } else {
            $consumer = (Get-Location).Path
        }
    } else {
        $consumer = (Resolve-Path -LiteralPath $consumer).Path
    }

    $parent = Split-Path -Parent $consumer
    foreach ($name in @('maestro', 'Maestro')) {
        $candidate = Join-Path $parent $name
        if (Test-MaestroRootCandidate -Candidate $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw @"
Maestro clone not found. Set MAESTRO_ROOT to the DataBoar/maestro checkout, or clone it as a sibling of data-boar (../maestro). Orchestration code no longer lives under data-boar/scripts/maestro/ (spinout complete - see DataBoar/maestro#8).
"@
}

function Resolve-MaestroCoreScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [string]$MaestroRoot = ''
    )
    $root = if ($MaestroRoot) { $MaestroRoot } else { Resolve-MaestroRoot }
    $path = Join-Path (Join-Path $root 'core') $ScriptName
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing Maestro core script: $path"
    }
    return (Resolve-Path -LiteralPath $path).Path
}
