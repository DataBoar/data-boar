#Requires -Version 5.1
<#
.SYNOPSIS
    Relatorio de energia: solar gerado vs grid consumido (correlacao Growatt x Enel).

.DESCRIPTION
    Le SOLAR_SYSTEM_NOTES.md e ENEL_ACCOUNT_NOTES.md e gera relatorio de balanco energetico.
    Exibe o que ja foi capturado e aponta lacunas de dados a serem preenchidas.

.PARAMETER Year
    Ano para filtrar. Default: ano atual.

.PARAMETER Out
    Salvar relatorio em arquivo (opcional). Ex: docs/private/homelab/ENERGY_REPORT_2026.md

.EXAMPLE
    .\scripts\energy-report.ps1
    .\scripts\energy-report.ps1 -Year 2025
    .\scripts\energy-report.ps1 -Out docs/private/homelab/ENERGY_REPORT_2026.md
#>
param(
    [int]$Year = (Get-Date).Year,
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"
$solarFile  = Join-Path $privateDir "SOLAR_SYSTEM_NOTES.md"
$enelFile   = Join-Path $privateDir "ENEL_ACCOUNT_NOTES.md"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

$report = @()
$report += "# Relatorio de Energia -- Growatt x Enel"
$report += "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm') | Ano: $Year"
$report += ""

Write-Header "Relatorio de Energia $Year"

# --- SOLAR ---
$report += "## Solar (Growatt MIC 3000TL-X -- Plant 843372)"
if (Test-Path $solarFile) {
    $solarContent = Get-Content $solarFile -Raw
    Write-Ok "Arquivo solar: $solarFile"

    if ($solarContent -match 'Geracao total acumulada.*?\|\s*([\d,. ]+kWh)') {
        $total = $Matches[1].Trim()
        Write-Ok "Total acumulado: $total"
        $report += "- **Total acumulado (vida util):** $total"
    }
    if ($solarContent -match 'Capacidade instalada.*?\|\s*([\d,. ]+W[^|]*)') {
        $cap = $Matches[1].Trim()
        $report += "- **Capacidade instalada:** $cap"
    }
    if ($solarContent -match 'Data de comissionamento.*?\|\s*(.+)') {
        $report += "- **Comissionado:** $($Matches[1].Trim())"
    }
    if ($solarContent -match 'Media mensal estimada.*?:\s*(.+)') {
        $report += "- **Media mensal estimada:** $($Matches[1].Trim())"
    }
    # Estimativas
    $report += ""
    $report += "### Estimativa de geracao (media historica)"
    $report += "- Media anual historica: ~5,874 kWh/ano (25,844 kWh / 4.4 anos)"
    $report += "- Media mensal estimada: ~490 kWh/mes (dia ensolarado: ~22 kWh)"
    $report += "- Nota: dados mensais exatos pendentes de coleta no portal Growatt"
} else {
    Write-Warn "Arquivo solar nao encontrado. Execute: .\scripts\growatt.ps1 -Mode api"
    $report += "- DADOS INDISPONIVEIS -- executar: .\scripts\growatt.ps1 -Mode api"
}

$report += ""
$report += "---"
$report += ""

# --- ENEL ---
$report += "## Grid / Concessionaria (Enel RJ -- UC <UC_NUMBER>)"
if (Test-Path $enelFile) {
    $enelContent = Get-Content $enelFile -Raw
    Write-Ok "Arquivo Enel: $enelFile"

    if ($enelContent -match 'Total de Debitos.*?(R\$[\s\d,\.]+)') {
        $report += "- **Debitos atuais:** $($Matches[1].Trim())"
    }

    $report += ""
    $report += "### Faturas disponiveis (IDs de referencia -- kWh nao capturados ainda)"
    $report += "| Referencia | Mes estimado | kWh consumido |"
    $report += "|---|---|---|"

    $refs = [regex]::Matches($enelContent, '(020\d{15,})\s*\|\s*([^\|]+)')
    if ($refs.Count -gt 0) {
        $refs | ForEach-Object {
            $ref = $_.Groups[1].Value
            $mes = $_.Groups[2].Value.Trim()
            $report += "| $ref | $mes | (pendente) |"
        }
        Write-Info "Faturas identificadas: $($refs.Count)"
    }

    $report += ""
    $report += "**LACUNA:** kWh mensais consumidos nao estao capturados."
    $report += "Para completar: operador acessa 'Grafico de Consumo' no portal Enel"
    $report += "e anota os kWh por mes. Passar aqui para atualizacao."
} else {
    Write-Warn "Arquivo Enel nao encontrado."
    $report += "- DADOS INDISPONIVEIS"
}

$report += ""
$report += "---"
$report += ""

# --- CORRELACAO ---
$report += "## Balanco Energetico (Solar x Grid)"
$report += ""
$report += "| Mes | Gerado (kWh) | Consumido (kWh) | Saldo | % Auto-suficiencia |"
$report += "|---|---|---|---|---|"
$report += "| Dados pendentes | -- | -- | -- | -- |"
$report += ""
$report += "**Para completar esta tabela:**"
$report += '1. Coletar geracao mensal do Growatt: .\scripts\growatt.ps1 -Mode api'
$report += "2. Coletar consumo mensal da Enel: operador baixa 'Grafico de Consumo' no portal"
$report += "3. Re-executar: .\scripts\energy-report.ps1 -Out docs/private/homelab/ENERGY_REPORT_$Year.md"

# --- EXIBIR E SALVAR ---
Write-Header "Resumo do Relatorio"
$report | ForEach-Object {
    if ($_ -match '^#') { Write-Host $_ -ForegroundColor Yellow }
    elseif ($_ -match '^\- \*\*') { Write-Host $_ -ForegroundColor Green }
    elseif ($_ -match 'LACUNA|pendente|INDISPONIVEL') { Write-Host $_ -ForegroundColor Red }
    else { Write-Host $_ -ForegroundColor White }
}

if ($Out) {
    $report | Set-Content -Encoding UTF8 -Path $Out
    Write-Host ""
    Write-Host "Relatorio salvo em: $Out" -ForegroundColor Green
    Write-Warn "Lembre: este arquivo e privado -- nao commitar no Git."
}

