BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
    $script:InvAdr = Get-RepoScript 'scripts/inv-adr.ps1'
}

Describe 'inv-adr.ps1 ADR inventory logic' {
    BeforeAll {
        $script:TempAdrDir = Join-Path $TestDrive 'adr-mini'
        New-Item -ItemType Directory -Path $script:TempAdrDir -Force | Out-Null
        @'
# ADR 9998 - Sample Accepted

## Status

Accepted

## Context

Fixture for Pester.
'@ | Set-Content -LiteralPath (Join-Path $script:TempAdrDir 'ADR-9998-sample-accepted.md') -Encoding UTF8

        @'
# ADR 9999 - Duplicate Status Line

- **Status:** Proposed

## Context

Legacy metadata line.
'@ | Set-Content -LiteralPath (Join-Path $script:TempAdrDir 'ADR-9999-legacy-status.md') -Encoding UTF8
    }

    It 'DryRun emits inventory hash without writing OutFile' {
        $outFile = Join-Path $TestDrive 'INVENTORY.txt'
        if (Test-Path -LiteralPath $outFile) {
            Remove-Item -LiteralPath $outFile -Force
        }

        $output = & $script:InvAdr -AdrDir $script:TempAdrDir -OutFile $outFile -DryRun *>&1 |
            ForEach-Object { "$_" } |
            Out-String

        $output | Should -Match 'DryRun: would write 2 ADR rows'
        $output | Should -Match 'InventoryHash:'
        Test-Path -LiteralPath $outFile | Should -Be $false
    }

    It 'writes deterministic SHA256 rows when not DryRun' {
        $outFile = Join-Path $TestDrive 'INVENTORY-out.txt'
        & $script:InvAdr -AdrDir $script:TempAdrDir -OutFile $outFile | Out-Null
        $LASTEXITCODE | Should -Be 0
        $text = Get-Content -LiteralPath $outFile -Raw
        $text | Should -Match '9998 \| Accepted \|'
        $text | Should -Match '9999 \| Proposed \|'
        $text | Should -Match 'InventoryHash:'
    }
}
