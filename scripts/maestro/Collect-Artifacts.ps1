#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Collect-Artifacts.ps1

.SYNOPSIS
 Coletor de Telemetria Fria (Post-Flight).
 Puxa logs operacionais do repo remoto (<path>/log/) e salva no cofre privado sem expor no GH publico.

 #956: scans gravam em <repo>/log/ (benchmark-rc export_audit_trail), nao ~/log/.
 #968: Join-Path (Linux-safe); nunca [SUCCESS] com diretorio vazio.
#>

param(
    [Parameter(Mandatory=$true)]$Node
)

Set-StrictMode -Version 2

function Get-CollectArtifactCount {
    param([Parameter(Mandatory = $true)][string]$Dir)
    if (-not (Test-Path -LiteralPath $Dir)) {
        return 0
    }
    return @(Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue).Count
}

# 1. Caminho Canônico do Cofre Privado
$privateReportsDir = (Resolve-Path "$PSScriptRoot/../../docs/private/homelab/reports").Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "   [Collect] Baixando artefatos de $($Node.hostname)..." -ForegroundColor DarkCyan

$repoPath = [string]$Node.path -replace "^~", "~"
$localDestDir = Join-Path $privateReportsDir "coleta_$($Node.hostname)_$timestamp"
New-Item -ItemType Directory -Force -Path $localDestDir | Out-Null

$remoteBase = "$($Node.user)@$($Node.hostname)"
$repoLogPattern = "${remoteBase}:${repoPath}/log/*.log"
$repoAuditPattern = "${remoteBase}:${repoPath}/log/audit_trail*.log"

$usedLegacy = $false
$scpAttempted = $false

scp -q -o BatchMode=yes $repoLogPattern "${localDestDir}/" > $null 2>&1
$scpAttempted = $true

if ((Get-CollectArtifactCount -Dir $localDestDir) -eq 0) {
    scp -q -o BatchMode=yes $repoAuditPattern "${localDestDir}/" > $null 2>&1
}

# Legacy fallback: operator home ~/log (pre-#956); warn once if only legacy exists.
if ((Get-CollectArtifactCount -Dir $localDestDir) -eq 0) {
    $legacyPattern = "${remoteBase}:~/log/*.log"
    scp -q -o BatchMode=yes $legacyPattern "${localDestDir}/" > $null 2>&1
    if ((Get-CollectArtifactCount -Dir $localDestDir) -gt 0) {
        $usedLegacy = $true
    }
}

$artifactCount = Get-CollectArtifactCount -Dir $localDestDir
if ($artifactCount -gt 0) {
    if ($usedLegacy) {
        Write-Warning "      [WARNING] Coleta usou fallback ~/log (esperado <repo>/log/ apos #956)."
    }
    Write-Host "      [SUCCESS] $artifactCount artefato(s) em $localDestDir" -ForegroundColor Green
    return $true
}

$hint = if ($scpAttempted) { "scp executou mas nenhum arquivo aterrou" } else { "scp nao tentado" }
Write-Error "      [REAL FAIL] Collect: zero artefatos em $localDestDir ($hint; host $($Node.hostname); repo log em $($Node.path)/log/)."
return $false
