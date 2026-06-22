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
