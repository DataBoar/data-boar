BeforeAll {
    . (Join-Path $PSScriptRoot '_RepoRoot.ps1')
}

Describe 'Sync-WorkingTree.ps1 wiring (#1022)' {
    It 'dots Maestro-CanonicalGuard from PSScriptRoot' {
        $raw = Get-ScriptRaw 'scripts/maestro/Sync-WorkingTree.ps1'
        $raw | Should -Match '\$PSScriptRoot/Maestro-CanonicalGuard\.ps1'
        $raw | Should -Not -Match 'maestro/maestro/Maestro-CanonicalGuard'
    }
}

Describe 'Lab-MaestroCommon remote path (#1022)' {
    It 'expands tilde for SSH gate cd' {
        $raw = Get-ScriptRaw 'scripts/maestro/Lab-MaestroCommon.ps1'
        $raw | Should -Match 'function Get-MaestroRemoteRepoPath'
        $raw | Should -Match '\$HOME'
        $raw | Should -Match 'cd \$repoPath'
        $raw | Should -Not -Match "cd '\`$repoPath'"
    }
}

Describe 'labop-gate-readiness privilege probe (#1022)' {
    It 'detects narrow grant without blanket true only' {
        $raw = Get-ScriptRaw 'scripts/labop-gate-readiness.sh'
        $raw | Should -Match '_detect_sudo_narrow'
        $raw | Should -Match '_detect_doas_narrow'
        $raw | Should -Match 'sudo -n -l'
        $raw | Should -Match 'doas -C'
        $raw | Should -Match 'no_narrow_grant'
        $raw | Should -Match '_FW_GUARD_PROBE_DONE'
    }
}
