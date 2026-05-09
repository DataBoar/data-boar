#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Sync-WorkingTree.ps1

.SYNOPSIS
 Author: Fábio Leitão com apoio da Gemini e Cursosr IDE
 Missão principal: Sub-Orquestrador de sincronismo em pré-flight para o teste Completão funcionar no Lab-Op a partir do repo no gh ou da working tree no ambiente canônico de Dev principal (Maestro PC).
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
ssh -q -o BatchMode=yes "$targetUser@$targetHost" "mkdir -p $finalPath" > $null 2>&1

# 3. Lógica de Transferência
if ($Ref -eq "WorkingTree") {
    # Fluxo Evoluído: rsync (Delta Transfer) via WSL2
    $repoRoot = (Resolve-Path "$PSScriptRoot/../../").Path

    Push-Location $repoRoot

    # Comando Rsync.
    # Nice catch excluding my docs/private from rsyncCmd so it wont exfiltrate the Dev PC private tree!!! Thanks a lot Gemini... :-o
    $rsyncCmd = "rsync -azq -e 'ssh -q -o BatchMode=yes' --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.bundle' --exclude='docs/private' --exclude='*.log' --exclude='*.xlsx' --exclude='*.db' --exclude='data-boar-blackbox-audit.txt' ./ ${targetUser}@${targetHost}:${finalPath}/"

    # Invocamos o WSL2 com aspas duplas no $rsyncCmd para o bash entender como argumento único
    wsl.exe -e bash -c "$rsyncCmd"

    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -ne 0) {
        Write-Warning "      [WARNING] O rsync via WSL2 falhou no nó $targetHost (Exit Code $exitCode)."
    }
} else {
    # Novo Fluxo: Git Remote Fetch (Efêmero)
    $gitCmd = "cd $finalPath && git init && git remote add origin git@github.com:FabioLeitao/data-boar.git && git fetch origin $Ref && git checkout FETCH_HEAD"
    ssh -q -o BatchMode=yes "$targetUser@$targetHost" "$gitCmd" > $null 2>&1
}

# 4. Validação SRE
if ($LASTEXITCODE -eq 0) {
    Write-Host "      [SUCCESS] $targetHost pronto em $finalPath." -ForegroundColor Green
    $Node.path = $finalPath
} else {
    Write-Warning "      [ERROR] Falha na preparação/sincronização de $targetHost."
}

# 5. Cria as sessões 'completao' e 'monitor' ignorando erros se elas já existirem
$tmuxInit = "tmux new-session -d -s completao 2>/dev/null || true ; tmux new-session -d -s monitor 2>/dev/null || true"
ssh -q -o BatchMode=yes "$targetUser@$targetHost" "$tmuxInit"

