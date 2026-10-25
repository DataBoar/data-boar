#Requires -Version 5.1
<#
.SYNOPSIS
  Run scripts/homelab-host-report.sh on all LAB-OP hosts (via SSH) and save logs under docs/private/homelab/reports/.

.DESCRIPTION
  Runs from the operator dev PC (Windows). Hosts come from docs/private/homelab/lab-op-hosts.manifest.json.
  This wrapper is intentionally simpler than lab-op-sync-and-collect.ps1: it does not git pull; it only runs the report.

  Optional privileged mode runs the script with `--privileged` on the remote host, which enables best-effort `sudo -n` probes.

.EXAMPLE
  .\scripts\run-homelab-host-report-all.ps1

.EXAMPLE
  .\scripts\run-homelab-host-report-all.ps1 -Privileged

.EXAMPLE
  # Elevate this wrapper (optional) using gsudo if present:
  .\scripts\run-homelab-host-report-all.ps1 -UseGsudo
#>
param(
    [string] $ManifestPath = "",
    [string] $RepoRoot = "",
    [switch] $Privileged,
    [switch] $Deep,
    [switch] $UseGsudo
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = [Security.Principal.WindowsPrincipal]::new($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if ($UseGsudo -and -not (Test-IsAdmin)) {
    $gsudo = Get-Command gsudo -ErrorAction SilentlyContinue
    if (-not $gsudo) {
        throw "UseGsudo was requested but gsudo is not on PATH."
    }
    $args = @("-File", $PSCommandPath)
    if ($ManifestPath) { $args += @("-ManifestPath", $ManifestPath) }
    if ($RepoRoot) { $args += @("-RepoRoot", $RepoRoot) }
    if ($Privileged) { $args += @("-Privileged") }
    if ($Deep) { $args += @("-Deep") }
    # Avoid recursion loop.
    $args += @("-UseGsudo:$false")
    & $gsudo.Source @args
    exit $LASTEXITCODE
}

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
$fallbackManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.example.json"
if (-not $ManifestPath) {
    if (Test-Path -LiteralPath $primaryManifest) {
        $ManifestPath = $primaryManifest
    } elseif (Test-Path -LiteralPath $fallbackManifest) {
        $ManifestPath = $fallbackManifest
        Write-Warning "Using example manifest: $fallbackManifest (copy to lab-op-hosts.manifest.json when final)."
    }
}
if (-not $ManifestPath -or -not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: $primaryManifest"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json

$outDir = Join-Path $RepoRoot "docs\private\homelab\reports"
if ($manifest.outDir) {
    $outDir = $manifest.outDir -replace "/", [IO.Path]::DirectorySeparatorChar
    if (-not [IO.Path]::IsPathRooted($outDir)) {
        $outDir = Join-Path $RepoRoot $outDir
    }
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$remoteArgs = @()
if ($Privileged) { $remoteArgs += "--privileged" }
if ($Deep) { $remoteArgs += "--deep" }

foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }
    Write-Host "=== Host: $alias ===" -ForegroundColor Cyan

    $safe = ($alias -replace '[^\w\-\.]', '_')
    $outFile = Join-Path $outDir "${safe}_${stamp}_homelab_host_report.log"
    $errFile = Join-Path $env:TEMP "homelab-ssh-stderr-$safe-$stamp.txt"
    Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue

    # Remote: run the script content via stdin (no dependency on repo path on host).
    $scriptPath = Join-Path $RepoRoot "scripts\homelab-host-report.sh"
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        throw "Missing $scriptPath"
    }

    $argList = [System.Collections.ArrayList]@()
    [void]$argList.Add("-o"); [void]$argList.Add("BatchMode=yes")
    [void]$argList.Add("-o"); [void]$argList.Add("ConnectTimeout=15")
    [void]$argList.Add($alias)
    [void]$argList.Add("bash")
    [void]$argList.Add("-s")
    # Pass script arguments after '--' so bash doesn't treat them as its own options.
    [void]$argList.Add("--")
    foreach ($a in $remoteArgs) { [void]$argList.Add($a) }

    $p = Start-Process -FilePath "ssh" `
        -ArgumentList ($argList.ToArray()) `
        -RedirectStandardInput $scriptPath `
        -RedirectStandardOutput $outFile `
        -RedirectStandardError $errFile `
        -Wait -NoNewWindow -PassThru

    if ($p.ExitCode -ne 0) {
        if (Test-Path -LiteralPath $errFile) {
            Write-Warning (Get-Content -LiteralPath $errFile -Raw -ErrorAction SilentlyContinue)
        }
        Write-Warning "ssh exited with $($p.ExitCode) for $alias (skipping)."
        continue
    }
    Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
    Write-Host "Wrote $outFile" -ForegroundColor Green
}

Write-Host "Done. Logs in $outDir (redact before sharing)." -ForegroundColor DarkGray

