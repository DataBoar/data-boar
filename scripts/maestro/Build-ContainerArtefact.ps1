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
$freshThresholdHours = 1
$staleWarnHours = 24

function Test-DockerEngineReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $false
    }
    $null = docker info --format '{{.ServerVersion}}' 2>$null
    return ($LASTEXITCODE -eq 0)
}

$tarExists = Test-Path -LiteralPath $tarPath
$fileAge = $null
if ($tarExists) {
    $fileAge = (Get-Date) - (Get-Item -LiteralPath $tarPath).LastWriteTime
}

$dockerReady = Test-DockerEngineReady
if ($dockerReady) {
    if ($tarExists) {
        if ($fileAge.TotalHours -gt $freshThresholdHours) {
            Write-Host ("   [Pre-flight] Docker online; artefato {0} stale ({1:N1}h). Rebuild forçado." -f $tarFile, $fileAge.TotalHours) -ForegroundColor Yellow
        } else {
            Write-Host ("   [Pre-flight] Docker online; refrescando {0} (cache atual {1:N1}h)." -f $tarFile, $fileAge.TotalHours) -ForegroundColor DarkGray
        }
        Remove-Item -LiteralPath $tarPath -Force
    } else {
        Write-Host "   [Pre-flight] Docker online e sem cache local. Build do artefato requerido." -ForegroundColor DarkGray
    }

    Write-Host "   [Pre-flight] Compilando $fullImage e gerando artefato SRE..." -ForegroundColor Yellow
    $null = docker build -q -t $fullImage "$PSScriptRoot/../../"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha no docker build para $fullImage."
        exit 7
    }
    $null = docker save $fullImage -o $tarPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha no docker save para $tarFile."
        exit 8
    }
    return
}

if (-not $tarExists) {
    Write-Error "Docker indisponivel e sem artefato local ($tarFile). Nao ha fallback seguro para sync."
    exit 9
}

if ($fileAge.TotalHours -ge $staleWarnHours) {
    Write-Warning ("   [Pre-flight] Docker indisponivel; usando fallback stale {0} ({1:N1}h). Resultados podem ficar incompletos/imprecisos. Registrar em lessons learned." -f $tarFile, $fileAge.TotalHours)
} elseif ($fileAge.TotalHours -ge $freshThresholdHours) {
    Write-Warning ("   [Pre-flight] Docker indisponivel; usando fallback {0} com idade {1:N1}h." -f $tarFile, $fileAge.TotalHours)
} else {
    Write-Host ("   [Pre-flight] Docker indisponivel; fallback em cache fresco {0} ({1:N1}h)." -f $tarFile, $fileAge.TotalHours) -ForegroundColor DarkGray
}
