#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-lxd.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'lxd'.

.DESCRIPTION
 Responsável por disparar a execução do teste Completão em um container LXD/LXC no nó alvo.
 Verifica se o LXD está ativo e se existe um container 'data-boar' rodando.
 Injeta o comando de smoke via 'lxc exec' na sessão Tmux existente.
 É 100% agnóstico: recebe o caminho do diretório e a Ref do Maestro.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep,
    # Benchmark context forwarded by Maestro.ps1 (opt-in A/B). Empty defaults = legacy behaviour.
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [LXD] Verificando container LXD e disparando Completão ($modoTexto) em $($Node.hostname)..." -ForegroundColor DarkMagenta

$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

# Bench context (opt-in): forward to lab-completao-host-smoke.sh inside the LXC container.
$benchEnvPrefix = if ($BenchCompare) { "LAB_COMPLETAO_BENCH_COMPARE=1 " } else { "" }
$benchTrackArg = if ($BenchTrack) { "--bench-track $BenchTrack" } else { "" }
$benchRunIdArg = if ($BenchRunId) { "--bench-run-id $BenchRunId" } else { "" }
$benchHealthArg = if ($BenchHealthUrl) { "--health-url $BenchHealthUrl" } else { "" }

# 1. Verifica se LXD está ativo e lista containers
$lxcCheck = ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "lxc list --format csv 2>/dev/null | head -n 10 || echo LXD_UNAVAILABLE"

if ($LASTEXITCODE -ne 0 -or $lxcCheck -match "LXD_UNAVAILABLE") {
    Write-Warning "      [ERROR] LXD indisponível em $($Node.hostname). Verifique 'lxc list'."
    return
}

Write-Host "      [LXD] Containers ativos:" -ForegroundColor DarkGray
$lxcCheck | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray }

# 2. Localiza o container data-boar (nome canônico ou primeiro RUNNING)
$containerName = $lxcCheck | Where-Object { $_ -match "data.boar.*RUNNING" } | Select-Object -First 1
if (-not $containerName) {
    $containerName = $lxcCheck | Where-Object { $_ -match "RUNNING" } | Select-Object -First 1
    if ($containerName) {
        $containerName = $containerName -split ',' | Select-Object -First 1
        Write-Warning "      [WARN] Nenhum container 'data-boar' encontrado. Usando primeiro RUNNING: $containerName"
    } else {
        Write-Warning "      [ERROR] Nenhum container LXC em estado RUNNING em $($Node.hostname). Smoke não disparado."
        return
    }
} else {
    $containerName = $containerName -split ',' | Select-Object -First 1
}

# 3. Injeta smoke via tmux → lxc exec
# Bench env é prefixado dentro do bash -c para que o LAB_COMPLETAO_BENCH_COMPARE seja visível ao smoke.
$payload = "lxc exec $containerName -- bash -c '${benchEnvPrefix}cd $($Node.path) && bash ./scripts/lab-completao-host-smoke.sh $configArg $benchTrackArg $benchRunIdArg $benchHealthArg'"
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Smoke LXD injetado no Tmux em $($Node.hostname) (container: $containerName)." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao injetar smoke LXD em $($Node.hostname)."
}
