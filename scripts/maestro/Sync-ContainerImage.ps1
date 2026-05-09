#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Sync-ContainerImage.ps1

.SYNOPSIS
 Distribuição SRE-compliant da imagem de container atual do Data Boar para os nós híbridos.

.DESCRIPTION
 Inspirado na arquitetura SRE (rigor DANFE).
 1. Extrai dinamicamente a versão (tag) diretamente do pyproject.toml local.
 2. Evita gasto de CPU fazendo Build Once no host central (Docker Desktop).
 3. Exporta o artefato como Tarball (.tar).
 4. Aplica inteligência de Cache (invalida se a imagem tiver mais de 1 hora de idade).
 5. Distribui via SCP apenas para nós que possuem personas declaradas de container.
 6. Executa a importação agnóstica (docker load ou podman load) no nó destino.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree"
)

# 1. Filtro de Persona: Executa apenas onde houver motor de container
$containerPersonas = @("docker", "podman", "dockerswarm")
$needsContainer = $false
foreach ($p in $containerPersonas) {
    if ($Node.personas -contains $p) { $needsContainer = $true }
}

if (-not $needsContainer) { return }

Write-Host "   [Container Sync] Certificando artefatos de container para $($Node.hostname)..." -ForegroundColor DarkCyan

# 2. Leitura Dinâmica do pyproject.toml (Zero Hardcode)
$pyprojectPath = "$PSScriptRoot/../../pyproject.toml"
if (-not (Test-Path $pyprojectPath)) {
    Write-Error "   [ERROR] pyproject.toml não encontrado em $pyprojectPath"
    exit 1
}

# Regex rigorosa para extrair a versão atual (ex: 1.7.4-rc, 1.7.4, etc.)
$tag = "latest"
$versionMatch = Get-Content $pyprojectPath | Select-String -Pattern '^version\s*=\s*"([^"]+)"'
if ($versionMatch -match '^version\s*=\s*"([^"]+)"') {
    $tag = $matches[1]
} else {
    Write-Warning "   [WARNING] Versão não identificada no pyproject.toml. Fallback para '$tag'."
}

# 3. Configuração de Nomes e Caminhos do Artefato
$imageName = "data-boar"
$fullImage = "${imageName}:${tag}"
$tarFile = "data-boar-${tag}.tar"
$tarPath = "$PSScriptRoot/../../$tarFile"

# 4. Inteligência de Cache (Stale check > 1 hora)
$needsBuild = $true
if (Test-Path $tarPath) {
    $fileAge = (Get-Date) - (Get-Item $tarPath).LastWriteTime
    if ($fileAge.TotalHours -lt 1) {
        Write-Host "      [Cache Hit] Tarball local ($tarFile) tem $($fileAge.Minutes) minutos. Reutilizando..." -ForegroundColor DarkGray
        $needsBuild = $false
    } else {
        Write-Host "      [Cache Miss] Imagem obsoleta (> 1 hora). Removendo..." -ForegroundColor Yellow
        Remove-Item $tarPath -Force
    }
}

# 5. Build & Export (Host Central / Local)
try {
    if ($needsBuild) {
        Write-Host "      [Build] Compilando $fullImage via Docker Desktop (Ref: $Ref)..." -ForegroundColor Yellow
        # SRE Note: Erros no build vão estourar para o catch
        $null = docker build -q -t $fullImage "$PSScriptRoot/../../"
        if ($LASTEXITCODE -ne 0) { throw "Falha no docker build." }

        Write-Host "      [Export] Gerando tarball $tarFile..." -ForegroundColor Yellow
        $null = docker save $fullImage -o $tarPath
        if ($LASTEXITCODE -ne 0) { throw "Falha no docker save." }
    }
} catch {
    Write-Error "   [FATAL] Ocorreu um erro ao gerar o artefato de container local: $_"
    exit 1
}

# 6. Distribuição SRE via SCP
Write-Host "      [Transfer] Enviando $tarFile para $($Node.hostname):$($Node.path)..." -ForegroundColor DarkCyan
scp -q $tarPath "$($Node.user)@$($Node.hostname):$($Node.path)/$tarFile"
if ($LASTEXITCODE -ne 0) {
    Write-Error "   [FATAL] Falha na transferência SCP para $($Node.hostname)."
    exit 1
}

# 7. Importação Agnóstica no Worker (Docker/Podman)
$engine = if ($Node.personas -contains "podman") { "podman" } else { "docker" }
Write-Host "      [Load] Importando imagem no motor remoto ($engine)..." -ForegroundColor Magenta

# Load silencioso no worker. Se a imagem já existir igualzinha, o motor otimiza.
$loadCmd = "cd $($Node.path) && $engine load -i $tarFile > /dev/null 2>&1"
ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" $loadCmd

Write-Host "      [SUCCESS] Imagem $fullImage provisionada com sucesso em $($Node.hostname)." -ForegroundColor Green
