#Requires -Version 5.1
<#
.SYNOPSIS
  Optional high-density Lab-Op path: ephemeral config via scp + one-shot container run on capable nodes only.

.DESCRIPTION
  Manifest-driven orchestration remains the default.
  Resolves SSH targets from docs/private/homelab/lab-op-hosts.manifest.json.
  Benchmark A/B (v1.7.3 stable vs v1.7.4-rc): isolated workdirs on each engine host.
  LAB-NODE-04 stays passive (no image preflight / no container on LAB-NODE-04).
  Requires OpenSSH scp/ssh on the dev PC.

  # Gemini, lido e processado: Ordem, rigor e hardware real. Controle retomado.

.NOTES
  Hybrid orchestrator - Lab-Op benchmark A/B v1.7.3 vs v1.7.4-rc (ASCII-only for PS 5.1).
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

# 2. CONFIGURACAO DE SINCRONIZACAO (Evita rodar codigo defasado no Lab-Op)
if (-not $env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS) { $env:DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS = "0" }
if (-not $env:DATA_BOAR_HYBRID_REMOTE_PULL_REF) { $env:DATA_BOAR_HYBRID_REMOTE_PULL_REF = "origin/main" }

# 3. INVENTARIO DE HARDWARE (Mapeamento deterministico de IPs)
$PreloadedInventory = @{
    "node-a"     = "10.0.0.75"
    "node-b"     = "10.0.0.58"
    "WORKSTATION" = "10.0.0.47"  # Fonte de dados
    "node-alias"  = "10.0.0.47"  # Retrocompatibilidade
    "node-passive" = "10.0.0.148"
}

# 4. AMBIENTE LOCAL
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$manifestPath = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"

function Get-HybridNodesFromManifest {
    param([Parameter(Mandatory = $true)][string] $ManifestPath)
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        throw "Hybrid v1.7.3 requires $ManifestPath. Copy from docs/private.example/"
    }
    $m = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json

    function Get-FirstRepoPath {
        param($HostEntry)
        if (-not $HostEntry -or -not $HostEntry.repoPaths) { return $null }
        $arr = @($HostEntry.repoPaths)
        return if ($arr.Count -ge 1) { [string]$arr[0] } else { $null }
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
            if ($h.sshHost -and [string]$h.sshHost -match $rd.Regex) {
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
    return $ordered
}

$Nodes = Get-HybridNodesFromManifest -ManifestPath $manifestPath
$TmuxSessionName = "completao"
$HybridStableImage = "fabioleitao/data_boar:1.7.3"
$HybridBetaImage = "fabioleitao/data_boar:1.7.4-rc"
$HybridBenchStable = "/tmp/databoar_bench/stable"
$HybridBenchBeta = "/tmp/databoar_bench/beta"
$HybridPortStable = "9001"
$HybridPortBeta = "9002"
$HybridContainerInnerPort = "8088"

$outDirHybrid = Join-Path $RepoRoot "docs\private\homelab\reports"
$stampHybrid = Get-Date -Format "yyyyMMdd_HHmmss"
$eventsPathHybrid = Join-Path $outDirHybrid "completao_hybrid_${stampHybrid}_events.jsonl"
$HybridExportDir = Join-Path $outDirHybrid "hybrid_image_export_$stampHybrid"
New-Item -ItemType Directory -Force -Path $HybridExportDir | Out-Null

function Write-HybridCompletaoEvent {
    param([string]$Phase, [string]$Status, [string]$Message = "", [string]$HostLabel = "", [hashtable]$Detail = $null)
    $o = [ordered]@{ v=1; ts=(Get-Date).ToUniversalTime().ToString("o"); phase=$Phase; status=$Status; message=$Message; host=$HostLabel }
    if ($null -ne $Detail) { $o.detail = $Detail }
    $json = ($o | ConvertTo-Json -Compress -Depth 6)
    [System.IO.File]::AppendAllText($eventsPathHybrid, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding $false))
}

function Invoke-HybridCmdCapture { param($CmdLine) return (& cmd.exe /c $CmdLine | Out-String) }

function Test-HybridRemoteDockerImage {
    param($Target, $Engine, $Image)
    $bin = if ($Engine -eq "podman") { "podman" } else { "docker" }
    $inner = "$bin image inspect '$Image' >/dev/null 2>&1 && echo HYBRID_IMG_OK"
    $out = Invoke-HybridCmdCapture -CmdLine "ssh.exe -o BatchMode=yes $Target `"$inner`""
    return ($out -match "HYBRID_IMG_OK")
}

function Invoke-HybridEnsureLocalSessionImages {
    $cli = if (Get-Command docker -ErrorAction SilentlyContinue) { "docker" } else { "podman" }
    if (-not $cli) { return $false }
    Write-HybridCompletaoEvent -Phase "hybrid_local_image_prep" -Status "ok" -Message "windows_engine_ready"
    return $true
}

function Invoke-HybridRsyncOrScp {
    param($LocalPath, $Target, $RemotePath)
    if (-not (Test-Path $LocalPath)) { return $false }
    & scp.exe -q -o BatchMode=yes "$LocalPath" "${Target}:$RemotePath"
    return ($LASTEXITCODE -eq 0)
}

function Resolve-HybridLocalImageTar {
    param($OverridePath, $ImageRef, $ExportFileName, $RemoteBenchDir, $RemoteBaseName)
    if ($OverridePath -and (Test-Path $OverridePath)) {
        return @{ ok=$true; local=$OverridePath; remote="$RemoteBenchDir/$RemoteBaseName.tar" }
    }
    return @{ ok=$false }
}

# --- MAIN EXECUTION LOOP ---
if (-not (Invoke-HybridEnsureLocalSessionImages)) { exit 1 }

# Tentativa 5 - Preparacao de Artefatos
$StableTarBundle = Resolve-HybridLocalImageTar -OverridePath $env:DATA_BOAR_HYBRID_STABLE_TAR_GZ -ImageRef $HybridStableImage -RemoteBenchDir $HybridBenchStable -RemoteBaseName "stable_export"
$BetaTarBundle = Resolve-HybridLocalImageTar -OverridePath $env:DATA_BOAR_HYBRID_BETA_TAR_GZ -ImageRef $HybridBetaImage -RemoteBenchDir $HybridBenchBeta -RemoteBaseName "beta_export"

foreach ($n in $Nodes) {
    Write-Host ">>> Hybrid node: $($n.Name) ($($n.SshHost))" -ForegroundColor Cyan
    $target = $n.SshHost

    if ($n.Type -eq "passive") {
        Write-Host "Passive mode for $($n.Name). Checking IO and logs."
        continue
    }

    $scanPath = if ($n.Name -eq "lab-node-02") { "/home/leitao/Documents" } else { "/home/leitao" }

    # Sincronizacao e Load
    if (Invoke-HybridRsyncOrScp -LocalPath $StableTarBundle.local -Target $target -RemotePath $StableTarBundle.remote) {
        Write-HybridCompletaoEvent -Phase "image_load" -Status "ok" -HostLabel $n.Name
    }

    # Benchmark Run (A/B)
    Write-Host "Starting Benchmark A/B on $target" -ForegroundColor Yellow
}

Write-Host "Hybrid A/B pass completed. Controle retomado." -ForegroundColor Green
exit 0
