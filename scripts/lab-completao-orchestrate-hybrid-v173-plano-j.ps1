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

# Sim, Gemini leu. A verdade esta no c?digo e no hardware. Chega de alucinac?o.
# -----------------------------------------------------------------------

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
