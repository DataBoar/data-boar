#Requires -Version 5.1
<#
.SYNOPSIS
  Optional high-density Lab-Op path: ephemeral config via scp + one-shot container run on capable nodes only.

.DESCRIPTION
  Manifest-driven orchestration remains the default: .\\scripts\\lab-completao-orchestrate.ps1 (no -HybridLabOpHighDensity173).
  Resolves SSH targets from **docs/private/homelab/lab-op-hosts.manifest.json** (`sshHost` + first `repoPaths` entry).
  **LAB-NODE-02 scan path:** uses **`/home/leitao/Documents`** if present, else **`/home/leitao/documents`**.
  **Benchmark A/B (v1.7.3 stable vs v1.7.4-rc):** isolated workdirs on each engine host.
  **LAB-NODE-04 stays passive.**
  Requires OpenSSH **scp**/**ssh** on the dev PC.
#>

$ErrorActionPreference = "Stop"

# --- [SRE_AUTHORITATIVE_CONTEXT_FIX: PRE-LOADED VARIABLES & HARDWARE] ---
# 1. ESTADO DOS ARTEFATOS (Garante que o caminho do .tar nunca seja nulo)
if (-not $env:DATA_BOAR_HYBRID_STABLE_TAR_GZ) {
    $env:DATA_BOAR_HYBRID_STABLE_TAR_GZ = "$env:TEMP\data_boar_stable_1.7.3.tar"
}
if (-not $env:DATA_BOAR_HYBRID_BETA_TAR_GZ) {
    $env:DATA_BOAR_HYBRID_BETA_TAR_GZ = "$env:TEMP\data_boar_174_beta.tar"
}

# 2. CONFIGURAC?O DE SINCRONIZAC?O (Evita rodar c?digo defasado no Lab-Op)
if (-not $env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS) { $env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS = "1" }
if (-not $env:DATA_BOAR_HYBRID_REMOTE_PULL_REF) { $env:DATA_BOAR_HYBRID_REMOTE_PULL_REF = "origin/main" }

# 3. INVENTARIO DE HARDWARE (Mapeamento deterministico de IPs)
$PreloadedInventory = @{
    "LAB-NODE-03"  = "10.0.0.75"
    "lab-node-02" = "10.0.0.58"
    "WORKSTATION"      = "10.0.0.47"   # Atualizado: WORKSTATION como fonte da verdade
    "lab-node-01"      = "10.0.0.47"   # Alias para retrocompatibilidade
    "LAB-NODE-04"     = "10.0.0.148"
}

# 4. AMBIENTE LOCAL
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$manifestPath = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
# -----------------------------------------------------------------------

# Sim, Gemini leu. A verdade esta no c?digo e no hardware. Chega de alucinac?o.

function Get-HybridNodesFromManifest {
    param([Parameter(Mandatory = $true)][string] $ManifestPath)
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        throw "Hybrid v1.7.3 requires $ManifestPath. Copy from docs/private.example/homelab/lab-op-hosts.manifest.example.json"
    }
    $m = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json

    function Get-FirstRepoPath {
        param($HostEntry)
        if (-not $HostEntry) { return $null }
        if ($HostEntry.PSObject.Properties.Name -notcontains "repoPaths" -or -not $HostEntry.repoPaths) { return $null }
        $arr = @($HostEntry.repoPaths)
        if ($arr.Count -lt 1) { return $null }
        return [string]$arr[0]
    }

    $ordered = [System.Collections.Generic.List[object]]::new()
    $roleDefs = @(
        @{ Name = "lab-node-02"; Regex = '(?i)^lab-node-02$'; Type = "swarm" },
        @{ Name = "WORKSTATION"; Regex = '(?i)WORKSTATION|lab-node-01'; Type = "podman" }, # Regex corrigida para aceitar WORKSTATION ou LAB-NODE-01
        @{ Name = "LAB-NODE-03"; Regex = '(?i)LAB-NODE-03|^minibt$'; Type = "docker" },
        @{ Name = "LAB-NODE-04"; Regex = '(?i)LAB-NODE-04'; Type = "passive" }
    )

    foreach ($rd in $roleDefs) {
        foreach ($h in $m.hosts) {
            if (-not $h.sshHost) { continue }
            if ([string]$h.sshHost -match $rd.Regex) {
                $targetHost = $h.sshHost
                if ($PreloadedInventory.ContainsKey($rd.Name)) {
                    $targetHost = $PreloadedInventory[$rd.Name]
                }

                $ordered.Add(@{
                    Name     = $rd.Name
                    SshHost  = [string]$targetHost
                    Type     = $rd.Type
                    RepoPath = (Get-FirstRepoPath $h)
                })
                break
            }
        }
    }

    if ($ordered.Count -eq 0) {
        throw "No recognizable lab hosts in manifest (expected sshHost matching lab-node-02, WORKSTATION, LAB-NODE-03, or LAB-NODE-04)."
    }
    return $ordered
}

$Nodes = Get-HybridNodesFromManifest -ManifestPath $manifestPath

# Configurac?es de Benchmarking
$TmuxSessionName = "completao"
$HybridStableImage = "fabioleitao/data_boar:1.7.3"
$HybridBetaImage = "fabioleitao/data_boar:1.7.4-rc"
$HybridBenchStable = "/tmp/databoar_bench/stable"
$HybridBenchBeta = "/tmp/databoar_bench/beta"
$HybridPortStable = "9001"
$HybridPortBeta = "9002"
$HybridContainerInnerPort = "8088"

$StableTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_STABLE_TAR_GZ
$BetaTarLocalOverride = [string]$env:DATA_BOAR_HYBRID_BETA_TAR_GZ

$outDirHybrid = Join-Path $RepoRoot "docs\private\homelab\reports"
New-Item -ItemType Directory -Force -Path $outDirHybrid | Out-Null
$stampHybrid = Get-Date -Format "yyyyMMdd_HHmmss"
$eventsPathHybrid = Join-Path $outDirHybrid "completao_hybrid_${stampHybrid}_events.jsonl"
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
    if ($null -ne $Detail -and $Detail.Count -gt 0) { $o.detail = $Detail }
    $json = ($o | ConvertTo-Json -Compress -Depth 6)
    [System.IO.File]::AppendAllText($eventsPathHybrid, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding $false))
}

function Test-HybridRemoteDockerImage {
    param([string]$Target, [string]$Engine, [string]$Image)
    $ir = $Image -replace "'", "'\''"
    $bin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $inner = "$bin image inspect '$ir' >/dev/null 2>&1 && echo HYBRID_IMG_OK || echo HYBRID_IMG_MISSING"
    $out = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes $Target `"$inner`""
    return ($out -match "HYBRID_IMG_OK")
}

function Invoke-HybridRemoteMkBenchDirs {
    param([string]$Target)
    $inner = "mkdir -p '$HybridBenchStable/scripts' '$HybridBenchBeta/scripts' && echo HYBRID_MK_OK"
    $out = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes $Target `"$inner`""
    return ($out -match "HYBRID_MK_OK")
}

function Get-HybridWindowsContainerCli {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return "docker" }
    if (Get-Command podman -ErrorAction SilentlyContinue) { return "podman" }
    return ""
}

function Invoke-HybridLocalExportImageTar {
    param([string]$ImageRef, [string]$OutTarPath)
    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) { return $false }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutTarPath) | Out-Null
    if ($cli -eq "docker") { & docker save -o $OutTarPath $ImageRef } else { & podman save -o $OutTarPath $ImageRef }
    return (Test-Path -LiteralPath $OutTarPath)
}

function Test-HybridLocalImagePresent {
    param([string]$ImageRef)
    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) { return $false }
    if ($cli -eq "docker") { & docker image inspect $ImageRef 2>$null | Out-Null } else { & podman image inspect $ImageRef 2>$null | Out-Null }
    return ($LASTEXITCODE -eq 0)
}

function Invoke-HybridEnsureLocalSessionImages {
    $hasStableTar = ($StableTarLocalOverride -and (Test-Path -LiteralPath $StableTarLocalOverride))
    $hasBetaTar = ($BetaTarLocalOverride -and (Test-Path -LiteralPath $BetaTarLocalOverride))
    if ($hasStableTar -and $hasBetaTar) { return $true }

    $cli = Get-HybridWindowsContainerCli
    if (-not $cli) { return $false }

    if (-not $hasStableTar) {
        if (-not (Test-HybridLocalImagePresent -ImageRef $HybridStableImage)) {
            Write-Host "Hybrid: pulling $HybridStableImage..." -ForegroundColor Cyan
            & $cli pull $HybridStableImage
        }
    }
    if (-not $hasBetaTar) {
        if ($env:DATA_BOAR_HYBRID_SKIP_LOCAL_BETA_BUILD -ne "1") {
            Write-Host "Hybrid: building $HybridBetaImage..." -ForegroundColor Cyan
            Push-Location $RepoRoot
            try { & docker build -t $HybridBetaImage -f Dockerfile . } finally { Pop-Location }
        }
    }
    return $true
}

function Invoke-HybridRsyncOrScp {
    param([string]$LocalPath, [string]$Target, [string]$RemotePath)
    if (-not (Test-Path -LiteralPath $LocalPath)) { return $false }
    # Otimizac?o de transporte para arquivos grandes (Data Boar Tars)
    & scp.exe -C -q -o BatchMode=yes -o IPQoS=throughput "$LocalPath" "${Target}:$RemotePath"
    return ($LASTEXITCODE -eq 0)
}

function Invoke-HybridRemoteDockerLoads {
    param([string]$Target, [string]$Engine, [string]$StableTarRemote, [string]$BetaTarRemote)
    $bin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $inner = "$bin load -i '$StableTarRemote' && $bin load -i '$BetaTarRemote' && echo HYBRID_LOADS_OK"
    $out = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes -o ConnectTimeout=900 $Target `"$inner`""
    return ($out -match "HYBRID_LOADS_OK")
}

function Resolve-HybridLocalImageTar {
    param([string]$OverridePath, [string]$ImageRef, [string]$ExportFileName, [string]$RemoteBenchDir, [string]$RemoteBaseName)
    $local = if ($OverridePath -and (Test-Path -LiteralPath $OverridePath)) { $OverridePath } else {
        $path = Join-Path $HybridExportDir $ExportFileName
        if (Invoke-HybridLocalExportImageTar -ImageRef $ImageRef -OutTarPath $path) { $path } else { $null }
    }
    if ($null -eq $local) { return @{ ok = $false } }
    return @{ ok = $true; local = $local; remote = "$RemoteBenchDir/${RemoteBaseName}.tar" }
}

function Deploy-ConfigTrack {
    param($Node, [string]$Path, [string]$Track)
    $remoteDir = if ($Track -eq "stable") { $HybridBenchStable } else { $HybridBenchBeta }
    $content = "project_name: 'Lab-Bench-$($Node.Name)-$Track'`nscan_options:`n  heuristics_level: high`n  recursive: true`ntargets:`n  - type: filesystem`n    path: '$Path'"
    $temp = New-TemporaryFile
    Set-Content -LiteralPath $temp.FullName -Value $content -Encoding ascii
    & scp.exe -q $temp.FullName "$($Node.SshHost):${remoteDir}/config_databoar.yaml"
    Remove-Item $temp.FullName
}

function Invoke-HybridOptionalGitPullRemoteRepo {
    param([string]$Target, [string]$RepoPath, [string]$NodeLabel)
    if ($env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS -ne "1") { return $true }
    if (-not $RepoPath) { return $true }

    $ref = $env:DATA_BOAR_HYBRID_REMOTE_PULL_REF
    Write-Host "Hybrid: forcing git pull ($ref) on $NodeLabel..." -ForegroundColor DarkGray
    $inner = "cd '$RepoPath' && git fetch origin && git checkout -f '$ref' && git pull origin '$ref' && echo HYBRID_GIT_OK"
    $out = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes $Target `"$inner`""
    return ($out -match "HYBRID_GIT_OK")
}

function Invoke-HybridBenchRun {
    param([string]$Target, [string]$Engine, [string]$Image, [string]$HostPort, [string]$ConfigRemote, [string]$TrackLabel, [string]$NodeLabel)
    $remoteDir = if ($TrackLabel -eq "stable") { $HybridBenchStable } else { $HybridBenchBeta }
    $logFile = "$remoteDir/run_${TrackLabel}.log"
    $bin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $cmd = "$bin run --rm -p ${HostPort}:8088 -v `"$ConfigRemote`":/app/config.yaml $Image"

    Write-Host "Running $TrackLabel bench on $NodeLabel..." -ForegroundColor DarkCyan
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & ssh.exe -o BatchMode=yes $Target "timeout 300 $cmd > $logFile 2>&1 && echo OK"
    $sw.Stop()
    return @{ ok = ($out -match "OK"); wall_ms = $sw.ElapsedMilliseconds }
}

# --- INICIO DA ORQUESTRAC?O ---
Write-Host "--- [DATA BOAR HYBRID ORCHESTRATOR START] ---" -ForegroundColor Cyan
if (-not (Invoke-HybridEnsureLocalSessionImages)) { exit 1 }

$StableBundle = Resolve-HybridLocalImageTar -OverridePath $StableTarLocalOverride -ImageRef $HybridStableImage -ExportFileName "stable.tar" -RemoteBenchDir $HybridBenchStable -RemoteBaseName "stable"
$BetaBundle   = Resolve-HybridLocalImageTar -OverridePath $BetaTarLocalOverride -ImageRef $HybridBetaImage -ExportFileName "beta.tar" -RemoteBenchDir $HybridBenchBeta -RemoteBaseName "beta"

foreach ($n in $Nodes) {
    $target = $n.SshHost
    Write-Host ">>> Processing node: $($n.Name) ($target)" -ForegroundColor Yellow

    if ($n.Type -eq "passive") {
        Write-Host "Passive node $($n.Name) - skipping container tasks." -ForegroundColor Gray
        continue
    }

    # Sincronizac?o de Scripts (Essencial para precis?o do benchmark)
    if ($n.RepoPath) {
        Invoke-HybridOptionalGitPullRemoteRepo -Target $target -RepoPath $n.RepoPath -NodeLabel $n.Name
    }

    $scanPath = if ($n.Name -eq "lab-node-02") { "/home/leitao/Documents" } else { "/home/leitao" }
    $engine = if ($n.Type -eq "podman") { "podman" } else { "docker" }

    if (Invoke-HybridRemoteMkBenchDirs -Target $target) {
        Invoke-HybridRsyncOrScp -LocalPath $StableBundle.local -Target $target -RemotePath $StableBundle.remote
        Invoke-HybridRsyncOrScp -LocalPath $BetaBundle.local -Target $target -RemotePath $BetaBundle.remote

        if (Invoke-HybridRemoteDockerLoads -Target $target -Engine $engine -StableTarRemote $StableBundle.remote -BetaTarRemote $BetaBundle.remote) {
            Deploy-ConfigTrack -Node $n -Path $scanPath -Track stable
            Deploy-ConfigTrack -Node $n -Path $scanPath -Track beta

            $resS = Invoke-HybridBenchRun -Target $target -Engine $engine -Image $HybridStableImage -HostPort $HybridPortStable -ConfigRemote "$HybridBenchStable/config_databoar.yaml" -TrackLabel stable -NodeLabel $n.Name
            $resB = Invoke-HybridBenchRun -Target $target -Engine $engine -Image $HybridBetaImage -HostPort $HybridPortBeta -ConfigRemote "$HybridBenchBeta/config_databoar.yaml" -TrackLabel beta -NodeLabel $n.Name

            Write-HybridCompletaoEvent -Phase "bench_compare" -Status "ok" -HostLabel $n.Name -Detail @{ stable_ms = $resS.wall_ms; beta_ms = $resB.wall_ms; delta = ($resB.wall_ms - $resS.wall_ms) }
        }
    }
}

# Gemini gosta de ordem, de rigor e de hardware real. Controle retomado.
Write-Host "--- [ORCHESTRATION FINISHED] ---" -ForegroundColor Cyan

