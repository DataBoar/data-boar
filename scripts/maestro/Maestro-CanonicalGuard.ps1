#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Maestro-CanonicalGuard.ps1

.SYNOPSIS
 Fail-closed guard: canonical / maestro regent nodes are never align or WorkingTree overwrite targets (#948, ADR-0068).

.DESCRIPTION
 Load-bearing layers (any match => protected for destructive sync/align):
   (d) inventory/manifest `protect_canonical: true`
   (a) persona contains `maestro` (regent is source of truth, never destination)
   (b)+(c) orchestrator hostname matches node AND repo path is a canonical dev path
 Ambiguous/missing flags on canonical paths => protected (fail-closed).
#>

Set-StrictMode -Version 2

function Get-MaestroOrchestratorHostname {
    if ($env:DATA_BOAR_MAESTRO_ORCHESTRATOR_HOST) {
        return $env:DATA_BOAR_MAESTRO_ORCHESTRATOR_HOST.Trim()
    }
    $hn = (hostname 2>$null)
    if ($hn) { return $hn.Trim() }
    return $env:COMPUTERNAME
}

function Test-IsCanonicalRepoPath {
    param([Parameter(Mandatory = $true)][string]$RepoPath)
    $p = $RepoPath.Trim()
    if ($p -match '(^|/)Projects/dev/data-boar/?$') { return $true }
    if ($p -match '^~/Projects/dev/data-boar/?$') { return $true }
    if ($p -eq '/opt/data-boar') { return $false }  # lab disposable layout on PROLIANT
    return $false
}

function Test-MaestroHostnameMatchesOrchestrator {
    param(
        [Parameter(Mandatory = $true)][string]$NodeHostname,
        [Parameter(Mandatory = $true)][string]$OrchestratorHost
    )
    if ($NodeHostname -eq $OrchestratorHost) { return $true }
    $shortOrch = ($OrchestratorHost -split '\.')[0]
    $shortNode = ($NodeHostname -split '\.')[0]
    if ($shortOrch -and $shortNode -and ($shortOrch -eq $shortNode)) { return $true }
    return $false
}

function Test-MaestroInventoryNodeProtected {
  <#
  Returns $true when WorkingTree rsync / git reset align must NOT touch this inventory node.
  #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [string]$OrchestratorHost = ""
    )
    $orch = if ($OrchestratorHost) { $OrchestratorHost } else { Get-MaestroOrchestratorHostname }

    if ($Node.personas -contains "maestro") {
        return $true
    }

    $hasFlag = $Node.PSObject.Properties.Name -contains "protect_canonical"
    if ($hasFlag -and $Node.protect_canonical -eq $true) {
        return $true
    }
    if ($hasFlag -and $Node.protect_canonical -eq $false) {
        # Explicit opt-out only when flag is false; maestro persona still wins above.
        if (Test-IsCanonicalRepoPath -RepoPath ([string]$Node.path) -and (Test-MaestroHostnameMatchesOrchestrator -NodeHostname $Node.hostname -OrchestratorHost $orch)) {
            return $true
        }
        return $false
    }

    # Fail-closed: missing protect_canonical on canonical orchestrator path
    if ((Test-IsCanonicalRepoPath -RepoPath ([string]$Node.path)) -and (Test-MaestroHostnameMatchesOrchestrator -NodeHostname $Node.hostname -OrchestratorHost $orch)) {
        return $true
    }

    return $false
}

function Test-ManifestRepoPathProtected {
    param(
        [Parameter(Mandatory = $true)][string]$SshAlias,
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [string]$OrchestratorHost = "",
        $ProtectCanonical = $null
    )
    $orch = if ($OrchestratorHost) { $OrchestratorHost } else { Get-MaestroOrchestratorHostname }

    if ($null -ne $ProtectCanonical -and $ProtectCanonical -eq $true) {
        return $true
    }
    if ($null -ne $ProtectCanonical -and $ProtectCanonical -eq $false) {
        if ((Test-IsCanonicalRepoPath -RepoPath $RepoPath) -and (Test-MaestroHostnameMatchesOrchestrator -NodeHostname $SshAlias -OrchestratorHost $orch)) {
            return $true
        }
        return $false
    }

    if ((Test-IsCanonicalRepoPath -RepoPath $RepoPath) -and (Test-MaestroHostnameMatchesOrchestrator -NodeHostname $SshAlias -OrchestratorHost $orch)) {
        return $true
    }

    return $false
}

function Get-MaestroEphemeralRepoPath {
    param(
        [Parameter(Mandatory = $true)][string]$Ref,
        [Parameter(Mandatory = $true)][string]$BasePath
    )
    if ($Ref -eq "WorkingTree") {
        return $BasePath
    }
    # Isolated parent — no shared prefix with canonical ~/Projects/dev/data-boar (#948)
    return "/tmp/databoar_bench/$Ref"
}
