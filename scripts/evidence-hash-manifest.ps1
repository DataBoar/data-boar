<#
.SYNOPSIS
    Writes a recursive file hash manifest (SHA256 or SHA512) for a directory tree.
.DESCRIPTION
    Generic helper for private evidence integrity under docs/private/. Suitable for
    GPG detached signing. Does not upload or log paths to CI; run locally only.
.PARAMETER RootPath
    Root directory to walk (recursive, files only).
.PARAMETER OutFile
    Output manifest path (UTF-8).
.PARAMETER Algorithm
    SHA256 (default) or SHA512.
.PARAMETER ExcludeGit
    Skip files under any .git directory (default: true).
.EXAMPLE
    .\scripts\evidence-hash-manifest.ps1 -RootPath "docs\private\employers\Corporate-Entity-B\artifacts" `
        -OutFile "docs\private\employers\Corporate-Entity-B\integrity\MANIFEST-SHA256-2026-04-09.txt"
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $RootPath,
    [Parameter(Mandatory = $true)]
    [string] $OutFile,
    [ValidateSet("SHA256", "SHA512")]
    [string] $Algorithm = "SHA256",
    [switch] $ExcludeGit = $true
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $RootPath)) {
    Write-Error "RootPath does not exist: $RootPath"
    exit 1
}

$resolved = Resolve-Path -LiteralPath $RootPath
$rootFull = $resolved.Path
if (-not (Test-Path -LiteralPath $rootFull -PathType Container)) {
    Write-Error "RootPath is not a directory: $RootPath"
    exit 1
}

$files = Get-ChildItem -LiteralPath $rootFull -File -Recurse -ErrorAction Stop | Sort-Object FullName
if ($ExcludeGit) {
    $files = $files | Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' }
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Evidence hash manifest")
[void]$sb.AppendLine("# Algorithm: $Algorithm")
[void]$sb.AppendLine(("# Root: " + (($rootFull -replace '\\', '/'))))
[void]$sb.AppendLine(("# Generated-UTC: " + ([DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"))))
[void]$sb.AppendLine("")

foreach ($f in $files) {
    $rel = $f.FullName.Substring($rootFull.Length).TrimStart('\', '/')
    $rel = $rel -replace '\\', '/'
    $hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm $Algorithm).Hash
    [void]$sb.AppendLine(("$hash  $rel"))
}

$outFull = [System.IO.Path]::GetFullPath($OutFile)
$parent = Split-Path -Parent $outFull
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($outFull, $sb.ToString(), $utf8NoBom)

Write-Host ("Wrote manifest: " + $outFull + " (" + ($files.Count) + " files)")
exit 0
