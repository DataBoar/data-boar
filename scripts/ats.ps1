<#
.SYNOPSIS
    ATS dispatcher principal do pipeline de candidatos.
#>
param(
    [Parameter(Position=0)] [string]$Command = "help",
    [Parameter(Position=1)] [string]$Arg1 = "",
    [Parameter(Position=2)] [string]$Arg2 = "",
    [switch]$Force,
    [switch]$JsonOnly
)

$RepoRoot     = Split-Path $PSScriptRoot -Parent
$TeamInfoDir  = Join-Path $RepoRoot "docs\private\team_info"
$IndividualDir = Join-Path $RepoRoot "docs\private\commercial\candidates\linkedin_peer_review\individual"
$PoolIndex    = Join-Path $RepoRoot "docs\private\commercial\candidates\linkedin_peer_review\POOL_INDEX.pt_BR.md"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

switch ($Command.ToLower()) {

    "import" {
        if (-not $Arg1) { Write-Error "Uso: ats import [caminho-pdf]"; exit 1 }
        $pdf = if ([System.IO.Path]::IsPathRooted($Arg1)) { $Arg1 } else { Join-Path $RepoRoot $Arg1 }
        if (-not (Test-Path $pdf)) {
            $found = Get-ChildItem $TeamInfoDir -Filter "*$Arg1*" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $pdf = $found.FullName } else { Write-Error "PDF nao encontrado: $Arg1"; exit 1 }
        }
        Write-Header "Importando: $(Split-Path $pdf -Leaf)"
        $importArgs = @("-PdfPath", $pdf)
        if ($Force) { $importArgs += "-Force" }
        powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\ats-candidate-import.ps1" @importArgs
    }

    "import-all" {
        Write-Header "Importando todos os PDFs novos em team_info/"
        $importArgs = @()
        if ($Force) { $importArgs += "-Force" }
        powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\ats-candidate-import.ps1" @importArgs
    }

    "scan" {
        if (-not $Arg1) { Write-Error "Uso: ats scan [caminho-ou-nome-pdf]"; exit 1 }
        $pdf = if ([System.IO.Path]::IsPathRooted($Arg1)) { $Arg1 } else { Join-Path $RepoRoot $Arg1 }
        if (-not (Test-Path $pdf)) {
            $found = Get-ChildItem $TeamInfoDir -Filter "*$Arg1*" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $pdf = $found.FullName } else { Write-Error "PDF nao encontrado: $Arg1"; exit 1 }
        }
        Write-Header "Extraindo: $(Split-Path $pdf -Leaf)"
        uv run --with pypdf python "$PSScriptRoot\extract_cv_pdf.py" $pdf --json
    }

    "list" {
        Write-Header "Pool de Talentos"
        if (Test-Path $PoolIndex) {
            $lines2 = Get-Content $PoolIndex | Where-Object { $_ -match "^\|" -and $_ -notmatch "^(\|---|\| Apelido|\| Candidato)" }
            $lines2 | ForEach-Object { Write-Host $_ }
        }
        Write-Header "Arquivos ATS"
        $files = @(Get-ChildItem $IndividualDir -Filter "*_ATS.pt_BR.md" -ErrorAction SilentlyContinue)
        Write-Host "Total: $($files.Count) arquivos"
        $files | Select-Object @{N="Candidato";E={$_.Name -replace "_ATS\.pt_BR\.md",""}}, @{N="Modificado";E={$_.LastWriteTime.ToString("yyyy-MM-dd HH:mm")}} | Format-Table -AutoSize
    }

    "show" {
        if (-not $Arg1) { Write-Error "Uso: ats show [nome-parcial]"; exit 1 }
        $found = @(Get-ChildItem $IndividualDir -Filter "*$($Arg1.ToUpper())*_ATS.pt_BR.md" -ErrorAction SilentlyContinue)
        if (-not $found -or $found.Count -eq 0) {
            $found = @(Get-ChildItem $IndividualDir -Filter "*ATS.pt_BR.md" | Where-Object { $_.Name -imatch $Arg1 })
        }
        if ($found.Count -eq 0) { Write-Error "Nenhum ATS para: $Arg1"; exit 1 }
        Get-Content $found[0].FullName | Out-Host
    }

    "linkedin" {
        if (-not $Arg1) { Write-Error "Uso: ats linkedin [slug]"; exit 1 }
        $url = if ($Arg1 -match "^https?://") { $Arg1 } else { "https://www.example.com/profile/redacted" }
        Write-Header "Abrindo: $url"
        Start-Process $url
    }

    "LAB-ROUTER-01" {
        Write-Header "LAB-ROUTER-01 status"
        powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\LAB-ROUTER-01.ps1" status
    }

    "LAB-ROUTER-01-scan" {
        Write-Header "LAB-ROUTER-01 scan completo"
        powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\LAB-ROUTER-01.ps1" scan
    }

    "help" {
        Write-Host "ATS Pipeline -- Comandos:" -ForegroundColor Cyan
        Write-Host "  ats import [pdf]     Importa PDF e gera ATS"
        Write-Host "  ats import-all       Processa todos PDFs novos"
        Write-Host "  ats scan [pdf/nome]  Extrai JSON de PDF"
        Write-Host "  ats list             Lista candidatos no pool"
        Write-Host "  ats show [nome]      Exibe ATS de candidato"
        Write-Host "  ats linkedin [slug]  Abre LinkedIn no browser"
        Write-Host "  ats LAB-ROUTER-01              Status do LAB-ROUTER-01"
        Write-Host "  ats LAB-ROUTER-01-scan         Scan completo da rede"
        Write-Host "  ats help             Exibe esta ajuda"
        Write-Host ""
        Write-Host "Exemplos:" -ForegroundColor Yellow
        Write-Host "  .\scripts\ats.ps1 import-all"
        Write-Host "  .\scripts\ats.ps1 show candidate_a"
        Write-Host "  .\scripts\ats.ps1 linkedin example_slug"
        Write-Host "  .\scripts\ats.ps1 LAB-ROUTER-01-scan"
    }

    default {
        Write-Error "Comando desconhecido: $Command. Use: ats help"
        exit 1
    }
}
