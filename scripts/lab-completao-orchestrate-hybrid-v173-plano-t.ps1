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
$ManifestPath = Join-Path $RepoRoot "docs/private/homelab/lab-op-hosts.manifest.json"

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Hybrid v1.7.3 requires $ManifestPath (same manifest as lab-completao-orchestrate.ps1). Copy from docs/private.example/homelab/lab-op-hosts.manifest.example.json"
}

$Manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json

function Get-HybridRepoPath {
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

$NodeDef = @(
    @{ Regex = "lab-node-02";  Name = "LAB-NODE-02-5400"; Type = "engine" }
    @{ Regex = "lab-node-01";       Name = "ThinkPad-LAB-NODE-01";  Type = "engine" }
    @{ Regex = "LAB-NODE-03";   Name = "Beelink-Mini";  Type = "engine" }
    @{ Regex = "LAB-NODE-04";      Name = "LAB-NODE-04-Passive";  Type = "passive" }
)

$Ordered = New-Object System.Collections.Generic.List[PSObject]
foreach ($rd in $NodeDef) {
    foreach ($h in $Manifest) {
        if (-not $h.sshHost) {
            continue
        }
        if ([string]$h.sshHost -match $rd.Regex) {
            $rp = Get-HybridRepoPath -HostEntry $h
            $Ordered.Add([PSCustomObject]@{
                Name    = $rd.Name
                SshHost = $h.sshHost
                Type    = $rd.Type
                Repo    = $rp
            })
            break
        }
    }
}

if ($Ordered.Count -eq 0) {
    throw "No recognizable lab hosts in manifest (expected sshHost matching lab-node-02, lab-node-01, LAB-NODE-03, or LAB-NODE-04)."
}

$HybridStableImage = "fabioleitao/data_boar:1.7.3"
$HybridBetaImage   = "fabioleitao/data_boar:1.7.4-rc"
$HybridPortStable  = "9001"
$HybridPortBeta    = "9002"
$HybridContainerInnerPort = "8088"

$HybridBenchStable = "/tmp/databoar_bench/stable"
$HybridBenchBeta   = "/tmp/databoar_bench/beta"
$TmuxSessionName   = "completao"

$stampHybrid = Get-Date -Format "yyyyMMdd_HHmmss"
$outDirHybrid = Join-Path $RepoRoot "out"
$eventsPathHybrid = Join-Path $outDirHybrid "hybrid_ab_bench_$stampHybrid.jsonl"

$StableTarLocalOverride = ""
if ($env:DATA_BOAR_HYBRID_STABLE_TAR_GZ) {
    $StableTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_STABLE_TAR_GZ
}
$BetaTarLocalOverride = ""
if ($env:DATA_BOAR_HYBRID_BETA_TAR_GZ) {
    $BetaTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_BETA_TAR_GZ
}

New-Item -ItemType Directory -Force -Path $outDirHybrid | Out-Null

$HybridExportDir = Join-Path $outDirHybrid "hybrid_image_export_$stampHybrid"
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
    $json = $o | ConvertTo-Json -Compress
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($eventsPathHybrid, $json + [Environment]::NewLine, $enc)
}


function Test-HybridRemoteImagePresent {
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

function Prepare-HybridWindowsEngineImages {
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
    & scp.exe -o BatchMode=yes -q $LocalPath "${Target}:$RemotePath"
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

function Invoke-HybridRemoteContainerBench {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Engine,
        [Parameter(Mandatory = $true)][string]$Image,
        [Parameter(Mandatory = $true)][string]$HostPort,
        [Parameter(Mandatory = $true)][string]$ConfigRemote,
        [Parameter(Mandatory = $true)][string]$TrackLabel,
        [Parameter(Mandatory = $true)][string]$NodeLabel
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $engineBin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $logFile = "$ConfigRemote.bench.log"
    $scriptRemote = "$ConfigRemote.bench.sh"
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
    $sn = "databoar_bench_$($stampHybrid)_$TrackLabel"
    $tm = "tmux new-session -d -s '$sn' `"sh $scriptRemote`""
    $tmEsc = $tm.Replace('"', '\"')
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
    $null = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes -o ConnectTimeout=15 $Target `"tmux kill-session -t '$sn' 2>/dev/null`" 2>&1"
    return @{ ok = $true; wall_ms = [int]$sw.ElapsedMilliseconds; log = $cat }
}

# --- Main Logic ---

if (-not (Prepare-HybridWindowsEngineImages)) {
    throw "Hybrid: local image prep failed on Windows orchestrator."
}

foreach ($n in $Ordered) {
    Write-Host "`n>>> Processing Hybrid Node: $($n.Name) ($($n.SshHost))" -ForegroundColor Cyan
    $target = $n.SshHost

    try {
        if (-not (Test-HybridSshOk -Target $target)) {
            Write-Warning "Hybrid: node $($n.Name) ($target) SSH unreachable (BatchMode) - skip."
            continue
        }

        if ($n.Type -eq "passive") {
            Invoke-LAB-NODE-04PassiveSsh -Node $n -RepoPath $n.Repo
            continue
        }

        if (-not (Invoke-HybridRemoteMkBenchDirs -Target $target)) {
            throw "Failed to create benchmark directories on $target"
        }

        Invoke-HybridOptionalGitPullRemoteRepo -Target $target -RepoPath $n.Repo -NodeLabel $n.Name

        $engine = if ($n.Name -match "ThinkPad") { "podman" } else { "docker" }

        $stableInfo = Resolve-HybridLocalImageTar -OverridePath $StableTarLocalOverride -ImageRef $HybridStableImage -ExportFileName "stable.tar" -RemoteBenchDir $HybridBenchStable -RemoteBaseName "data_boar_stable"
        $betaInfo   = Resolve-HybridLocalImageTar -OverridePath $BetaTarLocalOverride -ImageRef $HybridBetaImage -ExportFileName "beta.tar" -RemoteBenchDir $HybridBenchBeta -RemoteBaseName "data_boar_beta"

        if (-not $stableInfo.ok -or -not $betaInfo.ok) {
            throw "Local image resolution/export failed for $target"
        }

        Write-Host "Hybrid $($n.Name): syncing tars (stable ~300MB, beta ~350MB) -> $target" -ForegroundColor DarkGray
        if (-not (Invoke-HybridRsyncOrScp -LocalPath $stableInfo.local -Target $target -RemotePath $stableInfo.remote)) {
            throw "Stable tar sync failed to $target"
        }
        if (-not (Invoke-HybridRsyncOrScp -LocalPath $betaInfo.local -Target $target -RemotePath $betaInfo.remote)) {
            throw "Beta tar sync failed to $target"
        }

        if (-not (Invoke-HybridSyncCompletaoScriptsToBench -Target $target)) {
            throw "Smoke script sync failed to $target"
        }

        if (-not (Invoke-HybridRemoteHostEnvAuditLine -Target $target -SshAliasForEnv $target)) {
            Write-Warning "Hybrid $($n.Name): host_env audit failed (continuing)."
        }

        Write-Host "Hybrid $($n.Name): loading images via $engine..." -ForegroundColor DarkGray
        if (-not (Invoke-HybridRemoteDockerLoads -Target $target -Engine $engine -StableTarRemote $stableInfo.remote -BetaTarRemote $betaInfo.remote)) {
            throw "Docker/Podman load failed on $target"
        }

        $scanPath = if ($n.Name -match "LAB-NODE-02") { Resolve-LAB-NODE-02ScanPath -Target $target } else { "/etc" }
        if (-not $scanPath) {
            $scanPath = "/tmp"
        }

        Deploy-ConfigTrack -Node $n -Path $scanPath -Track "stable"
        Deploy-ConfigTrack -Node $n -Path $scanPath -Track "beta"

        $stableMs = 0
        $betaMs   = 0

        # Run A (Stable)
        if (Test-HybridRemoteImagePresent -Target $target -Engine $engine -Image $HybridStableImage) {
            Write-Host "Hybrid $($n.Name): starting bench A (stable v1.7.3)..." -ForegroundColor Gray
            $resA = Invoke-HybridRemoteContainerBench -Target $target -Engine $engine -Image $HybridStableImage -HostPort $HybridPortStable -ConfigRemote "${HybridBenchStable}/config_databoar.yaml" -TrackLabel "stable" -NodeLabel $n.Name
            $stableMs = $resA.wall_ms
            Write-HybridCompletaoEvent -Phase "benchmark_run" -Status (if ($resA.ok) { "ok" } else { "warning" }) -HostLabel $n.Name -Detail @{
                wall_ms   = $stableMs
                image     = $HybridStableImage
                port      = $HybridPortStable
                narrative = "v1.7.3 stable; reference point for legacy engine"
            }
        } else {
            Write-HybridCompletaoEvent -Phase "image_preflight" -Status "skipped" -Message "stable_missing_after_load" -HostLabel $n.Name -Detail @{ image = $HybridStableImage }
        }

        # Run B (Beta)
        if (Test-HybridRemoteImagePresent -Target $target -Engine $engine -Image $HybridBetaImage) {
            Write-Host "Hybrid $($n.Name): starting bench B (beta v1.7.4-rc)..." -ForegroundColor Gray
            $resB = Invoke-HybridRemoteContainerBench -Target $target -Engine $engine -Image $HybridBetaImage -HostPort $HybridPortBeta -ConfigRemote "${HybridBenchBeta}/config_databoar.yaml" -TrackLabel "beta" -NodeLabel $n.Name
            $betaMs = $resB.wall_ms
            Write-HybridCompletaoEvent -Phase "benchmark_run" -Status (if ($resB.ok) { "ok" } else { "warning" }) -HostLabel $n.Name -Detail @{
                wall_ms   = $betaMs
                image     = $HybridBetaImage
                port      = $HybridPortBeta
                narrative = "v1.7.4-rc Rust boar_fast_filter / FFI; compare wall_ms
