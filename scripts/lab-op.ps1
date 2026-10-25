#Requires -Version 5.1
<#
.SYNOPSIS
  LAB-OP shorthand wrapper (safe defaults).

.DESCRIPTION
  Provides a stable, memorable taxonomy of LAB-OP actions:
  - report (single host)
  - report-all (all hosts from manifest)
  - sync-collect (git pull + report via manifest)

  This is a wrapper only; it delegates to existing scripts and keeps guardrails:
  - privileged probes are opt-in
  - deep probes are opt-in

.EXAMPLE
  .\scripts\lab-op.ps1 -Action report -SshHost lab-op

.EXAMPLE
  .\scripts\lab-op.ps1 -Action report-all -Privileged -Deep

.EXAMPLE
  .\scripts\lab-op.ps1 -Action sync-collect -SkipFping
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("report", "report-all", "sync-collect")]
    [string] $Action,

    [string] $SshHost = "",
    [switch] $Privileged,
    [switch] $Deep,
    [switch] $UseGsudo,
    [switch] $SkipFping,
    [switch] $SkipGitPull,
    [string] $ManifestPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

switch ($Action) {
    "report" {
        if (-not $SshHost) { throw "Action=report requires -SshHost" }
        $params = @{ SshHost = $SshHost }
        # collect-homelab-report-remote.ps1 does not yet support privileged flags; prefer report-all for that.
        & (Join-Path $repoRoot "scripts\collect-homelab-report-remote.ps1") @params
    }
    "report-all" {
        $params = @{}
        if ($ManifestPath) { $params.ManifestPath = $ManifestPath }
        if ($Privileged) { $params.Privileged = $true }
        if ($Deep) { $params.Deep = $true }
        if ($UseGsudo) { $params.UseGsudo = $true }
        & (Join-Path $repoRoot "scripts\run-homelab-host-report-all.ps1") @params
    }
    "sync-collect" {
        $params = @{}
        if ($ManifestPath) { $params.ManifestPath = $ManifestPath }
        if ($SkipFping) { $params.SkipFping = $true }
        if ($SkipGitPull) { $params.SkipGitPull = $true }
        & (Join-Path $repoRoot "scripts\lab-op-sync-and-collect.ps1") @params
    }
}

