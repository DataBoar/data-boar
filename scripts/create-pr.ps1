# Create a PR using commit-or-pr.ps1 with the PR body read from a file (avoids CLI escaping of multi-line body).
# Usage:
#   .\scripts\create-pr.ps1 -Title "Short title" -BodyFilePath "path\to\body.txt"
#   .\scripts\create-pr.ps1 -Title "Title" -BodyFilePath $env:TEMP\pr-body.txt -RunTests
# Run from repo root. Body file should be UTF-8 text; newlines in the file become PR description newlines.
# -RunTests: run pytest before pushing (default: $true). Set -RunTests:$false to skip.

param(
    [Parameter(Mandatory = $true)]
    [string]$Title,

    [Parameter(Mandatory = $true)]
    [string]$BodyFilePath,

    [switch]$RunTests = $true
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BodyFilePath)) {
    Write-Error "Body file not found: $BodyFilePath"
    exit 1
}
$Body = Get-Content -LiteralPath $BodyFilePath -Raw -Encoding utf8
& (Join-Path $PSScriptRoot "commit-or-pr.ps1") -Action PR -Title $Title -Body $Body -RunTests:$RunTests
