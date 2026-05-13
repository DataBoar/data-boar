#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_nfs.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'target_nfs'.

.DESCRIPTION
 Responsável por preparar e validar um nó para atuar como ALVO de escaneamento via protocolo NFS.
 Garante que o diretório de dados alvo existe no storage remoto (neste laboratório, a princípio, o mini-bt) antes de ser exportado e montado pelos engines (workers) do Data Boar.
 É 100% agnóstico: recebe o caminho do diretório (efêmero ou canônico) e a referência de versão do Maestro, sem assumir IPs ou caminhos fixos.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep, # <--- Injeção do Maestro para habilitar o Benchmark
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

Write-Host "   [Target-NFS] Certificando alvo de dados NFS e disparando orquestração concentrada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor Magenta

# Se for Deep, passa o caminho do config. Se não, não passa nada (comportamento original)
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

# Construção do Payload Posix Native:
# 1. Validação de Diretório
# 1. Tradução de SRE: Converte o '~' do JSON para a variável $HOME do Linux
$linuxPath = $Node.path -replace "^~", "`$HOME"

# Validação Resiliente: 'test -d' confia no Exit Code silencioso, e > $null 2>&1 engole os banners multilíngues
$checkCmd = "test -d ""$linuxPath"""
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$checkCmd" > $null 2>&1

# $LASTEXITCODE é imune a banners de segurança e MotD
if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Target NFS validado. $($Node.hostname):$($Node.path) está pronto." -ForegroundColor Green

    # 2. NOVA FEATURE: Disparar monitoramento de IO no Tmux do Target
    # O payload atualiza o status (tirando o PENDING) e inicia o vmstat a cada 5 segundos, gravando num log
    $payload = "echo `"TARGET_ACTIVE at `$(date +'%H:%M:%S')`" > ~/.labop-status && mkdir -p ~/log && echo `"Monitorando IO/Load (vmstat 5)...`" && vmstat 5 | tee ~/log/target_io.log"

    $tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

    # Injeta no Tmux do Target NFS
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

} else {
    Write-Warning "      [WARNING] O diretório $($Node.path) não foi encontrado no alvo NFS $($Node.hostname)."
}
