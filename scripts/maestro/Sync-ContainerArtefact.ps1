#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Sync-ContainerArtefact.ps1
.SYNOPSIS
 Sincroniza o tarball gerado no Pre-flight apenas para hosts de container.
#>

param(
    [Parameter(Mandatory=$true)]$Node
)

# Extrai a versão para saber qual arquivo buscar
$tag = "latest"
$versionMatch = Get-Content "$PSScriptRoot/../../pyproject.toml" | Select-String -Pattern '^version\s*=\s*"([^"]+)"'
if ($versionMatch -match '^version\s*=\s*"([^"]+)"') { $tag = $matches[1] }

$tarFile = "data-boar-${tag}.tar"
$tarPath = "$PSScriptRoot/../../$tarFile"

Write-Host "      [Container Sync] Distribuindo $tarFile para $($Node.hostname)..." -ForegroundColor DarkCyan
scp -q -o BatchMode=yes -o ConnectTimeout=10 $tarPath "$($Node.user)@$($Node.hostname):$($Node.path)/$tarFile"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "      [WARNING] Falha ao enviar $tarFile para $($Node.hostname) (scp exit $LASTEXITCODE)."
    return
}

$engine = if ($Node.personas -contains "podman") { "podman" } else { "docker" }
$loadCmd = "cd $($Node.path) && $engine load -i $tarFile > /dev/null 2>&1"
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" $loadCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] Imagem provisionada remotamente via $engine." -ForegroundColor Green
} else {
    Write-Warning "      [WARNING] Falha ao carregar imagem via $engine em $($Node.hostname) (ssh exit $LASTEXITCODE)."
}
