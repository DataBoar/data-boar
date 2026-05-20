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
    Se informado, faz push para os remotes lab-* em docs/private/.git, push bare notes-sync.git em Z: ou Y: (VeraCrypt),
    copia homelab secrets para Z:\working\homelab (nunca para P:), e robocopy limitado para P: se montado.

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

# Homelab leaf names: VeraCrypt working/homelab only; excluded from pCloud robocopy (no secrets in sync cloud).
$Script:HomelabSecretLeafNames = @(".env.bitwarden.local")

function Get-VeraCryptDriveLetter {
    foreach ($dl in @("Z", "Y")) {
        if (Test-Path -LiteralPath "${dl}:\") { return $dl }
    }
    return $null
}

function Sync-VeraCryptHomelabSecrets {
    param(
        [string]$PrivateDirRoot
    )
    $homelabSrc = Join-Path $PrivateDirRoot "homelab"
    if (-not (Test-Path -LiteralPath $homelabSrc)) {
        Write-Info "VC homelab secrets: pasta homelab ausente -- pulando"
        return
    }
    $dl = Get-VeraCryptDriveLetter
    if (-not $dl) {
        Write-Info "VC homelab secrets: Z:/Y: nao montado -- pulando"
        return
    }
    $vcHomelab = Join-Path "${dl}:\" "working\homelab"
    $vcWorking = Join-Path "${dl}:\" "working"
    if (-not (Test-Path -LiteralPath $vcWorking)) {
        Write-Warn "VC homelab secrets: ${dl}:\working ausente -- pulando"
        return
    }
    if (-not (Test-Path -LiteralPath $vcHomelab)) {
        New-Item -ItemType Directory -Path $vcHomelab -Force | Out-Null
        Write-Info "VC homelab secrets: criado ${dl}:\working\homelab"
    }
    foreach ($leaf in $Script:HomelabSecretLeafNames) {
        $src = Join-Path $homelabSrc $leaf
        if (-not (Test-Path -LiteralPath $src)) {
            Write-Info "VC homelab secrets: ausente em homelab\$leaf"
            continue
        }
        $dst = Join-Path $vcHomelab $leaf
        try {
            Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
            $hSrc = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
            $hDst = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
            if ($hSrc -eq $hDst) {
                Write-Ok "VC homelab secrets: ${dl}:\working\homelab\$leaf"
            } else {
                Write-Warn "VC homelab secrets: hash diverge apos copia ($leaf)"
            }
        } catch {
            Write-Warn "VC homelab secrets: FALHOU homelab\$leaf -- $($_.Exception.Message)"
        }
    }
}

function Invoke-PCloudPrivateTreeMirror {
    param(
        [string]$SourceDir,
        [string]$DestDir
    )
    if (-not (Test-Path "P:\")) {
        Write-Info "pCloud (P:) nao montado -- pulando backup pCloud"
        return $true
    }
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }
    $robArgs = @(
        $SourceDir, $DestDir,
        "/MIR", "/XD", ".git",
        "/R:2", "/W:5",
        "/NFL", "/NDL", "/NJH", "/NJS"
    )
    foreach ($leaf in $Script:HomelabSecretLeafNames) {
        $robArgs += "/XF"
        $robArgs += $leaf
    }
    Write-Info "pCloud robocopy (sem secrets homelab listados em /XF) ..."
    & robocopy @robArgs | Out-Null
    $rc = $LASTEXITCODE
    # Robocopy: 0-7 = success with possible extras; >= 8 = hard failure
    if ($rc -ge 8) {
        Write-Warn "pCloud robocopy FALHOU (exit=$rc): $DestDir"
        return $false
    }
    if ($rc -ge 2) {
        Write-Ok "pCloud sync OK (exit=$rc, extras/removidos): $DestDir"
    } else {
        Write-Ok "pCloud sync OK: $DestDir"
    }
    return $true
}

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

# --- 4. Push e espelhos (opcional) ---
if ($Push) {
    $prevEapPush = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $pushHadFailure = $false

    Write-Header "Passo 3: Push para todos os lab remotes"
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
            else {
                Write-Warn "Push FALHOU: $r -- $outPreview"
                $pushHadFailure = $true
            }
        }
    }

    Write-Header "Passo 4: Push bare notes-sync.git (VeraCrypt Z: ou Y:)"
    $vcBareOk = $false
    foreach ($dl in @("Z", "Y")) {
        $driveRoot = "${dl}:\"
        if (-not (Test-Path -LiteralPath $driveRoot)) { continue }
        $bareWin = Join-Path $driveRoot "notes-sync.git"
        if (-not (Test-Path -LiteralPath $bareWin)) { continue }
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
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Push OK (VC bare): $bareUri"
                $vcBareOk = $true
            } else {
                Write-Warn "Push FALHOU (VC bare): $bareUri -- $pushOut"
                $pushHadFailure = $true
            }
        } else {
            Write-Ok "Push OK (VC bare): $bareUri"
            $vcBareOk = $true
        }
        if ($vcBareOk) { break }
    }
    if (-not $vcBareOk) {
        Write-Info "VC bare: nenhum notes-sync.git em Z:/Y: -- pulando"
    }

    Write-Header "Passo 5: Homelab secrets no VeraCrypt working/ (nunca pCloud)"
    Sync-VeraCryptHomelabSecrets -PrivateDirRoot $privateDir

    Write-Header "Passo 6: Espelho pCloud (P:) -- sem secrets homelab em /XF"
    $pcloudDest = "P:\lab-private-backup\notes-sync"
    if (-not (Invoke-PCloudPrivateTreeMirror -SourceDir $privateDir -DestDir $pcloudDest)) {
        $pushHadFailure = $true
    }

    $ErrorActionPreference = $prevEapPush
    if ($pushHadFailure) {
        Write-Warn "private-git-sync: concluido com avisos/falhas em push ou pCloud"
    }
}

Write-Header "private-git-sync: Concluido"
Set-Location $repoRoot