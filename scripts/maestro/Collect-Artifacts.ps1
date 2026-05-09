#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Collect-Artifacts.ps1

.SYNOPSIS
 Coletor de Telemetria Fria (Post-Flight).
 Puxa logs operacionais do Tmux remoto e salva no cofre privado sem expor no GH público.
#>

param(
    [Parameter(Mandatory=$true)]$Node
)

Set-StrictMode -Version 2

# 1. Caminho Canônico do Cofre Privado
$privateReportsDir = (Resolve-Path "$PSScriptRoot/../../docs/private/homelab/reports").Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "   [Collect] Baixando artefatos de $($Node.hostname)..." -ForegroundColor DarkCyan

# 2. Cria uma pasta específica para a coleta desta sessão
# 2.1 Puxa todos os logs da pasta ~/log/ do nó para a nova pasta no Maestro PC, renomeando com Host + Timestamp para não sobrescrever o histórico
$localDestDir = "$privateReportsDir\coleta_$($Node.hostname)_$timestamp"
New-Item -ItemType Directory -Force -Path $localDestDir > $null

$targetLogPattern = "$($Node.user)@$($Node.hostname):~/log/*.log"
scp -q -o BatchMode=yes $targetLogPattern "$localDestDir\" > $null 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Artefatos salvos em private/homelab/reports/" -ForegroundColor Green

    # Opcional de limpeza: limpa a sujeira na borda após coleta bem-sucedida (descomente se quiser)
    # ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "rm -f ~/log/*.log"
} else {
    Write-Warning "      [WARNING] Sem artefatos (ou falha) em $($Node.hostname)."
}
