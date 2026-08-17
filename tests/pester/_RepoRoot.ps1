# Shared repo root for Pester tests (#984).
$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Get-RepoScript {
    param([string]$RelativePath)
    Join-Path $script:RepoRoot ($RelativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Get-ScriptRaw {
    param([string]$RelativePath)
    Get-Content -LiteralPath (Get-RepoScript $RelativePath) -Raw -Encoding UTF8
}

function Resolve-PesterMaestroRoot {
    <#
    .SYNOPSIS
      DataBoar/maestro clone for post-spinout (#8) Pester reads. Fail-closed — no scripts/maestro/.
    #>
    $envRoot = [Environment]::GetEnvironmentVariable('MAESTRO_ROOT')
    if (-not [string]::IsNullOrWhiteSpace($envRoot)) {
        $candidate = $envRoot
        if (Test-Path -LiteralPath (Join-Path $candidate 'core/Maestro.ps1')) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    $parent = Split-Path -Parent $script:RepoRoot
    foreach ($name in @('maestro', 'Maestro')) {
        $candidate = Join-Path $parent $name
        if (Test-Path -LiteralPath (Join-Path $candidate 'core/Maestro.ps1')) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw 'Maestro clone not found for Pester (set MAESTRO_ROOT or clone ../maestro). See DataBoar/maestro#8.'
}

function Get-MaestroScript {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    $root = Resolve-PesterMaestroRoot
    Join-Path $root ($RelativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Get-MaestroScriptRaw {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    Get-Content -LiteralPath (Get-MaestroScript $RelativePath) -Raw -Encoding UTF8
}
