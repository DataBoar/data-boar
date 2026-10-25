#Requires -Version 5.1
<#
.SYNOPSIS
    Enel RJ -- coleta READ-ONLY via session cookie do browser.

.DESCRIPTION
    Usa cookie de sessao do browser (login Google OAuth em enel.com.br) para consultar
    consumo mensal, historico de faturas e status da conta -- SEM interagir com formularios
    ou botoes que possam gerar protocolos de servico.

    GUARDRAIL CRITICO: Este script NUNCA clica em botoes. Le apenas dados de texto.
    Background: em sessao anterior, interacao com o portal gerou 3 protocolos acidentais
    de "Falta de Luz" (PROTO-REDACTED, PROTO-REDACTED, PROTO-REDACTED).

    Modos:
    - summary (default) : dados basicos da conta e ultima fatura
    - invoices          : lista de faturas recentes (ultimas 12)
    - consumption       : grafico de consumo mensal
    - check             : verifica se a sessao e valida

.PARAMETER Mode
    summary (default) | invoices | consumption | check

.PARAMETER UC
    Unidade Consumidora (default: 8092489 -- UC de Fabio em Niteroi).

.EXAMPLE
    .\scripts\enel-session-collect.ps1
    .\scripts\enel-session-collect.ps1 -Mode invoices
    .\scripts\enel-session-collect.ps1 -Mode check

.NOTES
    Cookie: salvar em docs/private/homelab/.env.enel.session
    Formato: ENEL_SESSION=<valor-do-cookie-ASP.NET_SessionId-ou-equivalente>
    Contato Enel: ENEL-PHONE-REDACTED
    Portal: https://www.enel.com.br/pt/private-area.html
    GUARDRAIL: Nunca navegar para paginas de registro de ocorrencias ou servicos.
#>
param(
    [ValidateSet("summary","invoices","consumption","check")]
    [string]$Mode = "summary",
    [string]$UC = "8092489"
)

$ErrorActionPreference = "Stop"
$repoRoot   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"
$sessionEnv = Join-Path $privateDir ".env.enel.session"
$notesFile  = Join-Path $privateDir "ENEL_ACCOUNT_NOTES.md"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }
function Write-Guard($msg)  { Write-Host " SAFE $msg" -ForegroundColor Magenta }

Write-Guard "MODO READ-ONLY ATIVO -- Nenhum botao ou formulario sera submetido"

function Get-Session {
    $s = $env:ENEL_SESSION
    if (-not $s -and (Test-Path $sessionEnv)) {
        $line = (Get-Content $sessionEnv) | Where-Object { $_ -match '^ENEL_SESSION=' } | Select-Object -First 1
        if ($line) { $s = $line -replace '^ENEL_SESSION=','' }
    }
    return $s
}

function Show-SessionSetupGuide {
    Write-Warn "Cookie de sessao Enel nao encontrado ou expirado."
    Write-Host ""
    Write-Host "Para configurar (frequencia: mensal):" -ForegroundColor Yellow
    Write-Host "  1. Browser Cursor: abrir https://www.enel.com.br/pt/private-area.html" -ForegroundColor Yellow
    Write-Host "  2. Login com Google OAuth (mesmo email)" -ForegroundColor Yellow
    Write-Host "  3. DevTools (F12) -> Application -> Cookies -> enel.com.br" -ForegroundColor Yellow
    Write-Host "  4. Copiar valor do cookie de sessao (ASP.NET_SessionId ou similar)" -ForegroundColor Yellow
    Write-Host "  5. Criar: $sessionEnv" -ForegroundColor Yellow
    Write-Host "     Conteudo: ENEL_SESSION=<valor>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "GUARDRAIL: Ao navegar, NUNCA clicar em 'Registrar Falta' ou botoes de servico!" -ForegroundColor Red
}

$session = Get-Session

if ($Mode -eq "check") {
    Write-Header "Enel Session -- Verificacao"
    if (-not $session) { Show-SessionSetupGuide; exit 1 }
    Write-Info "Cookie: $($session.Substring(0, [Math]::Min(8,$session.Length)))..."
    # Verificar acesso a pagina de dados (sem formularios)
    try {
        $h = @{ "Cookie" = "ASP.NET_SessionId=$session"; "User-Agent" = "Mozilla/5.0" }
        $r = Invoke-WebRequest "https://www.enel.com.br/pt/private-area.html" -Headers $h -TimeoutSec 15 -UseBasicParsing
        if ($r.StatusCode -eq 200 -and $r.Content -notmatch 'login|authenticate') {
            Write-Ok "Sessao VALIDA"
        } else {
            Write-Warn "Sessao pode ter expirado -- verifique no browser"
            Show-SessionSetupGuide
        }
    } catch { Write-Warn "Erro ao verificar: $_" }
    exit 0
}

if (-not $session) { Show-SessionSetupGuide; exit 1 }

# AVISO: Para Enel, a API real requer tokens OAuth que mudam frequentemente.
# A abordagem mais confiavel e verificar a conta MENSALMENTE no browser Cursor
# e anotar os dados manualmente ou via screenshot.
Write-Header "Enel RJ -- Modo: $Mode"
Write-Guard "Este script le ENEL_ACCOUNT_NOTES.md (dados pre-capturados)"
Write-Info "Para dados ao vivo: verifique no browser Cursor (auth Google OAuth)"
Write-Info "UC: $UC | Portal: https://www.enel.com.br/pt/private-area.html"
Write-Host ""

# Le e exibe o arquivo de notas existente
if (Test-Path $notesFile) {
    switch ($Mode) {
        "summary" {
            $content = Get-Content $notesFile -Raw
            if ($content -match 'UC:\s*(\d+)') { Write-Ok "UC: $($Matches[1])" }
            if ($content -match 'Total.*debitos.*R\$\s*([\d,.]+)') { Write-Ok "Saldo: R$ $($Matches[1])" }
            if ($content -match 'Faturas.*visiveis:\s*(\d+)') { Write-Info "Faturas: $($Matches[1])" }
            $fi = Get-Item $notesFile
            Write-Info "Dados coletados em: $($fi.LastWriteTime.ToString('yyyy-MM-dd'))"
            Write-Info "Para detalhes: Get-Content '$notesFile'"
        }
        "invoices" {
            Write-Info "Conteudo de ENEL_ACCOUNT_NOTES.md:"
            Get-Content $notesFile
        }
        "consumption" {
            Write-Info "Conteudo de ENEL_ACCOUNT_NOTES.md:"
            Get-Content $notesFile | Where-Object { $_ -match 'kWh|consumo|fatura|R\$' }
        }
    }
    Write-Host ""
    Write-Info "Para atualizar dados: navegar https://www.enel.com.br/pt/private-area.html"
    Write-Info "e anotar valores em: $notesFile"
    Write-Warn "GUARDRAIL: ao navegar, apenas ler -- nunca submeter formularios de servico!"
} else {
    Write-Warn "ENEL_ACCOUNT_NOTES.md nao encontrado: $notesFile"
    Write-Info "Crie o arquivo apos coletar dados manualmente no portal."
}
