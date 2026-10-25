#Requires -Version 5.1
<#
.SYNOPSIS
    Enel RJ -- status READ-ONLY (sem browser, sem risco de protocolos acidentais).

.DESCRIPTION
    Le ENEL_ACCOUNT_NOTES.md e exibe status atual.
    NAO acessa o portal Enel via browser -- isso gerou protocolos de "Falta de Luz"
    acidentalmente (PROTO-REDACTED, PROTO-REDACTED, PROTO-REDACTED) em sessao anterior.

    Para novos dados:
    - Pedir ao operador para navegar manualmente: https://www.enel.com.br/pt/private-area.html
    - Baixar faturas como PDF e anotar kWh mensais para correlacao solar

.PARAMETER Show
    all (default) | invoices | alerts | summary

.EXAMPLE
    .\scripts\enel.ps1
    .\scripts\enel.ps1 -Show invoices
    .\scripts\enel.ps1 -Show summary

.NOTES
    Contato Enel: ENEL-PHONE-REDACTED (para cancelar protocolos acidentais ou verificar status)
    App Enel: iOS/Android -- login com Google (mesmo login do portal web)
    Portal: https://www.enel.com.br/pt/private-area.html
#>
param(
    [ValidateSet("all","invoices","alerts","summary")]
    [string]$Show = "all"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$notesFile = Join-Path $repoRoot "docs\private\homelab\ENEL_ACCOUNT_NOTES.md"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }
function Write-Alert($msg)  { Write-Host " ALRT $msg" -ForegroundColor Red }

if (-not (Test-Path $notesFile)) {
    Write-Warn "Arquivo nao encontrado: $notesFile"
    Write-Warn "Este arquivo e criado apos a primeira sessao de coleta com o browser Enel."
    exit 1
}

$content = Get-Content $notesFile -Raw
$fi = Get-Item $notesFile

Write-Header "Enel RJ -- Status (READ-ONLY)"
Write-Info "Fonte: $notesFile"
Write-Info "Ultima atualizacao: $($fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))"

# UC e debitos
if ($content -match 'UC N[:\s\*]+(\d+)') { Write-Ok "UC: $($Matches[1])" }
if ($content -match 'Total de Debitos[:\s\*]+(R\$[\s\d,\.]+)') { Write-Ok "Debitos: $($Matches[1].Trim())" }

if ($Show -in @("all","alerts")) {
    Write-Header "Alertas"
    if ($content -match 'FALTA DE LUZ') {
        Write-Alert "FALTA DE LUZ NA REGIAO ativa"
        # Extrair protocolos
        $protoMatches = [regex]::Matches($content, '(96\d{7}|7941\d+)')
        if ($protoMatches.Count -gt 0) {
            $protoMatches | ForEach-Object { Write-Alert "  Protocolo: $($_.Value)" }
        }
        Write-Warn "Verificar: ENEL-PHONE-REDACTED ou App Enel"
    } else {
        Write-Ok "Nenhum alerta ativo encontrado no arquivo"
    }
}

if ($Show -in @("all","invoices")) {
    Write-Header "Faturas (ultimo snapshot)"
    # Tentar extrair linhas de tabela com referencias
    $tableLines = $content -split "`n" | Where-Object { $_ -match '020\d{15,}' }
    if ($tableLines.Count -gt 0) {
        $tableLines | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Info "Nenhuma fatura encontrada no formato esperado"
    }
    if ($content -match '(\d+) paginas de historico') {
        Write-Info "Historico disponivel: ~$($Matches[1]) paginas (~$([int]$Matches[1] * 10) meses)"
    }
}

if ($Show -in @("all","summary")) {
    Write-Header "Instrucoes para novos dados"
    Write-Host ""
    Write-Host "  O browser-assistant NAO acessa o portal Enel diretamente." -ForegroundColor Yellow
    Write-Host "  O overlay do site gera protocolos de 'Falta de Luz' acidentalmente." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Para atualizar dados:" -ForegroundColor Cyan
    Write-Host "    1. Abrir: https://www.enel.com.br/pt/private-area.html" -ForegroundColor White
    Write-Host "    2. Login via Google" -ForegroundColor White
    Write-Host "    3. Clicar 'Grafico de Consumo' -> digitar 5 primeiros digitos do CPF" -ForegroundColor White
    Write-Host "    4. Screenshot ou CSV dos kWh mensais" -ForegroundColor White
    Write-Host "    5. Passar os dados aqui para ingesta e correlacao solar" -ForegroundColor White
    Write-Host ""
    Write-Host "  Para faturas PDF:" -ForegroundColor Cyan
    Write-Host "    1. 'Segunda Via de Conta e Historico' -> selecionar referencia -> Salvar PDF" -ForegroundColor White
    Write-Host ""
    Write-Host "  Para cancelar protocolo acidental:" -ForegroundColor Cyan
    Write-Host "    Ligar ENEL-PHONE-REDACTED com o numero do protocolo" -ForegroundColor White
}
