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

Describe 'Maestro login-env parity (#1003)' {
    It 'Lab-MaestroCommon bootstraps local PATH before uv/cargo/maturin' {
        $raw = Get-ScriptRaw 'scripts/maestro/Lab-MaestroCommon.ps1'
        $raw | Should -Match 'function Initialize-MaestroLoginToolPath'
        $raw | Should -Match '\.local/bin'
        $raw | Should -Match '\.cargo/env'
        $raw | Should -Match 'function Get-MaestroRemoteLoginPathPrelude'
    }

    It 'Invoke-HandlerTmuxPayload prepends remote login PATH before bash payload' {
        $raw = Get-ScriptRaw 'scripts/maestro/Lab-MaestroCommon.ps1'
        $raw | Should -Match 'Get-MaestroRemoteLoginPathPrelude'
        $raw | Should -Match 'base64 -d \| bash'
        $invokeIdx = $raw.IndexOf('function Invoke-HandlerTmuxPayload')
        $preludeIdx = $raw.IndexOf('Get-MaestroRemoteLoginPathPrelude', $invokeIdx)
        $preludeIdx | Should -BeGreaterThan $invokeIdx
    }

    It 'Handle-LicensingMatrix initializes login PATH before uv run' {
        $raw = Get-ScriptRaw 'scripts/maestro/Handle-LicensingMatrix.ps1'
        $initIdx = $raw.IndexOf('Initialize-MaestroLoginToolPath')
        $uvIdx = $raw.IndexOf('& uv run python')
        $initIdx | Should -BeGreaterThan -1
        $uvIdx | Should -BeGreaterThan $initIdx
    }

    It 'Handle-web remote recovery bootstraps PATH and uses login shell for uv' {
        $raw = Get-ScriptRaw 'scripts/maestro/handlers/Handle-web.ps1'
        $raw | Should -Match '\.local/bin'
        $raw | Should -Match '\.cargo/env'
        $raw | Should -Match 'bash -lc'
        $raw | Should -Match 'command -v uv'
    }

    It 'build-rust-prefilter initializes login PATH before uv run maturin' {
        $raw = Get-ScriptRaw 'scripts/build-rust-prefilter.ps1'
        $raw | Should -Match 'Initialize-MaestroLoginToolPath'
        $raw | Should -Match 'uv run maturin'
        $initIdx = $raw.IndexOf('Initialize-MaestroLoginToolPath')
        $maturinIdx = $raw.IndexOf('uv run maturin')
        $initIdx | Should -BeLessThan $maturinIdx
    }

    It 'lab-completao-host-smoke and gate-readiness mirror login-env for uv/cargo' {
        $smoke = Get-ScriptRaw 'scripts/lab-completao-host-smoke.sh'
        $gate = Get-ScriptRaw 'scripts/labop-gate-readiness.sh'
        $smoke | Should -Match '\.local/bin'
        $smoke | Should -Match 'uv run maturin'
        $gate | Should -Match '_ensure_login_path'
        $gate | Should -Match 'login-env:uv'
        $gate | Should -Match 'for bin in cargo maturin'
        $gate | Should -Match 'login-env:\$bin'
    }
}
