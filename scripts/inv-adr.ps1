#Requires -Version 5.1
<#
.SYNOPSIS
    Generate docs/adr/INVENTORY.txt with per-ADR SHA256 and self-attested inventory hash.

.DESCRIPTION
    Scans ADR-*.md under docs/adr/, extracts number/status/title/ratified-by, writes a deterministic
    audit file. Homelab secrets and product code are out of scope.

    Ratified-By (ADR-0045 / ADR-0072 UMADR): read from ### Status history lines containing
    "ratification by @<op>". While the line still says "signature PENDING", the inventory column
    is PENDING until the operator runs -RatifiedBy @<op> to stamp the canonical index.

.PARAMETER AdrDir
    Directory containing ADR-*.md files. Default: docs/adr under repo root.

.PARAMETER OutFile
    Output path for INVENTORY.txt. Default: docs/adr/INVENTORY.txt.

.PARAMETER DryRun
    Compute inventory but do not write OutFile.

.PARAMETER RatifiedBy
    Operator handle (e.g. @FabioLeitao). Stamps RATIFIED_BY for ADRs whose status history
    pending ratification matches this handle. Use with a signed commit trailer ADR-Ratified-By:.

.PARAMETER StampOnlyNumbers
    When used with -RatifiedBy, stamp only these ADR numbers (e.g. 0068 or 0060,0063).
    Other rows keep prior @handle from existing INVENTORY when regen would yield PENDING.

.PARAMETER Write
    Explicit write (default when -DryRun is not set). Accepted for operator ritual parity.

.EXAMPLE
    .\scripts\inv-adr.ps1
    .\scripts\inv-adr.ps1 -DryRun
    .\scripts\inv-adr.ps1 -RatifiedBy '@FabioLeitao' -Write
#>
param(
    [string]$AdrDir = "",
    [string]$OutFile = "",
    [switch]$DryRun,
    [string]$RatifiedBy = "",
    [string[]]$StampOnlyNumbers = @(),
    [switch]$Write
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $AdrDir) {
    $AdrDir = Join-Path $repoRoot "docs\adr"
}
if (-not $OutFile) {
    $OutFile = Join-Path $AdrDir "INVENTORY.txt"
}

if (-not (Test-Path -LiteralPath $AdrDir)) {
    Write-Error "ADR directory not found: $AdrDir"
    exit 1
}

function Get-AdrStatusFromContent {
    param([string]$Raw)
    # ADR 0045 amendment: ## Status section (full line - Accepted or "Duplicate of ADR-NNNN")
    if ($Raw -match '(?ms)^## Status\s*\r?\n\s*([^\r\n#]+?)\s*(?:\r?\n|$)') {
        $fromSection = $Matches[1].Trim()
        if ($fromSection) { return $fromSection }
    }
    if ($Raw -match '(?m)^-\s+\*\*Status:\*\*\s*(.+)') { return $Matches[1].Trim() }
    if ($Raw -match '\*\*Status:\*\*\s*(\S+)') { return $Matches[1].Trim() }
    return "Unknown"
}

function Get-AdrTitleFromContent {
    param([string]$Raw, [string]$FileName)
    if ($Raw -match '(?m)^#\s+ADR\s+\d{4}\s+.\s*(.+?)\s*$') {
        return $Matches[1].Trim()
    }
    return ($FileName -replace '^ADR-\d{4}-', '' -replace '\.md$', '' -replace '-', ' ')
}

function Get-AdrRatifiedByFromContent {
    param(
        [string]$Raw,
        [string]$StampHandle = ""
    )
    $history = ""
    if ($Raw -match '(?ms)^### Status history\s*\r?\n(.*?)(?=^##\s|\z)') {
        $history = $Matches[1]
    }
    if (-not $history) {
        return "-"
    }
    $pending = $false
    $handle = ""
    foreach ($line in ($history -split '\r?\n')) {
        if ($line -notmatch 'ratification by (@\S+)') { continue }
        $handle = $Matches[1].Trim()
        if ($line -match 'signature\s+PENDING') {
            $pending = $true
        }
    }
    if (-not $handle) {
        return "-"
    }
    if ($pending) {
        if ($StampHandle -and ($StampHandle -eq $handle)) {
            return $handle
        }
        return "PENDING"
    }
    return $handle
}

function Get-PreservedRatifiedByMap {
    param([string]$Path)
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $map }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match '^(\d{4}) \| .+ \| .+ \| .+ \| .+ \| (@\S+)$') {
            $map[$Matches[1]] = $Matches[2]
        }
    }
    return $map
}

$stampHandle = $RatifiedBy.Trim()
if ($stampHandle -and $stampHandle -notmatch '^@\S+$') {
    Write-Error "RatifiedBy must be an @handle (e.g. @FabioLeitao); got: $RatifiedBy"
    exit 1
}

$stampOnlySet = @{}
foreach ($n in $StampOnlyNumbers) {
    foreach ($part in ($n -split '[,\s]+')) {
        $p = $part.Trim()
        if ($p) { $stampOnlySet[$p] = $true }
    }
}
$useStampFilter = ($stampOnlySet.Count -gt 0)
$preservedRatifiedBy = Get-PreservedRatifiedByMap -Path $OutFile

$adrs = Get-ChildItem -LiteralPath $AdrDir -File -Filter "ADR-*.md" |
    Where-Object { $_.Name -match '^ADR-(\d{4})-' } |
    Sort-Object {
        [int]([regex]::Match($_.Name, '^ADR-(\d{4})-').Groups[1].Value)
    }

$dataLines = New-Object System.Collections.Generic.List[string]
foreach ($adr in $adrs) {
    $num = [regex]::Match($adr.Name, '^ADR-(\d{4})-').Groups[1].Value
    $raw = Get-Content -LiteralPath $adr.FullName -Raw -Encoding UTF8
    $title = Get-AdrTitleFromContent -Raw $raw -FileName $adr.Name
    $status = Get-AdrStatusFromContent -Raw $raw
    $stampForAdr = ""
    if ($stampHandle) {
        if (-not $useStampFilter -or $stampOnlySet.ContainsKey($num)) {
            $stampForAdr = $stampHandle
        }
    }
    $ratifiedBy = Get-AdrRatifiedByFromContent -Raw $raw -StampHandle $stampForAdr
    if ($ratifiedBy -eq 'PENDING' -and $preservedRatifiedBy.ContainsKey($num)) {
        $prev = $preservedRatifiedBy[$num]
        if ($prev -match '^@\S+$') {
            $ratifiedBy = $prev
        }
    }
    $norm = $raw -replace "`r`n", "`n" -replace "`r", "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($norm)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace("-", "")
    $dataLines.Add("$num | $status | $hash | $($adr.Name) | $title | $ratifiedBy")
}

$utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$header = @(
    "# ADR Inventory - generated by scripts/inv-adr.ps1"
    "# GeneratedUtc: $utc"
    "# Algorithm: SHA256"
    "# Format: NUMBER | STATUS | FILE_HASH | FILENAME | TITLE | RATIFIED_BY"
    "# RATIFIED_BY: - = N/A; PENDING = ratification line with signature PENDING; @op = stamped"
    "#"
)

$bodyText = ($header + $dataLines) -join "`n"
$dataOnly = $dataLines -join "`n"
$inventoryHash = (New-Object System.Security.Cryptography.SHA256Managed)
$hashBytes = [System.Text.Encoding]::UTF8.GetBytes($dataOnly)
$inventoryHashHex = [BitConverter]::ToString($inventoryHash.ComputeHash($hashBytes)).Replace("-", "")

$fullText = $bodyText + "`n#`n# InventoryHash: $inventoryHashHex`n"

$shouldWrite = (-not $DryRun) -or $Write
if (-not $shouldWrite) {
    Write-Host "DryRun: would write $($dataLines.Count) ADR rows to $OutFile"
    Write-Host "InventoryHash: $inventoryHashHex"
    if ($stampHandle) {
        $stamped = @($dataLines | Where-Object { $_ -match " \| $([regex]::Escape($stampHandle))$" })
        Write-Host "RatifiedBy stamp: $stampHandle ($($stamped.Count) row(s))"
    }
    exit 0
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($OutFile, $fullText.Replace("`r`n", "`n").Replace("`r", "`n"), $utf8NoBom)
Write-Host "OK: $($dataLines.Count) ADRs -> $OutFile"
Write-Host "InventoryHash: $inventoryHashHex"
if ($stampHandle) {
    $stamped = @($dataLines | Where-Object { $_ -match " \| $([regex]::Escape($stampHandle))$" })
    Write-Host "RatifiedBy stamp: $stampHandle ($($stamped.Count) row(s))"
}
