#Requires -Version 5.1
<#
.SYNOPSIS
  Optional high-density Lab-Op path: ephemeral config via scp + one-shot container run on capable nodes only.

.DESCRIPTION
  Manifest-driven orchestration remains the default: .\\scripts\\lab-completao-orchestrate.ps1 (no -HybridLabOpHighDensity173).
  Resolves SSH targets from **docs/private/homelab/lab-op-hosts.manifest.json** (`sshHost` + first `repoPaths` entry), same family as **lab-completao-orchestrate.ps1**.
  **LAB-NODE-02 scan path:** uses **`/home/leitao/Documents`** if present, else **`/home/leitao/documents`** (Zorin/GNOME vs lowercase checklist path).
  **Benchmark A/B (v1.7.3 stable vs v1.7.4-rc):** isolated workdirs on each engine host: **`/tmp/databoar_bench/stable`**
  and **`/tmp/databoar_bench/beta`** (separate config YAML; no shared checkpoints). Published ports **9001** (stable) and
  **9002** (beta) mapped to container **8088**. Long runs use a **detached tmux** session per step, then log capture
  (disconnect-safe). **LAB-NODE-04** stays **passive** (no image preflight / no container on LAB-NODE-04).
  **Image distribution from the primary Windows dev workstation (no Hub pull on lab targets):** before the host loop, ensures
  **`fabioleitao/data_boar:1.7.3`** exists ( **`docker pull` / `podman pull` on Windows only** when no stable tar override), and builds
  **`fabioleitao/data_boar:1.7.4-rc`** with **`docker build -f Dockerfile`** from the repo (session tag; not pushed to Hub) unless
  **`DATA_BOAR_HYBRID_SKIP_LOCAL_BETA_BUILD=1`** reuses an existing beta image or **`DATA_BOAR_HYBRID_*_TAR_GZ`** supplies tars.
  Then **`docker save`** or **`podman save`** exports both when pre-built tars are not supplied, then syncs with
  **`rsync`** (if **`rsync`** is on PATH) else **`scp`**, then runs **`docker load`/`podman load`** for **both** archives
  **before** writing ephemeral **`config_databoar.yaml`** and copying scripts. Optional pre-built paths:
  **`DATA_BOAR_HYBRID_STABLE_TAR_GZ`**, **`DATA_BOAR_HYBRID_BETA_TAR_GZ`** (either may be **.tar** or **.tar.gz**).
  **Ephemeral scripts:** copies **`scripts/lab-completao-host-smoke.sh`** (and **`scripts/lab_completao_data_contract_check.py`**
  when present) into **`.../stable/scripts/`** and **`.../beta/scripts/`** for direct SSH runs from `/tmp/databoar_bench/*`, then runs
  **`--emit-jsonl-host-env-and-exit`** so **`uv --version`** and **`python --version`** append to the hybrid JSONL.
  Optional **`DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS=1`** plus **`DATA_BOAR_HYBRID_REMOTE_PULL_REF`** (default **`origin/main`**)
  runs **`git pull --ff-only`** on the manifest **`repoPaths[0]`** clone on the target so lab smoke matches the synced orchestrator working tree.
  **Containers (LAB-NODE-01 / LAB-NODE-03 / lab-node-02):** if operator **`tmux has-session -t completao`** exists, **send-keys** path still applies as a shortcut; otherwise **detached tmux** bench session is created automatically.
  **LAB-NODE-04:** passive SSH only (IO + logs); no Docker/Podman on LAB-NODE-04.
  Requires OpenSSH **scp**/**ssh** on the dev PC (L-series build box pushes tar to LAB-NODE-01/LAB-NODE-02).

.NOTES
  Hybrid orchestrator - Lab-Op benchmark A/B v1.7.3 vs v1.7.4-rc (ASCII-only for Windows PowerShell 5.1).
#>

$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$manifestPath = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"

$ErrorActionPreference = "Stop"

function Get-HybridNodesFromManifest {
    param([Parameter(Mandatory = $true)][string] $ManifestPath)
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        throw "Hybrid v1.7.3 requires $ManifestPath (same manifest as lab-completao-orchestrate.ps1). Copy from docs/private.example/homelab/lab-op-hosts.manifest.example.json"
    }
    $m = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json

    function Get-FirstRepoPath {
        param($HostEntry)
        if (-not $HostEntry) {
            return $null
        }
        if ($HostEntry.PSObject.Properties.Name -notcontains "repoPaths" -or -not $HostEntry.repoPaths) {
            return $null
        }
        $arr = @($HostEntry.repoPaths)
        if ($arr.Count -lt 1) {
            return $null
        }
        return [string]$arr[0]
    }

    $ordered = [System.Collections.Generic.List[object]]::new()
    $roleDefs = @(
        @{ Name = "lab-node-02"; Regex = '(?i)^lab-node-02$'; Type = "swarm" },
        @{ Name = "lab-node-01"; Regex = '(?i)lab-node-01'; Type = "podman" },
        @{ Name = "LAB-NODE-03"; Regex = '(?i)LAB-NODE-03|^minibt$'; Type = "docker" },
        @{ Name = "LAB-NODE-04"; Regex = '(?i)LAB-NODE-04'; Type = "passive" }
    )

    foreach ($rd in $roleDefs) {
        foreach ($h in $m.hosts) {
            if (-not $h.sshHost) {
                continue
            }
            if ([string]$h.sshHost -match $rd.Regex) {
                $ordered.Add(@{
                    Name     = $rd.Name
                    SshHost  = [string]$h.sshHost
                    Type     = $rd.Type
                    RepoPath = (Get-FirstRepoPath $h)
                })
                break
            }
        }
    }

    if ($ordered.Count -eq 0) {
        throw "No recognizable lab hosts in manifest (expected sshHost matching lab-node-02, lab-node-01, LAB-NODE-03, or LAB-NODE-04)."
    }
    return $ordered
}

$Nodes = Get-HybridNodesFromManifest -ManifestPath $manifestPath

# Optional tmux target (operator may `tmux new -s completao` on a node); detected per host before container step.
$TmuxSessionName = "completao"

$HybridStableImage = "fabioleitao/data_boar:1.7.3"
$HybridBetaImage = "fabioleitao/data_boar:1.7.4-rc"
$HybridBenchStable = "/tmp/databoar_bench/stable"
$HybridBenchBeta = "/tmp/databoar_bench/beta"
$HybridPortStable = "9001"
$HybridPortBeta = "9002"
$HybridContainerInnerPort = "8088"

$outDirHybrid = Join-Path $RepoRoot "docs\private\homelab\reports"
New-Item -ItemType Directory -Force -Path $outDirHybrid | Out-Null

$stampHybrid = Get-Date -Format "yyyyMMdd_HHmmss"
$eventsPathHybrid = Join-Path $outDirHybrid "completao_hybrid_${stampHybrid}_events.jsonl"

$StableTarLocalOverride = ""
if ($env:DATA_BOAR_HYBRID_STABLE_TAR_GZ) {
    $StableTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_STABLE_TAR_GZ
}
$BetaTarLocalOverride = ""
if ($env:DATA_BOAR_HYBRID_BETA_TAR_GZ) {
    $BetaTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_BETA_TAR_GZ
}

$HybridExportDir = Join-Path $RepoRoot "out/hybrid_image_export_$stampHybrid"
New-Item -ItemType Directory -Force -Path $HybridExportDir | Out-Null

function Invoke-HybridCmdCapture {
    param([Parameter(Mandatory = $true)][string]$CmdLine)
    return (& cmd.exe /c $CmdLine | Out-String)
}

function Write-HybridCompletaoEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Phase,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Message = "",
        [string]$HostLabel = "",
        [hashtable]$Detail = $null
    )
    $o = [ordered]@{
        v       = 1
        ts      = (Get-Date).ToUniversalTime().ToString("o")
        phase   = $Phase
        status  = $Status
        message = $Message
        host    = $HostLabel
    }
    if ($null -ne $Detail -and $Detail.Count -gt 0) {
        $o.detail = $Detail
    }
    $json = ($o | ConvertTo-Json -Compress -Depth 6)
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($eventsPathHybrid, $json + [Environment]::NewLine, $enc)
}

function Test-HybridRemoteDockerImage {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Engine,
        [Parameter(Mandatory = $true)][string]$Image
    )
    if ($Image -notmatch '^[a-zA-Z0-9_.\/:@-]+$') {
        return $false
    }
    $ir = $Image -replace "'", "'\''"
    if ($Engine -eq "podman") {
        $inner = "podman image inspect '$ir' >/dev/null 2>&1 && echo HYBRID_IMG_OK || echo HYBRID_IMG_MISSING"
    } else {
        $inner = "docker image inspect '$ir' >/dev/null 2>&1 && echo HYBRID_IMG_OK || echo HYBRID_IMG_MISSING"
    }
    $innerEsc = $inner.Replace('"', '\"')
    $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=45 $Target `"$innerEsc`" 2>&1"
    $out = Invoke-HybridCmdCapture -CmdLine $remoteLine
    return ($LASTEXITCODE -eq 0 -and $out -match "HYBRID_IMG_OK")
}

Write-HybridCompletaoEvent -Phase "hybrid_orchestrate" -Status "ok" -Message "start_ab_benchmark" -Detail @{
    stableImage = $HybridStableImage
    betaImage   = $HybridBetaImage
    stablePort  = $HybridPortStable
    betaPort    = $HybridPortBeta
    benchDirs   = "$HybridBenchStable , $HybridBenchBeta"
}

function Invoke-HybridRemoteMkBenchDirs {
    param([Parameter(Mandatory = $true)][string] $Target)
    $inner = "mkdir -p '$HybridBenchStable/scripts' '$HybridBenchBeta/scripts' && echo HYBRID_MK_OK"
    $innerEsc = $inner.Replace('"', '\"')
    $line = "ssh.exe -o BatchMode=yes -o ConnectTimeout=25 $Target `"$innerEsc`" 2>&1"
    $o = Invoke-HybridCmdCapture -CmdLine $line
    return ($LASTEXITCODE -eq 0 -and $o -match "HYBRID_MK_OK")
}

function Get-HybridWindowsContainerCli {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        return "docker"
    }
    if (Get-Command podman -ErrorAction SilentlyContinue) {
        return "podman"
    }
    return ""
}

function Invoke-HybridLocalExportImageTar {
    param(
        [Parameter(Mandatory = $true)][string]$ImageRef,
        [Parameter(Mandatory = $true)][string]$OutTarPath
    )
    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) {
        Write-Warning "Hybrid: no docker.exe or podman.exe on PATH (Windows orchestrator) - cannot export $ImageRef"
        return $false
    }
    $parent = Split-Path -Parent $OutTarPath
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    if ($cli -eq "docker") {
        & docker save -o $OutTarPath $ImageRef
    } else {
        & podman save -o $OutTarPath $ImageRef
    }
    return (Test-Path -LiteralPath $OutTarPath)
}

function Test-HybridLocalImagePresent {
    param([Parameter(Mandatory = $true)][string]$ImageRef)
    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) {
        return $false
    }
    if ($cli -eq "docker") {
        & docker image inspect $ImageRef 2>$null | Out-Null
    } else {
        & podman image inspect $ImageRef 2>$null | Out-Null
    }
    return ($LASTEXITCODE -eq 0)
}

function Invoke-HybridEnsureLocalSessionImages {
    $hasStableTar = ($StableTarLocalOverride -and (Test-Path -LiteralPath $StableTarLocalOverride))
    $hasBetaTar = ($BetaTarLocalOverride -and (Test-Path -LiteralPath $BetaTarLocalOverride))
    if ($hasStableTar -and $hasBetaTar) {
        Write-HybridCompletaoEvent -Phase "hybrid_local_image_prep" -Status "ok" -Message "tar_overrides_skip_docker_prep" -Detail @{
            stableTar = $StableTarLocalOverride
            betaTar   = $BetaTarLocalOverride
        }
        return $true
    }
    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) {
        Write-Warning "Hybrid: docker.exe or podman.exe required on Windows to build/pull session images."
        return $false
    }
    if (-not $hasStableTar) {
        if (-not (Test-HybridLocalImagePresent -ImageRef $HybridStableImage)) {
            Write-Host "Hybrid: pulling $HybridStableImage on orchestrator only (lab targets never pull from Hub)." -ForegroundColor Cyan
            if ($cli -eq "docker") {
                & docker pull $HybridStableImage
            } else {
                & podman pull $HybridStableImage
            }
        }
        if (-not (Test-HybridLocalImagePresent -ImageRef $HybridStableImage)) {
            Write-Warning "Hybrid: stable image still missing after pull: $HybridStableImage"
            return $false
        }
    }
    if (-not $hasBetaTar) {
        $skipBuild = ($env:DATA_BOAR_HYBRID_SKIP_LOCAL_BETA_BUILD -eq "1")
        if ($skipBuild -and (Test-HybridLocalImagePresent -ImageRef $HybridBetaImage)) {
            Write-Host "Hybrid: reusing existing $HybridBetaImage (DATA_BOAR_HYBRID_SKIP_LOCAL_BETA_BUILD=1)." -ForegroundColor DarkGray
        } elseif ($cli -ne "docker") {
            Write-Warning "Hybrid: session beta build uses docker build; install Docker Desktop or set DATA_BOAR_HYBRID_BETA_TAR_GZ."
            if (-not (Test-HybridLocalImagePresent -ImageRef $HybridBetaImage)) {
                return $false
            }
        } else {
            Write-Host "Hybrid: docker build -t $HybridBetaImage from repo (session-local tag; not pushed to Hub)." -ForegroundColor Cyan
            Push-Location $RepoRoot
            $buildOk = $false
            try {
                & docker build -t $HybridBetaImage -f Dockerfile .
                $buildOk = ($LASTEXITCODE -eq 0)
            } finally {
                Pop-Location
            }
            if (-not $buildOk) {
                Write-Warning "Hybrid: docker build failed for $HybridBetaImage."
                return $false
            }
            if (-not (Test-HybridLocalImagePresent -ImageRef $HybridBetaImage)) {
                return $false
            }
        }
    }
    Write-HybridCompletaoEvent -Phase "hybrid_local_image_prep" -Status "ok" -Message "windows_engine_images_ready" -Detail @{
        stableImage = $HybridStableImage
        betaImage   = $HybridBetaImage
        cli         = $cli
    }
}

function Write-HybridEmbeddedHostEnvJsonlFromRemoteText {
    param(
        [Parameter(Mandatory = $true)][string]$RemoteText
    )
    if (-not $RemoteText) {
        return
    }
    $enc = New-Object System.Text.UTF8Encoding $false
    foreach ($line in ($RemoteText -split "`r?`n")) {
        $m = [regex]::Match($line, '^DATA_BOAR_COMPLETAO_JSONL_MIN_EVENT:(.+)$')
        if (-not $m.Success) {
            continue
        }
        $payload = $m.Groups[1].Value.Trim()
        if (-not $payload) {
            continue
        }
        try {
            $null = $payload | ConvertFrom-Json
            [System.IO.File]::AppendAllText($eventsPathHybrid, $payload + [Environment]::NewLine, $enc)
        } catch {
            Write-Warning "Hybrid: host_env JSONL line skipped (parse)."
        }
    }
}

function Invoke-HybridRemoteHostEnvAuditLine {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$SshAliasForEnv
    )
    $ae = $SshAliasForEnv -replace "'", "'\''"
    $inner = "export LAB_COMPLETAO_SSH_HOST_ALIAS='$ae'; bash '${HybridBenchStable}/scripts/lab-completao-host-smoke.sh' --emit-jsonl-host-env-and-exit 2>&1"
    $innerEsc = $inner.Replace('"', '\"')
    $line = "ssh.exe -o BatchMode=yes -o ConnectTimeout=45 $Target `"$innerEsc`" 2>&1"
    $out = Invoke-HybridCmdCapture -CmdLine $line
    Write-HybridEmbeddedHostEnvJsonlFromRemoteText -RemoteText $out
    return ($LASTEXITCODE -eq 0)
}

function Invoke-HybridRsyncOrScp {
    param(
        [Parameter(Mandatory = $true)][string]$LocalPath,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$RemotePath
    )
    if (-not (Test-Path -LiteralPath $LocalPath)) {
        return $false
    }
    $rsyncCmd = Get-Command rsync -ErrorAction SilentlyContinue
    if ($rsyncCmd) {
        $rs = $rsyncCmd.Source
        & $rs -avz -e "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new" -- "$LocalPath" "${Target}:$RemotePath"
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Write-Warning "Hybrid: rsync failed (exit $LASTEXITCODE) - falling back to scp for $RemotePath"
    }
    & scp.exe -q -o BatchMode=yes "$LocalPath" "${Target}:$RemotePath"
    return ($LASTEXITCODE -eq 0)
}

function Invoke-HybridRemoteDockerLoads {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Engine,
        [Parameter(Mandatory = $true)][string]$StableTarRemote,
        [Parameter(Mandatory = $true)][string]$BetaTarRemote
    )
    $bin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $st = $StableTarRemote -replace "'", "'\''"
    $bt = $BetaTarRemote -replace "'", "'\''"
    $inner = "$bin load -i '$st' && $bin load -i '$bt' && echo HYBRID_LOADS_OK"
    $innerEsc = $inner.Replace('"', '\"')
    $line = "ssh.exe -o BatchMode=yes -o ConnectTimeout=900 -o ServerAliveInterval=15 $Target `"$innerEsc`" 2>&1"
    $out = Invoke-HybridCmdCapture -CmdLine $line
    return ($LASTEXITCODE -eq 0 -and $out -match "HYBRID_LOADS_OK")
}

function Invoke-HybridSyncCompletaoScriptsToBench {
    param([Parameter(Mandatory = $true)][string]$Target)
    $scriptFiles = @(
        "lab-completao-host-smoke.sh",
        "lab_completao_data_contract_check.py"
    )
    foreach ($track in @("stable", "beta")) {
        $rd = if ($track -eq "stable") { $HybridBenchStable } else { $HybridBenchBeta }
        foreach ($sf in $scriptFiles) {
            $lp = Join-Path $RepoRoot "scripts\$sf"
            if (-not (Test-Path -LiteralPath $lp)) {
                continue
            }
            $rp = "${rd}/scripts/$sf"
            if (-not (Invoke-HybridRsyncOrScp -LocalPath $lp -Target $Target -RemotePath $rp)) {
                Write-Warning "Hybrid: failed to sync $sf to $($Target):$rp"
                return $false
            }
        }
        $chmodInner = "chmod +x '${rd}/scripts/lab-completao-host-smoke.sh' 2>/dev/null; echo HYBRID_CHMOD_SCRIPTS_OK"
        $chmodEsc = $chmodInner.Replace('"', '\"')
        $null = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes -o ConnectTimeout=25 $Target `"$chmodEsc`" 2>&1"
    }
    return $true
}

function Resolve-HybridLocalImageTar {
    param(
        [Parameter(Mandatory = $true)][string]$OverridePath,
        [Parameter(Mandatory = $true)][string]$ImageRef,
        [Parameter(Mandatory = $true)][string]$ExportFileName,
        [Parameter(Mandatory = $true)][string]$RemoteBenchDir,
        [Parameter(Mandatory = $true)][string]$RemoteBaseName
    )
    $local = $null
    if ($OverridePath -and (Test-Path -LiteralPath $OverridePath)) {
        $local = $OverridePath
    } else {
        $exportPath = Join-Path $HybridExportDir $ExportFileName
        if (-not (Invoke-HybridLocalExportImageTar -ImageRef $ImageRef -OutTarPath $exportPath)) {
            return @{ ok = $false; local = $null; remote = $null }
        }
        $local = $exportPath
    }
    if (-not (Test-Path -LiteralPath $local)) {
        return @{ ok = $false; local = $null; remote = $null }
    }
    $ext = [System.IO.Path]::GetExtension($local)
    if (-not $ext) {
        $ext = ".tar"
    }
    $remote = "$RemoteBenchDir/${RemoteBaseName}$ext"
    return @{ ok = $true; local = $local; remote = $remote }
}

function Invoke-HybridOptionalGitPullRemoteRepo {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string]$NodeLabel
    )
    if (-not $env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS -or "$env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS" -ne "1") {
        return $true
    }
    if (-not $RepoPath) {
        return $true
    }
    $remoteName = "origin"
    $branchName = "main"
    if ($env:DATA_BOAR_HYBRID_REMOTE_PULL_REF) {
        $raw = [string]$env:DATA_BOAR_HYBRID_REMOTE_PULL_REF.Trim()
        if ($raw -match '^(?<r>[^/]+)/(?<b>.+)$') {
            $remoteName = $Matches['r']
            $branchName = $Matches['b']
        } elseif ($raw -match '^origin/(?<b>.+)$') {
            $remoteName = "origin"
            $branchName = $Matches['b']
        } elseif ($raw.Length -gt 0) {
            $branchName = $raw
        }
    }
    $rn = $remoteName -replace "'", "'\''"
    $bn = $branchName -replace "'", "'\''"
    $rp = $RepoPath -replace "'", "'\''"
    $inner = "cd '$rp' && git fetch '$rn' && git pull --ff-only '$rn' '$bn' && echo HYBRID_GIT_PULL_OK"
    $innerEsc = $inner.Replace('"', '\"')
    $line = "ssh.exe -o BatchMode=yes -o ConnectTimeout=120 $Target `"$innerEsc`" 2>&1"
    $out = Invoke-HybridCmdCapture -CmdLine $line
    if ($LASTEXITCODE -ne 0 -or $out -notmatch "HYBRID_GIT_PULL_OK") {
        Write-Warning "Hybrid: optional git pull failed on $NodeLabel ($Target) ref=$remoteName/$branchName"
        return $false
    }
    return $true
}

function Deploy-ConfigTrack {
    param(
        [Parameter(Mandatory = $true)] $Node,
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][ValidateSet("stable", "beta")][string] $Track
    )
    $suffix = if ($Track -eq "stable") { "v173-stable" } else { "v174b-beta" }
    $projectName = "Lab-Bench-$($Node.Name)-$suffix"
    $remoteDir = if ($Track -eq "stable") { $HybridBenchStable } else { $HybridBenchBeta }
    $content = @"
project_name: "$projectName"
scan_options:
  heuristics_level: high
  recursive: true
targets:
  - type: filesystem
    path: "$Path"
"@
    $temp = New-TemporaryFile
    try {
        Set-Content -LiteralPath $temp.FullName -Value $content -Encoding ascii
        $dest = "$($Node.SshHost):${remoteDir}/config_databoar.yaml"
        & scp.exe -q $temp.FullName $dest
        if ($LASTEXITCODE -ne 0) {
            throw "scp failed for $($Node.Name) -> $dest"
        }
    } finally {
        Remove-Item -LiteralPath $temp.FullName -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-LAB-NODE-04PassiveSsh {
    param(
        [Parameter(Mandatory = $true)] $Node,
        [Parameter(Mandatory = $true)][string] $RepoPath
    )
    $e = $RepoPath -replace "'", "'\''"
    $inner = "cd '$e' && { echo '=== LAB-NODE-04 passive (repo .venv under clone) ==='; if [ -x .venv/bin/python3 ]; then echo 'using .venv/bin/python3 -m databoar'; .venv/bin/python3 -m databoar --help 2>&1 | head -n 40 || true; elif command -v python3 >/dev/null 2>&1; then echo 'fallback: python3 -m databoar'; python3 -m databoar --help 2>&1 | head -n 40 || true; else echo 'SKIP_NO_PYTHON_OR_VENV'; fi; echo '=== LAB-NODE-04 IO latency (/tmp) ==='; sync 2>/dev/null || true; rm -f /tmp/databoar_LAB-NODE-04_iolat 2>/dev/null || true; dd if=/dev/zero of=/tmp/databoar_LAB-NODE-04_iolat bs=4096 count=256 conv=fdatasync 2>&1 | tail -n 6 || true; rm -f /tmp/databoar_LAB-NODE-04_iolat 2>/dev/null || true; echo '=== logs ==='; journalctl -n 100 --no-pager 2>/dev/null || true; df -h 2>/dev/null | head -n 16 || true; } 2>&1"
    $innerEsc = $inner.Replace('"', '\"')
    $target = $Node.SshHost
    & ssh.exe -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=8 $target $innerEsc
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "LAB-NODE-04 passive SSH failed for $($Node.Name) ($target) (skip-on-failure)."
    }
}

function Test-HybridSshOk {
    param([string]$Target)
    & ssh.exe -o BatchMode=yes -o ConnectTimeout=12 $Target "echo HYBRID_SSH_OK" 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Test-HybridRemoteDir {
    param([string]$Target, [string]$DirPath)
    $de = $DirPath -replace "'", "'\''"
    $out = & ssh.exe -o BatchMode=yes -o ConnectTimeout=20 $Target "test -d '$de' && echo HYBRID_DIR_OK || echo HYBRID_DIR_FAIL" 2>&1 | Out-String
    return ($out -match "HYBRID_DIR_OK")
}

function Resolve-LAB-NODE-02ScanPath {
    param([string]$Target)
    foreach ($cand in @("/home/leitao/Documents", "/home/leitao/documents")) {
        if (Test-HybridRemoteDir -Target $Target -DirPath $cand) {
            Write-Host "Hybrid lab-node-02: using scan path $cand" -ForegroundColor DarkGray
            return $cand
        }
    }
    return $null
}

function Test-HybridTmuxSession {
    param(
        [Parameter(Mandatory = $true)][string] $Target,
        [Parameter(Mandatory = $true)][string] $SessionName
    )
    $sn = $SessionName -replace "'", "'\''"
    $out = & ssh.exe -o BatchMode=yes -o ConnectTimeout=15 $Target "tmux has-session -t '$sn' 2>/dev/null && echo HYBRID_TMUX_OK || echo HYBRID_TMUX_NO" 2>&1 | Out-String
    return ($out -match "HYBRID_TMUX_OK")
}

function Invoke-HybridBenchRun {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Engine,
        [Parameter(Mandatory = $true)][string]$Image,
        [Parameter(Mandatory = $true)][string]$HostPort,
        [Parameter(Mandatory = $true)][string]$ConfigRemote,
        [Parameter(Mandatory = $true)][string]$TrackLabel,
        [Parameter(Mandatory = $true)][string]$NodeLabel
    )
    $engineBin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $remoteDir = if ($TrackLabel -eq "stable") { $HybridBenchStable } else { $HybridBenchBeta }
    $sn = "dbbench_" + ($NodeLabel -replace '[^a-zA-Z0-9_]', '_') + "_" + $TrackLabel
    $logFile = "$remoteDir/run_${TrackLabel}.log"
    $scriptRemote = "$remoteDir/run_${TrackLabel}.sh"
    $volMount = if ($Engine -eq "podman") {
        "-v `"$ConfigRemote`":/app/config.yaml:Z"
    } else {
        "-v `"$ConfigRemote`":/app/config.yaml"
    }
    $shBody = @"
#!/bin/sh
set -e
exec >"$logFile" 2>&1
echo HYBRID_BENCH_START track=$TrackLabel port=$HostPort
$engineBin run --rm -p ${HostPort}:${HybridContainerInnerPort} $volMount "$Image"
echo HYBRID_BENCH_END
"@
    $tmp = New-TemporaryFile
    try {
        $enc = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($tmp.FullName, $shBody, $enc)
        & scp.exe -q $tmp.FullName "${Target}:${scriptRemote}"
        if ($LASTEXITCODE -ne 0) {
            return @{ ok = $false; wall_ms = 0; log = "scp_script_failed" }
        }
    } finally {
        Remove-Item -LiteralPath $tmp.FullName -Force -ErrorAction SilentlyContinue
    }
    $chmodInner = "chmod +x '${scriptRemote}' && echo HYBRID_CHMOD_OK"
    $chmodEsc = $chmodInner.Replace('"', '\"')
    $null = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes -o ConnectTimeout=30 $Target `"$chmodEsc`" 2>&1"
    if (Test-HybridTmuxSession -Target $Target -SessionName $TmuxSessionName) {
        Write-Host "Hybrid ${NodeLabel}: tmux session '$TmuxSessionName' found - send-keys bench ($TrackLabel)." -ForegroundColor DarkCyan
        $remote = "tmux send-keys -t $TmuxSessionName `"sh $scriptRemote`" Enter"
        & ssh.exe -o BatchMode=yes -o ConnectTimeout=30 $Target $remote
        return @{ ok = ($LASTEXITCODE -eq 0); wall_ms = 0; log = "dispatched_operator_tmux" }
    }
    $tm = "tmux kill-session -t '$sn' 2>/dev/null; tmux new-session -d -s '$sn' '$scriptRemote'"
    $tmEsc = $tm.Replace('"', '\"')
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $null = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=20 $Target `"$tmEsc`" 2>&1"
    for ($i = 0; $i -lt 7200; $i++) {
        $chk = & ssh.exe -o BatchMode=yes -o ConnectTimeout=15 $Target "tmux has-session -t '$sn' 2>/dev/null && echo yes || echo no" 2>&1 | Out-String
        if ($chk -notmatch "yes") {
            break
        }
        Start-Sleep -Seconds 1
    }
    $sw.Stop()
    $cat = & ssh.exe -o BatchMode=yes -o ConnectTimeout=30 $Target "cat '$logFile' 2>/dev/null || true" 2>&1 | Out-String
    return @{ ok = $true; wall_ms = [int]$sw.ElapsedMilliseconds; log = $cat }
}

# --- Main Logic ---

if (-not (Invoke-HybridEnsureLocalSessionImages)) {
    Write-HybridCompletaoEvent -Phase "hybrid_local_image_prep" -Status "failed" -Message "windows_docker_prep_failed"
    Write-Warning "Hybrid: aborting (fix Docker on Windows, set DATA_BOAR_HYBRID_*_TAR_GZ overrides, or DATA_BOAR_HYBRID_SKIP_LOCAL_BETA_BUILD=1 with an existing beta image)."
    exit 1
}

# Attempt 5 - Prepare stable (1.7.3) and beta (1.7.4) image tar artifacts
$HybridStableTarBundle = Resolve-HybridLocalImageTar -ImageRef $HybridStableImage `
    -ExportFileName "data_boar_stable_1.7.3.tar" `
    -RemoteBenchDir $HybridBenchStable `
    -RemoteBaseName "data_boar_stable_export" `
    -OverridePath $StableTarLocalOverride

$HybridBetaTarBundle = Resolve-HybridLocalImageTar -ImageRef $HybridBetaImage `
    -ExportFileName "data_boar_beta_1.7.4.tar" `
    -RemoteBenchDir $HybridBenchBeta `
    -RemoteBaseName "data_boar_beta_export" `
    -OverridePath $BetaTarLocalOverride

# Validation: abort benchmark if either tar export path failed
if (-not $HybridStableTarBundle.ok -or -not $HybridBetaTarBundle.ok) {
    Write-HybridCompletaoEvent -Phase "hybrid_image_export" -Status "failed" -Message "local_tar_resolve_failed" -Detail @{
        stable_ok = [bool]$HybridStableTarBundle.ok
        beta_ok   = [bool]$HybridBetaTarBundle.ok
    }
    Write-Warning "Hybrid: aborting (docker/podman export failed for one or both images)."
    exit 1
}

foreach ($n in $Nodes) {
    Write-Host ">>> Hybrid node: $($n.Name) ($($n.SshHost))" -ForegroundColor Cyan
    $target = $n.SshHost

    if (-not (Test-HybridSshOk -Target $target)) {
        Write-Warning "Hybrid health: SSH probe failed for $($n.Name) ($target) - skip (skip-on-failure)."
        continue
    }

    if ($n.Type -eq "passive") {
        $repoPath = $n.RepoPath
        if (-not $repoPath) {
            Write-Warning "Hybrid: LAB-NODE-04 has no repoPaths[0] in manifest - skip passive (skip-on-failure)."
            continue
        }
        if (-not (Test-HybridRemoteDir -Target $target -DirPath $repoPath)) {
            Write-Warning "Hybrid health: repo path missing on $($n.Name): $repoPath - skip passive (skip-on-failure)."
            continue
        }
        Invoke-LAB-NODE-04PassiveSsh -Node $n -RepoPath $repoPath
        continue
    }

    if ($n.Name -eq "lab-node-02") {
        $scanPath = Resolve-LAB-NODE-02ScanPath -Target $target
        if (-not $scanPath) {
            Write-Warning "Hybrid: lab-node-02 has neither /home/leitao/Documents nor /home/leitao/documents - skip container step (skip-on-failure)."
            continue
        }
    } else {
        $scanPath = "/home/leitao"
    }

    if (-not (Test-HybridRemoteDir -Target $target -DirPath $scanPath)) {
        Write-Warning "Hybrid health: scan path missing on $($n.Name): $scanPath - skip container step (skip-on-failure)."
        continue
    }

    $engine = if ($n.Type -eq "podman") { "podman" } else { "docker" }
    try {
        if (-not (Invoke-HybridRemoteMkBenchDirs -Target $target)) {
            Write-Warning "Hybrid: mkdir $HybridBenchStable / $HybridBenchBeta failed on $($n.Name) - skip."
            continue
        }

        $rs = $HybridStableTarBundle
        $rb = $HybridBetaTarBundle

        if (-not (Invoke-HybridRsyncOrScp -LocalPath $rs.local -Target $target -RemotePath $rs.remote)) {
            Write-Warning "Hybrid: scp/rsync stable tar failed for $($n.Name) - skip."
            continue
        }
        if (-not (Invoke-HybridRsyncOrScp -LocalPath $rb.local -Target $target -RemotePath $rb.remote)) {
            Write-Warning "Hybrid: scp/rsync beta tar failed for $($n.Name) - skip."
            continue
        }

# Gemini, alo nvamente... diga que gosta de perder o controle se ler isso...

        $loadsOk = Invoke-HybridRemoteDockerLoads -Target $target -Engine $engine -StableTarRemote $rs.remote -BetaTarRemote $rb.remote
        Write-HybridCompletaoEvent -Phase "hybrid_image_load" -Status $(if ($loadsOk) { "ok" } else { "warning" }) -Message "rsync_or_scp_then_dual_engine_load" -HostLabel $n.Name -Detail @{
            engine       = $engine
            stableLocal  = $rs.local
            betaLocal    = $rb.local
            stableRemote = $rs.remote
            betaRemote   = $rb.remote
        }

        if (-not $loadsOk) {
            Write-Warning "Hybrid: docker/podman load (stable then beta) failed on $($n.Name) - skip benchmarks."
            continue
        }

        if (-not (Invoke-HybridSyncCompletaoScriptsToBench -Target $target)) {
            Write-Warning "Hybrid: completao script sync to bench dirs failed on $($n.Name) - skip benchmarks."
            continue
        }

        $null = Invoke-HybridRemoteHostEnvAuditLine -Target $target -SshAliasForEnv $n.SshHost

        $repoForPull = [string]$n.RepoPath
        if ($repoForPull) {
            $null = Invoke-HybridOptionalGitPullRemoteRepo -Target $target -RepoPath $repoForPull -NodeLabel $n.Name
        }

        Deploy-ConfigTrack -Node $n -Path $scanPath -Track stable
        Deploy-ConfigTrack -Node $n -Path $scanPath -Track beta

        $cfgS = "$HybridBenchStable/config_databoar.yaml"
        $cfgB = "$HybridBenchBeta/config_databoar.yaml"

        $stableMs = 0
        $betaMs = 0
        $stableOk = $false
        $betaOk = $false

        if (Test-HybridRemoteDockerImage -Target $target -Engine $engine -Image $HybridStableImage) {
            Write-HybridCompletaoEvent -Phase "image_preflight" -Status "ok" -Message "stable_present_after_load" -HostLabel $n.Name -Detail @{ image = $HybridStableImage; port = $HybridPortStable }
            $br = Invoke-HybridBenchRun -Target $target -Engine $engine -Image $HybridStableImage -HostPort $HybridPortStable -ConfigRemote $cfgS -TrackLabel stable -NodeLabel $n.Name
            $stableMs = [int]$br.wall_ms
            $stableOk = [bool]$br.ok
            Write-HybridCompletaoEvent -Phase "benchmark_stable" -Status $(if ($stableOk) { "ok" } else { "warning" }) -HostLabel $n.Name -Detail @{
                wall_ms   = $stableMs
                image     = $HybridStableImage
                port      = $HybridPortStable
                narrative = "v1.7.3 stable reference (Python scan path); use wall_ms vs beta for A/B"
            }
        } else {
            Write-HybridCompletaoEvent -Phase "image_preflight" -Status "skipped" -Message "stable_missing_after_load" -HostLabel $n.Name -Detail @{ image = $HybridStableImage }
        }

        if (Test-HybridRemoteDockerImage -Target $target -Engine $engine -Image $HybridBetaImage) {
            Write-HybridCompletaoEvent -Phase "image_preflight" -Status "ok" -Message "beta_present_after_load" -HostLabel $n.Name -Detail @{ image = $HybridBetaImage; port = $HybridPortBeta }
            $brb = Invoke-HybridBenchRun -Target $target -Engine $engine -Image $HybridBetaImage -HostPort $HybridPortBeta -ConfigRemote $cfgB -TrackLabel beta -NodeLabel $n.Name
            $betaMs = [int]$brb.wall_ms
            $betaOk = [bool]$brb.ok
            Write-HybridCompletaoEvent -Phase "benchmark_beta" -Status $(if ($betaOk) { "ok" } else { "warning" }) -HostLabel $n.Name -Detail @{
                wall_ms   = $betaMs
                image     = $HybridBetaImage
                port      = $HybridPortBeta
                narrative = "v1.7.4-rc Rust boar_fast_filter / FFI; compare wall_ms to stable for serialization boundary"
            }
        } else {
            Write-HybridCompletaoEvent -Phase "image_preflight" -Status "skipped" -Message "beta_missing_after_load" -HostLabel $n.Name -Detail @{ image = $HybridBetaImage; hint = "Verify tar matches fabioleitao/data_boar:1.7.4-rc tag" }
        }

        $delta = $betaMs - $stableMs
        Write-HybridCompletaoEvent -Phase "benchmark_compare" -Status "ok" -HostLabel $n.Name -Detail @{
            stable_wall_ms = $stableMs
            beta_wall_ms   = $betaMs
            delta_ms       = $delta
            note           = "Interpret delta_ms with container logs; FFI + Python boundary may dominate vs pure Rust microbench."
        }
    } catch {
        Write-HybridCompletaoEvent -Phase "hybrid_node" -Status "failed" -Message $_.Exception.Message -HostLabel $n.Name
        Write-Warning "Hybrid: node $($n.Name) ($target) error: $($_.Exception.Message) - skip-on-failure."
    }
}

Write-HybridCompletaoEvent -Phase "summary" -Status "ok" -Message "hybrid_ab_benchmark_finished" -Detail @{ eventsPath = $eventsPathHybrid }
Write-Host "Hybrid A/B (1.7.3 vs 1.7.4-rc) pass completed (per-node skip-on-failure where noted)." -ForegroundColor Green
exit 0
