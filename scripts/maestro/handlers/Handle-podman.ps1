#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-podman.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'podman'.

.DESCRIPTION
 Responsável por disparar a execução do teste Completão utilizando a engine Podman.
 É injetado via Tmux no nó alvo para garantir resiliência e manter a sessão
 viva mesmo que o Maestro no host orquestrador desconecte.
 É 100% agnóstico: recebe o caminho do diretório (efêmero ou canônico) e a referência de versão do Maestro, sem assumir IPs ou caminhos fixos.
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

Write-Host "   [Podman] Disparando orquestração containerizada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor DarkCyan

# Se for Deep, passa o caminho do config. Se não, não passa nada (comportamento original)
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }
$stackArg = if ($Deep) { "--lab-stack-up" } else { "" }
$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }

# Bench context (opt-in): mesmo padrão do Handle-docker; LAB_COMPLETAO_BENCH_COMPARE=1 inline antes do bash.
$benchEnvPrefix = if ($BenchCompare) { "LAB_COMPLETAO_BENCH_COMPARE=1 " } else { "" }
$benchTrackArg = if ($BenchTrack) { "--bench-track $BenchTrack" } else { "" }
$benchRunIdArg = if ($BenchRunId) { "--bench-run-id $BenchRunId" } else { "" }
$benchHealthArg = if ($BenchHealthUrl) { "--health-url $BenchHealthUrl" } else { "" }

# $smokeArgs / $smokeArgText: contrato canônico para Deep handlers (vide tests/test_maestro_scripts.py).
$smokeArgs = @($configArg, $stackArg, $benchTrackArg, $benchRunIdArg, $benchHealthArg) | Where-Object { $_ -and $_.Trim() }
$smokeArgText = ($smokeArgs -join ' ').Trim()

# Construção do Payload Posix Native para Podman:
# 1. Substitua o .sh abaixo pelo script real que faz o 'podman run...' ou similar no seu ambiente mais tarde
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
    Write-Host "      [SUCCESS] Orquestração Podman injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname) para a persona Podman."
}
