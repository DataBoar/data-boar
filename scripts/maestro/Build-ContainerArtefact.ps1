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

function Test-ContainerEngineReady {
    if ($env:DOCKER_HOST -match "podman" -and (Get-Command podman -ErrorAction SilentlyContinue)) {
        $null = & podman info --format "{{.Host.Os}}" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{ Cmd = "podman"; Ready = $true; IsPodman = $true }
        }
    }
    foreach ($cmd in @("podman", "docker")) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            continue
        }
        $null = & $cmd info --format '{{.ServerVersion}}' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $isPodman = ($cmd -eq "podman")
            return [PSCustomObject]@{ Cmd = $cmd; Ready = $true; IsPodman = $isPodman }
        }
    }
    return [PSCustomObject]@{ Cmd = $null; Ready = $false; IsPodman = $false }
}

function Invoke-ContainerImageBuild {
    param(
        [string]$EngineCmd,
        [bool]$IsPodman,
        [string]$FullImage,
        [string]$Context
    )
    if ($IsPodman -or $EngineCmd -eq "podman") {
        & podman build -q -t $FullImage $Context
        return $LASTEXITCODE
    }
    if ($env:DOCKER_HOST -match "podman" -and (Get-Command podman -ErrorAction SilentlyContinue)) {
        & podman build -q -t $FullImage $Context
        return $LASTEXITCODE
    }
    $prevBuildKit = $env:DOCKER_BUILDKIT
    $env:DOCKER_BUILDKIT = "0"
    try {
        & docker build -q -t $FullImage $Context
        return $LASTEXITCODE
    } finally {
        if ($null -eq $prevBuildKit) {
            Remove-Item Env:DOCKER_BUILDKIT -ErrorAction SilentlyContinue
        } else {
            $env:DOCKER_BUILDKIT = $prevBuildKit
        }
    }
}

$tarExists = Test-Path -LiteralPath $tarPath
$fileAge = $null
if ($tarExists) {
    $fileAge = (Get-Date) - (Get-Item -LiteralPath $tarPath).LastWriteTime
}

$engine = Test-ContainerEngineReady
if ($engine.Ready) {
    $engineCmd = $engine.Cmd
    $shouldBuild = $true
    if ($tarExists -and $fileAge.TotalHours -le $freshThresholdHours) {
        Write-Host ("   [Pre-flight] {0} online; artefato {1} fresco ({2:N1}h < {3}h threshold). Reutilizando." -f $engineCmd, $tarFile, $fileAge.TotalHours, $freshThresholdHours) -ForegroundColor DarkGray
        $shouldBuild = $false
    } elseif ($tarExists) {
        Write-Host ("   [Pre-flight] {0} online; artefato {1} stale ({2:N1}h). Rebuild forcado." -f $engineCmd, $tarFile, $fileAge.TotalHours) -ForegroundColor Yellow
        Remove-Item -LiteralPath $tarPath -Force
    } else {
        Write-Host ("   [Pre-flight] {0} online e sem cache local. Build do artefato requerido." -f $engineCmd) -ForegroundColor DarkGray
    }

    if ($shouldBuild) {
        Write-Host "   [Pre-flight] Compilando $fullImage e gerando artefato SRE..." -ForegroundColor Yellow
        $buildExit = Invoke-ContainerImageBuild -EngineCmd $engineCmd -IsPodman $engine.IsPodman -FullImage $fullImage -Context "$PSScriptRoot/../../"
        if ($buildExit -ne 0) {
            Write-Error "Falha no build da imagem $fullImage (engine=$engineCmd)."
            exit 7
        }
        $null = & $engineCmd save $fullImage -o $tarPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falha no $engineCmd save para $tarFile."
            exit 8
        }
    } # end if ($shouldBuild)
    return
}

if (-not $tarExists) {
    Write-Error "Container engine indisponivel (docker/podman) e sem artefato local ($tarFile). Nao ha fallback seguro para sync."
    exit 9
}

if ($fileAge.TotalHours -ge $staleWarnHours) {
    Write-Warning ("   [Pre-flight] Container engine indisponivel; usando fallback stale {0} ({1:N1}h). Resultados podem ficar incompletos/imprecisos. Registrar em lessons learned." -f $tarFile, $fileAge.TotalHours)
} elseif ($fileAge.TotalHours -ge $freshThresholdHours) {
    Write-Warning ("   [Pre-flight] Container engine indisponivel; usando fallback {0} com idade {1:N1}h." -f $tarFile, $fileAge.TotalHours)
} else {
    Write-Host ("   [Pre-flight] Container engine indisponivel; fallback em cache fresco {0} ({1:N1}h)." -f $tarFile, $fileAge.TotalHours) -ForegroundColor DarkGray
}
