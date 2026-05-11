#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro-deep-rc-monitor-collect.ps1

.SYNOPSIS
 Token-aware wrapper: Maestro -Deep, optional lab status monitor loop, Maestro -Collect.

.DESCRIPTION
 Runs from repo root (or -ProjectRoot). Requires private inventory at
 docs/private/homelab/data/inventory.json (same contract as Maestro.ps1).

 Pre-flight image/tar build inside Maestro still uses local docker when the tarball
 is missing or stale; start Docker Desktop on Windows when you need that path.

.EXAMPLE
 .\scripts\maestro-deep-rc-monitor-collect.ps1

.EXAMPLE
 .\scripts\maestro-deep-rc-monitor-collect.ps1 -IntendedLoops 10 -MonitorIntervalSeconds 30

.EXAMPLE
 .\scripts\maestro-deep-rc-monitor-collect.ps1 -SkipMonitor -SkipCollect
#>

param(
    [ValidateRange(0, 9999)]
    [int]$IntendedLoops = 15,

    [ValidateRange(0, 3600)]
    [int]$MonitorIntervalSeconds = 20,

    [ValidateRange(0, 600)]
    [int]$PostDeepSleepSeconds = 5,

    [string]$Ref = "WorkingTree",

    [string]$ProjectRoot = "",

    [switch]$SkipMonitor,

    [switch]$SkipCollect,

    [switch]$ClearHostEachLoop,

    [switch]$SkipDockerPrecheck,

    [string]$HealthUrl = "",

    [ValidateSet("skip", "warn", "fail")]
    [string]$WebReadinessMode = "skip",

    [ValidateRange(1, 120)]
    [int]$HealthTimeoutSeconds = 5
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"

function Get-WorstExitCode {
    param([int]$Current, [int]$Candidate)
    if ($null -eq $Candidate) { return $Current }
    if ($Candidate -gt $Current) { return $Candidate }
    return $Current
}

function Test-DockerEngineReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $false
    }

    $null = docker info --format '{{.ServerVersion}}' 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Get-VersionTagFromPyproject {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PyprojectPath
    )
    $tag = "latest"
    if (Test-Path -LiteralPath $PyprojectPath) {
        $versionMatch = Get-Content -LiteralPath $PyprojectPath | Select-String -Pattern '^version\s*=\s*"([^"]+)"'
        if ($versionMatch -match '^version\s*=\s*"([^"]+)"') {
            $tag = $matches[1]
        }
    }
    return $tag
}

function Test-WebReadiness {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [int]$TimeoutSeconds
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSeconds -UseBasicParsing
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    } catch {
        return $false
    }
}

$repoRoot = if ($ProjectRoot) {
    (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

$maestro = Join-Path $repoRoot "scripts\maestro\Maestro.ps1"
$getLabStatus = Join-Path $repoRoot "scripts\maestro\Get-LabStatus.ps1"
$inventoryPath = Join-Path $repoRoot "docs\private\homelab\data\inventory.json"
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"
$tarTag = Get-VersionTagFromPyproject -PyprojectPath $pyprojectPath
$tarPath = Join-Path $repoRoot ("data-boar-{0}.tar" -f $tarTag)

if (-not (Test-Path -LiteralPath $maestro)) {
    Write-Error "Maestro.ps1 not found: $maestro"
    exit 2
}
if (-not (Test-Path -LiteralPath $getLabStatus)) {
    Write-Error "Get-LabStatus.ps1 not found: $getLabStatus"
    exit 2
}
if (-not (Test-Path -LiteralPath $inventoryPath)) {
    Write-Error "inventory.json not found: $inventoryPath"
    exit 2
}

$worst = 0

Push-Location -LiteralPath $repoRoot
try {
    if (-not $SkipDockerPrecheck) {
        if (-not (Test-DockerEngineReady)) {
            if (Test-Path -LiteralPath $tarPath) {
                $tarAge = (Get-Date) - (Get-Item -LiteralPath $tarPath).LastWriteTime
                Write-Warning ("Docker indisponivel; seguindo com fallback via {0} ({1:N1}h). Build local sera pulado." -f (Split-Path -Leaf $tarPath), $tarAge.TotalHours)
            } else {
                Write-Error ("Docker indisponivel e fallback ausente ({0}). Start Docker Desktop or provide tar cache." -f (Split-Path -Leaf $tarPath))
                exit 4
            }
        } else {
            Write-Host "[Precheck] Docker engine reachable." -ForegroundColor DarkGray
        }
    }

    Write-Host "--- [Phase 1] Maestro Deep (RC-style) ---" -ForegroundColor Magenta
    & $maestro -Ref $Ref -Deep
    $worst = Get-WorstExitCode -Current $worst -Candidate $LASTEXITCODE

    if ($PostDeepSleepSeconds -gt 0) {
        Start-Sleep -Seconds $PostDeepSleepSeconds
    }

    if (-not $SkipMonitor) {
        if ($WebReadinessMode -ne "skip" -and $HealthUrl) {
            $webReady = Test-WebReadiness -Url $HealthUrl -TimeoutSeconds $HealthTimeoutSeconds
            if ($webReady) {
                Write-Host ("[Precheck] Web readiness OK: {0}" -f $HealthUrl) -ForegroundColor DarkGray
            } elseif ($WebReadinessMode -eq "fail") {
                Write-Error ("Web readiness failed for {0}. Use -WebReadinessMode warn to continue on warning." -f $HealthUrl)
                exit 5
            } else {
                Write-Warning ("Web readiness failed for {0}. Continuing due to -WebReadinessMode warn." -f $HealthUrl)
            }
        } elseif ($WebReadinessMode -ne "skip" -and -not $HealthUrl) {
            Write-Warning "Web readiness requested but -HealthUrl is empty; skipping readiness check."
        }

        $loop = 1
        $start = Get-Date
        while ($loop -le $IntendedLoops) {
            if ($ClearHostEachLoop) {
                Clear-Host
            }
            $runTime = (Get-Date) - $start
            $msg = "--- [Phase 2] Lab monitor | Loop {0}/{1} | Started {2} | Elapsed {3}h {4}m {5}s ---" -f @(
                $loop,
                $IntendedLoops,
                $start.ToString("HH:mm:ss"),
                $runTime.Hours,
                $runTime.Minutes,
                $runTime.Seconds
            )
            Write-Host $msg -ForegroundColor Cyan

            $inventory = Get-Content -LiteralPath $inventoryPath | ConvertFrom-Json
            $report = foreach ($node in $inventory.lab_members) {
                & $getLabStatus -TargetHost $node.hostname -TargetUser $node.user
            }
            $report | Format-Table -AutoSize

            $loop++
            if ($loop -le $IntendedLoops -and $MonitorIntervalSeconds -gt 0) {
                Start-Sleep -Seconds $MonitorIntervalSeconds
            }
        }
    }

    if (-not $SkipCollect) {
        Write-Host ""
        Write-Host "--- [Phase 3] Maestro Collect (post-flight) ---" -ForegroundColor Yellow
        & $maestro -Ref $Ref -Collect
        $worst = Get-WorstExitCode -Current $worst -Candidate $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

exit $worst
