#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-microk8s.ps1

.SYNOPSIS
 Sub-Orquestrador especialista na persona 'microk8s'.

.DESCRIPTION
 Responsavel por verificar o estado do cluster MicroK8s e disparar o teste Completao
 dentro do pod do Data Boar (ou via kubectl exec).
 E 100% agnostico: recebe o caminho do diretorio e a Ref do Maestro.

 Sentinel (#831): payload writes /tmp/databoar_handler/microk8s_sentinel.txt with the smoke
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
    Write-Error "[MicroK8s] Invalid -Ref value '$Ref' rejected by allowlist"
    exit 2
}

$modoTexto = if ($Deep) { "Benchmark RC (Deep)" } else { $Ref }
Write-Host "   [MicroK8s] Verificando cluster e disparando Completao ($modoTexto) em $($Node.hostname)..." -ForegroundColor DarkBlue

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
$sentinelFile = "$sentinelDir/microk8s_sentinel.txt"

# 1. Verifica status do cluster MicroK8s
$k8sCheck = ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "microk8s status --wait-ready --timeout 10 2>/dev/null | head -n 5 || echo MICROK8S_UNAVAILABLE"

if ($LASTEXITCODE -ne 0 -or $k8sCheck -match "MICROK8S_UNAVAILABLE") {
    Write-Warning "      [ERROR] MicroK8s indisponivel em $($Node.hostname). Verifique 'microk8s status'."
    return
}

Write-Host "      [MicroK8s] Status:" -ForegroundColor DarkGray
$k8sCheck | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray }

# 2. Localiza pod do Data Boar
$podName = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" `
    "microk8s kubectl get pods --all-namespaces -l app=data-boar --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null"

$nodePath = $Node.path

if (-not $podName) {
    Write-Warning "      [WARN] Nenhum pod 'data-boar' Running em $($Node.hostname). Fallback para baremetal path."
    $payload    = "cd $nodePath && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText ; _rc=`$? ; mkdir -p $sentinelDir ; echo `$_rc > $sentinelFile ; exit `$_rc"
    $payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))
    $tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"
    return
}

Write-Host "      [MicroK8s] Pod encontrado: $podName" -ForegroundColor DarkGray

# 3. Injeta smoke via tmux -> kubectl exec
# Base64-encode to eliminate shell-quoting issues in kubectl exec + tmux send-keys. (#830)
$innerCmd   = "cd $nodePath 2>/dev/null || cd /app && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $smokeArgText"
$payload    = "microk8s kubectl exec $podName -- bash -c '$innerCmd' ; _rc=`$? ; mkdir -p $sentinelDir ; echo `$_rc > $sentinelFile ; exit `$_rc"
$payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))
$tmuxCmd    = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao 'echo $payloadB64 | base64 -d | bash' Enter"

ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Smoke MicroK8s injetado no Tmux em $($Node.hostname) (pod: $podName)." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao injetar smoke MicroK8s em $($Node.hostname)."
    exit 1
}
