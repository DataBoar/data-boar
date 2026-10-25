#Requires -Version 5.1
<#
.SYNOPSIS
    Claro Celular -- coleta READ-ONLY de plano, consumo e faturas.
.DESCRIPTION
    Modos: status | browser | save | plan
    Portal: https://minhaconta.claro.com.br/ (ou app Minha Claro)
    Conta: login com Google/email associado ao numero Claro
    Dados: docs/private/homelab/CLARO_ACCOUNT_NOTES.md
.NOTES
    GUARDRAIL: Nao contratar servicos, nao mudar plano -- apenas leitura.
#>
param(
    [ValidateSet("status","browser","save","plan")]
    [string]$Mode = "status"
)
$repoRoot  = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$notesFile = Join-Path $repoRoot "docs\private\homelab\CLARO_ACCOUNT_NOTES.md"
function Write-Header($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok($m)     { Write-Host "  OK  $m" -ForegroundColor Green }
function Write-Info($m)   { Write-Host "  ... $m" -ForegroundColor Gray }
function Write-Guard($m)  { Write-Host " SAFE $m" -ForegroundColor Magenta }
Write-Guard "MODO READ-ONLY -- Apenas leitura de dados"
switch ($Mode) {
    "status" {
        Write-Header "Claro Celular -- Status"
        if (Test-Path $notesFile) { Get-Content $notesFile }
        else { Write-Info "Sem dados. Use -Mode browser para coletar via app/portal." }
    }
    "plan" {
        Write-Header "Claro -- Plano Atual (dados locais)"
        if (Test-Path $notesFile) {
            Get-Content $notesFile | Where-Object { $_ -match 'plano|GB|R\$|franquia|validade' }
        } else { Write-Info "Sem dados de plano. Use -Mode browser." }
    }
    "browser" {
        Write-Header "Claro -- Instrucoes de Coleta"
        Write-Info "Opcoes de acesso:"
        Write-Info "  1. App Minha Claro (iOS/Android) -- mais confiavel"
        Write-Info "  2. Portal web: https://minhaconta.claro.com.br/"
        Write-Info "  3. Portal alternativo: https://www.claro.com.br/minha-claro"
        Write-Info "  4. WhatsApp Claro: 1052 (autoatendimento)"
        Write-Info ""
        Write-Info "Dados a coletar mensalmente:"
        Write-Info "  - Plano atual (nome, GB de dados, valor R$)"
        Write-Info "  - Consumo de dados do mes (GB usados vs franquia)"
        Write-Info "  - Valor da fatura do mes"
        Write-Info "  - Vencimento"
        Write-Info "  - Numero da linha"
        Write-Info "  - Status de debito automatico"
        Write-Info ""
        Write-Info "Salvar em: $notesFile"
    }
    "save" {
        Write-Info "Edite diretamente o arquivo: $notesFile"
        Write-Info "Formato sugerido: ver AGUAS_NITEROI_NOTES.md como modelo"
    }
}
