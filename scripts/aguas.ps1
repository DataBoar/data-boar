#Requires -Version 5.1
<#
.SYNOPSIS
    Aguas de Niteroi -- coleta READ-ONLY de consumo e faturas.
.DESCRIPTION
    Modos:
    - status  (default): exibe dados do arquivo local
    - browser : instrucoes para coleta manual via browser warm
    - save    : salva snapshot de dados informados manualmente
.NOTES
    Portal: https://agenciavirtual.grupoaguasdobrasil.com.br/
    CPF/login: ver docs/private/homelab/AGUAS_NITEROI_NOTES.md (nunca hardcoded aqui)
    Sessao: docs/private/homelab/.env.aguas.session
    Dados: docs/private/homelab/AGUAS_NITEROI_NOTES.md
#>
param(
    [ValidateSet("status","browser","save")]
    [string]$Mode = "status",
    [string]$Month = "",  # yyyy-MM para registrar consumo especifico
    [int]$ConsumoM3 = 0,
    [decimal]$ValorRS = 0
)
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$notesFile = Join-Path $repoRoot "docs\private\homelab\AGUAS_NITEROI_NOTES.md"
function Write-Header($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok($m)     { Write-Host "  OK  $m" -ForegroundColor Green }
function Write-Info($m)   { Write-Host "  ... $m" -ForegroundColor Gray }
function Write-Guard($m)  { Write-Host " SAFE $m" -ForegroundColor Magenta }
Write-Guard "MODO READ-ONLY -- Apenas leitura de dados"
switch ($Mode) {
    "status" {
        Write-Header "Aguas de Niteroi -- Status"
        if (Test-Path $notesFile) {
            Get-Content $notesFile | Select-Object -First 40
            Write-Info "Arquivo completo: $notesFile"
        } else {
            Write-Info "Sem dados locais ainda. Use -Mode browser para coletar."
        }
    }
    "browser" {
        Write-Header "Aguas de Niteroi -- Instrucoes de Coleta"
        Write-Info "Portal: https://agenciavirtual.grupoaguasdobrasil.com.br/"
        Write-Info "Login: CPF/e-mail em docs/private/homelab/AGUAS_NITEROI_NOTES.md"
        Write-Info ""
        Write-Info "Dados a coletar mensalmente:"
        Write-Info "  - Consumo em m3 do mes"
        Write-Info "  - Valor da fatura (R$)"
        Write-Info "  - Data de vencimento"
        Write-Info "  - Numero da matricula/RGI"
        Write-Info "  - Status de debito automatico"
        Write-Info ""
        Write-Info "Apos coletar, registrar com:"
        Write-Info "  .\scripts\aguas.ps1 -Mode save -Month yyyy-MM -ConsumoM3 X -ValorRS Y"
    }
    "save" {
        Write-Header "Aguas de Niteroi -- Salvar Dados"
        if ($ConsumoM3 -le 0 -and $ValorRS -le 0) {
            Write-Host "Informe pelo menos -ConsumoM3 ou -ValorRS" -ForegroundColor Yellow
            exit 1
        }
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
        $monthLabel = if ($Month) { $Month } else { Get-Date -Format "yyyy-MM" }
        $entry = @"

## $monthLabel (registrado em $timestamp)
- Consumo: ${ConsumoM3} m3
- Valor: R$ ${ValorRS}
- Fonte: coleta manual via portal Agencias Virtuais
"@
        if (-not (Test-Path $notesFile)) {
            Set-Content $notesFile "# Aguas de Niteroi -- Historico de Consumo`n" -Encoding UTF8
        }
        Add-Content $notesFile $entry -Encoding UTF8
        Write-Ok "Dados de $monthLabel salvos em $notesFile"
    }
}
