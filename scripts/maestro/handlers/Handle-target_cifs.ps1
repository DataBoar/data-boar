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

 Quote/escape safety (#830): IO monitor payload is base64-encoded before tmux injection;
 ensure script path uses canonical repo path from Node.path.
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
# Ensure scripts always use canonical repo path (not ephemeral versioned checkout)
# so the path matches the narrow sudoers entry exactly.
$canonicalRepo = ($repoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/]*$", "")
$ensureScript = "$canonicalRepo/scripts/labop-smb-server-ensure.sh"

# --- Phase 1: SMB server-side ensure (service + port + firewall) ---
$ensureMode = if ($Deep) { "--apply" } else { "--check" }
$ensureCmd  = "sudo -n bash $ensureScript $ensureMode 2>&1"

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
# Sentinel path for pass/fail aggregation (#831)
$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_cifs_sentinel.txt"

# Base64-encode IO monitor payload to eliminate shell-quoting issues. (#830)
$ioPayload  = "echo TARGET_ACTIVE at \$(date +%H:%M:%S) > ~/.labop-status && mkdir -p ~/log $sentinelDir && vmstat 5 | tee ~/log/target_cifs_io.log ; echo \$? > $sentinelFile"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ioPayload))
$tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    "$($Node.user)@$($Node.hostname)" "$tmuxCmd" > $null 2>&1

Write-Host "      [CIFS] IO monitor injected in tmux on $($Node.hostname)." -ForegroundColor DarkGreen
