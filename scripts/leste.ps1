#Requires -Version 5.1
<#
.SYNOPSIS
    Leste Telecom -- coleta READ-ONLY de plano de internet e faturas.
.DESCRIPTION
    Modos: status | browser | save
    Dados: docs/private/homelab/LESTE_TELECOM_NOTES.md
.NOTES
    GUARDRAIL: Apenas leitura. Nao alterar planos ou configuracoes.
    Portal: confirmar URL com o operador (leste.com.br, lestetelecom.com.br, ou outro)
    Numero de contrato / CPF para login a confirmar.
#>
param(
    [ValidateSet("status","browser","save")]
    [string]$Mode = "status"
)
$repoRoot  = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$notesFile = Join-Path $repoRoot "docs\private\homelab\LESTE_TELECOM_NOTES.md"
function Write-Header($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok($m)     { Write-Host "  OK  $m" -ForegroundColor Green }
function Write-Info($m)   { Write-Host "  ... $m" -ForegroundColor Gray }
function Write-Guard($m)  { Write-Host " SAFE $m" -ForegroundColor Magenta }
Write-Guard "MODO READ-ONLY -- Apenas leitura de dados"
switch ($Mode) {
    "status" {
        Write-Header "Leste Telecom -- Status"
        if (Test-Path $notesFile) { Get-Content $notesFile }
        else {
            Write-Info "Sem dados ainda."
            Write-Info "Confirme a URL do portal Leste Telecom e seu login."
            Write-Info "Use -Mode browser para instrucoes."
        }
    }
    "browser" {
        Write-Header "Leste Telecom -- Instrucoes de Coleta"
        Write-Info "PENDENTE: confirmar URL do portal com o operador"
        Write-Info "URLs possiveis a testar:"
        Write-Info "  - https://www.lestetelecom.com.br/cliente"
        Write-Info "  - https://cliente.lestetelecom.com.br"
        Write-Info "  - https://leste.com.br/minha-conta"
        Write-Info ""
        Write-Info "Dados a coletar mensalmente:"
        Write-Info "  - Plano contratado (velocidade Mbps, valor R$)"
        Write-Info "  - Fatura do mes"
        Write-Info "  - Vencimento"
        Write-Info "  - Numero do contrato"
        Write-Info "  - Status de debito automatico"
        Write-Info "  - IP fixo? (relevante para homelab)"
        Write-Info ""
        Write-Info "Quando autenticado, use session-collect para capturar."
        Write-Info "Salvar em: $notesFile"
    }
    "save" {
        Write-Info "Edite diretamente: $notesFile"
    }
}
