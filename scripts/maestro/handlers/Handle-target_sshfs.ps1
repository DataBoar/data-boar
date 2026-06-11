#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_sshfs.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'target_sshfs'.

.DESCRIPTION
 Responsavel por preparar e validar um no para atuar como ALVO de escaneamento via protocolo
 SSH (sshfs ou sftp). Garante que o diretorio de dados alvo existe no storage remoto antes de
 ser exportado e montado pelos engines (workers) do Data Boar.
 E 100% agnostico: recebe o caminho do diretorio (efemero ou canonico) e a referencia de
 versao do Maestro, sem assumir IPs ou caminhos fixos.

 Sentinel (#831): IO monitor payload writes /tmp/databoar_handler/target_sshfs_sentinel.txt
 with the vmstat start result so Maestro can verify SSHFS target readiness.

 Quote/escape safety (#830): IO monitor payload is base64-encoded before tmux injection.
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

Write-Host "   [Target-SSHFS] Certificando alvo de dados e disparando orquestracao concentrada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

# Traducao de SRE: Converte o '~' do JSON para a variavel $HOME do Linux
$linuxPath = $Node.path -replace "^~", "`$HOME"

# Validacao Resiliente: 'test -d' confia no Exit Code silencioso
$checkCmd = "test -d `"$linuxPath`""
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$checkCmd" > $null 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Target SSHFS validado. $($Node.hostname):$($Node.path) esta pronto." -ForegroundColor Green

    # Sentinel path for pass/fail aggregation (#831)
    $sentinelDir  = "/tmp/databoar_handler"
    $sentinelFile = "$sentinelDir/target_sshfs_sentinel.txt"

    # Base64-encode IO monitor payload to eliminate shell-quoting issues. (#830)
    $ioPayload  = "echo TARGET_ACTIVE at \$(date +%H:%M:%S) > ~/.labop-status && mkdir -p ~/log $sentinelDir && echo Monitorando IO/Load vmstat 5... && vmstat 5 | tee ~/log/target_io.log ; echo \$? > $sentinelFile"
    $payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ioPayload))
    $tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

} else {
    Write-Warning "      [WARNING] O diretorio $($Node.path) nao foi encontrado no alvo $($Node.hostname)."
}
