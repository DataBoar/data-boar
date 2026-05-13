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
$repoPath  = $Node.path -replace "^~", "`$HOME"  # canonical repo path on this node
$ensureScript = "$repoPath/scripts/labop-nfs-server-ensure.sh"

# --- Phase 1: NFS server-side ensure (service + export + port + firewall) ---
$ensureMode = if ($Deep) { "--apply" } else { "--check" }
$ensureCmd  = "sudo -n bash $ensureScript $ensureMode 2>&1"

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

# --- Phase 2: IO monitoring in tmux (same as before) ---
$payload  = "echo `"TARGET_ACTIVE at `$(date +'%H:%M:%S')`" > ~/.labop-status && mkdir -p ~/log && vmstat 5 | tee ~/log/target_nfs_io.log"
$tmuxCmd  = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$tmuxCmd" > $null 2>&1

Write-Host "      [NFS] IO monitor injected in tmux on $($Node.hostname)." -ForegroundColor DarkGreen
