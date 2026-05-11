#Requires -Version 5.1
<#
.SYNOPSIS
    Print a minimal Cursor chat starter for lab completao (token + tier shorthand).

.DESCRIPTION
    Pairs with docs/ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md - line 1 must stay the
    English session token "completao" alone; line 2 is a tier:* shorthand so you
    rarely need the full LAB_COMPLETAO_FRESH_AGENT_BRIEF copy-paste blocks.

.PARAMETER Tier
    smoke | smoke-main | smoke-tag | followup-repo | followup-poc | followup-cli |
    closure-min | coverage-plus | evidence |
    release-master (use -ReleaseSemver; optional -GitTag) | release-master-v1-7-3 (frozen alias)

.PARAMETER LabGitRef
    Used when Tier is smoke-tag (e.g. v1.7.3) or to override smoke-main default.

.PARAMETER ReleaseSemver
    PEP 440-ish product version for Tier release-master (e.g. 1.7.3, 1.7.4-rc).
    Leading "v" is stripped for doc resolution. Implied 1.7.3 when Tier is release-master-v1-7-3.

.PARAMETER GitTag
    Git tag for lab alignment (e.g. v1.7.4). Default: v + ReleaseSemver after stripping a leading v.

.PARAMETER Clip
    Copy printed block to clipboard (Windows).

.EXAMPLE
    .\scripts\completao-chat-starter.ps1
    .\scripts\completao-chat-starter.ps1 -Tier followup-repo -Clip
    .\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver 1.7.4
    .\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver 1.7.2+safe -GitTag v1.7.2-safe
#>
param(
    [ValidateSet(
        "smoke",
        "smoke-main",
        "smoke-tag",
        "followup-repo",
        "followup-poc",
        "followup-cli",
        "closure-min",
        "coverage-plus",
        "evidence",
        "release-master",
        "release-master-v1-7-3"
    )]
    [string]$Tier = "smoke-main",

    [string]$LabGitRef = "",

    [string]$ReleaseSemver = "",

    [string]$GitTag = "",

    [switch]$Clip,

    [switch]$Help
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OpsDir = Join-Path $RepoRoot "docs/ops"

function Normalize-ReleaseSemver([string]$raw) {
    $t = $raw.Trim()
    if ($t -match '^[vV](.+)$') { return $matches[1].Trim() }
    return $t
}

function Resolve-DefaultGitTag([string]$semverNorm, [string]$explicit) {
    if ($explicit.Trim()) { return $explicit.Trim() }
    return "v$semverNorm"
}

function Resolve-ReleaseMasterDocBasename([string]$semverNorm) {
    $versioned = Join-Path $OpsDir "COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_$semverNorm.md"
    if (Test-Path -LiteralPath $versioned) {
        return "COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_$semverNorm.md"
    }
    return "COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md"
}

function Show-Help {
    @'
completao-chat-starter.ps1 - print minimal chat lines for lab completao (UTF-8 docs; this help is ASCII-only)

Tiers (line 2 after completao):
  smoke           -> tier:smoke  -> lab-completao-orchestrate.ps1 -Privileged
  smoke-main      -> tier:smoke-main (default) + -LabGitRef origin/main
  smoke-tag       -> tier:smoke-tag + -LabGitRef <tag> -SkipGitPullOnInventoryRefresh (pass -LabGitRef vX.Y.Z)
  followup-repo   -> tier:followup-repo -> lab-op-repo-status.ps1
  followup-poc    -> tier:followup-poc -> smoke-maturity + smoke-webauthn scripts
  followup-cli    -> tier:followup-cli -> LAB_EXTERNAL_CONNECTIVITY_EVAL
  closure-min     -> tier:closure-min -> close 3 minimum pending items (extra host CLI + API/dashboard + private lessons)
  coverage-plus   -> tier:coverage-plus -> expanded host/target matrix + severity map + rerun plan
  evidence        -> tier:evidence -> consolidate session notes
  release-master  -> tier:release-master + semver:/tag: lines -> read versioned COMPLETAO_MESTRE_* doc (requires -ReleaseSemver)
  release-master-v1-7-3 -> frozen alias for 1.7.3 (same docs as today)

Doc resolution (release-master): docs/ops/COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<ReleaseSemver>.md if present, else COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md (canonical fallback).

Docs: docs/ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md
'@
}

if ($Help) {
    Show-Help
    exit 0
}

$releaseMasterSemverNorm = ""
$releaseMasterGitTag = ""
$releaseMasterDocBase = ""

if ($Tier -eq "release-master-v1-7-3") {
    # Frozen shorthand for the first archived master prompt; optional -GitTag overrides orchestrator ref.
    $ReleaseSemver = "1.7.3"
    if (-not $GitTag.Trim()) {
        $GitTag = "v1.7.3"
    }
}

if ($Tier -eq "release-master") {
    if (-not $ReleaseSemver.Trim()) {
        Write-Error "Tier release-master requires -ReleaseSemver (e.g. -ReleaseSemver 1.7.4). Use -GitTag when the tag is not v<semver> (e.g. -GitTag v1.7.2-safe)."
    }
    $releaseMasterSemverNorm = Normalize-ReleaseSemver $ReleaseSemver
    $releaseMasterGitTag = Resolve-DefaultGitTag $releaseMasterSemverNorm $GitTag
    $releaseMasterDocBase = Resolve-ReleaseMasterDocBasename $releaseMasterSemverNorm
}

$line2 = switch ($Tier) {
    "smoke" { "tier:smoke" }
    "smoke-main" { "tier:smoke-main" }
    "smoke-tag" { "tier:smoke-tag" }
    "followup-repo" { "tier:followup-repo" }
    "followup-poc" { "tier:followup-poc" }
    "followup-cli" { "tier:followup-cli" }
    "closure-min" { "tier:closure-min" }
    "coverage-plus" { "tier:coverage-plus" }
    "evidence" { "tier:evidence" }
    "release-master" { "tier:release-master" }
    "release-master-v1-7-3" { "tier:release-master-v1-7-3" }
}

$extraTierLines = ""
if ($Tier -eq "release-master") {
    $extraTierLines = "semver:$releaseMasterSemverNorm`ntag:$releaseMasterGitTag"
}

$cmd = switch ($Tier) {
    "smoke" { ".\scripts\lab-completao-orchestrate.ps1 -Privileged" }
    "smoke-main" { ".\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main" }
    "smoke-tag" {
        if (-not $LabGitRef) {
            Write-Error "Tier smoke-tag requires -LabGitRef vX.Y.Z (e.g. -LabGitRef v1.7.3)"
        }
        ".\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef $LabGitRef -SkipGitPullOnInventoryRefresh"
    }
    "followup-repo" { ".\scripts\lab-op-repo-status.ps1" }
    "followup-poc" { ".\scripts\smoke-maturity-assessment-poc.ps1; .\scripts\smoke-webauthn-json.ps1" }
    "followup-cli" { "# Read docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md then run main.py with private config if present" }
    "closure-min" { "# Execute minimum closure: (1) soup CLI on >=1 extra host; (2) API/dashboard checks (/health + /); (3) update private session lessons under docs/private/homelab/" }
    "coverage-plus" { "# Execute expanded coverage matrix (FS/DB/API/connectors per host), classify failures by severity, and prepare rerun slice after fixes" }
    "evidence" { "# Consolidate session notes under docs/private/homelab/ per LAB_COMPLETAO_FRESH_AGENT_BRIEF block E" }
    "release-master" {
        $en = "docs/ops/$releaseMasterDocBase"
        $ptName = $releaseMasterDocBase -replace '\.md$', '.pt_BR.md'
        $ptPath = "docs/ops/$ptName"
        "# Read $en and $ptPath (EN is canonical; add the pt-BR pair when you archive a new release). Then .\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef $releaseMasterGitTag when applicable; never destructive git on primary Windows dev PC."
    }
    "release-master-v1-7-3" { "# Read docs/ops/COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md (policy notes + verbatim prompt). Then .\scripts\lab-completao-orchestrate.ps1 -Privileged when applicable; never destructive git on primary Windows dev PC." }
}

$middleLines = if ($extraTierLines) { "$line2`n$extraTierLines" } else { $line2 }

$block = @"
completao

$middleLines

# Suggested command (repo root):
$cmd
"@

Write-Host $block

if ($Clip) {
    Set-Clipboard -Value ($block.TrimEnd())
    Write-Host "`n( Copied to clipboard )" -ForegroundColor DarkGray
}
