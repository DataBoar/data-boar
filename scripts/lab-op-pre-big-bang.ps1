#Requires -Version 5.1
<#
.SYNOPSIS
  Pre-Big-Bang gate: align LAB-OP git clones to a ref (check or reset), optional read-only network/deps probes, operator checklist for firewall/AppArmor/fail2ban.

.DESCRIPTION
  Runs ONLY against hosts and repoPaths in docs/private/homelab/lab-op-hosts.manifest.json (same contract as
  lab-op-git-ensure-ref.ps1). Never touches the operator canonical Windows/WSL2 clone in this repo root.

  1) Git: invokes lab-op-git-ensure-ref.ps1 with -Ref (default origin/main). Use -ForceLabGitReset for -Mode Reset
     (destructive on LAB clones only: checkout tag or hard reset to origin/main tip).
  2) When -Ref looks like a release tag (vX.Y.Z), optionally runs lab-completao-inventory-preflight.ps1 with
     -SkipGitPullOnRefresh so a stale inventory refresh does not git pull clones to main before the tag pin.
  3) -IncludeProbes: per-host SSH read-only snippets (ufw/fail2ban where unprivileged; sudo -n best-effort),
     git dirty line count on first repoPath, and on LAB-NODE-03 / LAB-NODE-04 hosts a compression/stdlib smoke via python3.
  4) Emits a non-executable firewall / NFS / SMB / fail2ban checklist into the same report log for operator
     application in tmux after sudo -v (lab targets only; primary Windows dev PC is out of scope for remote writes).

  "Git Synced" in logs: LABOP_REF_OK / reset output from lab-op-git-ensure-ref plus LABOP_BB_GIT_* probe lines.
  "Firewall Clear" is NOT asserted by this script; operator confirms after applying narrow rules; log contains
  LABOP_BB_OPERATOR_FIREWALL_CLEAR_PENDING and ignoreip guidance for the orchestration PC.

.EXAMPLE
  .\scripts\lab-op-pre-big-bang.ps1 -Ref v1.7.3 -ForceLabGitReset -IncludeProbes

.EXAMPLE
  Check only (no reset on LAB clones):
  .\scripts\lab-op-pre-big-bang.ps1 -Ref origin/main -IncludeProbes
#>
param(
    [string] $Ref = "origin/main",
    [switch] $ForceLabGitReset,
    [string] $ManifestPath = "",
    [string] $RepoRoot = "",
    [switch] $SkipFping,
    [switch] $IncludeProbes,
    [switch] $SkipInventoryWarmup,
    [string] $OrchestratorSshSourceIp = "",
    [string] $LabOpCidrsExample = "10.0.0.0/24 10.0.1.0/24"
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}

$gitMode = if ($ForceLabGitReset) { "Reset" } else { "Check" }
$ensureScript = Join-Path $RepoRoot "scripts\lab-op-git-ensure-ref.ps1"
if (-not (Test-Path -LiteralPath $ensureScript)) {
    throw "Missing $ensureScript"
}

$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
if (-not $ManifestPath) {
    $ManifestPath = $primaryManifest
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $ManifestPath - copy docs/private.example/homelab/lab-op-hosts.manifest.example.json"
}

$outDir = Join-Path $RepoRoot "docs\private\homelab\reports"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$summaryFile = Join-Path $outDir "lab_op_pre_big_bang_${stamp}.log"

function Escape-BashSingleQuoted {
    param([string]$S)
    return ($S -replace "'", "'\''")
}

$sb = [System.Text.StringBuilder]::new()
[void]$sb.AppendLine("=== lab-op-pre-big-bang $stamp ===")
[void]$sb.AppendLine("Ref=$Ref GitMode=$gitMode ForceLabGitReset=$ForceLabGitReset IncludeProbes=$IncludeProbes")
[void]$sb.AppendLine("Primary Windows dev PC: this script does not modify the canonical clone at $RepoRoot (LAB-OP manifest paths only).")
[void]$sb.AppendLine("")

$tagLike = $Ref -match '^v\d+\.\d+\.\d+'
if (-not $SkipInventoryWarmup -and $tagLike) {
    $preflight = Join-Path $RepoRoot "scripts\lab-completao-inventory-preflight.ps1"
    if (Test-Path -LiteralPath $preflight) {
        [void]$sb.AppendLine("--- inventory preflight (SkipGitPullOnRefresh for tag pin) ---")
        Write-Host "Running inventory preflight with -SkipGitPullOnRefresh (tag-like Ref)." -ForegroundColor Cyan
        & $preflight -RepoRoot $RepoRoot -ManifestPath $ManifestPath -AutoRefresh -SkipFping:$SkipFping -SkipGitPullOnRefresh
        if ($LASTEXITCODE -ne 0) {
            [void]$sb.AppendLine("inventory preflight exit=$LASTEXITCODE (see script output above)")
        }
        [void]$sb.AppendLine("")
    }
} elseif ($tagLike) {
    [void]$sb.AppendLine("(skipped inventory preflight: -SkipInventoryWarmup)")
    [void]$sb.AppendLine("")
}

Write-Host "lab-op-pre-big-bang: lab-op-git-ensure-ref -Ref $Ref -Mode $gitMode" -ForegroundColor Cyan
$ensureTmp = [IO.Path]::GetTempFileName()
try {
    & $ensureScript -Ref $Ref -Mode $gitMode -ManifestPath $ManifestPath -RepoRoot $RepoRoot -SkipFping:$SkipFping > $ensureTmp 2>&1
    $ensureExit = $LASTEXITCODE
    $ensureLog = Get-Content -LiteralPath $ensureTmp -Raw -Encoding utf8
} finally {
    Remove-Item -LiteralPath $ensureTmp -Force -ErrorAction SilentlyContinue
}
Write-Host $ensureLog
[void]$sb.AppendLine("--- lab-op-git-ensure-ref ---")
[void]$sb.AppendLine($ensureLog)
if ($ensureExit -ne 0) {
    [void]$sb.AppendLine("LABOP_BB_GIT_GATE_FAIL ensure-ref exit=$ensureExit")
    Set-Content -LiteralPath $summaryFile -Value $sb.ToString() -Encoding utf8
    Write-Host "Wrote $summaryFile" -ForegroundColor Yellow
    Write-Host "Pre-Big-Bang stopped: fix git alignment or re-run with -ForceLabGitReset when appropriate." -ForegroundColor Red
    exit $ensureExit
}

[void]$sb.AppendLine("LABOP_BB_GIT_ENSURE_REF_OK")
[void]$sb.AppendLine("")

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json

[void]$sb.AppendLine("=== OPERATOR_CHECKLIST (non-destructive; apply on LAB hosts via tmux after sudo -v) ===")
[void]$sb.AppendLine("LABOP_BB_OPERATOR_FIREWALL_CLEAR_PENDING")
[void]$sb.AppendLine("A) Between LAB-OP nodes only, allow TCP 5432 (Postgres), 3306 (MariaDB), NFS (111/tcpudp, 2049/tcp, 20048/tcp as used), SMB (445/tcp) on paths $LabOpCidrsExample - adapt to your LAN.")
[void]$sb.AppendLine("B) ufw example (on each Linux host, adjust from/to): allow from <peer>/32 to any port 5432 proto tcp")
[void]$sb.AppendLine("C) nftables: add accept rules in inet filter INPUT chain for lab source IPs to dports 5432,3306,2049,445 - keep default deny.")
[void]$sb.AppendLine("D) AppArmor/SELinux: if scans hit Permission denied on /var/log or mounts, check auditd/ausearch; consider complain mode ONLY for the Data Boar binary profile (revert after test).")
[void]$sb.AppendLine("E) fail2ban / sshguard: add orchestrator dev PC SSH source to ignoreip / whitelist for sshd jail during orchestration bursts.")
if ($OrchestratorSshSourceIp) {
    [void]$sb.AppendLine("   Suggested ignoreip addition includes: $OrchestratorSshSourceIp")
} else {
    [void]$sb.AppendLine("   Pass -OrchestratorSshSourceIp <dev-pc-lan-ip> next run to embed a concrete ignoreip hint.")
}
[void]$sb.AppendLine("F) LAB-NODE-03 Void: sudo xbps-install -S libmariadbclient-devel pkg-config if mysqlclient wheels fail; keep heavy DB work on LAB-NODE-02/LAB-NODE-01.")
[void]$sb.AppendLine("")

if (-not $IncludeProbes) {
    [void]$sb.AppendLine("Probes skipped (-IncludeProbes not set). Re-run with -IncludeProbes after network clearance.")
    Set-Content -LiteralPath $summaryFile -Value $sb.ToString() -Encoding utf8
    Write-Host "Wrote $summaryFile" -ForegroundColor Green
    Write-Host "Done. Git gate OK. Operator must confirm firewall checklist before declaring LABOP_BB_FIREWALL_CLEAR." -ForegroundColor Cyan
    exit 0
}

foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }

    $firstRp = $null
    foreach ($rp in $h.repoPaths) {
        if ($rp) {
            $firstRp = $rp
            break
        }
    }
    if (-not $firstRp) {
        [void]$sb.AppendLine("### $alias ### SKIP_PROBE no repoPaths")
        continue
    }

    $rpEsc = Escape-BashSingleQuoted -S $firstRp
    $depBlock = ""
    if ($alias -match "LAB-NODE-03|minibt|LAB-NODE-04") {
        $depBlock = 'echo "--- deps ---"; if command -v xbps-query >/dev/null 2>&1; then xbps-query -l 2>/dev/null | grep -iE "zlib|bzip|xz|lzma" | head -n 18 || true; fi; if command -v dpkg >/dev/null 2>&1; then dpkg -l 2>/dev/null | grep -iE "zlib1g|libbz2|liblzma" | head -n 18 || true; fi; if command -v python3 >/dev/null 2>&1; then python3 -c "import zlib,bz2,lzma; print(' + "'LABOP_PY_COMPRESSION_OK'" + ')" 2>&1 || echo LABOP_PY_COMPRESSION_FAIL; else echo LABOP_PY_SKIP; fi; '
    }

    $bashHead = 'echo LABOP_BB_HOST=$(hostname -s 2>/dev/null || hostname); '
    $bashMidA = 'if [ -d '''
    $bashMidB = ''' ]; then cd '''
    $bashMidC = ''' && echo LABOP_BB_GIT_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo none) && echo LABOP_BB_GIT_DIRTY=$(git status --porcelain 2>/dev/null | wc -l); else echo LABOP_BB_NO_REPO_DIR; fi; '
    $bashTail = 'echo ---listeners---; command -v ss >/dev/null 2>&1 && ss -tlnp 2>/dev/null | grep -E ":5432|:3306" || echo no_match_or_no_ss; echo ---ufw---; if command -v ufw >/dev/null 2>&1; then ufw status numbered 2>/dev/null | head -n 35 || ufw status 2>/dev/null | head -n 35; else echo ufw_absent; fi; echo ---fail2ban---; sudo -n fail2ban-client status 2>/dev/null || fail2ban-client status 2>/dev/null || echo fail2ban_need_sudo_or_absent; echo ---sshguard---; command -v sshguard >/dev/null 2>&1 && (pgrep -a sshguard 2>/dev/null || echo sshguard_process_unknown) || echo sshguard_absent; '
    $remoteInner = $bashHead + $bashMidA + $rpEsc + $bashMidB + $rpEsc + $bashMidC + $bashTail + $depBlock + 'echo LABOP_BB_PROBE_END'
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("### PROBE $alias ###")
    Write-Host "Probe: $alias" -ForegroundColor Cyan
    try {
        $pout = & ssh.exe -o BatchMode=yes -o ConnectTimeout=120 $alias $remoteInner 2>&1 | Out-String
        $pex = $LASTEXITCODE
        [void]$sb.AppendLine($pout)
        [void]$sb.AppendLine("exit=$pex")
    } catch {
        [void]$sb.AppendLine("PROBE_EXCEPTION: $($_.Exception.Message)")
    }
}

[void]$sb.AppendLine("")
[void]$sb.AppendLine("=== END ===")
[void]$sb.AppendLine("When operator has applied firewall + fail2ban safeguards, record LABOP_BB_FIREWALL_CLEAR in private session notes (this script does not auto-detect clearance).")

Set-Content -LiteralPath $summaryFile -Value $sb.ToString() -Encoding utf8
Write-Host "Wrote $summaryFile" -ForegroundColor Green
Write-Host "Pre-Big-Bang: git gate OK; probes captured. Confirm checklist + logs before Big Bang." -ForegroundColor Green
exit 0
