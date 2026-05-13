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
    # Benchmark context forwarded by Maestro.ps1 (opt-in A/B). Empty defaults = legacy behaviour.
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

# Bench context (opt-in): track/run_id/health URL get forwarded as smoke flags;
# BenchCompare exports LAB_COMPLETAO_BENCH_COMPARE=1 inline so the remote tmux bash sees it.
$benchEnvPrefix = if ($BenchCompare) { "LAB_COMPLETAO_BENCH_COMPARE=1 " } else { "" }
$benchTrackArg = if ($BenchTrack) { "--bench-track $BenchTrack" } else { "" }
$benchRunIdArg = if ($BenchRunId) { "--bench-run-id $BenchRunId" } else { "" }
$benchHealthArg = if ($BenchHealthUrl) { "--health-url $BenchHealthUrl" } else { "" }

# $smokeArgs is the canonical contract (test_container_handlers_enable_lab_stack_up_in_deep_mode):
# array → trimmed/joined string → single-string arg list to lab-completao-host-smoke.sh.
# Empty fragments are filtered out so the bash side never sees stray empty positional args.
$smokeArgs = @($configArg, $stackArg, $benchTrackArg, $benchRunIdArg, $benchHealthArg) | Where-Object { $_ -and $_.Trim() }
$smokeArgText = ($smokeArgs -join ' ').Trim()

# Construção do Payload Posix Native:
# 1. Substitua o .sh abaixo pelo script real que faz o 'docker run' ou 'docker compose up' no seu ambiente
# 2. Protegendo aspas internas com escape de PowerShell:
# 3. Repassamos os argumentos consolidados (config + stack + bench) via $smokeArgText.
$payload = "cd $($Node.path) && echo `"Iniciando Baremetal Smoke ($modoTexto)...`" && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText"

# Prepara resiliencia via TMUX (Ctrl+C garante que o prompt está limpo antes do Enter)
# SRE Fix: Separamos o Ctrl+C da injeção de texto com um micro-sleep (anti-race-condition)
# Isso garante que o bash se recupere do SIGINT e não engula o 'c' do 'cd'.
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

# Injeção resiliente via TMUX
ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Orquestração Docker.io ou CE injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname) para a persona Docker.io ou CE."
}
