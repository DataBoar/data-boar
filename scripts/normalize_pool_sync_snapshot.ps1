param(
    [Parameter(Mandatory = $true)]
    [string]$SnapshotPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SnapshotPath)) {
    throw "Snapshot file not found: $SnapshotPath"
}

$content = Get-Content -LiteralPath $SnapshotPath -Raw -Encoding UTF8

# Target only the mojibake patterns we have seen so far.
$replacements = @(
    @("Andr? Colleague-I", "Andr? Colleague-I"),
    @("Ferr?o", "Ferr?o"),
    @("Re-run de pool sync apos", "Re-run de pool sync ap?s"),
    @("Re-run de pool sync apos", "Re-run de pool sync ap?s"),
    @("automa??o", "automa?ao"),
    @("automacao", "automa?ao"),
    @("automacao", "automa?ao")
)

foreach ($r in $replacements) {
    $content = $content -replace [regex]::Escape($r[0]), $r[1]
}

Set-Content -LiteralPath $SnapshotPath -Value $content -Encoding UTF8

Write-Host "Normalized: $SnapshotPath"

