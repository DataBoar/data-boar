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
        $text | Should -Match '(?m) \| -$'
        $text | Should -Match 'InventoryHash:'
    }

    It 'emits PENDING Ratified-By for pending ratification history' {
        $ratDir = Join-Path $TestDrive 'adr-ratify'
        New-Item -ItemType Directory -Path $ratDir -Force | Out-Null
        @'
# ADR 9997 - Ratification Pending

## Status

Accepted

### Status history

- 2026-06-23 — Accepted (ratification by @FabioLeitao — signature PENDING).

## Context

Fixture.
'@ | Set-Content -LiteralPath (Join-Path $ratDir 'ADR-9997-ratification-pending.md') -Encoding UTF8

        $outFile = Join-Path $TestDrive 'INVENTORY-ratify.txt'
        & $script:InvAdr -AdrDir $ratDir -OutFile $outFile | Out-Null
        $text = Get-Content -LiteralPath $outFile -Raw
        $text | Should -Match '9997 \| Accepted \|'
        $text | Should -Match '(?m) \| PENDING$'
    }

    It 'stamps Ratified-By when -RatifiedBy matches pending handle' {
        $ratDir = Join-Path $TestDrive 'adr-stamp'
        New-Item -ItemType Directory -Path $ratDir -Force | Out-Null
        @'
# ADR 9996 - Ratification Stamp

## Status

Accepted

### Status history

- 2026-06-23 — Accepted (ratification by @FabioLeitao — signature PENDING).

## Context

Fixture.
'@ | Set-Content -LiteralPath (Join-Path $ratDir 'ADR-9996-ratification-stamp.md') -Encoding UTF8

        $outFile = Join-Path $TestDrive 'INVENTORY-stamp.txt'
        & $script:InvAdr -AdrDir $ratDir -OutFile $outFile -RatifiedBy '@FabioLeitao' | Out-Null
        $text = Get-Content -LiteralPath $outFile -Raw
        $text | Should -Match '(?m) \| @FabioLeitao$'
    }
}
