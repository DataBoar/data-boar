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

Write-Host "   [Target-NFS] Certificando alvo NFS e disparando orquestracao (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

$linuxPath = $Node.path -replace "^~", "`$HOME"
$repoPath  = $Node.path -replace "^~", "`$HOME"
# Ensure scripts always use canonical repo path (not ephemeral versioned checkout)
$canonicalRepo = ($repoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/]*$", "")
$ensureScript = "$canonicalRepo/scripts/labop-nfs-server-ensure.sh"

# --- Phase 1: NFS server-side ensure (service + export + port + firewall) ---
$ensureMode = if ($Deep) { "--apply" } else { "--check" }
# Pass inventory-driven service/pkg info via env vars (sudo -n preserves LAB_* if sudoers allows,
# or scripts read them when running as root via sudo - they are set in the SSH session env)
$nfsSvc  = if ($Node.PSObject.Properties["nfs_svc"] -and $Node.nfs_svc) { $Node.nfs_svc } else { "" }
$pkgMgr  = if ($Node.PSObject.Properties["pkg_mgr"] -and $Node.pkg_mgr) { $Node.pkg_mgr } else { "" }
$envPrefix = ""
if ($nfsSvc)  { $envPrefix += "LAB_NFS_SVC='$nfsSvc' " }
if ($pkgMgr)  { $envPrefix += "LAB_PKG_MGR='$pkgMgr' " }
$ensureCmd  = "${envPrefix}sudo -n bash $ensureScript $ensureMode 2>&1"

Write-Host "      [NFS-Ensure] Running: $ensureMode on $($Node.hostname)" -ForegroundColor DarkGray
$ensureOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$ensureCmd"
$ensureExit = $LASTEXITCODE

if ($ensureOut) { $ensureOut | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray } }

if ($ensureExit -eq 0) {
    Write-Host "      [SUCCESS] NFS server-side validated: $($Node.hostname):$($Node.path)" -ForegroundColor Green
} elseif ($Deep) {
    Write-Warning "      [WARNING] NFS ensure --apply returned exit $ensureExit on $($Node.hostname). Continuing (non-fatal)."
} else {
    Write-Warning "      [WARNING] NFS ensure --check returned exit $ensureExit on $($Node.hostname). Run with -Deep to attempt remediation."
}

# --- Phase 2: IO monitoring in tmux ---
# Sentinel path for pass/fail aggregation (#831)
$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_nfs_sentinel.txt"

# Base64-encode IO monitor payload to eliminate shell-quoting issues. (#830)
$ioPayload  = "echo TARGET_ACTIVE at \$(date +%H:%M:%S) > ~/.labop-status && mkdir -p ~/log $sentinelDir && vmstat 5 | tee ~/log/target_nfs_io.log ; echo \$? > $sentinelFile"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ioPayload))
$tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$tmuxCmd" > $null 2>&1

Write-Host "      [NFS] IO monitor injected in tmux on $($Node.hostname)." -ForegroundColor DarkGreen
