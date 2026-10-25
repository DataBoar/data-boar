<#
.SYNOPSIS
  Espelha exports planos do ATS hub (docx, md, pdf, txt, html) para pastas por candidato.

.DESCRIPTION
  Le em docs/private/commercial/ats_sli_hub/exports/{docx,md,pdf,txt} e
  docs/private/commercial/ats_sli_hub/exports/pdf/*.html
  e copia para exports/by_candidate/<slug>/{docx|md|pdf|txt|html}/.

  Slug = parte entre ATS_SLI_RECOMMENDATIONS_ e _2026_v2 no nome do arquivo,
  em minusculas (ex.: FELIPPE_Colleague-C -> felippe_Colleague-C_2026_v2).

  Arquivos INDEX (*_INDEX.md) vao para .../<slug>/md/ junto com os demais .md do mesmo prefixo.

.PARAMETER HubExports
  Pasta exports do hub. Default: docs/private/commercial/ats_sli_hub/exports

.EXAMPLE
  pwsh -NoProfile -File .\scripts\ats-hub-mirror-by-candidate.ps1
#>
param(
    [string]$HubExports = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $HubExports) {
    $HubExports = Join-Path $repoRoot "docs\private\commercial\ats_sli_hub\exports"
}

if (-not (Test-Path $HubExports)) {
    Write-Error "Pasta nao encontrada: $HubExports"
    exit 1
}

$byCandidate = Join-Path $HubExports "by_candidate"
New-Item -ItemType Directory -Path $byCandidate -Force | Out-Null

function Get-SlugFromName {
    param([string]$Name)
    # ATS_SLI_RECOMMENDATIONS_FELIPPE_Colleague-C_2026_v2.en.docx -> felippe_Colleague-C_2026_v2
    # ATS_SLI_RECOMMENDATIONS_FELIPPE_Colleague-C_2026_v2_INDEX.md -> felippe_Colleague-C_2026_v2
    if ($Name -match '^ATS_SLI_RECOMMENDATIONS_(.+)_2026_v2_INDEX\.md$') {
        return ($Matches[1].ToLowerInvariant() + "_2026_v2")
    }
    if ($Name -match '^ATS_SLI_RECOMMENDATIONS_(.+)_2026_v2') {
        return ($Matches[1].ToLowerInvariant() + "_2026_v2")
    }
    return $null
}

function Get-Subdir {
    param([string]$FileName)
    $ext = [System.IO.Path]::GetExtension($FileName).ToLowerInvariant()
    switch ($ext) {
        ".docx" { return "docx" }
        ".md"   { return "md" }
        ".pdf"  { return "pdf" }
        ".html" { return "html" }
        ".txt"  { return "txt" }
        default { return "other" }
    }
}

$count = 0
Get-ChildItem $HubExports -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch '\\by_candidate\\' -and
        ($_.Name -like "ATS_SLI_RECOMMENDATIONS_*")
    } |
    ForEach-Object {
        $slug = Get-SlugFromName $_.Name
        if (-not $slug) { return }
        $sub = Get-Subdir $_.Name
        $destDir = Join-Path $byCandidate $slug $sub
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        $dest = Join-Path $destDir $_.Name
        Copy-Item $_.FullName $dest -Force
        $count++
    }

Write-Host "=== ATS hub: espelho by_candidate ===" -ForegroundColor Cyan
Write-Host "Origem: $HubExports"
Write-Host "Destino base: $byCandidate"
Write-Host "Arquivos copiados: $count"
Write-Host "Concluido." -ForegroundColor Green
