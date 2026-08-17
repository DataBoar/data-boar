#requires -Module Pester
# maestro#6 / #1021 — sudoers.d load-order parse + WARN detection (fixture dirs).

Describe 'labop-sudoers-load-order-lib (maestro#6)' {
    BeforeAll {
        . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
        $script:Lib = Get-RepoScript 'scripts/labop-sudoers-load-order-lib.sh'

        function script:Invoke-SudoersLib {
            param(
                [Parameter(Mandatory = $true)][string]$BashSnippet
            )
            $libUnix = ($script:Lib -replace '\\', '/')
            # Normalize CRLF → LF: pwsh here-strings may embed `r; bash then treats
            # `path`r` as a missing file (first classify → other; last line often OK).
            $scriptBody = (@(
                'set -euo pipefail'
                ". '$libUnix'"
                $BashSnippet
            ) -join "`n") -replace "`r`n", "`n" -replace "`r", "`n"
            $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("sudoers-lib-" + [guid]::NewGuid().ToString('n') + '.sh')
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($tmp, $scriptBody, $utf8NoBom)
            try {
                $out = & bash "$tmp" 2>&1
                return [pscustomobject]@{
                    ExitCode = $LASTEXITCODE
                    Output   = @($out | ForEach-Object { "$_" })
                }
            } finally {
                Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
            }
        }

        function script:New-SudoersFixtureDir {
            $root = Join-Path ([System.IO.Path]::GetTempPath()) ("sudoers-lo-" + [guid]::NewGuid().ToString('n'))
            New-Item -ItemType Directory -Path $root | Out-Null
            return $root
        }

        function script:Write-FixtureFile {
            param([string]$Path, [string]$Content)
            [System.IO.File]::WriteAllText($Path, ($Content -replace "`r", ''))
        }
    }

    It 'classifies generic %wheel and maestro NOPASSWD drop-ins' {
        $dir = New-SudoersFixtureDir
        try {
            Write-FixtureFile (Join-Path $dir 'wheel') '%wheel ALL=(ALL:ALL) ALL'
            Write-FixtureFile (Join-Path $dir 'labop-maestro') @"
Cmnd_Alias LABOP_FW_GUARD = /usr/bin/bash /opt/data-boar/scripts/labop-fw-guard-ensure.sh --check
operator ALL=(root) NOPASSWD: LABOP_FW_GUARD
"@
            $r = Invoke-SudoersLib @"
labop_sudoers_classify_dropin '$dir/wheel'
labop_sudoers_classify_dropin '$dir/labop-maestro'
"@
            $r.ExitCode | Should -Be 0
            $r.Output -join "`n" | Should -Match 'generic_wheel'
            $r.Output -join "`n" | Should -Match 'maestro_narrow'
        } finally {
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It 'detects worked-example: labop-maestro before wheel (WARN tip z-)' {
        $dir = New-SudoersFixtureDir
        try {
            Write-FixtureFile (Join-Path $dir 'labop-maestro') @"
Cmnd_Alias LABOP_FW_GUARD = /bin/bash /repo/scripts/labop-fw-guard-ensure.sh --check
op ALL=(root) NOPASSWD: LABOP_FW_GUARD
"@
            Write-FixtureFile (Join-Path $dir 'wheel') '%wheel ALL=(ALL:ALL) ALL'
            Write-FixtureFile (Join-Path $dir 'z-labop-host-report') @"
Cmnd_Alias LABOP_DEP_DOCTOR = /usr/bin/bash /repo/scripts/labop-dep-doctor.sh --check
op ALL=(root) NOPASSWD: LABOP_DEP_DOCTOR
"@

            $r = Invoke-SudoersLib "labop_sudoers_find_load_order_violations '$dir' || true"
            ($r.Output -join "`n") | Should -Match 'before=labop-maestro'
            ($r.Output -join "`n") | Should -Match 'after=wheel'
            ($r.Output -join "`n") | Should -Match 'tip=rename_to_z-labop-maestro'
            ($r.Output -join "`n") | Should -Not -Match 'before=z-labop-host-report'
        } finally {
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It 'accepts z-labop-maestro after wheel (clean)' {
        $dir = New-SudoersFixtureDir
        try {
            Write-FixtureFile (Join-Path $dir 'wheel') '%wheel ALL=(ALL:ALL) ALL'
            Write-FixtureFile (Join-Path $dir 'z-labop-maestro') @"
Cmnd_Alias LABOP_FW_GUARD = /usr/bin/bash /repo/scripts/labop-fw-guard-ensure.sh --check
op ALL=(root) NOPASSWD: LABOP_FW_GUARD
"@

            $r = Invoke-SudoersLib @"
if labop_sudoers_find_load_order_violations '$dir'; then echo HAS_VIOLATION; else echo CLEAN; fi
"@
            $r.Output -join "`n" | Should -Match 'CLEAN'
            $r.Output -join "`n" | Should -Not -Match 'HAS_VIOLATION'
        } finally {
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It 'emit_gate_lines prints WARN with lesson tag' {
        $dir = New-SudoersFixtureDir
        try {
            Write-FixtureFile (Join-Path $dir 'labop-maestro') "LABOP_X`nNOPASSWD: ALL"
            Write-FixtureFile (Join-Path $dir 'wheel') '%sudo ALL=(ALL) ALL'
            $r = Invoke-SudoersLib "labop_sudoers_emit_gate_lines 'lab-pb-01' '$dir'"
            $joined = $r.Output -join "`n"
            $joined | Should -Match 'check=sudoers_load_order status=WARN'
            $joined | Should -Match 'lesson=test_RUN_not_sudo_l'
            $joined | Should -Match 'tip=rename_to_z-labop-maestro'
        } finally {
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    It 'gate-readiness sources load-order lib and documents bash readlink doctrine' {
        $raw = Get-ScriptRaw 'scripts/labop-gate-readiness.sh'
        $raw | Should -Match 'labop-sudoers-load-order-lib\.sh'
        $raw | Should -Match 'labop_sudoers_emit_gate_lines'
        $raw | Should -Match 'readlink -f'
        $raw | Should -Match 'maestro#6'
        $lib = Get-ScriptRaw 'scripts/labop-sudoers-load-order-lib.sh'
        $lib | Should -Match 'sudoers_load_order'
        $lib | Should -Match 'test_RUN_not_sudo_l'
    }
}
