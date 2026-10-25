# Dot-source only: shared helpers for docker-*.ps1 scripts in this folder's parent.
# Usage: . (Join-Path $PSScriptRoot 'docker\DataBoarDockerCommon.ps1')
# Not intended to be run standalone.

<#
.SYNOPSIS
  Repo root is the parent of the `scripts` folder (pass $PSScriptRoot from a script under scripts/).
#>
function Get-DataBoarRepoRoot {
    param([Parameter(Mandatory)][string]$ScriptsDirectory)
    return (Get-Item -LiteralPath $ScriptsDirectory).Parent.FullName
}

function Get-DataBoarVersionFromPyproject {
    param([string]$RepoRoot)
    $pyproject = Join-Path $RepoRoot "pyproject.toml"
    if (-not (Test-Path -LiteralPath $pyproject)) {
        throw "pyproject.toml not found at $pyproject"
    }
    $text = Get-Content -LiteralPath $pyproject -Raw -Encoding UTF8
    if ($text -match '(?m)^version\s*=\s*"([^"]+)"') {
        return $Matches[1].Trim()
    }
    throw "Could not parse version from pyproject.toml"
}

<#
.SYNOPSIS
  Returns previous patch version for semver x.y.z (e.g. 1.6.4 -> 1.6.3). If patch is 0, returns $null (caller may pass -PreviousVersion manually).
#>
function Get-DataBoarPreviousPatchVersion {
    param([string]$Version)
    if ($Version -match '^(\d+)\.(\d+)\.(\d+)$') {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        $patch = [int]$Matches[3]
        if ($patch -gt 0) {
            return "$major.$minor.$($patch - 1)"
        }
        return $null
    }
    return $null
}

function Test-DataBoarDockerAvailable {
    return [bool](Get-Command docker -ErrorAction SilentlyContinue)
}
