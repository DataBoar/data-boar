#Requires -Version 5.1
<#
.SYNOPSIS
    Sincroniza e commita o stacked private repo (docs/private).

.DESCRIPTION
    Workflow obrigatorio apos qualquer sessao que modifique docs/private/:
    1. Copia feedbacks do inbox gitignored para docs/private/feedbacks_and_reviews/
    2. Faz git add -A e commit no private repo
    3. Opcionalmente faz push para o remote privado configurado (ex.: backup)
    4. Relata status e contagem de arquivos committed

.PARAMETER Message
    Mensagem de commit (default: auto-gerada com timestamp).

.PARAMETER Push
    Se informado, faz push para os remotes lab-* em docs/private/.git, depois tenta bare notes-sync.git em Z: ou Y: (VeraCrypt; Z: e o padrao do operador; Y: apenas como fallback se remapeado), e robocopy para P: se montado.

.PARAMETER FeedbacksOnly
    Apenas sincroniza feedbacks (nao faz commit geral).

.EXAMPLE
    .\scripts\private-git-sync.ps1
    .\scripts\private-git-sync.ps1 -Push
    .\scripts\private-git-sync.ps1 -Message "chore(private): update homelab notes after lab-op session"
#>
param(
    [string]$Message = "",
    [switch]$Push,
    [switch]$FeedbacksOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private"
$inboxDir = Join-Path $repoRoot "docs\feedbacks, reviews, comments and criticism"
$feedbacksDest = Join-Path $privateDir "feedbacks_and_reviews"

function Write-Header($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok($m)     { Write-Host "  OK  $m" -ForegroundColor Green }
function Write-Info($m)   { Write-Host "  ... $m" -ForegroundColor Gray }
function Write-Warn($m)   { Write-Host " WARN $m" -ForegroundColor Yellow }

Write-Header "private-git-sync: Stacked Private Repo Sync"

# --- 1. Sync feedbacks from gitignored inbox to private canonical ---
Write-Header "Passo 1: Sincronizar feedbacks do inbox para docs/private/feedbacks_and_reviews/"
if (Test-Path $inboxDir) {
    if (-not (Test-Path $feedbacksDest)) {
        New-Item -ItemType Directory -Path $feedbacksDest | Out-Null
        Write-Info "Criado: $feedbacksDest"
    }
    $before = (Get-ChildItem $feedbacksDest -Recurse -File -ErrorAction SilentlyContinue).Count
    Copy-Item "$inboxDir\*" -Destination $feedbacksDest -Recurse -Force -ErrorAction SilentlyContinue
    $after = (Get-ChildItem $feedbacksDest -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Ok "Feedbacks sincronizados: $before -> $after arquivos em feedbacks_and_reviews/"
} else {
    Write-Info "Inbox nao encontrado em: $inboxDir (ok se vazio)"
}

if ($FeedbacksOnly) {
    Write-Info "Modo FeedbacksOnly: encerrado apos sync de feedbacks."
    exit 0
}

# --- 2. Remove stale index.lock if exists ---
$lockFile = Join-Path $privateDir ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Warn "Removido stale index.lock"
}

# --- 3. git add -A e commit ---
Write-Header "Passo 2: Commit no private repo"
Set-Location $privateDir

# Git may write CRLF/LF warnings to stderr; with $ErrorActionPreference = Stop, PowerShell 5.1 treats that as terminating.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"

$status = git status --short 2>&1
$pendingCount = ($status | Measure-Object).Count
Write-Info "Arquivos pendentes (M/A/?): $pendingCount"

if ($pendingCount -eq 0) {
    Write-Ok "Private repo ja esta em dia. Nenhum arquivo pendente."
} else {
    # Staged explicito por pasta (git add -A pode falhar silenciosamente)
    $folders = @("feedbacks_and_reviews", "homelab", "author_info", "commercial", "operator_economics", "legal_dossier", "raw_pastes", "plans", "pitch", "security_audit", "social_drafts", "employers", "evidence_catalog", "scripts")
    foreach ($f in $folders) {
        $fp = Join-Path $privateDir $f
        if (Test-Path $fp) { git add $f 2>&1 | Out-Null }
    }
    # Root-level files (explicit globs can miss renames; catch rest with -A on repo root only)
    git add *.md *.ps1 *.py *.yml *.json *.txt 2>&1 | Out-Null
    git add --all -- . 2>&1 | Out-Null

    $stagedCount = (git diff --cached --name-only 2>&1 | Measure-Object).Count
    Write-Info "Staged: $stagedCount arquivos"

    if ($stagedCount -eq 0) {
        Write-Warn "Nenhum arquivo staged. Verificar .gitignore interno ou paths."
    } else {
        if (-not $Message) {
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
            $Message = "chore(private): session sync $ts"
        }
        git commit --trailer "Made-with: Cursor" -m $Message 2>&1 | Select-Object -First 3
        Write-Ok "Commit realizado: $Message"
    }
}

$ErrorActionPreference = $prevEap

# --- 4. Push para todos os remotes configurados (opcional) ---
if ($Push) {
    Write-Header "Passo 3: Push para todos os lab remotes"
    $prevEapPush = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $remotes = git remote 2>&1
    $labRemotes = $remotes | Where-Object { $_ -match "^lab-" }
    if (-not $labRemotes) {
        Write-Warn "Nenhum remote 'lab-*' configurado. Configure com:"
        Write-Warn "  git -C docs/private remote add lab-host-1 ssh://<user>@<host-1>/<home>/<user>/Documents/.kb-cache/repos/notes-sync.git"
        Write-Warn "  git -C docs/private remote add lab-host-2 ssh://<user>@<host-2>/<home>/<user>/Documents/.kb-cache/repos/notes-sync.git"
        Write-Warn "  git -C docs/private remote add lab-host-3 ssh://<user>@<host-3>/<home>/<user>/Documents/.kb-cache/repos/notes-sync.git"
    } else {
        foreach ($r in $labRemotes) {
            Write-Info "Pushing para $r ..."
            # Capture stderr (SSH MOTD) without piping - pipeline resets $LASTEXITCODE on Windows PS 5.1
            $out = git push $r main 2>&1
            $pushExit = $LASTEXITCODE
            $outPreview = $out | Select-Object -First 8
            if ($pushExit -eq 0) { Write-Ok "Push OK: $r" }
            else { Write-Warn "Push FALHOU: $r -- $outPreview" }
        }
    }
    # Bare mirror on VeraCrypt volume (Windows): probe Z: first (operator default), then Y: fallback; path name only (ADR 0040).
    foreach ($dl in @("Z", "Y")) {
        $driveRoot = "${dl}:\"
        if (-not (Test-Path -LiteralPath $driveRoot)) { continue }
        $bareWin = Join-Path $driveRoot "notes-sync.git"
        if (-not (Test-Path -LiteralPath $bareWin)) { continue }
        # VeraCrypt (and some FUSE stacks): receive-pack fsync on temp pack can fail with "Bad file descriptor".
        # core.fsync none applies only to this bare repo path (Git 2.41+). Idempotent.
        git -C $bareWin config core.fsync none 2>&1 | Out-Null
        $bareUri = "${dl}:/notes-sync.git"
        Write-Info "Push bare (VC): $bareUri ..."
        $pushOut = git push $bareUri main:main 2>&1 | Select-Object -First 12
        if ($LASTEXITCODE -ne 0) {
            $pushStr = "$pushOut"
            if ($pushStr -match "dubious ownership" -and $pushStr -match "safe\.directory") {
                $canon = ($bareWin -replace "\\", "/")
                Write-Warn "Git safe.directory: registering $canon (one-time helper)"
                git config --global --add safe.directory $canon 2>&1 | Out-Null
                $pushOut = git push $bareUri main:main 2>&1 | Select-Object -First 12
            }
            if ($LASTEXITCODE -eq 0) { Write-Ok "Push OK (VC bare): $bareUri" }
            else { Write-Warn "Push FALHOU (VC bare): $bareUri -- $pushOut" }
        }
        else {
            Write-Ok "Push OK (VC bare): $bareUri"
        }
    }
    # pCloud via robocopy (se P: montado)
    if (Test-Path "P:\") {
        $pcloudDest = "P:\lab-private-backup\notes-sync"
        if (-not (Test-Path $pcloudDest)) { New-Item -ItemType Directory -Path $pcloudDest -Force | Out-Null }
        robocopy $privateDir $pcloudDest /MIR /XD ".git" /NFL /NDL /NJH /NJS 2>&1 | Out-Null
        Write-Ok "pCloud sync OK: $pcloudDest"
    } else {
        Write-Info "pCloud (P:) nao montado -- pulando backup pCloud"
    }
    $ErrorActionPreference = $prevEapPush
}

Write-Header "private-git-sync: Concluido"
Set-Location $repoRoot