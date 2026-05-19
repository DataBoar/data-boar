<#
.SYNOPSIS
    Scaffold a new Architecture Decision Record (ADR) from the project template.

.DESCRIPTION
    - Auto-detects the next ADR number from docs/adr/*.md
    - Creates the file with the correct header and template sections
    - Prints the file path so you can open it immediately
    - Optionally adds a stub row to docs/adr/README.md index

.PARAMETER Title
    Short kebab-case title (e.g. "docker-ce-swarm-over-podman-only").
    Will be sanitised to lowercase-kebab automatically.

.PARAMETER Summary
    One-line human-readable summary for the README index (optional).

.PARAMETER Status
    ADR status: Accepted, Proposed, Deprecated. Default: Proposed.

.PARAMETER AddToIndex
    If set, appends a stub row to docs/adr/README.md. Default: true.

.EXAMPLE
    .\scripts\new-adr.ps1 -Title "my-tooling-decision" -Summary "Chose X over Y because Z"
    .\scripts\new-adr.ps1 -Title "uv-over-pip-poetry" -Summary "uv as the project package manager" -Status Accepted
#>
param(
    [Parameter(Mandatory)]
    [string]$Title,

    [string]$Summary = "(fill in)",

    [ValidateSet("Accepted","Proposed","Deprecated","Superseded")]
    [string]$Status = "Proposed",

    [bool]$AddToIndex = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
$adrDir   = Join-Path $repoRoot "docs\adr"

# Sanitise title to lowercase-kebab
$safeTitle = $Title.ToLower() `
    -replace '[^a-z0-9\-]', '-' `
    -replace '-+', '-' `
    -replace '^-|-$', ''

# Auto-detect next number (supports both legacy "0001-..." and new "ADR-0001-..." names)
$existing = Get-ChildItem -Path $adrDir -File |
    Where-Object { $_.Name -match '^(ADR-)?\d{4}-.+\.md$' } |
    ForEach-Object {
        $m = [regex]::Match($_.Name, '^(?:ADR-)?(\d{4})-')
        if ($m.Success) { [int]$m.Groups[1].Value }
    } |
    Sort-Object -Descending |
    Select-Object -First 1

$nextNum  = if ($null -ne $existing) { $existing + 1 } else { 1 }
$numStr   = $nextNum.ToString("D4")
$filename = "ADR-$numStr-$safeTitle.md"
$filepath = Join-Path $adrDir $filename
$today    = (Get-Date).ToString("yyyy-MM-dd")

if (Test-Path $filepath) {
    Write-Error "File already exists: $filepath"
    exit 1
}

$template = @"
# ADR ${numStr} - $Title

**Status:** $Status
**Date:** $today

## Context

[Describe the situation that forced this decision. What problem existed? What alternatives were evaluated?]

| Option | Pros | Cons |
|---|---|---|
| **Chosen approach** | ... | ... |
| Alternative A | ... | ... |

## Decision

1. [First specific choice made -- be concrete.]
2. [Second choice, if any.]
3. [Guard rails / defaults set as part of this decision.]

## Consequences

- **Positive:** ...
- **Negative:** ...
- **Watch:** ...

## References

- [Link to doc, plan, rule, or script that implements this decision]
"@

Set-Content $filepath $template -Encoding UTF8
Write-Host ""
Write-Host "Created: $filepath" -ForegroundColor Green
Write-Host "  ADR:   $numStr"
Write-Host "  Title: $Title"
Write-Host "  Status: $Status"

if ($AddToIndex) {
    $readmePath = Join-Path $adrDir "README.md"
    if (Test-Path $readmePath) {
        $readme = Get-Content $readmePath -Raw -Encoding UTF8
        # Find the index table and append before the next blank line after the last row
        $stub = "| $numStr  | [$Title]($filename) | $Status |"
        if ($readme -notmatch [regex]::Escape($stub)) {
            # Insert before the line "## Related docs"
            $readme = $readme -replace '(## Related docs)', "$stub`n`n`$1"
            Set-Content $readmePath $readme -Encoding UTF8
            Write-Host "  Index: updated docs/adr/README.md" -ForegroundColor Cyan
        }
    }
    $readmePtPath = Join-Path $adrDir "README.pt_BR.md"
    if (Test-Path -LiteralPath $readmePtPath) {
        $readmePt = Get-Content $readmePtPath -Raw -Encoding UTF8
        $stubPt = "| $numStr  | [$Title]($filename) | $Status |"
        if ($readmePt -notmatch [regex]::Escape($stubPt)) {
            $readmePt = $readmePt -replace '(## Docs relacionados|## Related docs)', "$stubPt`n`n`$1"
            Set-Content $readmePtPath $readmePt -Encoding UTF8
            Write-Host "  Index pt-BR: updated docs/adr/README.pt_BR.md" -ForegroundColor Cyan
        }
    }
}

$invScript = Join-Path $PSScriptRoot "inv-adr.ps1"
if (Test-Path -LiteralPath $invScript) {
    & $invScript -AdrDir $adrDir -OutFile (Join-Path $adrDir "INVENTORY.txt")
    Write-Host "  Inventory: updated docs/adr/INVENTORY.txt" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open: $filepath"
Write-Host "  2. Fill in Context, Decision, Consequences, References"
Write-Host "  3. Change Status from 'Proposed' to 'Accepted' when the decision is confirmed"
Write-Host "  4. Commit: git add docs/adr/ && git commit --trailer "Made-with: Cursor" -m ""docs(adr): add ADR $numStr -- $safeTitle"""
