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

Write-Host "   [Target-CIFS] Certificando alvo CIFS e disparando orquestracao (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

$linuxPath    = $Node.path -replace "^~", "`$HOME"
$repoPath     = $Node.path -replace "^~", "`$HOME"
$ensureScript = "$repoPath/scripts/labop-smb-server-ensure.sh"

# --- Phase 1: SMB server-side ensure (service + port + firewall) ---
$ensureMode = if ($Deep) { "--apply" } else { "--check" }
$ensureCmd  = "sudo -n bash $ensureScript $ensureMode --share-path $linuxPath 2>&1"

Write-Host "      [CIFS-Ensure] Running: $ensureMode on $($Node.hostname)" -ForegroundColor DarkGray
$ensureOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$ensureCmd"
$ensureExit = $LASTEXITCODE

if ($ensureOut) { $ensureOut | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray } }

if ($ensureExit -eq 0) {
    Write-Host "      [SUCCESS] CIFS server-side validated: $($Node.hostname):$($Node.path)" -ForegroundColor Green
} elseif ($Deep) {
    Write-Warning "      [WARNING] CIFS ensure --apply returned exit $ensureExit on $($Node.hostname). Continuing (non-fatal)."
} else {
    Write-Warning "      [WARNING] CIFS ensure --check returned exit $ensureExit on $($Node.hostname). Run with -Deep to attempt remediation."
}

# --- Phase 2: IO monitoring in tmux ---
$payload = "echo `"TARGET_ACTIVE at `$(date +'%H:%M:%S')`" > ~/.labop-status && mkdir -p ~/log && vmstat 5 | tee ~/log/target_cifs_io.log"
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$tmuxCmd" > $null 2>&1

Write-Host "      [CIFS] IO monitor injected in tmux on $($Node.hostname)." -ForegroundColor DarkGreen
