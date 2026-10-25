#Requires -Version 5.1
<#
.SYNOPSIS
    Extrai texto estruturado e JSON de um PDF de perfil LinkedIn (operador ou candidato).

.DESCRIPTION
    LinkedIn nao oferece API publica para "perfil completo em JSON" para scripts pessoais.
    O fluxo suportado neste repo e o mesmo dos candidatos: exportar PDF do perfil no site
    LinkedIn, guardar em docs/private/author_info/, depois correr este script.

    Saida padrao: docs/private/author_info/career/exports_linkedin_snapshot/

.PARAMETER PdfPath
    Caminho absoluto ou relativo ao repo para o PDF. Se omitido, usa o PDF mais recente
    em docs/private/author_info/ cujo nome sugira perfil LinkedIn (LinkedIn, Profile, linkedin).

.PARAMETER OutDir
    Pasta de saida (opcional).

.EXAMPLE
    .\scripts\operator-linkedin-profile-extract.ps1
    .\scripts\operator-linkedin-profile-extract.ps1 -PdfPath "docs\private\author_info\MeuPerfil.pdf"
#>

param(
    [string]$PdfPath = "",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot "docs\private\author_info\career\exports_linkedin_snapshot"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not $PdfPath) {
    $authorInfo = Join-Path $RepoRoot "docs\private\author_info"
    if (-not (Test-Path -LiteralPath $authorInfo)) {
        Write-Error "Pasta nao encontrada: $authorInfo"
    }
    $pdfs = @(Get-ChildItem -Path $authorInfo -Recurse -Filter "*.pdf" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '(?i)linkedin|profile' } |
        Sort-Object LastWriteTime -Descending)
    if ($pdfs.Count -eq 0) {
        Write-Error "Nenhum PDF encontrado. No LinkedIn: Ver perfil como se ve publicamente -> imprimir / guardar PDF, ou exportar PDF do perfil; coloque em docs\private\author_info\"
    }
    $PdfPath = $pdfs[0].FullName
    Write-Host "PDF selecionado (mais recente com LinkedIn/Profile no nome): $PdfPath" -ForegroundColor Cyan
} else {
    if (-not [System.IO.Path]::IsPathRooted($PdfPath)) {
        $PdfPath = Join-Path $RepoRoot $PdfPath
    }
    if (-not (Test-Path -LiteralPath $PdfPath)) {
        Write-Error "Ficheiro nao encontrado: $PdfPath"
    }
}

$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$jsonOut = Join-Path $OutDir "linkedin_extract_${stamp}.json"
$txtOut = Join-Path $OutDir "linkedin_extract_${stamp}.txt"

Push-Location $RepoRoot
try {
    & uv run python scripts/extract_cv_pdf.py $PdfPath --json --out $jsonOut
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & uv run python scripts/extract_cv_pdf.py $PdfPath --out $txtOut
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "JSON: $jsonOut" -ForegroundColor Green
Write-Host "TXT:  $txtOut" -ForegroundColor Green
Write-Host "Agente: read_file no JSON para ATS/SLI sem depender so do browser snapshot." -ForegroundColor DarkCyan
