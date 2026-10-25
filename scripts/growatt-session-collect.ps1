#Requires -Version 5.1
<#
.SYNOPSIS
    Growatt solar -- coleta via session cookie do browser (sem token OpenAPI).

.DESCRIPTION
    Usa o cookie de sessao extraido do browser Cursor (apos login em server.growatt.com)
    para consultar os endpoints web da Growatt sem precisar de API token registrado.

    Modos:
    - today   : geracao do dia atual
    - month   : geracao do mes atual (ou -Date "yyyy-MM")
    - year    : geracao do ano atual (ou -Date "yyyy")
    - plant   : lista de plantas e dispositivos
    - save    : coleta e atualiza SOLAR_SYSTEM_NOTES.md
    - check   : verifica se o cookie ainda e valido

    WORKFLOW RECOMENDADO:
    1. Fazer login em server.growatt.com no browser Cursor
    2. Exportar cookie: agent usa browser_navigate + extrai cookie da pagina
    3. Salvar em docs/private/homelab/.env.growatt.session:
           GROWATT_SESSION=<valor do cookie JSESSIONID>
    4. Rodar este script com -Mode today/month/save

.PARAMETER Mode
    today (default) | month | year | plant | save | check

.PARAMETER Date
    Data para -Mode month (yyyy-MM) ou year (yyyy). Default: atual.

.PARAMETER PlantId
    ID da planta Growatt. Default: 843372 (valor conhecido).

.EXAMPLE
    .\scripts\growatt-session-collect.ps1
    .\scripts\growatt-session-collect.ps1 -Mode month
    .\scripts\growatt-session-collect.ps1 -Mode save
    .\scripts\growatt-session-collect.ps1 -Mode check

.NOTES
    Se a sessao expirou: faca login novamente em server.growatt.com no browser Cursor,
    entao exporte o cookie novamente.
    Arquivo de sessao: docs/private/homelab/.env.growatt.session
    Alternativa com token OpenAPI: .\scripts\growatt.ps1 -Mode api
#>
param(
    [ValidateSet("today","month","year","plant","save","check")]
    [string]$Mode = "today",
    [string]$Date = "",
    [string]$PlantId = "843372"
)

$ErrorActionPreference = "Stop"
$repoRoot   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"
$sessionEnv = Join-Path $privateDir ".env.growatt.session"
$notesFile  = Join-Path $privateDir "SOLAR_SYSTEM_NOTES.md"
$base       = "https://server.growatt.com"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

function Get-Session {
    $session = $env:GROWATT_SESSION
    if (-not $session -and (Test-Path $sessionEnv)) {
        $lines = Get-Content $sessionEnv
        $line = $lines | Where-Object { $_ -match '^GROWATT_SESSION=' } | Select-Object -First 1
        if ($line) { $session = $line -replace '^GROWATT_SESSION=','' }
    }
    return $session
}

function Get-Headers($session) {
    return @{
        "Cookie"           = "JSESSIONID=$session"
        "Content-Type"     = "application/x-www-form-urlencoded"
        "X-Requested-With" = "XMLHttpRequest"
        "Referer"          = "$base/index"
        "User-Agent"       = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
}

function Test-SessionValid($session) {
    try {
        $h = Get-Headers $session
        $r = Invoke-WebRequest "$base/indexbC.do" -Headers $h -Method POST -Body "plantId=$PlantId" -TimeoutSec 10 -UseBasicParsing
        return ($r.StatusCode -eq 200 -and $r.Content -notmatch 'errorNoLogin|login\.do')
    } catch { return $false }
}

function Show-SessionSetupGuide {
    Write-Warn "Cookie de sessao Growatt nao encontrado ou expirado."
    Write-Host ""
    Write-Host "Para configurar:" -ForegroundColor Yellow
    Write-Host "  1. No browser Cursor, navegue: https://server.growatt.com/login" -ForegroundColor Yellow
    Write-Host "  2. Faca login com suas credenciais" -ForegroundColor Yellow
    Write-Host "  3. Abra DevTools (F12) -> Application -> Cookies -> server.growatt.com" -ForegroundColor Yellow
    Write-Host "  4. Copie o valor do cookie 'JSESSIONID'" -ForegroundColor Yellow
    Write-Host "  5. Crie o arquivo: $sessionEnv" -ForegroundColor Yellow
    Write-Host "     Conteudo: GROWATT_SESSION=<valor-copiado>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternativa com token OpenAPI (mais estavel, sem expiracao curta):" -ForegroundColor Gray
    Write-Host "  .\scripts\growatt.ps1 -Mode api   (requer registro em openapi.growatt.com)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "DICA: O agente pode extrair o cookie automaticamente se o browser estiver warm:" -ForegroundColor Cyan
    Write-Host "  browser_navigate https://server.growatt.com/index" -ForegroundColor Cyan
    Write-Host "  -> extrair document.cookie ou via DevTools -> salvar em $sessionEnv" -ForegroundColor Cyan
}

# --- MAIN ---
$session = Get-Session

# --- CHECK ---
if ($Mode -eq "check") {
    Write-Header "Growatt Session -- Verificacao"
    if (-not $session) { Show-SessionSetupGuide; exit 1 }
    Write-Info "Cookie encontrado: $(if ($session.Length -gt 8) { $session.Substring(0,8) + '...' } else { '(curto)' })"
    $valid = Test-SessionValid $session
    if ($valid) {
        Write-Ok "Sessao VALIDA -- pronto para coletar dados"
    } else {
        Write-Warn "Sessao EXPIRADA ou invalida"
        Show-SessionSetupGuide
        exit 1
    }
    exit 0
}

if (-not $session) { Show-SessionSetupGuide; exit 1 }

$h = Get-Headers $session
$today  = Get-Date -Format "yyyy-MM-dd"
$month  = if ($Date -match '^\d{4}-\d{2}$') { $Date } else { Get-Date -Format "yyyy-MM" }
$year   = if ($Date -match '^\d{4}$')       { $Date } else { Get-Date -Format "yyyy" }

switch ($Mode) {

    "plant" {
        Write-Header "Growatt -- Lista de Plantas"
        $r = Invoke-RestMethod "$base/index/getPlantListTitle" -Headers $h -Method POST -TimeoutSec 15
        $r | ConvertTo-Json -Depth 4
    }

    "today" {
        Write-Header "Growatt -- Geracao de Hoje ($today)"
        $body = "date=$today&plantId=$PlantId"
        try {
            $r = Invoke-RestMethod "$base/panel/getDevicesByPlantList" -Headers $h -Method POST -Body $body -TimeoutSec 15
            if ($r.obj) {
                Write-Ok "Dados recebidos"
                $r.obj | ConvertTo-Json -Depth 4
            } else {
                Write-Warn "Resposta inesperada. Sessao pode ter expirado."
                $r | ConvertTo-Json -Depth 2
            }
        } catch {
            Write-Warn "Erro ao consultar dados de hoje: $_"
            Write-Info "Tente: .\scripts\growatt-session-collect.ps1 -Mode check"
        }
    }

    "month" {
        Write-Header "Growatt -- Geracao Mensal ($month)"
        $body = "date=$month&type=2&plantId=$PlantId"
        try {
            $r = Invoke-RestMethod "$base/energy/compare/getCompareChartData" -Headers $h -Method POST -Body $body -TimeoutSec 15
            $r | ConvertTo-Json -Depth 4
        } catch {
            Write-Warn "Erro: $_"
            Write-Info "Endpoint alternativo tentado: energy/compare/getCompareChartData"
        }
    }

    "year" {
        Write-Header "Growatt -- Geracao Anual ($year)"
        $body = "date=$year&type=3&plantId=$PlantId"
        try {
            $r = Invoke-RestMethod "$base/energy/compare/getCompareChartData" -Headers $h -Method POST -Body $body -TimeoutSec 15
            $r | ConvertTo-Json -Depth 4
        } catch {
            Write-Warn "Erro: $_"
        }
    }

    "save" {
        Write-Header "Growatt -- Coleta e Salvar em SOLAR_SYSTEM_NOTES.md"
        Write-Info "Verificando sessao..."
        if (-not (Test-SessionValid $session)) {
            Write-Warn "Sessao invalida. Refaca login e atualize $sessionEnv"
            exit 1
        }
        Write-Ok "Sessao valida"
        Write-Info "Coletando dados do dia ($today)..."
        $body  = "date=$today&plantId=$PlantId"
        try {
            $today_data  = Invoke-RestMethod "$base/panel/getDevicesByPlantList" -Headers $h -Method POST -Body $body -TimeoutSec 15
            $month_body  = "date=$month&type=2&plantId=$PlantId"
            $month_data  = Invoke-RestMethod "$base/energy/compare/getCompareChartData" -Headers $h -Method POST -Body $month_body -TimeoutSec 15
            $timestamp   = Get-Date -Format "yyyy-MM-dd HH:mm"
            $newSection  = @"

---

## Update $timestamp (growatt-session-collect.ps1)

### Dados do dia ($today)
$($today_data | ConvertTo-Json -Depth 4)

### Dados mensais ($month)
$($month_data | ConvertTo-Json -Depth 4)
"@
            Add-Content -Encoding UTF8 -Path $notesFile -Value $newSection
            Write-Ok "Dados salvos em: $notesFile"
        } catch {
            Write-Warn "Erro ao coletar/salvar: $_"
        }
    }
}
