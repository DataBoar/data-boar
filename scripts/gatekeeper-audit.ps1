#Requires -Version 5.1
<#
.SYNOPSIS
    Pre-push style gate: block staging when non-public PII seed literals appear in staged blobs.

.DESCRIPTION
    1. Load docs/private/security_audit/PII_LOCAL_SEEDS.txt (one fixed string per non-comment line).

    2. Drop seeds classified as public maintainer identity (operator policy): FabioLeitao,
       C:\Users\fabio (and c:/users/fabio), /home/leitao; those lines are not passed to git grep.

    3. Staged paths only: git diff --cached --name-only --diff-filter=ACMRT, then
       git grep -n -w -F -f <strict-seeds> --cached -- <paths> (word-boundary fixed strings
       from file; -w stops short seeds substring-colliding inside larger words -- issue #944).

    3b. Leaf names like uv.lock are still skipped (defense-in-depth): PyPI wheel/sdist URLs embed
        ISO8601 timestamps; -w already rejects those substring collisions, but machine-generated
        lock churn is irrelevant to PII review, so we skip it explicitly.

    4. Any remaining hit -> red error, exit 1.

    If nothing staged, or no strict seeds after filtering, exits 0. Missing seeds file -> skip (CI) unless -RequireSeeds.

.PARAMETER SeedsPath
    Override path to the seeds file (default: docs/private/security_audit/PII_LOCAL_SEEDS.txt).

.PARAMETER RequireSeeds
    If set, fail when the seeds file is missing instead of skipping.

.EXAMPLE
    .\scripts\gatekeeper-audit.ps1
    .\scripts\gatekeeper-audit.ps1 -RequireSeeds
#>
param(
    [string] $SeedsPath = "",
    [switch] $RequireSeeds
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if (-not $SeedsPath) {
    $SeedsPath = Join-Path $repoRoot "docs\private\security_audit\PII_LOCAL_SEEDS.txt"
}
elseif (-not [System.IO.Path]::IsPathRooted($SeedsPath)) {
    $SeedsPath = Join-Path $repoRoot $SeedsPath
}

function Write-GateFail($msg) {
    Write-Host "GATEKEEPER-AUDIT: $msg" -ForegroundColor Red
}

function Write-GateSkip($msg) {
    Write-Host "GATEKEEPER-AUDIT: $msg" -ForegroundColor Yellow
}

function Test-PublicIdentitySeedExcluded([string] $seed) {
    $t = $seed.Trim()
    if ($t.Length -eq 0) { return $true }
    $lower = $t.ToLowerInvariant()
    # Whole-line identity tokens (public maintainer / lab path anchors - excluded from strict scan).
    if ($lower -eq "fabioleitao") { return $true }

    $pathish = $lower -replace '/', '\'
    if ($pathish -eq 'c:\users\fabio' -or $pathish -eq 'c:\users\fabio\') { return $true }

    if ($lower -eq '/home/leitao' -or $lower -eq '/home/leitao/') { return $true }
    if ($pathish -eq '\home\leitao' -or $pathish -eq '\home\leitao\') { return $true }

    return $false
}

function Get-PiiGateAllowlist([string] $root) {
    # Operator-approved per-location FP exceptions (issue #944, ADR-0071).
    # Active line format: <repo-relative-path>|<seed>|<reason>
    $allowPath = Join-Path $root "security\pii_gate_allowlist.txt"
    $entries = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $allowPath)) { return $entries }
    foreach ($raw in (Get-Content -LiteralPath $allowPath -Encoding UTF8)) {
        $t = $raw.Trim()
        if ($t.Length -eq 0 -or $t.StartsWith("#")) { continue }
        $parts = $t -split '\|'
        if ($parts.Count -lt 2) { continue }
        $rel = ($parts[0]).Trim().Replace('\', '/')
        $seed = ($parts[1]).Trim()
        if ($rel -and $seed) {
            $entries.Add([pscustomobject]@{ Path = $rel; Seed = $seed }) | Out-Null
        }
    }
    return $entries
}

function Test-LineFullyAllowlisted([string] $line, $strictSeeds, $allowlist) {
    # Parse "path:line:content"; suppress only if EVERY matched seed is allowlisted for that path.
    # Fail-safe: unparsable line or no identifiable seed -> not suppressed.
    $m = [regex]::Match($line, '^(.*?):(\d+):(.*)$')
    if (-not $m.Success) { return $false }
    $path = $m.Groups[1].Value.Replace('\', '/')
    $content = $m.Groups[3].Value
    $allowedHere = @($allowlist | Where-Object { $_.Path -eq $path } | ForEach-Object { $_.Seed })
    $matched = @()
    foreach ($seed in $strictSeeds) {
        $pat = "(?<!\w)" + [regex]::Escape($seed) + "(?!\w)"
        if ([regex]::IsMatch($content, $pat)) { $matched += $seed }
    }
    if ($matched.Count -eq 0) { return $false }
    foreach ($seed in $matched) {
        if ($allowedHere -notcontains $seed) { return $false }
    }
    return $true
}

if (-not (Test-Path -LiteralPath $SeedsPath)) {
    if ($RequireSeeds) {
        Write-GateFail "Seeds file required but missing: $SeedsPath"
        Write-GateFail "Copy from docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt"
        exit 1
    }
    Write-GateSkip "SKIP (no seeds file). Not an error - enable by copying PII_LOCAL_SEEDS.example.txt to docs/private/security_audit/PII_LOCAL_SEEDS.txt"
    exit 0
}

$lines = Get-Content -LiteralPath $SeedsPath -Encoding UTF8
$allSeeds = New-Object System.Collections.Generic.List[string]
foreach ($raw in $lines) {
    $t = $raw.Trim()
    if ($t.Length -eq 0) { continue }
    if ($t.StartsWith("#")) { continue }
    $allSeeds.Add($t) | Out-Null
}

if ($allSeeds.Count -eq 0) {
    Write-GateSkip "No active seed lines (only comments/blank). Nothing to scan."
    exit 0
}

$strictSeeds = New-Object System.Collections.Generic.List[string]
$skippedPublic = 0
foreach ($s in $allSeeds) {
    if (Test-PublicIdentitySeedExcluded $s) {
        $skippedPublic++
        continue
    }
    $strictSeeds.Add($s) | Out-Null
}

Write-Host "=== gatekeeper-audit: PII seeds vs staged paths (--cached, strict seeds only) ===" -ForegroundColor Cyan
Write-Host "  Seeds file: $SeedsPath ($($allSeeds.Count) active; $($strictSeeds.Count) after public-identity filter)" -ForegroundColor Gray
if ($skippedPublic -gt 0) {
    Write-Host "  Public-identity seeds excluded from scan: $skippedPublic (FabioLeitao, C:\Users\fabio, /home/leitao)" -ForegroundColor DarkGray
}

if ($strictSeeds.Count -eq 0) {
    Write-Host "GATEKEEPER-AUDIT: OK (no strict seeds to scan)." -ForegroundColor Green
    exit 0
}

$allowlist = Get-PiiGateAllowlist $repoRoot
if ($allowlist.Count -gt 0) {
    Write-Host "  Sanctioned FP allowlist: $($allowlist.Count) entr(y/ies) from security/pii_gate_allowlist.txt (operator-approved, per-location)." -ForegroundColor DarkGray
}

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$stagedOut = git -C $repoRoot diff --cached --name-only --diff-filter=ACMRT 2>&1
$ErrorActionPreference = $prevEap
if ($LASTEXITCODE -ne 0) {
    Write-GateFail "git diff --cached --name-only failed: $stagedOut"
    exit 2
}

$excludeLeaves = New-Object "System.Collections.Generic.HashSet[string]" ([StringComparer]::OrdinalIgnoreCase)
[void]$excludeLeaves.Add("uv.lock")

$allStaged = @(
    $stagedOut | ForEach-Object { $_.Trim() } | Where-Object { $_.Length -gt 0 }
)
if ($allStaged.Count -eq 0) {
    Write-Host "GATEKEEPER-AUDIT: OK (nothing staged; no paths to scan)." -ForegroundColor Green
    exit 0
}

$skippedLock = 0
$paths = New-Object System.Collections.Generic.List[string]
foreach ($p in $allStaged) {
    $leaf = Split-Path -Leaf $p
    if ($excludeLeaves.Contains($leaf)) {
        $skippedLock++
        continue
    }
    $paths.Add($p) | Out-Null
}
if ($skippedLock -gt 0) {
    Write-Host "  Skipped seed scan for $skippedLock path(s) (machine-generated: uv.lock)." -ForegroundColor DarkGray
}

if ($paths.Count -eq 0) {
    Write-Host "GATEKEEPER-AUDIT: OK (only machine-generated paths staged; nothing left to scan)." -ForegroundColor Green
    exit 0
}

Write-Host "  Staged path(s) scanned: $($paths.Count) (of $($allStaged.Count) total staged)" -ForegroundColor Gray

$tmp = [System.IO.Path]::GetTempFileName()
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($tmp, [string[]]$strictSeeds.ToArray(), $utf8NoBom)

    $batchSize = 60
    for ($i = 0; $i -lt $paths.Count; $i += $batchSize) {
        $end = [Math]::Min($i + $batchSize, $paths.Count) - 1
        $chunk = $paths[$i..$end]
        $ErrorActionPreference = "Continue"
        # -n -w -F -f: line numbers, word-boundary, fixed-string patterns from file.
        # -w (word-boundary) makes a short seed match only when delimited by non-word
        # chars, so it never substring-collides with a larger word (issue #944);
        # sensitivity is preserved for whole-word / full-string seeds. Twin of
        # scripts/gatekeeper_audit.py. Pair with distinctive seeds, never fragments.
        $grepArgs = @("-C", $repoRoot, "grep", "-n", "-w", "-F", "-f", $tmp, "--cached", "--") + $chunk
        $out = & git @grepArgs 2>&1
        $ErrorActionPreference = $prevEap
        $text = if ($null -eq $out) { "" } else { ($out | Out-String).TrimEnd() }
        $code = $LASTEXITCODE

        if ($code -eq 0) {
            if ($text.Length -gt 0) {
                $kept = @()
                foreach ($ln in ($text -split "`n")) {
                    if ($ln.Trim().Length -eq 0) { continue }
                    if (Test-LineFullyAllowlisted $ln $strictSeeds $allowlist) { continue }
                    $kept += $ln
                }
                if ($kept.Count -gt 0) {
                    Write-GateFail "HIT - staged content matches a strict PII seed (not public-identity allowlist):"
                    Write-Host ($kept -join "`n") -ForegroundColor Red
                    Write-GateFail "ABORT: redact or unstage before commit/push."
                    exit 1
                }
            }
        }
        elseif ($code -eq 1) {
            if ($text.Length -gt 0) {
                Write-GateFail "Unexpected output with exit 1: $text"
                exit 2
            }
        }
        else {
            Write-GateFail "git grep failed (exit $code): $text"
            exit 2
        }
    }
}
finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "GATEKEEPER-AUDIT: OK (no strict seed hits in staged paths)." -ForegroundColor Green
exit 0
