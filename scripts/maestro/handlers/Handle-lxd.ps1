#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-lxd.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'lxd'.

.DESCRIPTION
 Responsavel por disparar a execucao do teste Completao em um container LXD/LXC no no alvo.
 Verifica se o LXD esta ativo e se existe um container 'data-boar' rodando.
 Injeta o comando de smoke via 'lxc exec' na sessao Tmux existente.
 E 100% agnostico: recebe o caminho do diretorio e a Ref do Maestro.

 Sentinel (#831): payload writes /tmp/databoar_handler/lxd_sentinel.txt with the smoke
 exit code for real pass/fail aggregation.

 Quote/escape safety (#830): payload is base64-encoded before tmux injection; Ref validated
 against an allowlist.
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

# Allowlist: reject Ref values that could inject shell metacharacters (#830)
$safeRefPattern = '^(WorkingTree|stable|beta|v\d+\.\d+\.\d+(-[\w.]+)?)$'
if ($Ref -notmatch $safeRefPattern) {
    Write-Error "[LXD] Invalid -Ref value '$Ref' rejected by allowlist"
    exit 2
}

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [LXD] Verificando container LXD e disparando Completao ($modoTexto) em $($Node.hostname)..." -ForegroundColor DarkMagenta

$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }
$smokeArgs = @()
if (-not [string]::IsNullOrWhiteSpace($configArg)) { $smokeArgs += "--bench-config $configArg" }
if (-not [string]::IsNullOrWhiteSpace($BenchTrack)) { $smokeArgs += "--bench-track $BenchTrack" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $smokeArgs += "--bench-run-id $BenchRunId" }
if ($BenchWebPort -gt 0) { $smokeArgs += "--health-url http://127.0.0.1:$BenchWebPort/health" }
if (-not [string]::IsNullOrWhiteSpace($BenchHealthUrl)) { $smokeArgs += "--health-url $BenchHealthUrl" }
$smokeArgText = ($smokeArgs -join " ")
$benchEnv = @()
if ($BenchCompare) { $benchEnv += "LAB_COMPLETAO_BENCH_COMPARE=1" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $benchEnv += "LAB_COMPLETAO_BENCH_RUN_ID=$BenchRunId" }
$benchEnvPrefix = if ($benchEnv.Count -gt 0) { ($benchEnv -join " ") + " " } else { "" }

# 1. Verifica se LXD esta ativo e lista containers
$lxcCheck = ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "lxc list --format csv 2>/dev/null | head -n 10 || echo LXD_UNAVAILABLE"

if ($LASTEXITCODE -ne 0 -or $lxcCheck -match "LXD_UNAVAILABLE") {
    Write-Warning "      [ERROR] LXD indisponivel em $($Node.hostname). Verifique 'lxc list'."
    return
}

Write-Host "      [LXD] Containers ativos:" -ForegroundColor DarkGray
$lxcCheck | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray }

# 2. Localiza o container data-boar (nome canonico ou primeiro RUNNING)
$containerName = $lxcCheck | Where-Object { $_ -match "data.boar.*RUNNING" } | Select-Object -First 1
if (-not $containerName) {
    $containerName = $lxcCheck | Where-Object { $_ -match "RUNNING" } | Select-Object -First 1
    if ($containerName) {
        $containerName = $containerName -split ',' | Select-Object -First 1
        Write-Warning "      [WARN] Nenhum container 'data-boar' encontrado. Usando primeiro RUNNING: $containerName"
    } else {
        Write-Warning "      [ERROR] Nenhum container LXC em estado RUNNING em $($Node.hostname). Smoke nao disparado."
        return
    }
} else {
    $containerName = $containerName -split ',' | Select-Object -First 1
}

# Sentinel path for pass/fail aggregation (#831)
$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/lxd_sentinel.txt"

# 3. Injeta smoke via tmux -> lxc exec
# Base64-encode to eliminate shell-quoting issues in lxc exec + tmux send-keys. (#830)
$nodePath   = $Node.path
$innerCmd   = "cd $nodePath 2>/dev/null || cd /app && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText"
$payload    = "lxc exec $containerName -- bash -c '$innerCmd' ; _rc=`$? ; mkdir -p $sentinelDir ; echo `$_rc > $sentinelFile ; exit `$_rc"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))
$tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"

ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Smoke LXD injetado no Tmux em $($Node.hostname) (container: $containerName)." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao injetar smoke LXD em $($Node.hostname)."
    exit 1
}
