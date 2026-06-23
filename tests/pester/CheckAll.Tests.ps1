BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
}

Describe 'check-all.ps1 workflow contract' {
    It 'calls gatekeeper-audit before Rust and pytest' {
        $raw = Get-ScriptRaw 'scripts/check-all.ps1'
        $gatePos = $raw.IndexOf('gatekeeper-audit.ps1')
        $rustPos = $raw.IndexOf('cargo fmt')
        $pesterPos = $raw.IndexOf('run-pester.ps1')
        $prePos = $raw.IndexOf('pre-commit-and-tests.ps1')
        $gatePos | Should -BeGreaterThan -1
        $rustPos | Should -BeGreaterThan $gatePos
        $pesterPos | Should -BeGreaterThan $rustPos
        $prePos | Should -BeGreaterThan $pesterPos
    }

    It 'forwards -SkipPreCommit to pre-commit-and-tests.ps1' {
        $raw = Get-ScriptRaw 'scripts/check-all.ps1'
        $raw | Should -Match '\[switch\]\$SkipPreCommit'
        $raw | Should -Match 'argsList \+= "-SkipPreCommit"'
    }

    It 'supports optional -IncludeVersionSmoke after pytest success' {
        $raw = Get-ScriptRaw 'scripts/check-all.ps1'
        $raw | Should -Match '\[switch\]\$IncludeVersionSmoke'
        $raw | Should -Match 'version-readiness-smoke\.ps1'
    }

    It 'aborts when gatekeeper-audit fails' {
        $raw = Get-ScriptRaw 'scripts/check-all.ps1'
        $raw | Should -Match 'ABORTED by gatekeeper-audit'
    }
}
