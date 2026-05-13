#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Sync-WorkingTree.ps1

.SYNOPSIS
 Author: Fábio Leitão com apoio da Gemini e Cursosr IDE
 Missão principal: Sub-Orquestrador de sincronismo em pré-flight para o teste Completão funcionar no Lab-Op a partir do repo no gh ou da working tree no ambiente canônico de Dev principal no PC de desenvolvimento.
#>

param(
    [Parameter(Mandatory=$true)]$Node,
    [string]$Ref = "WorkingTree"
)

# O StrictMode entra LOGO APÓS os parâmetros
Set-StrictMode -Version 2

# Mapeamento alinhado com o objeto JSON recebido do Maestro
$targetHost = $Node.hostname
$targetIp   = $Node.ip
$targetUser = $Node.user
$basePath   = $Node.path

# Lógica de Pasta Efêmera: se não for WorkingTree, cria um sufixo
# 1. Definição Limpa do Path (Onde o erro começou)
if ($Ref -eq "WorkingTree") {
    $finalPath = $basePath
    Write-Host "   [Sync] Sincronizando Working Tree -> $targetHost" -ForegroundColor Cyan
} else {
    $finalPath = "$basePath-$Ref" # Ex: ~/Projects/dev/data-boar-1.7.3
    Write-Host "   [Ref-Fetch] Preparando versão $Ref em pasta efêmera no $targetHost" -ForegroundColor Yellow
}

# 2. Garantir que o diretório existe (Silenciando banners do Linux remoto)
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "mkdir -p $finalPath" > $null 2>&1

# 3. Lógica de Transferência
$syncOk = $false
if ($Ref -eq "WorkingTree") {
    # Fluxo Evoluído: rsync (Delta Transfer) via WSL2
    $repoRoot = (Resolve-Path "$PSScriptRoot/../../").Path

    Push-Location $repoRoot

    # Comando Rsync.
    # Nice catch excluding my docs/private from rsyncCmd so it wont exfiltrate operator private tree!!! Thanks a lot Gemini... :-o
    $rsyncCmd = "rsync -azq -e 'ssh -q -o BatchMode=yes -o ConnectTimeout=15' --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.bundle' --exclude='docs/private' --exclude='*.log' --exclude='*.xlsx' --exclude='*.db' --exclude='data-boar-blackbox-audit.txt' --exclude='data-boar-*.tar' ./ ${targetUser}@${targetHost}:${finalPath}/"

    # Invocamos o WSL2 com aspas duplas no $rsyncCmd para o bash entender como argumento único
    wsl.exe -e bash -c "$rsyncCmd"

    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -ne 0) {
        Write-Warning "      [WARNING] O rsync via WSL2 falhou no nó $targetHost (Exit Code $exitCode)."
    } else {
        # Verificacao SRE: confirmar que arquivos chave ficaram identicos no host remoto.
        $localPyprojectHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot "pyproject.toml")).Hash.ToLower()
        $localMaestroHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $repoRoot "scripts/maestro/Maestro.ps1")).Hash.ToLower()
        $verifyCmd = "cd $finalPath && sha256sum pyproject.toml scripts/maestro/Maestro.ps1 2>/dev/null"
        $verifyOut = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "$verifyCmd"
        if ($LASTEXITCODE -ne 0 -or -not $verifyOut) {
            Write-Warning "      [WARNING] Nao foi possivel validar hash remoto pos-rsync em $targetHost."
        } else {
            $remoteHashes = @{}
            foreach ($line in $verifyOut) {
                if ($line -match '^([0-9a-fA-F]{64})\s+(.+)$') {
                    $remoteHashes[$matches[2]] = $matches[1].ToLower()
                }
            }
            $hashOk = $true
            if (($remoteHashes["pyproject.toml"] -ne $localPyprojectHash) -or ($remoteHashes["scripts/maestro/Maestro.ps1"] -ne $localMaestroHash)) {
                $hashOk = $false
            }

            if ($hashOk) {
                Write-Host "      [Sync-Verify] Hash check OK (pyproject + Maestro)." -ForegroundColor DarkGray
                $syncOk = $true
            } else {
                Write-Warning "      [WARNING] Hash mismatch apos rsync em $targetHost. Sync invalido para run."
            }
        }
    }
} else {
    # Novo Fluxo: Git Remote Fetch (Efêmero)
    # Remove stale origin if present from a previous ephemeral checkout (local or remote URL),
    # then re-add the canonical GitHub remote before fetching the ref.
    $gitCmd = "cd $finalPath && git init && (git remote remove origin 2>/dev/null || true) && git remote add origin git@github.com:FabioLeitao/data-boar.git && git fetch origin $Ref --depth=1 && git checkout FETCH_HEAD"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "$gitCmd" > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $syncOk = $true
    }
}

# 4. Validação SRE
if ($syncOk) {
    Write-Host "      [SUCCESS] $targetHost pronto em $finalPath." -ForegroundColor Green
    $Node.path = $finalPath

    # Sessões tmux só fazem sentido com sync válido.
    $tmuxInit = "tmux new-session -d -s completao 2>/dev/null || true ; tmux new-session -d -s monitor 2>/dev/null || true"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$targetUser@$targetHost" "$tmuxInit" > $null 2>&1
} else {
    Write-Warning "      [ERROR] Falha na preparação/sincronização de $targetHost."
}

# Retorna boolean puro para o Maestro.
return [bool]$syncOk

