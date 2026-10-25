#Requires -Version 5.1
<#
.SYNOPSIS
    Carrega variaveis de ambiente LAB-OP para a sessao PowerShell atual.

.DESCRIPTION
    Prioridade:
    1. Bitwarden (se BW_SESSION definido) -- fonte autoritativa
    2. Arquivos .env.*.local em docs/private/homelab/ -- fallback offline

    Exporta variaveis para $env: para uso pelos outros scripts
    (growatt.ps1, LAB-ROUTER-01.ps1, enel.ps1, energy-report.ps1).

    Uso tipico no inicio de sessao:
      $env:BW_SESSION = (bw unlock --raw)
      . .\scripts\lab-env-load.ps1        # dot-source para exportar no shell atual

.PARAMETER Systems
    Sistemas a carregar. Padrao: todos.
    Opcoes: LAB-ROUTER-01, growatt, enel, ssh, all

.PARAMETER SkipBitwarden
    Pular tentativa de Bitwarden e usar apenas arquivos locais.

.EXAMPLE
    # Sessao completa com Bitwarden:
    $env:BW_SESSION = (bw unlock --raw)
    . .\scripts\lab-env-load.ps1

    # Apenas LAB-ROUTER-01 via arquivo local (sem BW):
    . .\scripts\lab-env-load.ps1 -Systems LAB-ROUTER-01 -SkipBitwarden

    # Apenas Growatt:
    . .\scripts\lab-env-load.ps1 -Systems growatt
#>
param(
    [ValidateSet("LAB-ROUTER-01","growatt","enel","ssh","all")]
    [string]$Systems = "all",
    [switch]$SkipBitwarden
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"

function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  ... $msg" -ForegroundColor Gray }

function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | Where-Object { $_ -match '^\s*[A-Z_]+=.' -and $_ -notmatch '^\s*#' } | ForEach-Object {
        $parts = $_ -split '=', 2
        $key = $parts[0].Trim()
        $val = $parts[1].Trim()
        if (-not [Environment]::GetEnvironmentVariable($key)) {
            [Environment]::SetEnvironmentVariable($key, $val)
            Set-Item -Path "env:$key" -Value $val
        }
    }
}

function Load-BwItem {
    param([string]$ItemName, [string]$EnvKey, [string]$Field = "password")
    if (-not $env:BW_SESSION) { return $null }
    try {
        $item = bw get item $ItemName --session $env:BW_SESSION 2>$null | ConvertFrom-Json
        if (-not $item) { return $null }
        $val = switch ($Field) {
            "password" { $item.login.password }
            "username" { $item.login.username }
            default {
                ($item.fields | Where-Object { $_.name -eq $Field } | Select-Object -First 1).value
            }
        }
        if ($val) {
            Set-Item -Path "env:$EnvKey" -Value $val
            return $val
        }
    } catch { }
    return $null
}

Write-Host ""
Write-Host "=== LAB-OP env loader ===" -ForegroundColor Cyan

$loadLAB-ROUTER-01     = $Systems -in @("LAB-ROUTER-01", "all")
$loadGrowatt = $Systems -in @("growatt", "all")
$loadEnel    = $Systems -in @("enel", "all")
$loadSsh     = $Systems -in @("ssh", "all")
$useBw       = (-not $SkipBitwarden) -and $env:BW_SESSION

if ($useBw) {
    Write-Info "Bitwarden: BW_SESSION detectado -- priorizando BW"
} else {
    Write-Info "Modo arquivo local (sem BW_SESSION ou -SkipBitwarden)"
}

# --- LAB-ROUTER-01 ---
if ($loadLAB-ROUTER-01) {
    Write-Info "Carregando LAB-ROUTER-01..."
    Load-EnvFile (Join-Path $privateDir ".env.api.LAB-ROUTER-01-se.local")
    if ($useBw) {
        $bwKey = Load-BwItem "LAB-ROUTER-01 cursor.auto.ai" "LAB_LAB-ROUTER-01_API_KEY"
        if ($bwKey) { Write-Ok "LAB-ROUTER-01: API key via Bitwarden" }
        else { Write-Info "LAB-ROUTER-01: BW item nao encontrado -- usando arquivo local" }
    }
    if ($env:LAB_LAB-ROUTER-01_API_KEY) { Write-Ok "LAB-ROUTER-01: LAB_LAB-ROUTER-01_API_KEY carregada" }
    else { Write-Warn "LAB-ROUTER-01: LAB_LAB-ROUTER-01_API_KEY nao definida" }
}

# --- Growatt ---
if ($loadGrowatt) {
    Write-Info "Carregando Growatt..."
    Load-EnvFile (Join-Path $privateDir ".env.growatt.local")
    if ($useBw) {
        $bwToken = Load-BwItem "Growatt ShinePhone API" "GROWATT_TOKEN"
        if ($bwToken) { Write-Ok "Growatt: token via Bitwarden" }
        else { Write-Info "Growatt: BW item nao encontrado -- usando arquivo local" }
    }
    if ($env:GROWATT_TOKEN -and $env:GROWATT_TOKEN -ne "PREENCHER_AQUI") {
        Write-Ok "Growatt: GROWATT_TOKEN carregada"
    } else {
        Write-Warn "Growatt: GROWATT_TOKEN nao definida (registrar em openapi.growatt.com)"
    }
}

# --- Enel (referencia apenas -- sem automatizacao) ---
if ($loadEnel) {
    Write-Info "Carregando Enel (referencia -- sem automacao de browser)..."
    Load-EnvFile (Join-Path $privateDir ".env.enel.local")
    if ($env:ENEL_UC) { Write-Ok "Enel: UC $env:ENEL_UC carregada (referencia)" }
}

# --- SSH hosts ---
if ($loadSsh) {
    Write-Info "Carregando SSH hosts..."
    Load-EnvFile (Join-Path $privateDir ".env.ssh-hosts.local")
    if ($env:LAB_SSH_USER) { Write-Ok "SSH: user=$env:LAB_SSH_USER key=$env:LAB_SSH_KEY" }
}

Write-Host ""
Write-Host "Variaveis disponiveis para esta sessao:" -ForegroundColor Cyan
$vars = @("LAB_LAB-ROUTER-01_API_KEY","LAB_LAB-ROUTER-01_API_BASE_URL","GROWATT_TOKEN","GROWATT_PLANT_ID",
           "ENEL_UC","LAB_SSH_USER","LAB_HOST_LAB-NODE-02","LAB_HOST_MINIBT","LAB_HOST_LAB-NODE-04")
foreach ($v in $vars) {
    $val = [Environment]::GetEnvironmentVariable($v)
    if ($val) {
        $display = if ($v -match 'KEY|TOKEN|PASSWORD') { "***" } else { $val }
        Write-Host "  `$$v = $display" -ForegroundColor White
    }
}
Write-Host ""
Write-Host "Uso: .\scripts\LAB-ROUTER-01.ps1 -Command scan" -ForegroundColor Gray
Write-Host "     .\scripts\growatt.ps1 -Mode api" -ForegroundColor Gray
Write-Host "     .\scripts\energy-report.ps1" -ForegroundColor Gray
