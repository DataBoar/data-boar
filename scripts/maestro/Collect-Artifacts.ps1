#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Collect-Artifacts.ps1

.SYNOPSIS
 Coletor de Telemetria Fria (Post-Flight).
 Puxa logs operacionais do repo remoto (<path>/log/) e salva no cofre privado sem expor no GH publico.

 #956: scans gravam em <repo>/log/ (benchmark-rc export_audit_trail), nao ~/log/.
#>

param(
    [Parameter(Mandatory=$true)]$Node
)

Set-StrictMode -Version 2

# 1. Caminho Canônico do Cofre Privado
$privateReportsDir = (Resolve-Path "$PSScriptRoot/../../docs/private/homelab/reports").Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "   [Collect] Baixando artefatos de $($Node.hostname)..." -ForegroundColor DarkCyan

$repoPath = [string]$Node.path -replace "^~", "~"
$localDestDir = "$privateReportsDir\coleta_$($Node.hostname)_$timestamp"
New-Item -ItemType Directory -Force -Path $localDestDir > $null

$remoteBase = "$($Node.user)@$($Node.hostname)"
$repoLogPattern = "${remoteBase}:${repoPath}/log/*.log"
$repoAuditPattern = "${remoteBase}:${repoPath}/log/audit_trail*.log"

$collected = $false
scp -q -o BatchMode=yes $repoLogPattern "$localDestDir\" > $null 2>&1
if ($LASTEXITCODE -eq 0) { $collected = $true }

if (-not $collected) {
    scp -q -o BatchMode=yes $repoAuditPattern "$localDestDir\" > $null 2>&1
    if ($LASTEXITCODE -eq 0) { $collected = $true }
}

# Legacy fallback: operator home ~/log (pre-#956); warn once if only legacy exists.
if (-not $collected) {
    $legacyPattern = "${remoteBase}:~/log/*.log"
    scp -q -o BatchMode=yes $legacyPattern "$localDestDir\" > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Warning "      [WARNING] Coleta usou fallback ~/log (esperado <repo>/log/ apos #956)."
        $collected = $true
    }
}

if ($collected) {
    Write-Host "      [SUCCESS] Artefatos salvos em private/homelab/reports/" -ForegroundColor Green
    return $true
} else {
    Write-Warning "      [WARNING] Sem artefatos em $($Node.path)/log/ (ou falha scp) em $($Node.hostname)."
    return $false
}
