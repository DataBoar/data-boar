<#
.SYNOPSIS
    Exporta os docs ATS/SLI do talent pool hub em multiplos formatos.

.DESCRIPTION
    Le todos os .md em docs/private/commercial/ats_sli_hub/
    e gera saidas em:
      - exports/md/    (copia .md -- preserva para o agente)
      - exports/txt/   (texto puro -- sem markdown, para colar/enviar)
      - exports/docx/  (Word -- via pandoc)
      - exports/pdf/   (PDF  -- via pandoc + pdflatex ou wkhtmltopdf)

.PARAMETER Hub
    Caminho para a pasta hub. Default: docs/private/commercial/ats_sli_hub

.PARAMETER Format
    Um ou mais formatos: md, txt, docx, pdf, all. Default: all

.EXAMPLE
    .\scripts\ats-hub-export.ps1
    .\scripts\ats-hub-export.ps1 -Format txt,docx
    .\scripts\ats-hub-export.ps1 -Format pdf
#>
param(
    [string]$Hub = "docs\private\commercial\ats_sli_hub",
    [string[]]$Format = @("all")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
$hubPath  = Join-Path $repoRoot $Hub
$exports  = Join-Path $hubPath "exports"

if (-not (Test-Path $hubPath)) {
    Write-Error "Hub nao encontrado: $hubPath"
    exit 1
}

$doAll  = $Format -contains "all"
$doMd   = $doAll -or ($Format -contains "md")
$doTxt  = $doAll -or ($Format -contains "txt")
$doDocx = $doAll -or ($Format -contains "docx")
$doPdf  = $doAll -or ($Format -contains "pdf")

# Verificar pandoc
$pandocPath = (Get-Command pandoc -ErrorAction SilentlyContinue)?.Source
if (-not $pandocPath) {
    $pandocCandidates = @(
        "$env:LOCALAPPDATA\Pandoc\pandoc.exe",
        "C:\Program Files\Pandoc\pandoc.exe",
        # winget install path (detectado 2026-04-03)
        (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\JohnMacFarlane.Pandoc*" -Recurse -Filter "pandoc.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName)
    ) | Where-Object { $_ -and (Test-Path $_) }
    $pandocPath = $pandocCandidates | Select-Object -First 1
}

if (-not $pandocPath -and ($doDocx -or $doPdf)) {
    Write-Warning "pandoc nao encontrado no PATH. DOCX e PDF usarao fallback Python ou serao pulados."
    Write-Warning "  Instalar: winget install JohnMacFarlane.Pandoc"
}

# Arquivos MD do hub (excluir README e subpastas)
$mdFiles = Get-ChildItem $hubPath -Filter "*.md" -File |
           Where-Object { $_.Name -ne "README.md" }

Write-Host "=== ATS Hub Export ===" -ForegroundColor Cyan
Write-Host "Hub:    $hubPath"
Write-Host "Docs:   $($mdFiles.Count) arquivos prioritarios"
Write-Host "Saida:  $exports"
Write-Host ""

# Funcao: converter markdown para texto puro
function Convert-MdToTxt {
    param([string]$mdContent)
    $txt = $mdContent

    # Remover blocos de codigo
    $txt = $txt -replace '```[a-z]*\r?\n', '' -replace '```', ''

    # Converter headers -> texto em maiusculas com sublinhado
    $txt = $txt -replace '(?m)^#{4,}\s+(.+)$', '  $1'
    $txt = $txt -replace '(?m)^###\s+(.+)$', '--- $1 ---'
    $txt = $txt -replace '(?m)^##\s+(.+)$', '=== $1 ==='
    $txt = [regex]::Replace($txt, '(?m)^#\s+(.+)$', {
        param($m)
        $line = '=' * 40
        "$line`n$($m.Groups[1].Value)`n$line"
    })

    # Bold/italic
    $txt = $txt -replace '\*\*(.+?)\*\*', '$1'
    $txt = $txt -replace '\*(.+?)\*', '$1'
    $txt = $txt -replace '__(.+?)__', '$1'
    $txt = $txt -replace '_(.+?)_', '$1'

    # Links: [texto](url) -> texto (url)
    $txt = $txt -replace '\[([^\]]+)\]\(([^)]+)\)', '$1 ($2)'

    # Inline code
    $txt = $txt -replace '`([^`]+)`', '$1'

    # Blockquotes
    $txt = $txt -replace '(?m)^>\s*', '  | '

    # Tabelas MD -> texto alinhado (simplificado: remover pipes)
    $txt = $txt -replace '(?m)^\|[-: |]+\|$', ''   # remover linha de separacao
    $txt = $txt -replace '(?m)^\|', '' -replace '\|$', '' -replace '\|', '  |  '

    # Checkboxes
    $txt = $txt -replace '\[ \]', '[ ]'
    $txt = $txt -replace '\[x\]', '[x]'

    # Separadores
    $txt = $txt -replace '(?m)^---+$', ('-' * 60)

    # Limpar linhas em branco excessivas (max 2 seguidas)
    $txt = $txt -replace '(\r?\n){3,}', "`n`n"

    return $txt.Trim()
}

foreach ($file in $mdFiles) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    Write-Host ">> $($file.Name)" -ForegroundColor Yellow
    $mdContent = Get-Content $file.FullName -Raw -Encoding UTF8

    # --- MD copy ---
    if ($doMd) {
        $dest = Join-Path $exports "md\$($file.Name)"
        Copy-Item $file.FullName $dest -Force
        Write-Host "   MD   -> $dest"
    }

    # --- TXT ---
    if ($doTxt) {
        $txtContent = Convert-MdToTxt $mdContent
        $dest = Join-Path $exports "txt\$stem.txt"
        Set-Content $dest $txtContent -Encoding UTF8
        Write-Host "   TXT  -> $dest"
    }

    # --- DOCX via pandoc ---
    if ($doDocx) {
        $dest = Join-Path $exports "docx\$stem.docx"
        if ($pandocPath) {
            & $pandocPath $file.FullName `
                --from markdown `
                --to docx `
                --output $dest `
                --standalone `
                2>&1 | Out-Null
            Write-Host "   DOCX -> $dest"
        } else {
            Write-Warning "   DOCX pulado (pandoc nao encontrado)"
        }
    }

    # --- PDF via pandoc ---
    if ($doPdf) {
        $dest = Join-Path $exports "pdf\$stem.pdf"
        if ($pandocPath) {
            # Tenta com pdflatex; fallback para wkhtmltopdf se falhar
            $result = & $pandocPath $file.FullName `
                --from markdown `
                --to pdf `
                --output $dest `
                --pdf-engine=weasyprint `
                --standalone `
                2>&1
            if ($LASTEXITCODE -ne 0) {
                # Fallback: HTML intermediario e print via Edge se disponivel
                $htmlDest = Join-Path $exports "pdf\$stem.html"
                & $pandocPath $file.FullName `
                    --from markdown `
                    --to html5 `
                    --output $htmlDest `
                    --standalone `
                    --metadata title="$stem" `
                    2>&1 | Out-Null
                Write-Warning "   PDF  -> falhou engine pdf; HTML salvo em $htmlDest"
                Write-Warning "          Abra o HTML no navegador e imprima como PDF (Ctrl+P -> Salvar como PDF)"
            } else {
                Write-Host "   PDF  -> $dest"
            }
        } else {
            Write-Warning "   PDF pulado (pandoc nao encontrado)"
        }
    }
    Write-Host ""
}

Write-Host "=== Concluido ===" -ForegroundColor Green
Write-Host "Pasta de saida: $exports"
Write-Host ""
Write-Host "Proximos passos:"
Write-Host "  - DOCX: enviar para os destinatarios acordados (fora do repo)"
Write-Host "  - PDF:  se gerado por HTML, abrir no Edge/Chrome -> Ctrl+P -> Salvar como PDF"
Write-Host "  - TXT:  colar em e-mail, WhatsApp, Notion, etc."

