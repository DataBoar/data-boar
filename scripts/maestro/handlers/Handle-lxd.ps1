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
    [switch]$Deep
)

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [LXD] Verificando container LXD e disparando Completão ($modoTexto) em $($Node.hostname)..." -ForegroundColor DarkMagenta

$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

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
$payload = "lxc exec $containerName -- bash -c 'cd $($Node.path) && bash ./scripts/lab-completao-host-smoke.sh $configArg'"
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Smoke LXD injetado no Tmux em $($Node.hostname) (container: $containerName)." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao injetar smoke LXD em $($Node.hostname)."
}
