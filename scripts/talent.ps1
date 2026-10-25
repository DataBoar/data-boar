<#
.SYNOPSIS
    Wrapper CLI para pipeline ATS de talentos.

.DESCRIPTION
    Centraliza acoes de importacao de CVs, revisao de perfis, abertura de LinkedIn
    e exploracao de redes sociais de candidatos mapeados no pool de talentos.

.EXAMPLE
    .\scripts\talent.ps1 list
    .\scripts\talent.ps1 import "Sample_Candidate.pdf"
    .\scripts\talent.ps1 scan
    .\scripts\talent.ps1 review candidate_a
    .\scripts\talent.ps1 linkedin candidate_b
    .\scripts\talent.ps1 social candidate_c
    .\scripts\talent.ps1 extract "Sample_Candidate.pdf"
    .\scripts\talent.ps1 search "LGPD"
#>
[CmdletBinding()]
param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("import","scan","list","review","linkedin","social","extract","search","help")]
    [string]$Action,
    [Parameter(Position=1)] [string]$Arg1 = "",
    [Parameter(Position=2)] [string]$Arg2 = "",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot   = Split-Path $PSScriptRoot -Parent
$TeamInfo   = Join-Path $RepoRoot "docs\private\team_info"
$PoolDir    = Join-Path $RepoRoot "docs\private\commercial\candidates\linkedin_peer_review"
$IndividDir = Join-Path $PoolDir "individual"
$ExtractPy  = Join-Path $RepoRoot "scripts\extract_cv_pdf.py"
$ImportPs1  = Join-Path $RepoRoot "scripts\ats-candidate-import.ps1"
$TalentPoolPath = Join-Path $RepoRoot "docs\private\commercial\talent_pool.json"

$Candidates = @{
    "example" = @{ Name="Example Person"; LinkedIn="https://www.example.com/profile/example"; File="EXAMPLE_ATS.pt_BR.md" }
}

function Write-Ok   { param([string]$M) Write-Host "[OK]  $M" -ForegroundColor Green  }
function Write-Info { param([string]$M) Write-Host "[>>]  $M" -ForegroundColor Cyan   }
function Write-Warn { param([string]$M) Write-Host "[!!]  $M" -ForegroundColor Yellow }
function Write-Err  { param([string]$M) Write-Host "[ERR] $M" -ForegroundColor Red    }

if (Test-Path -LiteralPath $TalentPoolPath) {
    try {
        $privateCandidates = Get-Content -Raw -LiteralPath $TalentPoolPath | ConvertFrom-Json -AsHashtable
        foreach ($key in $privateCandidates.Keys) {
            $Candidates[$key] = $privateCandidates[$key]
        }
    } catch {
        Write-Warn "Falha ao carregar pool privado em '$TalentPoolPath': $($_.Exception.Message)"
    }
}

function Resolve-Candidate {
    param([string]$Input)
    $key = $Input.ToLower() -replace "[aaaaae]","a" -replace "[eeee]","e" -replace "[iiii]","i" `
        -replace "[oooooe]","o" -replace "[uuuu]","u" -replace "[c]","c" -replace "\s+","_"
    if ($Candidates.ContainsKey($key)) { return $key }
    $ms = $Candidates.Keys | Where-Object { $_ -like "*$key*" }
    if ($ms.Count -eq 1) { return $ms[0] }
    if ($ms.Count -gt 1) { Write-Warn "Ambiguo: $($ms -join ', ')"; return $null }
    Write-Err "Candidato nao encontrado: '$Input'. Use: talent list"
    return $null
}

function Open-Url { param([string]$Url) Start-Process $Url }

switch ($Action) {

    "help" {
        Write-Host ""
        Write-Host "  talent list                  Listar todos os candidatos do pool" -ForegroundColor White
        Write-Host "  talent scan                  Detectar PDFs novos em docs/private/team_info/" -ForegroundColor White
        Write-Host "  talent import <pdf>          Importar PDF (nome ou caminho)" -ForegroundColor White
        Write-Host "  talent extract <pdf>         Extrair JSON de um PDF" -ForegroundColor White
        Write-Host "  talent review <apelido>      Abrir arquivo ATS no editor" -ForegroundColor White
        Write-Host "  talent linkedin <apelido>    Abrir LinkedIn no browser" -ForegroundColor White
        Write-Host "  talent social <apelido>      Abrir todas as redes sociais conhecidas" -ForegroundColor White
        Write-Host "  talent search <keyword>      Buscar keyword nos arquivos ATS" -ForegroundColor White
        Write-Host ""
        Write-Host "  Apelidos disponiveis:" -ForegroundColor DarkGray
        $Candidates.Keys | Sort-Object | ForEach-Object {
            Write-Host "    $_  ($($Candidates[$_].Name))" -ForegroundColor DarkGray
        }
        Write-Host ""
    }

    "list" {
        Write-Host ""
        Write-Host ("  {0,-20} {1,-35} {2}" -f "APELIDO", "NOME", "STATUS") -ForegroundColor Cyan
        Write-Host ("  " + ("-" * 65)) -ForegroundColor DarkGray
        foreach ($key in ($Candidates.Keys | Sort-Object)) {
            $c = $Candidates[$key]
            $atsPath = Join-Path $IndividDir $c.File
            $status = if (Test-Path $atsPath) { "OK" } else { "FALTANDO" }
            $color  = if ($status -eq "OK") { "White" } else { "Red" }
            Write-Host ("  {0,-20} {1,-35} {2}" -f $key, $c.Name, $status) -ForegroundColor $color
        }
        Write-Host ""
    }

    "scan" {
        Write-Host ""
        Write-Info "Escaneando $TeamInfo para PDFs..."
        $pdfs = Get-ChildItem $TeamInfo -Filter "*.pdf" | Sort-Object LastWriteTime -Descending
        Write-Host ("  {0,-48} {1,-22} {2}" -f "ARQUIVO", "MODIFICADO", "STATUS") -ForegroundColor Cyan
        Write-Host ("  " + ("-" * 80)) -ForegroundColor DarkGray
        foreach ($pdf in $pdfs) {
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($pdf.Name)
            $hasAts = Get-ChildItem $IndividDir -Filter "*.md" -ErrorAction SilentlyContinue |
                      Where-Object { $_.Name -match ($baseName -replace "[^a-zA-Z0-9]",".") }
            $status = if ($hasAts) { "IMPORTADO" } else { "NOVO" }
            $color  = if ($status -eq "IMPORTADO") { "DarkGray" } else { "Yellow" }
            $ts     = $pdf.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
            Write-Host ("  {0,-48} {1,-22} {2}" -f $pdf.Name, $ts, $status) -ForegroundColor $color
        }
        Write-Host ""
        Write-Info "Para importar: .\scripts\talent.ps1 import `"<nome.pdf>`""
        Write-Host ""
    }

    "import" {
        if ([string]::IsNullOrWhiteSpace($Arg1)) {
            Write-Err "Informe o PDF. Ex: talent import `"Sample_Candidate.pdf`""
            exit 1
        }
        $pdfPath = $Arg1
        if (-not [System.IO.Path]::IsPathRooted($pdfPath)) {
            $c1 = Join-Path (Get-Location) $pdfPath
            $c2 = Join-Path $TeamInfo $pdfPath
            if     (Test-Path $c1) { $pdfPath = $c1 }
            elseif (Test-Path $c2) { $pdfPath = $c2 }
            else {
                $found = Get-ChildItem $TeamInfo -Filter "*.pdf" |
                         Where-Object { $_.Name -like "*$Arg1*" } | Select-Object -First 1
                if ($found) { $pdfPath = $found.FullName }
                else { Write-Err "PDF nao encontrado: '$Arg1'"; exit 1 }
            }
        }
        Write-Info "Importando: $pdfPath"
        $forceFlag = if ($Force) { @("-Force") } else { @() }
        & powershell -ExecutionPolicy Bypass -File $ImportPs1 -PdfPath $pdfPath @forceFlag
    }

    "extract" {
        if ([string]::IsNullOrWhiteSpace($Arg1)) { Write-Err "Informe o PDF."; exit 1 }
        $pdfPath = $Arg1
        if (-not [System.IO.Path]::IsPathRooted($pdfPath)) {
            $c2 = Join-Path $TeamInfo $pdfPath
            if (Test-Path $c2) { $pdfPath = $c2 }
            else {
                $found = Get-ChildItem $TeamInfo -Filter "*.pdf" |
                         Where-Object { $_.Name -like "*$Arg1*" } | Select-Object -First 1
                if ($found) { $pdfPath = $found.FullName }
                else { Write-Err "PDF nao encontrado: '$Arg1'"; exit 1 }
            }
        }
        Write-Info "Extraindo: $(Split-Path $pdfPath -Leaf)"
        uv run --with pypdf python $ExtractPy $pdfPath --json
    }

    "review" {
        $key = Resolve-Candidate $Arg1
        if (-not $key) { exit 1 }
        $atsFile = Join-Path $IndividDir $Candidates[$key].File
        if (-not (Test-Path $atsFile)) {
            Write-Warn "Arquivo ATS nao encontrado. Execute: talent import primeiro."
        } else {
            Write-Ok "Abrindo: $($Candidates[$key].File)"
            code $atsFile
        }
    }

    "linkedin" {
        $key = Resolve-Candidate $Arg1
        if (-not $key) { exit 1 }
        $url = $Candidates[$key].LinkedIn
        Write-Ok "Abrindo LinkedIn: $url"
        Open-Url $url
    }

    "social" {
        $key = Resolve-Candidate $Arg1
        if (-not $key) { exit 1 }
        $c = $Candidates[$key]
        Write-Info "Perfis sociais de $($c.Name):"
        Write-Ok "LinkedIn: $($c.LinkedIn)"
        Open-Url $c.LinkedIn
        Write-Warn "X/Twitter, GitHub, Gravatar, YouTube: adicione campo 'Social:' no ATS para automacao completa."
    }

    "search" {
        if ([string]::IsNullOrWhiteSpace($Arg1)) { Write-Err "Informe um termo. Ex: talent search LGPD"; exit 1 }
        Write-Info "Buscando '$Arg1' nos arquivos ATS..."
        $results = Get-ChildItem $IndividDir -Filter "*.md" | ForEach-Object {
            $ms = Select-String -Path $_.FullName -Pattern $Arg1 -SimpleMatch
            if ($ms) {
                [PSCustomObject]@{
                    Arquivo     = $_.Name -replace "_ATS.pt_BR.md",""
                    Ocorrencias = $ms.Count
                    Contexto    = ($ms | Select-Object -First 2 | ForEach-Object { $_.Line.Trim() }) -join " | "
                }
            }
        }
        if ($results) {
            $results | Sort-Object Ocorrencias -Descending | Format-Table -AutoSize -Wrap
        } else {
            Write-Warn "Nenhum resultado para '$Arg1'"
        }
    }
}

