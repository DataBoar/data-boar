#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_cifs.ps1

.SYNOPSIS
 Sub-orchestrator for persona 'target_cifs'.

.DESCRIPTION
 Validates and optionally ensures SMB/Samba server-side prerequisites on a target node.
 Invokes labop-smb-server-ensure.sh (narrow sudoers LABOP_SMB_SERVER) to confirm
 smbd is running, ports 445/139 are accessible from the lab-op subnet, and applies
 ephemeral firewall rules when needed (auto-reverted via --cleanup).
 After validation, starts IO monitoring via vmstat in the target tmux session.
 100% agnostic: receives path and hostname from inventory.

 Sentinel (#831): payload writes /tmp/databoar_handler/target_cifs_sentinel.txt with
 the IO monitor result so Maestro can verify CIFS target readiness.

 Privilege (#954/#1021 R8): .labop-gate context + canonical bash for grant-match.
#>

param(
    [Parameter(Mandatory = $true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep,
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

. "$PSScriptRoot/../Lab-MaestroCommon.ps1"

Write-Host "   [Target-CIFS] Certificando alvo CIFS e disparando orquestracao (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

$repoPath     = $Node.path -replace "^~", "`$HOME"
$canonicalRepo = ($repoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/]*$", "")
$ensureScript = "$canonicalRepo/scripts/labop-smb-server-ensure.sh"

$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_cifs_sentinel.txt"

# --- Phase 1: SMB server-side ensure (service + port + firewall) ---
# Maestro/orchestrator nodes scan remote CIFS targets; they are not SMB servers (#1021).
$personaList = @($Node.personas)
$skipServerEnsure = ($personaList -contains "maestro")
if ($skipServerEnsure) {
    Write-Host "      [CIFS-Ensure] Skip server ensure on maestro orchestrator (client-only persona mix)." -ForegroundColor DarkGray
} else {
    $ensureMode = if ($Deep) { "--apply" } else { "--check" }
    $ensureEnv = @{}
    if ($Node.PSObject.Properties["lab_op_subnet"] -and $Node.lab_op_subnet) {
        $ensureEnv["LAB_OP_SUBNET"] = [string]$Node.lab_op_subnet
    }
    $ensureCmd = Build-EnsureRemoteCommand -EnsureScript $ensureScript -EnsureMode $ensureMode -EnvVars $ensureEnv

    Write-Host "      [CIFS-Ensure] Running: $ensureMode on $($Node.hostname)" -ForegroundColor DarkGray
    $ensureOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
        "$($Node.user)@$($Node.hostname)" "$ensureCmd"
    $ensureExit = $LASTEXITCODE

    if ($ensureOut) { $ensureOut | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray } }

    if ($ensureExit -eq 0) {
        Write-Host "      [SUCCESS] CIFS server-side validated: $($Node.hostname):$($Node.path)" -ForegroundColor Green
    } elseif ($Deep) {
        Write-Warning "      [REAL FAIL] CIFS ensure --apply returned exit $ensureExit on $($Node.hostname)."
        Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
        exit 1
    } else {
        Write-Warning "      [WARNING] CIFS ensure --check returned exit $ensureExit on $($Node.hostname). Run with -Deep to attempt remediation."
    }
}

# --- Phase 2: IO monitoring in tmux ---
$repoLogDir = "$repoPath/log"
$ioPayload  = "rm -f $sentinelFile ; mkdir -p $repoLogDir $sentinelDir ; echo 0 > $sentinelFile ; echo TARGET_ACTIVE at \$(date +%H:%M:%S) > ~/.labop-status && vmstat 5 | tee $repoLogDir/target_cifs_io.log"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ioPayload))
$null = Invoke-HandlerTmuxPayload -Node $Node -Persona "target_cifs" -PayloadB64 $payloadB64

Write-Host "      [CIFS] IO monitor injected in tmux session $(Get-HandlerTmuxSessionName -Persona 'target_cifs') on $($Node.hostname)." -ForegroundColor DarkGreen
