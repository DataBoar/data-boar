#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Build-ContainerArtefact.ps1
.SYNOPSIS
 Compila a imagem local do Data Boar a partir do Working Tree, lendo a versão do pyproject.toml.
#>

$pyprojectPath = "$PSScriptRoot/../../pyproject.toml"
$tag = "latest"
$versionMatch = Get-Content $pyprojectPath | Select-String -Pattern '^version\s*=\s*"([^"]+)"'
if ($versionMatch -match '^version\s*=\s*"([^"]+)"') { $tag = $matches[1] }

$fullImage = "data-boar:${tag}"
$tarFile = "data-boar-${tag}.tar"
$tarPath = "$PSScriptRoot/../../$tarFile"

$needsBuild = $true
if (Test-Path $tarPath) {
    $fileAge = (Get-Date) - (Get-Item $tarPath).LastWriteTime
    if ($fileAge.TotalHours -lt 1) {
        Write-Host "   [Pre-flight] Artefato $tarFile fresco em cache ($($fileAge.Minutes) min)." -ForegroundColor DarkGray
        $needsBuild = $false
    } else {
        Remove-Item $tarPath -Force
    }
}

if ($needsBuild) {
    Write-Host "   [Pre-flight] Compilando $fullImage e gerando artefato SRE..." -ForegroundColor Yellow
    $null = docker build -q -t $fullImage "$PSScriptRoot/../../"
    $null = docker save $fullImage -o $tarPath
}
