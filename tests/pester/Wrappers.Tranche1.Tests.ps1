BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
}

Describe 'lint-only.ps1' {
    It 'delegates to uv run pre-commit run --all-files' {
        $raw = Get-ScriptRaw 'scripts/lint-only.ps1'
        $raw | Should -Match 'uv run pre-commit run --all-files'
        $raw | Should -Match 'exit \$exitCode'
    }
}

Describe 'quick-test.ps1' {
    It 'builds pytest args from -Path and -Keyword' {
        $raw = Get-ScriptRaw 'scripts/quick-test.ps1'
        $raw | Should -Match '\[string\]\$Path'
        $raw | Should -Match '\[string\]\$Keyword'
        $raw | Should -Match 'uv run pytest'
        $raw | Should -Match 'if \(\$Path\)'
        $raw | Should -Match 'if \(\$Keyword\)'
    }
}

Describe 'workflow-security-lint.ps1' {
    It 'defaults to advisory unless -Enforce or env flag' {
        $raw = Get-ScriptRaw 'scripts/workflow-security-lint.ps1'
        $raw | Should -Match '\[switch\]\$Enforce'
        $raw | Should -Match 'DATA_BOAR_ENFORCE_ZIZMOR'
        $raw | Should -Match '\[switch\]\$SkipIfMissing'
    }

    It 'skips cleanly when workflows directory is missing' {
        $raw = Get-ScriptRaw 'scripts/workflow-security-lint.ps1'
        $raw | Should -Match 'missing.*workflows'
    }
}

Describe 'gatekeeper-audit.ps1' {
    It 'uses word-boundary git grep and supports -RequireSeeds' {
        $raw = Get-ScriptRaw 'scripts/gatekeeper-audit.ps1'
        $raw | Should -Match 'git grep.*-w'
        $raw | Should -Match '\[switch\]\s*\$RequireSeeds'
        $raw | Should -Match 'PII_LOCAL_SEEDS\.txt'
    }
}

Describe 'new-adr.ps1 title sanitization (mirror script logic)' {
    BeforeAll {
        function script:ConvertTo-SafeAdrTitle {
            param([string]$Title)
            $Title.ToLower() `
                -replace '[^a-z0-9\-]', '-' `
                -replace '-+', '-' `
                -replace '^-|-$', ''
        }
    }

    It 'lowercases and kebab-cases unsafe characters' {
        ConvertTo-SafeAdrTitle 'Foo Bar!!' | Should -Be 'foo-bar'
        ConvertTo-SafeAdrTitle '  UV Over Pip  ' | Should -Be 'uv-over-pip'
    }

    It 'script auto-detects next ADR number from ADR-NNNN filenames' {
        $raw = Get-ScriptRaw 'scripts/new-adr.ps1'
        $raw | Should -Match 'Auto-detect next number'
        $raw | Should -Match '\^\(\?:ADR-\)\?\(\\d\{4\}\)-'
        $raw | Should -Match 'ValidateSet\("Accepted","Proposed","Deprecated","Superseded"\)'
    }
}
