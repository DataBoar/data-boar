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

# Actionable guard: the scp fallback only works if Build-ContainerArtefact produced
# (or kept) the local tar. Without it, scp would fail with an opaque "No such file"
# error per node. Fail loud but non-fatally (Write-Error keeps the multi-node loop
# alive) so the operator knows the engine path and the artefact path both missed.
if (-not (Test-Path -LiteralPath $tarPath)) {
    Write-Error "      [ERROR] Artefato local ausente ($tarFile). Build-ContainerArtefact nao gerou o tar (engine indisponivel e sem cache). Sem fallback scp para $($Node.hostname)."
    return
}

Write-Host "      [Container Sync] Distribuindo $tarFile para $($Node.hostname)..." -ForegroundColor DarkCyan
scp -q -o BatchMode=yes -o ConnectTimeout=10 $tarPath "$($Node.user)@$($Node.hostname):$($Node.path)/$tarFile"
if ($LASTEXITCODE -ne 0) {
    Write-Error "      [ERROR] Falha ao enviar $tarFile para $($Node.hostname) (scp exit $LASTEXITCODE). Verifique SSH/rede/espaco em disco no alvo."
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
