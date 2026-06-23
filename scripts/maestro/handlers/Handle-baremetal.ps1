#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-baremetal.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'baremetal'.

.DESCRIPTION
 Responsavel por disparar a execucao do teste Completao utilizando shell script ou equivalente.
 Injeta o comando de execucao do Data Boar diretamente em uma sessao Tmux existente no no remoto
 para garantir resiliencia e manter a sessao viva mesmo que o Maestro desconecte.
 E 100% agnostico: recebe o caminho do diretorio (efemero ou canonico) e a referencia de versao
 do Maestro, sem assumir IPs ou caminhos fixos.

 Sentinel (#831): payload writes /tmp/databoar_handler/baremetal_sentinel.txt with the smoke
 exit code so Maestro can verify real pass/fail via Wait-HandlerSentinel.ps1.

 Quote/escape safety (#830): payload is base64-encoded before injection into tmux send-keys,
 eliminating all shell-quoting ambiguity from Node.path, Ref, or BenchRunId values.
 Ref is validated against an allowlist before use.
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

. "$PSScriptRoot/../Lab-MaestroCommon.ps1"

# Allowlist: reject Ref values that could inject shell metacharacters (#830)
$safeRefPattern = '^(WorkingTree|stable|beta|v\d+\.\d+\.\d+(-[\w.]+)?)$'
if ($Ref -notmatch $safeRefPattern) {
    Write-Error "[Baremetal] Invalid -Ref value '$Ref' rejected by allowlist"
    exit 2
}

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [Baremetal] Disparando $modoTexto em $($Node.hostname)..." -ForegroundColor DarkGreen

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

# Sentinel path for pass/fail aggregation (#831)
$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/baremetal_sentinel.txt"

# Build the payload as a plain string (PowerShell expands its own variables here).
# Backtick-$ (`$) produces a literal $ that survives into the bash command. (#830)
# Node.path is used as-is: bash handles ~ expansion; base64 encoding removes quoting risk.
$nodePath    = $Node.path
$payload     = "rm -f $sentinelFile ; cd $nodePath && echo 'Iniciando Baremetal Smoke ($modoTexto)...' && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText ; _rc=`$? ; mkdir -p $sentinelDir ; echo `$_rc > $sentinelFile ; exit `$_rc"

# Base64-encode the payload: eliminates ALL shell-quoting issues in tmux send-keys. (#830)
$payloadB64  = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))

# Per-persona tmux session (no C-c clobber) (#955).
$injectExit = Invoke-HandlerTmuxPayload -Node $Node -Persona "baremetal" -PayloadB64 $payloadB64
$LASTEXITCODE = $injectExit

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Orquestracao injetada no Tmux com sucesso." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao comunicar com o Tmux em $($Node.hostname)."
    exit 1
}
