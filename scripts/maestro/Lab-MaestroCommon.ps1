#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Lab-MaestroCommon.ps1

.SYNOPSIS
 Shared helpers for Maestro handlers (#955 tmux isolation, #954 doas/sudo + env, sentinel contract).

.DESCRIPTION
 Dot-source from handlers: . "$PSScriptRoot/../Lab-MaestroCommon.ps1" (handlers) or
 . "$PSScriptRoot/Lab-MaestroCommon.ps1" (Maestro.ps1).
#>

Set-StrictMode -Version 2

function Get-HandlerTmuxSessionName {
    param([Parameter(Mandatory = $true)][string]$Persona)
    # Per-persona session avoids C-c clobber on multi-persona nodes (#955).
    return "completao_$Persona"
}

function Get-LabPrivilegeInvoker {
    <#
    Returns the non-interactive privilege prefix for remote ensure scripts (#954).
    doas strips caller env by default; callers must use: $priv env VAR=val bash script.sh
    #>
    return @'
if command -v doas >/dev/null 2>&1; then echo "doas -n"; elif command -v sudo >/dev/null 2>&1; then echo "sudo -n"; else echo "NO_PRIV"; fi
'@.Trim()
}

function Build-EnsureRemoteCommand {
    param(
        [Parameter(Mandatory = $true)][string]$EnsureScript,
        [Parameter(Mandatory = $true)][string]$EnsureMode,
        [hashtable]$EnvVars = @{}
    )
    $privProbe = Get-LabPrivilegeInvoker
    $envPairs = @()
    foreach ($k in $EnvVars.Keys) {
        $v = [string]$EnvVars[$k]
        if ($v -match "[\s'`"$\\]") {
            throw "Build-EnsureRemoteCommand: unsafe env value for $k"
        }
        $envPairs += "${k}=${v}"
    }
    $envPrefix = if ($envPairs.Count -gt 0) { "env $($envPairs -join ' ') " } else { "" }
    return "PRIV=`$($privProbe)` ; if [ `"`$PRIV`" = NO_PRIV ]; then echo '[Ensure] NO doas/sudo on host' >&2; exit 2; fi; `$PRIV $envPrefix bash $EnsureScript $EnsureMode 2>&1"
}

function Invoke-HandlerTmuxPayload {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$Persona,
        [Parameter(Mandatory = $true)][string]$PayloadB64,
        [switch]$SkipSessionCreate
    )
    $session = Get-HandlerTmuxSessionName -Persona $Persona
    $create = if ($SkipSessionCreate) { "" } else {
        "tmux has-session -t $session 2>/dev/null || tmux new-session -d -s $session ; "
    }
    # No C-c: dedicated session per persona (#955).
    $tmuxCmd = "${create}tmux send-keys -t $session 'echo $PayloadB64 | base64 -d | bash' Enter"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
        "$($Node.user)@$($Node.hostname)" "$tmuxCmd"
    return $LASTEXITCODE
}

function Write-RemoteSentinel {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$SentinelFile,
        [Parameter(Mandatory = $true)][int]$ExitCode
    )
    $dir = Split-Path -Parent $SentinelFile
    $cmd = "mkdir -p $dir && echo $ExitCode > $SentinelFile"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
}

function Clear-RemoteSentinel {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$SentinelFile
    )
    $cmd = "rm -f $SentinelFile"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
}

function Reset-LabOpStatus {
    <#
    #969: clear stale ~/.labop-status at the start of each Maestro turn so yesterday's
    DONE_FAILED does not masquerade as the current run outcome.
    #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$RunMarker
    )
    $safeMarker = $RunMarker -replace "'", ""
    $cmd = "echo 'NOT_RUN maestro=$safeMarker at '`$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)' > ~/.labop-status"
    ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
    return ($LASTEXITCODE -eq 0)
}

function Get-MaestroCanonicalRepoPath {
    param([Parameter(Mandatory = $true)][string]$RepoPath)
    # Same suffix strip as Handle-target_nfs.ps1 / Handle-target_cifs.ps1 (#99b6fdc).
    return ($RepoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/\\]*$", "")
}

function Invoke-LabopGateReadiness {
    <#
    #960: ALARM (--check) skips handlers; REMEDIATE (-Deep / --apply) uses narrow grants.
    #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [switch]$Deep
    )
    $personaList = @($Node.personas)
    if (-not $personaList -or $personaList.Count -eq 0) {
        return $true
    }
    $personaCsv = ($personaList -join ',')
    $repoPath = Get-MaestroCanonicalRepoPath -RepoPath ([string]$Node.path)
    $mode = if ($Deep) { '--apply' } else { '--check' }
    $envPrefix = ""
    if ($Node.PSObject.Properties.Name -contains 'lab_op_subnet' -and $Node.lab_op_subnet) {
        $subnet = [string]$Node.lab_op_subnet
        if ($subnet -match "[\s'`"$\\]") {
            throw "Invoke-LabopGateReadiness: unsafe lab_op_subnet on $($Node.hostname)"
        }
        $envPrefix = "env LAB_OP_SUBNET=$subnet "
    }
    $gateScript = "$repoPath/scripts/labop-gate-readiness.sh"
    $remoteCmd = "cd '$repoPath' && ${envPrefix}bash '$gateScript' $mode --personas '$personaCsv' 2>&1"
    Write-Host "      [GateReadiness] $mode on $($Node.hostname) personas=$personaCsv" -ForegroundColor DarkCyan
    $output = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 `
        "$($Node.user)@$($Node.hostname)" $remoteCmd 2>&1
    foreach ($line in @($output)) {
        if ($line) { Write-Host "      $line" }
    }
    if ($LASTEXITCODE -ne 0) {
        if ($Deep) {
            Write-Warning "      [REAL FAIL] Gate readiness --apply failed on $($Node.hostname)"
        } else {
            Write-Warning "      [ALARM] Gate readiness failed on $($Node.hostname). Handlers skipped. Use -Deep to remediate."
        }
        return $false
    }
    return $true
}
