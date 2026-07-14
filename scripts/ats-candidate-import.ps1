<#
.SYNOPSIS
    Pipeline ATS automatizado: extrai dados de PDFs LinkedIn/CV e gera arquivos ATS individuais.

.DESCRIPTION
    1. Escaneia docs/private/team_info/ por PDFs (ou um especifico com -PdfPath)
    2. Extrai dados estruturados via scripts/extract_cv_pdf.py
    3. Gera arquivo ATS individual skeleton se nao existir (ou -Force para sobrescrever)
    4. Imprime resumo de acoes

.PARAMETER PdfPath
    Caminho para um PDF especifico. Se omitido, escaneia toda a pasta team_info.
.PARAMETER OutDir
    Pasta para arquivos ATS individuais.
    Padrao: docs\private\commercial\candidates\linkedin_peer_review\individual
.PARAMETER Force
    Re-processa todos os PDFs, mesmo que arquivos ATS ja existam.
.PARAMETER JsonOnly
    Apenas extrai JSON de cada PDF e imprime na tela (sem escrever arquivos ATS).

.EXAMPLE
    # Processar um PDF novo:
    .\scripts\ats-candidate-import.ps1 -PdfPath "docs\private\team_info\Sample_Candidate_2026.pdf"

    # Escanear todos e gerar skeletons faltantes:
    .\scripts\ats-candidate-import.ps1

    # Forcionar reprocessamento:
    .\scripts\ats-candidate-import.ps1 -Force

    # Ver dados extraidos sem escrever:
    .\scripts\ats-candidate-import.ps1 -JsonOnly
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$PdfPath = "",
    [string]$OutDir = "docs\private\commercial\candidates\linkedin_peer_review\individual",
    [switch]$Force,
    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $RepoRoot

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK   $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "  WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ...  $msg" -ForegroundColor Gray }

# --- Verificar dependencias ---
Write-Header "Verificando dependencias"
$pythonVer = uv run python --version 2>&1
if ($LASTEXITCODE -ne 0) { Write-Error "uv/python nao encontrado."; exit 1 }
Write-Ok $pythonVer

# --- Determinar lista de PDFs ---
Write-Header "Localizando PDFs"
if ($PdfPath) {
    $pdfs = @(Get-Item $PdfPath)
} else {
    $teamInfoDir = Join-Path $RepoRoot "docs\private\team_info"
    if (-not (Test-Path $teamInfoDir)) { Write-Error "Pasta nao encontrada: $teamInfoDir"; exit 1 }
    $pdfs = @(Get-ChildItem $teamInfoDir -Filter "*.pdf" | Sort-Object LastWriteTime -Descending)
}
Write-Info "Total de PDFs: $($pdfs.Count)"

# --- Criar OutDir se necessario ---
$outDirFull = Join-Path $RepoRoot $OutDir
if (-not (Test-Path $outDirFull)) {
    New-Item -ItemType Directory -Path $outDirFull -Force | Out-Null
    Write-Ok "Criado: $outDirFull"
}

# --- Processar PDFs ---
$results = [System.Collections.Generic.List[PSObject]]::new()

foreach ($pdf in $pdfs) {
    Write-Header "Processando: $($pdf.Name)"

    $jsonRaw = uv run --with pypdf python scripts/extract_cv_pdf.py "$($pdf.FullName)" --json 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Falha ao extrair: $($pdf.Name)"
        $results.Add([PSCustomObject]@{ PDF = $pdf.Name; Status = "ERRO"; LinkedIn = ""; Arquivo = "" })
        continue
    }

    $data = $jsonRaw | ConvertFrom-Json
    Write-Info "Email   : $($data.email)"
    Write-Info "LinkedIn: $($data.linkedin_url)"
    Write-Info "Certs   : $($data.certifications_detected -join ", ")"
    Write-Info "Idiomas : $($data.languages_detected -join ", ")"
    Write-Info "Headline: $($data.headline)"

    if ($JsonOnly) {
        $results.Add([PSCustomObject]@{ PDF = $pdf.Name; Status = "JSON-ONLY"; LinkedIn = $data.linkedin_url; Arquivo = "" })
        continue
    }

    # Nome do arquivo ATS derivado do PDF
    $baseName = $pdf.BaseName
    $baseName = $baseName -replace "Linked in Profile - ", ""
    $baseName = $baseName -replace "Head de TI_", ""
    $baseName = $baseName -replace "\s+", "_"
    $baseName = $baseName -replace "[^a-zA-Z0-9_]", ""
    $atsFileName = "$($baseName.ToUpper())_ATS.pt_BR.md"
    $atsFile = Join-Path $outDirFull $atsFileName

    if ((Test-Path $atsFile) -and -not $Force) {
        Write-Warn "Ja existe (use -Force para sobrescrever): $atsFileName"
        $results.Add([PSCustomObject]@{ PDF = $pdf.Name; Status = "JA_EXISTE"; LinkedIn = $data.linkedin_url; Arquivo = $atsFileName })
        continue
    }

    $atsDate = Get-Date -Format "yyyy-MM-dd"
    $certs       = if ($data.certifications_detected.Count -gt 0) { $data.certifications_detected -join ", " } else { "(nao detectado)" }
    $langs       = if ($data.languages_detected.Count -gt 0) { $data.languages_detected -join ", " } else { "(nao detectado)" }
    $headline    = if ($data.headline) { $data.headline } else { "(verificar no perfil)" }
    $linkedinUrl = if ($data.linkedin_url) { $data.linkedin_url } else { "(nao encontrado no PDF)" }
    $emailVal    = if ($data.email) { $data.email } else { "(nao encontrado)" }
    $displayName = ($baseName -replace "_", " ").Trim()

    $atsContent = @(
        "# $displayName - Avaliacao ATS/LinkedIn"
        ""
        "**PDF fonte:** ``$($pdf.Name)``"
        "**LinkedIn:** $linkedinUrl"
        "**Email:** $emailVal"
        "**Avaliado em (import automatico):** $atsDate"
        ""
        "---"
        ""
        "## 1. Headline Detectada no PDF"
        ""
        "> $headline"
        ""
        "---"
        ""
        "## 2. Dados Extraidos Automaticamente"
        ""
        "| Campo | Valor |"
        "|---|---|"
        "| LinkedIn URL | $linkedinUrl |"
        "| Email | $emailVal |"
        "| Certificacoes detectadas | $certs |"
        "| Idiomas detectados | $langs |"
        "| Tamanho texto extraido | $($data.raw_text_length) chars |"
        ""
        "---"
        ""
        "## 3. Checklist LinkedIn ATS"
        ""
        "- [ ] **Headline**: refletir cargo + 2-3 keywords de busca da area"
        "- [ ] **About / Resumo**: incluir keywords para recrutadores"
        "- [ ] **Skills**: adicionar/confirmar skills principais"
        "- [ ] **Certificacoes**: listar em secao dedicada"
        "- [ ] **Open to Work**: ativar se em busca ativa"
        "- [ ] **URL customizada**: verificar se ja esta personalizada"
        ""
        "---"
        ""
        "## 4. Acoes Imediatas"
        ""
        "| Acao | Prioridade | Quem |"
        "|---|---|---|"
        "| Otimizar Headline com keywords da area | Alta | Candidato |"
        "| Confirmar/adicionar Skills principais | Alta | Candidato |"
        "| Incluir metricas nas posicoes | Media | Candidato |"
        "| Ativar Open to Work (se disponivel) | Media | Candidato |"
        ""
        "---"
        ""
        "## 5. Observacoes do Operador"
        ""
        "> **NOTA:** Gerado automaticamente por ``scripts/ats-candidate-import.ps1``."
        "> Para avaliacao detalhada, analise o PDF com o agente de IA e a skill ``.cursor/private/skills/candidate-ats-evaluation/SKILL.md``."
        ""
        "_(Campo livre para anotacoes adicionais)_"
    ) -join "`n"

    Set-Content -Encoding UTF8 $atsFile $atsContent
    Write-Ok "ATS gerado: $atsFileName"
    $results.Add([PSCustomObject]@{ PDF = $pdf.Name; Status = "GERADO"; LinkedIn = $linkedinUrl; Arquivo = $atsFileName })
}

# --- Resumo ---
Write-Header "Resumo"
$results | Format-Table -AutoSize

$gerados    = @($results | Where-Object { $_.Status -eq "GERADO" }).Count
$existentes = @($results | Where-Object { $_.Status -eq "JA_EXISTE" }).Count
$erros      = @($results | Where-Object { $_.Status -eq "ERRO" }).Count

Write-Host ""
Write-Host "Gerados: $gerados  |  Ja existiam: $existentes  |  Erros: $erros" -ForegroundColor White
Write-Host ""
Write-Host "Proximo passo: revise os arquivos em $OutDir" -ForegroundColor Yellow
        Write-Host "Para analise detalhada: use .cursor/private/skills/candidate-ats-evaluation/SKILL.md" -ForegroundColor Yellow


Pop-Location
