#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_nfs.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'target_nfs'.

.DESCRIPTION
 Prepara e valida um no para atuar como ALVO de escaneamento via NFS.
 Invoca labop-nfs-server-ensure.sh (narrow sudoers LABOP_NFS_SERVER) para
 garantir servicos NFS ativos, path exportado, porta 2049 acessivel da subnet
 do lab-op e regra de firewall efemera se necessario.
 Apos validacao bem-sucedida, inicia monitoramento de IO via vmstat no tmux.
 E 100% agnostico: recebe path e hostname do inventario, sem IPs fixos no codigo.

 Sentinel (#831): payload writes /tmp/databoar_handler/target_nfs_sentinel.txt with
 the IO monitor result so Maestro can verify NFS target readiness.

 Quote/escape safety (#830): IO monitor payload is base64-encoded before tmux injection;
 ensure script path uses canonical repo path from Node.path.

 Privilege (#954/#1021 R8): Build-EnsureRemoteCommand writes .labop-gate context then
 $PRIV <canonical-bash> script (no env-prefix on privileged argv).
 Deep (#949 bundle): ensure --apply hard failure exits non-zero; exit 3 = graceful ALARM (#1021 R9).
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep,
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

. "$PSScriptRoot/../Lab-MaestroCommon.ps1"

Write-Host "   [Target-NFS] Certificando alvo NFS e disparando orquestracao (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

$repoPath  = $Node.path -replace "^~", "`$HOME"
$canonicalRepo = ($repoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/]*$", "")
$ensureScript = "$canonicalRepo/scripts/labop-nfs-server-ensure.sh"

$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_nfs_sentinel.txt"

# --- Phase 1: NFS server-side ensure (service + export + port + firewall) ---
$ensureMode = if ($Deep) { "--apply" } else { "--check" }
$ensureEnv = @{}
if ($Node.PSObject.Properties["nfs_svc"] -and $Node.nfs_svc) { $ensureEnv["LAB_NFS_SVC"] = [string]$Node.nfs_svc }
if ($Node.PSObject.Properties["pkg_mgr"] -and $Node.pkg_mgr) { $ensureEnv["LAB_PKG_MGR"] = [string]$Node.pkg_mgr }
if ($Node.PSObject.Properties["lab_op_subnet"] -and $Node.lab_op_subnet) {
    $ensureEnv["LAB_OP_SUBNET"] = [string]$Node.lab_op_subnet
}
$ensureCmd = Build-EnsureRemoteCommand -EnsureScript $ensureScript -EnsureMode $ensureMode -EnvVars $ensureEnv

Write-Host "      [NFS-Ensure] Running: $ensureMode on $($Node.hostname)" -ForegroundColor DarkGray
$ensureOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$ensureCmd"
$ensureExit = $LASTEXITCODE

if ($ensureOut) { $ensureOut | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray } }

if ($ensureExit -eq 0) {
    Write-Host "      [SUCCESS] NFS server-side validated: $($Node.hostname):$($Node.path)" -ForegroundColor Green
} elseif ($ensureExit -eq 3) {
    $grace = Get-EnsureAlarmFromOutput -Lines @($ensureOut) -LogTag 'NFS-Ensure'
    $alarm = if ($grace) { $grace.Alarm } else { 'nfs_degraded' }
    $hint = if ($grace -and $grace.Hint) { $grace.Hint } else { 'see_ensure_log' }
    Write-Warning "      [ALARM] NFS ensure graceful on $($Node.hostname): $alarm hint=$hint"
} elseif ($Deep) {
    Write-Warning "      [REAL FAIL] NFS ensure --apply returned exit $ensureExit on $($Node.hostname)."
    Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
    exit 1
} else {
    Write-Warning "      [WARNING] NFS ensure --check returned exit $ensureExit on $($Node.hostname). Run with -Deep to attempt remediation."
}

# --- Phase 2: IO monitoring in tmux ---
# Early readiness sentinel (0) before long-running vmstat; non-Deep may continue after check warn.
$repoLogDir = "$repoPath/log"
$ioPayload  = "rm -f $sentinelFile ; mkdir -p $repoLogDir $sentinelDir ; echo 0 > $sentinelFile ; echo TARGET_ACTIVE at \$(date +%H:%M:%S) > ~/.labop-status && vmstat 5 | tee $repoLogDir/target_nfs_io.log"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ioPayload))
$null = Invoke-HandlerTmuxPayload -Node $Node -Persona "target_nfs" -PayloadB64 $payloadB64

Write-Host "      [NFS] IO monitor injected in tmux session $(Get-HandlerTmuxSessionName -Persona 'target_nfs') on $($Node.hostname)." -ForegroundColor DarkGreen
