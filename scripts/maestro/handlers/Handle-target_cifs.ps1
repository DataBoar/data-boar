#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_cifs.ps1

.SYNOPSIS
 Sub-orchestrator for persona 'target_cifs'.

.DESCRIPTION
 Validates that the target directory exists on the remote node and marks the
 target session as active in tmux, same contract used by SSHFS/NFS target handlers.
#>

param(
    [Parameter(Mandatory = $true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep
)

Write-Host "   [Target-CIFS] Certificando alvo de dados CIFS e disparando orquestracao concentrada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

# Keep signature parity with other handlers.
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

$linuxPath = $Node.path -replace "^~", "`$HOME"
$checkCmd = "test -d ""$linuxPath"""
ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$checkCmd" > $null 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Target CIFS validado. $($Node.hostname):$($Node.path) esta pronto." -ForegroundColor Green

    $payload = "echo `"TARGET_ACTIVE at `$(date +'%H:%M:%S')`" > ~/.labop-status && mkdir -p ~/log && echo `"Monitorando IO/Load (vmstat 5)...`" && vmstat 5 | tee ~/log/target_io.log"
    $tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"
    ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"
} else {
    Write-Warning "      [WARNING] O diretorio $($Node.path) nao foi encontrado no alvo CIFS $($Node.hostname)."
}
