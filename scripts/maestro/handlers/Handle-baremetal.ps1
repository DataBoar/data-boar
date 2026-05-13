#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-baremetal.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'baremetal'.

.DESCRIPTION
 Responsável por disparar a execução do teste Completão utilizando shell script ou equivalente.
 Injeta o comando de execução do Data Boar diretamente em uma sessão Tmux existente no nó remoto para garantir resiliência e manter a sessão viva mesmo que o Maestro (14) desconecte.
 É 100% agnóstico: recebe o caminho do diretório (efêmero ou canônico) e a referência de versão do Maestro, sem assumir IPs ou caminhos fixos.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep, # <--- Injeção do Maestro para habilitar o Benchmark RC
    # Benchmark context forwarded by Maestro.ps1 (opt-in A/B). Empty defaults = legacy behaviour.
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { "$Ref" }
Write-Host "   [Baremetal] Disparando $modoTexto em $($Node.hostname)..." -ForegroundColor DarkGreen

# Se for Deep, passa o caminho do config. Se não, não passa nada (comportamento original)
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

# LAB_COMPLETAO_BENCH_COMPARE=1 ativa o probe coarse de wall-clock no smoke (stable: core.engine vs beta: boar_fast_filter).
# Mantemos export inline no payload para não persistir variável no shell remoto e respeitar a injeção via tmux.
$benchEnvPrefix = if ($BenchCompare) { "LAB_COMPLETAO_BENCH_COMPARE=1 " } else { "" }
$benchTrackArg = if ($BenchTrack) { "--bench-track $BenchTrack" } else { "" }
$benchRunIdArg = if ($BenchRunId) { "--bench-run-id $BenchRunId" } else { "" }
$benchHealthArg = if ($BenchHealthUrl) { "--health-url $BenchHealthUrl" } else { "" }

# Construção do Payload Posix Native:
# 1. Entra na pasta correta (fornecida pelo Node.path dinâmico do Maestro)
# 2. Ativa o venv (source para bash/zsh nativos)
# 3. Executa usando 'bash' explícito laboral caso as permissões (+x) tenham sido perdidas no scp, repassando a Ref desejada
# 4. Repassamos o argumento do config + bench flags para o bash script
$payload = "cd $($Node.path) && echo `"Iniciando Baremetal Smoke ($modoTexto)...`" && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $configArg $benchTrackArg $benchRunIdArg $benchHealthArg"

# Prepara resiliencia via TMUX (Ctrl+C garante que o prompt está limpo antes do Enter)
# SRE Fix: Separamos o Ctrl+C da injeção de texto com um micro-sleep (anti-race-condition)
# Isso garante que o bash se recupere do SIGINT e não engula o 'c' do 'cd'.
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

# Injeção resiliente via TMUX
ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Orquestração injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname)."
}
