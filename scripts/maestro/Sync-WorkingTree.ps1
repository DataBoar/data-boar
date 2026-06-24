#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Sync-WorkingTree.ps1

.SYNOPSIS
 Author: Fábio Leitão com apoio da Gemini e Cursosr IDE
 Missão principal: Sub-Orquestrador de sincronismo em pré-flight para o teste Completão funcionar no Lab-Op a partir do repo no gh ou da working tree no ambiente canônico de Dev principal no PC de desenvolvimento.

 #969: rsync e pre-req; se falhar (ex. exit 12 / rsync ausente no remoto), fallback scp+tar
 #969b: depois tar|ssh stream. Narrow doas+apk rsync install fica para #958.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree"
)

# O StrictMode entra LOGO APÓS os parâmetros
Set-StrictMode -Version 2

. "$PSScriptRoot/Maestro-CanonicalGuard.ps1"
$script:MaestroOrchestratorHost = Get-MaestroOrchestratorHostname

# Mapeamento alinhado com o objeto JSON recebido do Maestro
$targetHost = $Node.hostname
$targetIp   = $Node.ip
$targetUser = $Node.user
$basePath   = $Node.path

# Lógica de Pasta Efêmera: parent isolado /tmp/databoar_bench (#948) — sem sibling data-boar*
if ($Ref -eq "WorkingTree") {
    $finalPath = $basePath
    Write-Host "   [Sync] Sincronizando Working Tree -> $targetHost" -ForegroundColor Cyan
} else {
    $finalPath = Get-MaestroEphemeralRepoPath -Ref $Ref -BasePath $basePath
    Write-Host "   [Ref-Fetch] Preparando versão $Ref em $finalPath no $targetHost" -ForegroundColor Yellow
}

if ($Ref -eq "WorkingTree" -and (Test-MaestroInventoryNodeProtected -Node $Node -OrchestratorHost $script:MaestroOrchestratorHost)) {
    Write-Warning "   [GUARD #948] Skip WorkingTree sync overwrite on protected node $targetHost (canonical/maestro/loopback)."
    $Node.path = $finalPath
    return $true
}

function Test-SyncHashVerify {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$RemoteUser,
        [Parameter(Mandatory = $true)][string]$RemoteHost,
        [Parameter(Mandatory = $true)][string]$RemotePath
    )

    $localPyprojectHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $RepoRoot "pyproject.toml")).Hash.ToLower()
    $localMaestroHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $RepoRoot "scripts/maestro/Maestro.ps1")).Hash.ToLower()
    $verifyCmd = "cd $RemotePath && sha256sum pyproject.toml scripts/maestro/Maestro.ps1 2>/dev/null"
    $verifyOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "${RemoteUser}@${RemoteHost}" "$verifyCmd"
    if ($LASTEXITCODE -ne 0 -or -not $verifyOut) {
        Write-Warning "      [WARNING] Nao foi possivel validar hash remoto pos-sync em $RemoteHost."
        return $false
    }

    $remoteHashes = @{}
    foreach ($line in $verifyOut) {
        if ($line -match '^([0-9a-fA-F]{64})\s+(.+)$') {
            $remoteHashes[$matches[2]] = $matches[1].ToLower()
        }
    }

    if (($remoteHashes["pyproject.toml"] -ne $localPyprojectHash) -or ($remoteHashes["scripts/maestro/Maestro.ps1"] -ne $localMaestroHash)) {
        Write-Warning "      [WARNING] Hash mismatch apos sync em $RemoteHost. Sync invalido para run."
        return $false
    }

    Write-Host "      [Sync-Verify] Hash check OK (pyproject + Maestro)." -ForegroundColor DarkGray
    return $true
}

function Invoke-SyncScpTarFallback {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$RemoteUser,
        [Parameter(Mandatory = $true)][string]$RemoteHost,
        [Parameter(Mandatory = $true)][string]$RemotePath,
        [int]$RsyncExitCode
    )

    Write-Warning "      [Sync-Fallback #969] rsync exit $RsyncExitCode em $RemoteHost; tentando scp+tar (remoto nao precisa de rsync — Consigliere #F4)."
    $localTar = Join-Path ([System.IO.Path]::GetTempPath()) ("databoar-sync-" + [guid]::NewGuid().ToString("n") + ".tar.gz")
    $remoteTar = "/tmp/databoar-sync-upload.tar.gz"
    $escapedRoot = $RepoRoot -replace "'", "'\\''"
    $tarLocalCmd = "tar -czf '$localTar' --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.bundle' --exclude='docs/private' --exclude='*.log' --exclude='*.xlsx' --exclude='*.db' --exclude='data-boar-blackbox-audit.txt' --exclude='data-boar-*.tar' --exclude='.env' --exclude='.env.*' -C '$escapedRoot' ."

    if ($IsWindows) {
        wsl.exe -e bash -c $tarLocalCmd
    } else {
        bash -c $tarLocalCmd
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $localTar)) {
        Write-Warning "      [Sync-Fallback] scp: falha ao criar tarball local (exit $LASTEXITCODE)."
        if (Test-Path -LiteralPath $localTar) { Remove-Item -LiteralPath $localTar -Force -ErrorAction SilentlyContinue }
        return $false
    }

    scp -q -o BatchMode=yes -o ConnectTimeout=15 "$localTar" "${RemoteUser}@${RemoteHost}:${remoteTar}"
    $scpExit = $LASTEXITCODE
    Remove-Item -LiteralPath $localTar -Force -ErrorAction SilentlyContinue
    if ($scpExit -ne 0) {
        Write-Warning "      [Sync-Fallback] scp falhou em $RemoteHost (exit $scpExit)."
        ssh -q -o BatchMode=yes -o ConnectTimeout=15 "${RemoteUser}@${RemoteHost}" "rm -f $remoteTar" > $null 2>&1
        return $false
    }

    $extractCmd = "mkdir -p $RemotePath && tar -xzf $remoteTar -C $RemotePath && rm -f $remoteTar"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "${RemoteUser}@${RemoteHost}" "$extractCmd"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "      [Sync-Fallback] scp: extract remoto falhou em $RemoteHost (exit $LASTEXITCODE)."
        return $false
    }

    Write-Host "      [Sync-Fallback] scp+tar OK em $RemoteHost." -ForegroundColor DarkGray
    return $true
}

function Invoke-SyncTarSshFallback {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$RemoteUser,
        [Parameter(Mandatory = $true)][string]$RemoteHost,
        [Parameter(Mandatory = $true)][string]$RemotePath,
        [int]$RsyncExitCode
    )

    Write-Warning "      [Sync-Fallback #969] rsync exit $RsyncExitCode em $RemoteHost; tentando tar|ssh (mesmas exclusoes que rsync; remoto pode nao ter rsync — ex. alpine)."
    $escapedRoot = $RepoRoot -replace "'", "'\\''"
    $tarPipeCmd = "tar -czf - --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.bundle' --exclude='docs/private' --exclude='*.log' --exclude='*.xlsx' --exclude='*.db' --exclude='data-boar-blackbox-audit.txt' --exclude='data-boar-*.tar' --exclude='.env' --exclude='.env.*' -C '$escapedRoot' . | ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ${RemoteUser}@${RemoteHost} `"mkdir -p $RemotePath && tar -xzf - -C $RemotePath`""

    if ($IsWindows) {
        wsl.exe -e bash -c $tarPipeCmd
    } else {
        bash -c $tarPipeCmd
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "      [Sync-Fallback] tar|ssh falhou em $RemoteHost (exit $LASTEXITCODE). Instalar rsync no remoto ou ver #958 (narrow doas apk)."
        return $false
    }

    Write-Host "      [Sync-Fallback] tar|ssh OK em $RemoteHost." -ForegroundColor DarkGray
    return $true
}

# 2. Garantir que o diretório existe (Silenciando banners do Linux remoto)
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "mkdir -p $finalPath" > $null 2>&1

# 3. Lógica de Transferência
$syncOk = $false
if ($Ref -eq "WorkingTree") {
    # Fluxo Evoluído: rsync (Delta Transfer) via WSL2 / bash nativo Linux
    $repoRoot = (Resolve-Path "$PSScriptRoot/../../").Path

    Push-Location $repoRoot

    # Comando Rsync.
    # Nice catch excluding my docs/private from rsyncCmd so it wont exfiltrate operator private tree!!! Thanks a lot Gemini... :-o
    $rsyncCmd = "rsync -azq -e 'ssh -q -o BatchMode=yes -o ConnectTimeout=15' --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.bundle' --exclude='docs/private' --exclude='*.log' --exclude='*.xlsx' --exclude='*.db' --exclude='data-boar-blackbox-audit.txt' --exclude='data-boar-*.tar' --exclude='.env' --exclude='.env.*' ./ ${targetUser}@${targetHost}:${finalPath}/"

    # Invocamos bash nativo no Linux ou WSL2 no Windows
    if ($IsWindows) {
        wsl.exe -e bash -c "$rsyncCmd"
    } else {
        bash -c "$rsyncCmd"
    }

    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -eq 0) {
        $syncOk = Test-SyncHashVerify -RepoRoot $repoRoot -RemoteUser $targetUser -RemoteHost $targetHost -RemotePath $finalPath
    } else {
        Write-Warning "      [WARNING] rsync falhou no no $targetHost (exit $exitCode)."
        if (Invoke-SyncScpTarFallback -RepoRoot $repoRoot -RemoteUser $targetUser -RemoteHost $targetHost -RemotePath $finalPath -RsyncExitCode $exitCode) {
            $syncOk = Test-SyncHashVerify -RepoRoot $repoRoot -RemoteUser $targetUser -RemoteHost $targetHost -RemotePath $finalPath
        } elseif (Invoke-SyncTarSshFallback -RepoRoot $repoRoot -RemoteUser $targetUser -RemoteHost $targetHost -RemotePath $finalPath -RsyncExitCode $exitCode) {
            $syncOk = Test-SyncHashVerify -RepoRoot $repoRoot -RemoteUser $targetUser -RemoteHost $targetHost -RemotePath $finalPath
        }
    }
} else {
    # Novo Fluxo: Git Remote Fetch (Efêmero)
    # Remove stale origin if present from a previous ephemeral checkout (local or remote URL),
    # then re-add origin (per-node git_origin override or canonical GitHub) before fetching the ref.
    $gitOrigin = "git@github.com:FabioLeitao/data-boar.git"
    if ($Node.PSObject.Properties['git_origin'] -and $Node.git_origin) {
        $gitOrigin = $Node.git_origin
    }
    $gitCmd = "cd $finalPath && git init && (git remote remove origin 2>/dev/null || true) && git remote add origin $gitOrigin && git fetch origin $Ref --depth=1 && git checkout FETCH_HEAD"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "$gitCmd" > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $syncOk = $true
    }
}

# 4. Validação SRE
if ($syncOk) {
    Write-Host "      [SUCCESS] $targetHost pronto em $finalPath." -ForegroundColor Green
    $Node.path = $finalPath

    # Legacy session `completao`: hook reservado p/ status central / observe-from-inside — ver #967.
    # Multi-persona live runs inject into completao_<persona> (Lab-MaestroCommon.ps1).
    $tmuxInit = "tmux new-session -d -s completao 2>/dev/null || true ; tmux new-session -d -s monitor 2>/dev/null || true"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "$tmuxInit" > $null 2>&1
} else {
    Write-Warning "      [ERROR] Falha na preparação/sincronização de $targetHost."
}

# Retorna boolean puro para o Maestro.
return [bool]$syncOk
