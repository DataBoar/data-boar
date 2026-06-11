#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-dockerswarm.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'dockerswarm'.

.DESCRIPTION
 Responsavel por disparar a execucao do teste Completao utilizando a engine Docker Swarm.
 Injeta o comando via Tmux no no alvo para garantir resiliencia e manter a sessao.
 E 100% agnostico: recebe o caminho do diretorio (efemero ou canonico) e a referencia de versao
 do Maestro, sem assumir IPs ou caminhos fixos.

 Sentinel (#831): payload writes /tmp/databoar_handler/dockerswarm_sentinel.txt with the smoke
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
    Write-Error "[DockerSwarm] Invalid -Ref value '$Ref' rejected by allowlist"
    exit 2
}

$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }
$stackArg  = if ($Deep) { "--lab-stack-up" } else { "" }
$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [Docker Swarm] Disparando orquestracao containerizada (Deep: $Deep) em $($Node.hostname)..." -ForegroundColor DarkCyan

$smokeArgs = @()
if (-not [string]::IsNullOrWhiteSpace($configArg)) { $smokeArgs += "--bench-config $configArg" }
if (-not [string]::IsNullOrWhiteSpace($stackArg))  { $smokeArgs += $stackArg }
if (-not [string]::IsNullOrWhiteSpace($BenchTrack)) { $smokeArgs += "--bench-track $BenchTrack" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $smokeArgs += "--bench-run-id $BenchRunId" }
if ($BenchWebPort -gt 0) { $smokeArgs += "--health-url http://127.0.0.1:$BenchWebPort/health" }
if (-not [string]::IsNullOrWhiteSpace($BenchHealthUrl)) { $smokeArgs += "--health-url $BenchHealthUrl" }
$smokeArgText = ($smokeArgs -join " ")
$benchEnv = @()
if ($BenchCompare) { $benchEnv += "LAB_COMPLETAO_BENCH_COMPARE=1" }
if (-not [string]::IsNullOrWhiteSpace($BenchRunId)) { $benchEnv += "LAB_COMPLETAO_BENCH_RUN_ID=$BenchRunId" }
$benchEnvPrefix = if ($benchEnv.Count -gt 0) { ($benchEnv -join " ") + " " } else { "" }

# Sentinel path for pass/fail aggregation (#831)
$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/dockerswarm_sentinel.txt"

$nodePath = $Node.path
$payload  = "cd $nodePath && echo 'Iniciando DockerSwarm Smoke ($modoTexto)...' && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText ; _rc=`$? ; mkdir -p $sentinelDir ; echo `$_rc > $sentinelFile ; exit `$_rc"

# Base64-encode to eliminate shell-quoting issues in tmux send-keys. (#830)
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))
$tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"

ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Orquestracao Docker Swarm injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname) para a persona Docker Swarm."
    exit 1
}
