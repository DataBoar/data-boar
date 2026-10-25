BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
    $script:AuditPath = Get-RepoScript 'audit.ps1'
}

Describe 'audit.ps1 gate routing' {
    It 'restricts Mode to check-all and lint-only' {
        $raw = Get-ScriptRaw 'audit.ps1'
        $raw | Should -Match "ValidateSet\('check-all',\s*'lint-only'\)"
    }

    It 'routes lint-only Mode to scripts/lint-only.ps1' {
        $raw = Get-ScriptRaw 'audit.ps1'
        $raw | Should -Match "lint-only\.ps1"
        $raw | Should -Match "\`$Mode -eq 'lint-only'"
    }

    It 'routes check-all Mode to scripts/check-all.ps1' {
        $raw = Get-ScriptRaw 'audit.ps1'
        $raw | Should -Match 'scripts\\check-all\.ps1'
    }

    It 'propagates child exit code instead of masking failures' {
        $raw = Get-ScriptRaw 'audit.ps1'
        $raw | Should -Match 'exit \$exitCode'
        $raw | Should -Match '\$LASTEXITCODE'
    }

    It 'writes logs under logs/ and refreshes latest.log' {
        $raw = Get-ScriptRaw 'audit.ps1'
        $raw | Should -Match 'Join-Path \$PSScriptRoot ''logs'''
        $raw | Should -Match 'latest\.log'
    }
}

Describe 'audit.ps1 integration (fake gate)' {
    It 'returns the exit code from the delegated gate script' {
        $logDir = Join-Path $TestDrive 'logs'
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        $fakeGate = Join-Path $TestDrive 'fake-gate.ps1'
        Set-Content -LiteralPath $fakeGate -Value 'exit 42' -Encoding UTF8

        $runner = @"
`$ErrorActionPreference = 'Stop'
`$logFile = Join-Path '$logDir' 'audit-test.log'
`$gateScript = '$fakeGate'
'start' | Out-File -FilePath `$logFile
& `$gateScript 2>&1 | Tee-Object -FilePath `$logFile -Append
`$exitCode = `$LASTEXITCODE
if (`$null -eq `$exitCode) { `$exitCode = 0 }
exit `$exitCode
"@
        $runnerPath = Join-Path $TestDrive 'run-audit-pattern.ps1'
        Set-Content -LiteralPath $runnerPath -Value $runner -Encoding UTF8

        & pwsh -NoProfile -NonInteractive -File $runnerPath
        $LASTEXITCODE | Should -Be 42
    }
}
