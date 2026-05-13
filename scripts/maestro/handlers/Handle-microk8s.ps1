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
Write-Host "   [MicroK8s] Verificando cluster e disparando Completao ($modoTexto) em $($Node.hostname)..." -ForegroundColor DarkBlue

$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }

# Bench context (opt-in): forwarded to lab-completao-host-smoke.sh inside the kubectl-exec'd pod.
$benchEnvPrefix = if ($BenchCompare) { "LAB_COMPLETAO_BENCH_COMPARE=1 " } else { "" }
$benchTrackArg = if ($BenchTrack) { "--bench-track $BenchTrack" } else { "" }
$benchRunIdArg = if ($BenchRunId) { "--bench-run-id $BenchRunId" } else { "" }
$benchHealthArg = if ($BenchHealthUrl) { "--health-url $BenchHealthUrl" } else { "" }

# 1. Verifica status do cluster MicroK8s
$k8sCheck = ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "microk8s status --wait-ready --timeout 10 2>/dev/null | head -n 5 || echo MICROK8S_UNAVAILABLE"

if ($LASTEXITCODE -ne 0 -or $k8sCheck -match "MICROK8S_UNAVAILABLE") {
    Write-Warning "      [ERROR] MicroK8s indisponivel em $($Node.hostname). Verifique 'microk8s status'."
    return
}

Write-Host "      [MicroK8s] Status:" -ForegroundColor DarkGray
$k8sCheck | ForEach-Object { Write-Host "        $_" -ForegroundColor DarkGray }

# 2. Localiza pod do Data Boar
$podName = ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" `
    "microk8s kubectl get pods --all-namespaces -l app=data-boar --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null"

if (-not $podName) {
    Write-Warning "      [WARN] Nenhum pod 'data-boar' Running em $($Node.hostname). Fallback para baremetal path."
    # Fallback baremetal: bench env prefixado inline para o tmux/bash remoto.
    $payload = "cd $($Node.path) && ${benchEnvPrefix}bash ./scripts/lab-completao-host-smoke.sh $configArg $benchTrackArg $benchRunIdArg $benchHealthArg"
    $tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"
    ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"
    return
}

Write-Host "      [MicroK8s] Pod encontrado: $podName" -ForegroundColor DarkGray

# 3. Injeta smoke via tmux -> kubectl exec
# Bench env vai dentro do bash -c para que o LAB_COMPLETAO_BENCH_COMPARE seja visível ao smoke no pod.
$payload = "microk8s kubectl exec $podName -- bash -c '${benchEnvPrefix}cd $($Node.path) 2>/dev/null || cd /app && bash ./scripts/lab-completao-host-smoke.sh $configArg $benchTrackArg $benchRunIdArg $benchHealthArg'"
$tmuxCmd = "tmux send-keys -t completao C-c ; sleep 0.5 ; tmux send-keys -t completao '$payload' Enter"

ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$tmuxCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Smoke MicroK8s injetado no Tmux em $($Node.hostname) (pod: $podName)." -ForegroundColor Green
} else {
    Write-Warning "      [ERROR] Falha ao injetar smoke MicroK8s em $($Node.hostname)."
}