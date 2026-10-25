#Requires -Version 5.1
<#
.SYNOPSIS
    Baixa fotos iCloud (stubs RecallOnDataAccess) para pasta local acessivel ao agente.
.PARAMETER Start
    Data inicio (ex: "2022-11-01"). Default: 30 dias atras.
.PARAMETER End
    Data fim (ex: "2022-11-30"). Default: hoje.
.PARAMETER MaxFiles
    Maximo de arquivos a baixar (default: 100).
.PARAMETER Extensions
    Extensoes de arquivo a incluir.
.PARAMETER FilePath
    Modo pontual: arquivo especifico para forcar download.
.PARAMETER Cleanup
    Remove docs/private/icloud_temp/ apos analise.
.PARAMETER Library
    Qual biblioteca: main (default) | recent | both.
.EXAMPLE
    .\scripts\icloud-photos-fetch-range.ps1 -Start "2022-11-01" -End "2022-11-30"
    .\scripts\icloud-photos-fetch-range.ps1 -Start "2025-01-01" -End "2025-06-30" -MaxFiles 50
    .\scripts\icloud-photos-fetch-range.ps1 -Cleanup
    .\scripts\icloud-photos-fetch-range.ps1 -FilePath "C:\Users\<username>\Arquivo das Fotos do iCloud\IMG_7641.JPEG"
.NOTES
    Guia: docs/private/homelab/ICLOUD_PHOTOS_SYNC_GUIDE.md
#>
param(
    [string]$Start = "",
    [string]$End   = "",
    [int]$MaxFiles = 100,
    [string[]]$Extensions = @(".jpg",".jpeg",".png",".mp4",".mov",".heic",".JPG",".JPEG",".PNG",".MP4",".MOV",".HEIC"),
    [string]$FilePath = "",
    [switch]$Cleanup,
    [ValidateSet("main","recent","both")]
    [string]$Library = "main"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$tempDir  = Join-Path $repoRoot "docs\private\icloud_temp"

$libraries = @{
    main   = "C:\Users\<username>\Arquivo das Fotos do iCloud"
    recent = "C:\Users\<username>\Arquivo das Fotos do iCloud(1)"
}

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }

if ($Cleanup) {
    Write-Header "iCloud Temp -- Limpeza"
    if (Test-Path $tempDir) {
        $count = (Get-ChildItem $tempDir -File -Recurse).Count
        Remove-Item $tempDir -Recurse -Force
        Write-Ok "Removido: $tempDir ($count arquivos)"
    } else { Write-Info "Pasta temp nao existe: $tempDir" }
    exit 0
}

if ($FilePath) {
    Write-Header "iCloud -- Download pontual"
    if (-not (Test-Path $FilePath)) { Write-Warn "Arquivo nao encontrado: $FilePath"; exit 1 }
    if (-not (Test-Path $tempDir)) { New-Item $tempDir -ItemType Directory | Out-Null }
    $dest = Join-Path $tempDir (Split-Path $FilePath -Leaf)
    Write-Info "Copiando (forca download do stub): $FilePath"
    Copy-Item $FilePath $dest -Force
    Write-Ok "Disponivel em: $dest"
    exit 0
}

Write-Header "iCloud Photos -- Download Seletivo"
$startDate = if ($Start) { [DateTime]$Start } else { (Get-Date).AddDays(-30) }
$endDate   = if ($End)   { [DateTime]$End }   else { Get-Date }

Write-Info "Periodo: $($startDate.ToString('yyyy-MM-dd')) a $($endDate.ToString('yyyy-MM-dd'))"
Write-Info "Max arquivos: $MaxFiles | Biblioteca: $Library"

$libPaths = switch ($Library) {
    "main"   { @($libraries.main) }
    "recent" { @($libraries.recent) }
    "both"   { @($libraries.main, $libraries.recent) }
}

$freeGB = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Write-Info "Espaco livre em C: ${freeGB} GB"
if ($freeGB -lt 1) { Write-Warn "Menos de 1 GB livre. Abort."; exit 1 }

$allFiles = @()
foreach ($libPath in $libPaths) {
    if (-not (Test-Path $libPath)) { Write-Warn "Biblioteca nao encontrada: $libPath"; continue }
    $files = Get-ChildItem $libPath -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $startDate -and $_.LastWriteTime -le $endDate -and $_.Extension -iin $Extensions } |
        Sort-Object LastWriteTime
    Write-Info "Encontrados em $(Split-Path $libPath -Leaf): $($files.Count)"
    $allFiles += $files
}

if ($allFiles.Count -eq 0) {
    Write-Warn "Nenhum arquivo encontrado no periodo."
    Write-Info "Dica: LastWriteTime pode nao refletir data de captura exata para fotos antigas."
    exit 0
}

$toDownload = $allFiles | Select-Object -First $MaxFiles
Write-Ok "Selecionados: $($toDownload.Count) de $($allFiles.Count) encontrados"

if (-not (Test-Path $tempDir)) { New-Item $tempDir -ItemType Directory | Out-Null }
$runDir = Join-Path $tempDir ("run_" + (Get-Date -Format "yyyyMMdd_HHmm"))
New-Item $runDir -ItemType Directory | Out-Null

$copied = 0; $failed = 0; $counter = 0
Write-Info "Copiando (forca download dos stubs)..."
foreach ($f in $toDownload) {
    $counter++
    $dest = Join-Path $runDir $f.Name
    if (Test-Path $dest) { $dest = Join-Path $runDir ("$($f.BaseName)_$counter$($f.Extension)") }
    try {
        Copy-Item $f.FullName $dest -Force
        $copied++
        if ($counter % 20 -eq 0) { Write-Info "Progresso: $counter/$($toDownload.Count)" }
    } catch { $failed++; Write-Warn "Falha: $($f.Name) -- $_" }
}

Write-Header "Resultado"
Write-Ok "Copiados: $copied | Falhas: $failed"
Write-Ok "Pasta para o agente ler: $runDir"
Write-Info "Para limpar: .\scripts\icloud-photos-fetch-range.ps1 -Cleanup"

$manifest = @{
    GeneratedAt = (Get-Date -Format "o"); Library = $Library
    Period = @{ Start = $startDate.ToString("yyyy-MM-dd"); End = $endDate.ToString("yyyy-MM-dd") }
    CopiedCount = $copied; FailedCount = $failed; TempPath = $runDir
    Files = ($toDownload | Select-Object -ExpandProperty Name)
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $runDir "_manifest.json") -Encoding UTF8
Write-Ok "Manifesto gerado: $(Join-Path $runDir '_manifest.json')"
