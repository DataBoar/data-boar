#Requires -Version 5.1
<#
.SYNOPSIS
    Growatt solar data collection (ShinePhone API ou modo leitura de arquivo).

.DESCRIPTION
    Modos de operacao:
    - file   (default): le SOLAR_SYSTEM_NOTES.md e exibe resumo (sem rede, zero custo)
    - api    : coleta dados via ShinePhone OpenAPI (requer token em env GROWATT_TOKEN
               ou arquivo docs/private/homelab/.env.growatt.local)
    - status : exibe ultima atualizacao do arquivo de dados

    Nao navega o browser -- usa API token-based para acesso programatico.
    Para dados ao vivo sem token: operador navega server.growatt.com manualmente.

.PARAMETER Mode
    file (default) | api | status

.PARAMETER Out
    Arquivo de saida para dados novos (default: docs/private/homelab/SOLAR_SYSTEM_NOTES.md).

.EXAMPLE
    .\scripts\growatt.ps1                         # resumo do arquivo existente
    .\scripts\growatt.ps1 -Mode api               # coleta via API (precisa de token)
    .\scripts\growatt.ps1 -Mode status            # ultima atualizacao

.NOTES
    Token ShinePhone API: registrar em https://openapi.growatt.com
    Guardar token em docs/private/homelab/.env.growatt.local como:
      GROWATT_TOKEN=seu-token-aqui
    Ou exportar: $env:GROWATT_TOKEN = "seu-token"
#>
param(
    [ValidateSet("file","api","status")]
    [string]$Mode = "file",
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"
$notesFile  = Join-Path $privateDir "SOLAR_SYSTEM_NOTES.md"
$envFile    = Join-Path $privateDir ".env.growatt.local"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

switch ($Mode.ToLower()) {

    "file" {
        Write-Header "Growatt Solar -- Resumo (arquivo local)"
        if (-not (Test-Path $notesFile)) {
            Write-Warn "Arquivo nao encontrado: $notesFile"
            Write-Warn "Execute -Mode api para coletar dados, ou navegue server.growatt.com manualmente."
            exit 1
        }
        $content = Get-Content $notesFile -Raw
        # Extrair data do snapshot
        if ($content -match 'Extraido em:\*\*\s*(.+)') { Write-Info "Snapshot: $($Matches[1])" }
        # Extrair geracao de hoje e total
        if ($content -match 'Geracao hoje.*\|\s*([\d,.]+\s*kWh)') { Write-Ok "Geracao hoje: $($Matches[1])" }
        if ($content -match 'Geracao total acumulada.*\|\s*([\d,. ]+kWh)') { Write-Ok "Total acumulado: $($Matches[1])" }
        if ($content -match 'Capacidade instalada.*\|\s*(.+)') { Write-Ok "Capacidade: $($Matches[1])" }
        if ($content -match 'Data de comissionamento.*\|\s*(.+)') { Write-Info "Comissionado: $($Matches[1])" }
        Write-Host ""
        Write-Info "Para dados completos: Get-Content '$notesFile'"
        Write-Info "Para atualizar: .\scripts\growatt.ps1 -Mode api (requer GROWATT_TOKEN)"
    }

    "status" {
        Write-Header "Growatt Solar -- Status do arquivo"
        if (Test-Path $notesFile) {
            $fi = Get-Item $notesFile
            Write-Ok "Arquivo: $notesFile"
            Write-Ok "Ultima modificacao: $($fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))"
            $size = [math]::Round($fi.Length / 1KB, 1)
            Write-Info "Tamanho: ${size} KB"
        } else {
            Write-Warn "Arquivo nao existe ainda. Execute: .\scripts\growatt.ps1 -Mode api"
        }
    }

    "api" {
        Write-Header "Growatt Solar -- Coleta via ShinePhone API"

        # Tentar carregar token
        $token = $env:GROWATT_TOKEN
        if (-not $token -and (Test-Path $envFile)) {
            $envLines = Get-Content $envFile
            $tokenLine = $envLines | Where-Object { $_ -match '^GROWATT_TOKEN=' } | Select-Object -First 1
            if ($tokenLine) { $token = $tokenLine -replace '^GROWATT_TOKEN=','' }
        }

        if (-not $token) {
            Write-Warn "Token Growatt nao encontrado."
            Write-Host ""
            Write-Host "Para configurar:" -ForegroundColor Yellow
            Write-Host "  1. Registrar em: https://openapi.growatt.com" -ForegroundColor Yellow
            Write-Host "  2. Criar arquivo: $envFile" -ForegroundColor Yellow
            Write-Host "     Conteudo: GROWATT_TOKEN=seu-token-aqui" -ForegroundColor Yellow
            Write-Host "  3. Ou exportar: `$env:GROWATT_TOKEN = 'seu-token'" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Alternativa (browser): navegar https://server.growatt.com e extrair dados manualmente." -ForegroundColor Gray
            exit 1
        }

        $apiBase = "https://openapi.growatt.com/v1"
        $headers = @{ "token" = $token; "Content-Type" = "application/json" }

        Write-Info "Consultando lista de plantas..."
        try {
            $plants = Invoke-RestMethod "$apiBase/plant/list" -Headers $headers -Method GET -TimeoutSec 15
            if ($plants.data) {
                Write-Ok "Plantas encontradas: $($plants.data.Count)"
                $plants.data | ForEach-Object { Write-Info "  Plant: $($_.plant_id) -- $($_.plant_name)" }

                # Usar primeiro plant_id (ou o conhecido)
                $plantId = if ($plants.data[0].plant_id) { $plants.data[0].plant_id } else { "843372" }
                Write-Info "Usando Plant ID: $plantId"

                $today = Get-Date -Format "yyyy-MM-dd"
                $month = Get-Date -Format "yyyy-MM"
                $year  = Get-Date -Format "yyyy"

                Write-Info "Coletando dados mensais ($month)..."
                $monthly = Invoke-RestMethod "$apiBase/energy/month?plant_id=$plantId&date=$month" -Headers $headers -Method GET -TimeoutSec 15

                Write-Info "Coletando dados anuais ($year)..."
                $annual = Invoke-RestMethod "$apiBase/energy/year?plant_id=$plantId&year=$year" -Headers $headers -Method GET -TimeoutSec 15

                Write-Ok "Dados coletados com sucesso."

                # Exibir resumo
                if ($monthly.data) {
                    Write-Header "Geracao Mensal ($month)"
                    $monthly.data | Format-Table -AutoSize
                }

                # Salvar em arquivo
                $outPath = if ($Out) { $Out } else { $notesFile }
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
                $newSection = @"

---

## Update $timestamp via ShinePhone API

### Dados Mensais ($month)
$($monthly | ConvertTo-Json -Depth 5)

### Dados Anuais ($year)
$($annual | ConvertTo-Json -Depth 5)
"@
                Add-Content -Encoding UTF8 -Path $outPath -Value $newSection
                Write-Ok "Dados salvos em: $outPath"
            }
        } catch {
            Write-Warn "Erro na API Growatt: $_"
            Write-Warn "Verifique se o token e valido e se o endpoint esta correto."
            Write-Host "URL tentada: $apiBase/plant/list" -ForegroundColor Gray
            Write-Host "Documentacao: https://www.showdoc.com.br/opensolarapi" -ForegroundColor Gray
        }
    }
}
