#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-docker.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'docker'.

.DESCRIPTION
 Responsável por disparar a execução do teste Completão utilizando a engine Docker CE (Container Engine padrão).
 Diferente do Swarm, esta persona foca em execuções singulares via 'docker run' ou 'docker compose'.
 Injeta o comando via Tmux no nó alvo para garantir resiliência e manter a sessão ativa.
 É 100% agnóstico: recebe o caminho do diretório e a Ref do Maestro.
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

Write-Host "   [Docker.io ou CE] Disparando orquestração containerizada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor DarkCyan

# Se for Deep, passa o caminho do config. Se não, não passa nada (comportamento original)
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }
$stackArg = if ($Deep) { "--lab-stack-up" } else { "" }
$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
$smokeArgs = @()
if (-not [string]::IsNullOrWhiteSpace($configArg)) { $smokeArgs += $configArg }
if (-not [string]::IsNullOrWhiteSpace($stackArg)) { $smokeArgs += $stackArg }
if (-not [string]::IsNullOrWhiteSpace($BenchTrack)) { $smokeArgs += "--bench-track $BenchTrack" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $smokeArgs += "--bench-run-id $BenchRunId" }
if ($BenchWebPort -gt 0) { $smokeArgs += "--health-url http://127.0.0.1:$BenchWebPort/health" }
if (-not [string]::IsNullOrWhiteSpace($BenchHealthUrl)) { $smokeArgs += "--health-url $BenchHealthUrl" }
$smokeArgText = ($smokeArgs -join " ")
$benchEnv = @()
if ($BenchCompare) { $benchEnv += "LAB_COMPLETAO_BENCH_COMPARE=1" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $benchEnv += "LAB_COMPLETAO_BENCH_RUN_ID=$BenchRunId" }
$benchEnvPrefix = if ($benchEnv.Count -gt 0) { ($benchEnv -join " ") + " " } else { "" }

# Construção do Payload Posix Native:
# 1. Substitua o .sh abaixo pelo script real que faz o 'docker run' ou 'docker compose up' no seu ambiente
# 2. Protegendo aspas internas com escape de PowerShell:
# 3. Repassamos o argumento do config para o bash script
$payload = "cd $($Node.path) && echo `"Iniciando Baremetal Smoke ($modoTexto)...`" && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText"

# Prepara resiliencia via TMUX (Ctrl+C garante que o prompt está limpo antes do Enter)
# SRE Fix: Separamos o Ctrl+C da injeção de texto com um micro-sleep (anti-race-condition)
# Isso garante que o bash se recupere do SIGINT e não engula o 'c' do 'cd'.
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

# Injeção resiliente via TMUX
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Orquestração Docker.io ou CE injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname) para a persona Docker.io ou CE."
}
