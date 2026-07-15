BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
    $script:PackScript = Get-RepoScript 'scripts/external-review-pack.ps1'
}

Describe 'external-review-pack.ps1 (#1192)' {
    It 'does not use Invoke-Expression; validates DateStamp and calls uv via splat' {
        $raw = Get-ScriptRaw 'scripts/external-review-pack.ps1'
        $raw | Should -Not -Match 'Invoke-Expression'
        $raw | Should -Match '& uv @argv'
        $raw | Should -Match 'Assert-ExternalReviewDateStamp'
        $raw | Should -Match ([regex]::Escape('^\d{4}-\d{2}-\d{2}$'))
    }

    It 'Accepts a valid YYYY-MM-DD DateStamp (regex guard)' {
        # Mirror Assert-ExternalReviewDateStamp — valid path only; avoid running uv/bundle.
        $Value = '2026-07-15'
        { if ($Value -notmatch '^\d{4}-\d{2}-\d{2}$') {
                throw "Invalid -DateStamp '$Value' - expected YYYY-MM-DD."
            }
        } | Should -Not -Throw
    }

    It 'Throws on injection-shaped DateStamp before calling uv' {
        $bad = '2026-01-01"; evil'
        { & $script:PackScript -DateStamp $bad } | Should -Throw -Because 'injection must fail closed before & uv'
    }

    It 'Throws on non-date DateStamp before calling uv' {
        { & $script:PackScript -DateStamp 'abc' } | Should -Throw
    }

    It 'Throw message names YYYY-MM-DD for invalid DateStamp' {
        { & $script:PackScript -DateStamp 'not-a-date' } |
            Should -Throw -ExpectedMessage '*YYYY-MM-DD*'
    }
}
