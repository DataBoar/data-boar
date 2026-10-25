#Requires -Version 5.1
<#
.SYNOPSIS
  Run lab-completao-host-smoke.sh on each LAB-OP host from the manifest; save consolidated logs.

.DESCRIPTION
  Same manifest as lab-op-sync-and-collect.ps1 (docs/private/homelab/lab-op-hosts.manifest.json).
  Optional per-host "completaoHealthUrl" for remote curl from the dev PC after SSH smoke.
  Optional per-host "completaoEngineMode":"container" or "completaoSkipEngineImport":true when the host
  runs Data Boar only via Docker/Swarm/Podman (skip bare-metal uv / import core.engine) - see LAB_COMPLETAO_RUNBOOK.md.
  Optional "completaoHardwareProfile":"pi3b" (or sshHost matching pi3b): PASSIVE target only - no Docker/Podman,
  no image_preflight probe on pi3b, skip undervoltage gate for pi3b in host-smoke; IO latency snippet over SSH;
  local python3/.venv plus journal/syslog tail for T14/Latitude review.
  Optional root "completaoMainEngineSshHost": SSH alias of the primary benchmark/engine host; undervoltage on other
  hosts is logged as warning only (host-smoke never fails the orchestrator for power throttling alone).
  Image preflight is non-blocking: missing images or probe SSH failure logs warnings and continues host smoke.
  Optional "completaoHardwareProfile":"mini-bt-void" (or sshHost matching mini-bt): forces skip-engine-import and logs
  Void xbps hint for mysqlclient build deps; keep DB/Swarm-heavy work on Latitude and T14.

  Optional root "completaoDataContractsPath": YAML for scripts/lab_completao_data_contract_check.py (column contract
  preflight). Runs after lab-op-git-ensure-ref when present and the file exists. See docs/private.example/homelab/completao_data_contracts.example.yaml.

  Optional root "completaoImageRefs": JSON array of image refs (e.g. fabioleitao/data_boar:lab). When set and
  -SkipImagePreflight is not used, probes completaoImageProbeSshHost or the first non-pi3b manifest sshHost with docker/podman
  image inspect (read-only) before host smoke; missing images log warnings and the run continues (idempotent: no pull/create).

  Writes docs/private/homelab/reports/completao_<stamp>_orchestrate_events.jsonl (one JSON object per line) for tooling.

  Idempotent agent-facing JSON: each run overwrites lab_result.json and lab_status.json (same payload) via a temp
  file then move, so agents never read a half-written file. Stamped copies per run_stamp remain history artifacts.

  Exit code contract DATA_BOAR_COMPLETAO_EXIT_v1 (success path process exit): 0 = all hosts completed without degraded
  connectivity; 1 = completed_with_skips or degraded (SSH/repo skip patterns). Uncaught throws still use PowerShell
  defaults (often 1). JSON includes exit_code_semantic and audit_trail (USERNAME, COMPUTERNAME, optional env
  DATA_BOAR_COMPLETAO_INVOKER for agent or ticket correlation) for ISO 27001 / LGPD-oriented traceability.

  By default, runs scripts/lab-completao-inventory-preflight.ps1 (15-day freshness) and lab-op-sync-and-collect.ps1
  when private LAB_SOFTWARE_INVENTORY.md / OPERATOR_SYSTEM_MAP.md are missing or stale - see LAB_COMPLETAO_RUNBOOK.md.

  "Completao" is NOT pytest - see docs/ops/LAB_COMPLETAO_RUNBOOK.md.

  Optional -LabGitRef (or manifest "completaoTargetRef") runs lab-op-git-ensure-ref.ps1 before host smoke so LAB clones
  match a known ref (release tag, origin/main, branch tip). Use -AlignLabClonesToLabGitRef to reset clones (destructive).
  When pinning a tag, use -SkipGitPullOnInventoryRefresh so inventory refresh does not git pull clones to main first.

.EXAMPLE
  .\scripts\lab-completao-orchestrate.ps1

.EXAMPLE
  .\scripts\lab-completao-orchestrate.ps1 -Privileged

.EXAMPLE
  .\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef v1.2.0 -SkipGitPullOnInventoryRefresh

.EXAMPLE
  Optional fixed-matrix high-density container path (Podman on T14, Docker elsewhere, ephemeral /tmp config):
  .\scripts\lab-completao-orchestrate.ps1 -HybridLabOpHighDensity173
#>
param(
    [string] $ManifestPath = "",
    [string] $RepoRoot = "",
    [switch] $HybridLabOpHighDensity173,
    [switch] $Privileged,
    [switch] $SkipFping,
    [int] $InventoryMaxAgeDays = 15,
    [switch] $SkipInventoryPreflight,
    [switch] $SkipGitPullOnInventoryRefresh,
    [string] $LabGitRef = "",
    [switch] $SkipLabGitRefCheck,
    [switch] $AlignLabClonesToLabGitRef,
    [switch] $SkipDataContractPreflight,
    [switch] $SkipImagePreflight
)

$ErrorActionPreference = "Stop"
if ($HybridLabOpHighDensity173) {
    $hybrid = Join-Path $PSScriptRoot "lab-completao-orchestrate-hybrid-v173.ps1"
    if (-not (Test-Path -LiteralPath $hybrid)) {
        throw "Missing $hybrid"
    }
    & $hybrid
    exit $LASTEXITCODE
}
if (-not $RepoRoot) {
    $RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
}

function Get-SshHostname {
    param([string]$Alias)
    $g = & ssh -G $Alias 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    foreach ($line in $g) {
        if ($line -match '^hostname (.+)$') {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Invoke-CmdCapture {
    param([Parameter(Mandatory = $true)][string]$CmdLine)
    return (& cmd.exe /c $CmdLine | Out-String)
}

function Get-CompletaoHardwareProfile {
    param($HostEntry, [string]$Alias)
    if ($HostEntry.PSObject.Properties.Name -contains "completaoHardwareProfile" -and $HostEntry.completaoHardwareProfile) {
        return [string]$HostEntry.completaoHardwareProfile
    }
    if ($Alias -match "pi3b") {
        return "pi3b"
    }
    if ($Alias -match "mini-bt|minibt") {
        return "mini-bt-void"
    }
    return ""
}

function Test-CompletaoSshRepoDir {
    param([string]$Alias, [string]$RepoPath)
    if (-not $RepoPath) {
        return $true
    }
    $e = $RepoPath -replace "'", "'\''"
    $inner = "test -d '$e' && echo COMPLETAO_HEALTH_OK || echo COMPLETAO_HEALTH_FAIL"
    $innerEsc = $inner.Replace('"', '\"')
    $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=25 $Alias `"$innerEsc`" 2>&1"
    $out = Invoke-CmdCapture -CmdLine $remoteLine
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    return ($out -match "COMPLETAO_HEALTH_OK")
}

function Build-Pi3bPassiveRemoteCmd {
    param([string]$RepoPathEsc)
    # Single-line bash for ssh: no Docker/Podman; IO latency on /tmp; venv/system databoar --help; logs for T14/Latitude.
    return "cd '$RepoPathEsc' && { echo '=== pi3b passive path (no container engine) ==='; if [ -x .venv/bin/python3 ]; then echo 'using .venv/bin/python3 -m databoar --help'; .venv/bin/python3 -m databoar --help 2>&1 | head -n 50 || true; elif command -v python3 >/dev/null 2>&1; then echo 'no .venv; trying python3 -m databoar --help'; python3 -m databoar --help 2>&1 | head -n 50 || true; else echo 'SKIP_NO_PYTHON_OR_VENV'; fi; echo '=== pi3b IO latency (isolated /tmp file, fdatasync) ==='; sync 2>/dev/null || true; rm -f /tmp/databoar_pi3b_iolat 2>/dev/null || true; dd if=/dev/zero of=/tmp/databoar_pi3b_iolat bs=4096 count=256 conv=fdatasync 2>&1 | tail -n 6 || true; rm -f /tmp/databoar_pi3b_iolat 2>/dev/null || true; echo '=== recent logs (journal/syslog) ==='; journalctl -n 120 --no-pager 2>/dev/null || true; test -r /var/log/syslog && tail -n 80 /var/log/syslog 2>/dev/null || true; test -r /var/log/messages && tail -n 80 /var/log/messages 2>/dev/null || true; df -h 2>/dev/null | head -n 24 || true; } 2>&1"
}

function Write-CompletaoOrchestrateEvent {
    param(
        [Parameter(Mandatory = $true)][string]$ReportPath,
        [Parameter(Mandatory = $true)][string]$Phase,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Message = "",
        [string]$HostAlias = "",
        [int]$ExitCode = 0,
        [hashtable]$Detail = $null
    )
    $o = [ordered]@{
        v        = 1
        ts       = (Get-Date).ToUniversalTime().ToString("o")
        phase    = $Phase
        status   = $Status
        message  = $Message
        host     = $HostAlias
        exitCode = $ExitCode
    }
    if ($null -ne $Detail -and $Detail.Count -gt 0) {
        $o.detail = $Detail
    }
    $json = ($o | ConvertTo-Json -Compress -Depth 8)
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($ReportPath, $json + [Environment]::NewLine, $enc)
}

function Add-CompletaoHostConnectivityRecord {
    param(
        [Parameter(Mandatory = $true)][System.Collections.Generic.List[object]]$Records,
        [Parameter(Mandatory = $true)][string]$Alias,
        [bool]$SshProbeOk,
        [Parameter(Mandatory = $true)][string]$Outcome,
        [string]$LogFileName = "",
        [double]$ElapsedSec = 0.0
    )
    $row = [ordered]@{
        sshHost         = $Alias
        ssh_probe_ok    = $SshProbeOk
        outcome         = $Outcome
        host_log        = $LogFileName
        seconds_elapsed = [math]::Round([double]$ElapsedSec, 2)
    }
    [void]$Records.Add($row)
}

function Write-CompletaoLabResultJsonFiles {
    param(
        [Parameter(Mandatory = $true)][string]$OutDir,
        [Parameter(Mandatory = $true)][string]$Stamp,
        [Parameter(Mandatory = $true)][object]$Payload
    )
    $json = $Payload | ConvertTo-Json -Depth 14
    $enc = New-Object System.Text.UTF8Encoding $false
    $latest = Join-Path $OutDir "lab_result.json"
    $stamped = Join-Path $OutDir "completao_${Stamp}_lab_result.json"
    $statusAlias = Join-Path $OutDir "lab_status.json"
    $tmpName = "lab_result." + [Guid]::NewGuid().ToString("n") + ".tmp"
    $tmp = Join-Path $OutDir $tmpName
    try {
        [System.IO.File]::WriteAllText($tmp, $json, $enc)
        if (Test-Path -LiteralPath $latest) {
            Remove-Item -LiteralPath $latest -Force
        }
        Move-Item -LiteralPath $tmp -Destination $latest -Force
    } catch {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
        throw
    }
    Copy-Item -LiteralPath $latest -Destination $stamped -Force
    Copy-Item -LiteralPath $latest -Destination $statusAlias -Force
}

function Test-CompletaoSshProbe {
    param([Parameter(Mandatory = $true)][string]$Alias)
    $probeCmd = "ssh.exe -o BatchMode=yes -o ConnectTimeout=12 $Alias `"echo LABOP_SSH_OK`" 2>&1"
    $probeText = Invoke-CmdCapture -CmdLine $probeCmd
    return ($LASTEXITCODE -eq 0 -and $probeText -match "LABOP_SSH_OK")
}

function Get-CompletaoImageRefsFromManifest {
    param($ManifestObj)
    $list = New-Object System.Collections.Generic.List[string]
    if (-not $ManifestObj) {
        return ,$list.ToArray()
    }
    if ($ManifestObj.PSObject.Properties.Name -notcontains "completaoImageRefs") {
        return ,$list.ToArray()
    }
    $raw = $ManifestObj.completaoImageRefs
    if ($null -eq $raw) {
        return ,$list.ToArray()
    }
    # If JSON stored a single string, foreach over @($raw) would iterate characters ([char]) and break
    # Test-CompletaoRemoteDockerImage -ImageRef ([string] binding).
    if ($raw -is [string]) {
        $v = $raw.Trim()
        if ($v) {
            $list.Add($v)
        }
        return ,$list.ToArray()
    }
    foreach ($x in @($raw)) {
        if ($null -eq $x) {
            continue
        }
        if ($x -is [string]) {
            $s = $x.Trim()
            if ($s) {
                $list.Add($s)
            }
            continue
        }
        if ($null -ne $x.ref) {
            $s = [string]$x.ref
            if ($s -and $s.Trim()) {
                $list.Add($s.Trim())
            }
        } elseif ($null -ne $x.image) {
            $s = [string]$x.image
            if ($s -and $s.Trim()) {
                $list.Add($s.Trim())
            }
        }
    }
    return ,$list.ToArray()
}

function Test-CompletaoHostEntryIsPi3b {
    param($HostEntry, [string]$Alias)
    if ($Alias -match '(?i)pi3b') {
        return $true
    }
    if ($HostEntry) {
        $p = Get-CompletaoHardwareProfile -HostEntry $HostEntry -Alias $Alias
        return ($p -match '^pi3b')
    }
    return $false
}

function Test-CompletaoHostEntrySkipsImageProbe {
    param($HostEntry, [string]$Alias)
    if (Test-CompletaoHostEntryIsPi3b -HostEntry $HostEntry -Alias $Alias) {
        return $true
    }
    if ($Alias -match '(?i)mini-bt|^minibt$') {
        return $true
    }
    if ($HostEntry) {
        $p = Get-CompletaoHardwareProfile -HostEntry $HostEntry -Alias $Alias
        if ($p -match '^mini-bt-void') {
            return $true
        }
    }
    return $false
}

function Get-CompletaoImageProbeAlias {
    param($ManifestObj)
    if (-not $ManifestObj) {
        return ""
    }
    # Skip passive pi3b and mini-bt Void (no container engine / missing deps): never use them for image inspect.
    if ($ManifestObj.PSObject.Properties.Name -contains "completaoImageProbeSshHost" -and $ManifestObj.completaoImageProbeSshHost) {
        $cand = [string]$ManifestObj.completaoImageProbeSshHost
        $he = $null
        foreach ($hx in $ManifestObj.hosts) {
            if ($hx.sshHost -and [string]$hx.sshHost -eq $cand) {
                $he = $hx
                break
            }
        }
        if (-not (Test-CompletaoHostEntrySkipsImageProbe -HostEntry $he -Alias $cand)) {
            return $cand
        }
    }
    foreach ($h2 in $ManifestObj.hosts) {
        if (-not $h2.sshHost) {
            continue
        }
        $a2 = [string]$h2.sshHost
        if (Test-CompletaoHostEntrySkipsImageProbe -HostEntry $h2 -Alias $a2) {
            continue
        }
        return $a2
    }
    return ""
}

function Write-CompletaoHostSmokeEmbeddedJsonlLines {
    param(
        [Parameter(Mandatory = $true)][string]$ReportPath,
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
            [System.IO.File]::AppendAllText($ReportPath, $payload + [Environment]::NewLine, $enc)
        } catch {
            Write-Warning "lab-completao-orchestrate: host_smoke embedded JSONL line skipped (parse): $($line.Substring(0, [Math]::Min(120, $line.Length)))"
        }
    }
}

function Test-CompletaoRemoteDockerImage {
    param(
        [Parameter(Mandatory = $true)][string]$Alias,
        [Parameter(Mandatory = $true)][string]$ImageRef
    )
    if ($ImageRef -notmatch '^[a-zA-Z0-9_.\/:@-]+$') {
        return $false
    }
    $ir = $ImageRef -replace "'", "'\''"
    $inner = "if command -v docker >/dev/null 2>&1 && docker image inspect '$ir' >/dev/null 2>&1; then echo COMPLETAO_IMG_OK; elif command -v podman >/dev/null 2>&1 && podman image inspect '$ir' >/dev/null 2>&1; then echo COMPLETAO_IMG_OK; else echo COMPLETAO_IMG_MISSING; fi"
    $innerEsc = $inner.Replace('"', '\"')
    $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=45 $Alias `"$innerEsc`" 2>&1"
    $out = Invoke-CmdCapture -CmdLine $remoteLine
    return ($LASTEXITCODE -eq 0 -and $out -match "COMPLETAO_IMG_OK")
}

$primaryManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.json"
$fallbackManifest = Join-Path $RepoRoot "docs\private\homelab\lab-op-hosts.manifest.example.json"
if (-not $ManifestPath) {
    if (Test-Path -LiteralPath $primaryManifest) {
        $ManifestPath = $primaryManifest
    } elseif (Test-Path -LiteralPath $fallbackManifest) {
        $ManifestPath = $fallbackManifest
        Write-Warning "Using example manifest; copy to lab-op-hosts.manifest.json for real hosts."
    }
}
if (-not $ManifestPath -or -not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing manifest: copy docs/private.example/homelab/lab-op-hosts.manifest.example.json to docs/private/homelab/lab-op-hosts.manifest.json"
}

try {
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
} catch {
    throw "Invalid lab manifest JSON: $($_.Exception.Message)"
}

$outDir = Join-Path $RepoRoot "docs\private\homelab\reports"
if ($manifest.outDir) {
    $outDir = $manifest.outDir -replace "/", [IO.Path]::DirectorySeparatorChar
    if (-not [IO.Path]::IsPathRooted($outDir)) {
        $outDir = Join-Path $RepoRoot $outDir
    }
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$eventsPath = Join-Path $outDir "completao_${stamp}_orchestrate_events.jsonl"
Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "orchestrate" -Status "ok" -Message "start"

$labResultStarted = Get-Date
$LabHostRecords = New-Object System.Collections.Generic.List[object]
$LabResultPhases = [ordered]@{
    inventory_preflight     = "not_run"
    lab_git_ensure_ref      = "not_run"
    data_contract_preflight = "not_run"
    image_preflight         = "not_run"
    host_smoke_loop        = "pending"
}

if (-not $SkipInventoryPreflight) {
    $preflight = Join-Path $RepoRoot "scripts\lab-completao-inventory-preflight.ps1"
    if (Test-Path -LiteralPath $preflight) {
        try {
            & $preflight -RepoRoot $RepoRoot -ManifestPath $ManifestPath -MaxAgeDays $InventoryMaxAgeDays -AutoRefresh -SkipFping:$SkipFping -SkipGitPullOnRefresh:$SkipGitPullOnInventoryRefresh
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "inventory_preflight" -Status "ok" -Message "completed"
            $LabResultPhases.inventory_preflight = "ok"
        } catch {
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "inventory_preflight" -Status "failed" -Message $_.Exception.Message
            $LabResultPhases.inventory_preflight = "failed"
            throw
        }
    } else {
        Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "inventory_preflight" -Status "skipped" -Message "script_missing"
        $LabResultPhases.inventory_preflight = "skipped_missing_script"
    }
} else {
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "inventory_preflight" -Status "skipped" -Message "SkipInventoryPreflight_switch"
    $LabResultPhases.inventory_preflight = "skipped_switch"
}

$effectiveLabRef = $LabGitRef
if (-not $effectiveLabRef -and $manifest.PSObject.Properties.Name -contains "completaoTargetRef" -and $manifest.completaoTargetRef) {
    $effectiveLabRef = [string]$manifest.completaoTargetRef
}
if ($effectiveLabRef -and -not $SkipLabGitRefCheck) {
    $ensureScript = Join-Path $RepoRoot "scripts\lab-op-git-ensure-ref.ps1"
    if (-not (Test-Path -LiteralPath $ensureScript)) {
        throw "Missing $ensureScript"
    }
    $ensureMode = "Check"
    if ($AlignLabClonesToLabGitRef) {
        $ensureMode = "Reset"
    }
    Write-Host "lab-completao-orchestrate: lab-op-git-ensure-ref ref=$effectiveLabRef mode=$ensureMode" -ForegroundColor Cyan
    try {
        & $ensureScript -RepoRoot $RepoRoot -ManifestPath $ManifestPath -Ref $effectiveLabRef -Mode $ensureMode -SkipFping:$SkipFping
        if ($LASTEXITCODE -ne 0) {
            throw "lab-op-git-ensure-ref failed (ref=$effectiveLabRef mode=$ensureMode). Align LAB clones or use -SkipLabGitRefCheck. See docs/ops/LAB_COMPLETAO_RUNBOOK.md (Target git ref for reproducible completao)."
        }
        Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "lab_git_ensure_ref" -Status "ok" -Message "completed" -Detail @{ ref = $effectiveLabRef; mode = $ensureMode }
        $LabResultPhases.lab_git_ensure_ref = "ok"
    } catch {
        Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "lab_git_ensure_ref" -Status "failed" -Message $_.Exception.Message -Detail @{ ref = $effectiveLabRef; mode = $ensureMode }
        $LabResultPhases.lab_git_ensure_ref = "failed"
        throw
    }
} elseif ($effectiveLabRef -and $SkipLabGitRefCheck) {
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "lab_git_ensure_ref" -Status "skipped" -Message "SkipLabGitRefCheck_switch"
    $LabResultPhases.lab_git_ensure_ref = "skipped_switch"
} else {
    $LabResultPhases.lab_git_ensure_ref = "not_configured"
}

if (-not $SkipDataContractPreflight) {
    $contractsRel = ""
    if ($manifest.PSObject.Properties.Name -contains "completaoDataContractsPath" -and $manifest.completaoDataContractsPath) {
        $contractsRel = [string]$manifest.completaoDataContractsPath
    }
    if (-not $contractsRel) {
        $LabResultPhases.data_contract_preflight = "skipped_no_yaml_configured"
    }
    if ($contractsRel) {
        $contractsPath = if ([IO.Path]::IsPathRooted($contractsRel)) {
            $contractsRel
        } else {
            Join-Path $RepoRoot ($contractsRel -replace "/", [IO.Path]::DirectorySeparatorChar)
        }
        if (-not (Test-Path -LiteralPath $contractsPath)) {
            throw "completaoDataContractsPath is set but file not found: $contractsPath. Create the YAML under docs/private/homelab/ or remove the manifest key. See docs/private.example/homelab/completao_data_contracts.example.yaml"
        }
        $checker = Join-Path $RepoRoot "scripts\lab_completao_data_contract_check.py"
        if (-not (Test-Path -LiteralPath $checker)) {
            throw "Missing $checker"
        }
        Write-Host "lab-completao-orchestrate: data contract preflight -> $contractsPath" -ForegroundColor Cyan
        try {
            Push-Location $RepoRoot
            try {
                & uv run python $checker --contracts $contractsPath
            } finally {
                Pop-Location
            }
            if ($LASTEXITCODE -ne 0) {
                throw "Data contract check failed (exit $LASTEXITCODE). Fix lab schema or env URLs, or use -SkipDataContractPreflight to bypass."
            }
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "data_contract_preflight" -Status "ok" -Message "completed" -Detail @{ contractsPath = $contractsPath }
            $LabResultPhases.data_contract_preflight = "ok"
        } catch {
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "data_contract_preflight" -Status "failed" -Message $_.Exception.Message -Detail @{ contractsPath = $contractsPath }
            $LabResultPhases.data_contract_preflight = "failed"
            throw
        }
    }
} else {
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "data_contract_preflight" -Status "skipped" -Message "SkipDataContractPreflight_switch"
    $LabResultPhases.data_contract_preflight = "skipped_switch"
}

if (-not $SkipImagePreflight) {
    $imgRefs = @(Get-CompletaoImageRefsFromManifest -ManifestObj $manifest)
    $hasImageRefsKey = ($manifest.PSObject.Properties.Name -contains "completaoImageRefs")
    if ($hasImageRefsKey -and $imgRefs.Count -eq 0) {
        Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "skipped" -Message "completaoImageRefs_empty_array"
        $LabResultPhases.image_preflight = "skipped_empty_array"
    }
    if ($imgRefs.Count -gt 0) {
        $probeHost = Get-CompletaoImageProbeAlias -ManifestObj $manifest
        if (-not $probeHost) {
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "warning" -Message "no_engine_probe_host_skipped" -Detail @{ note = "pi3b and mini-bt-void excluded from image inspect; set completaoImageProbeSshHost to an engine host (Latitude/T14) or add one before mini-bt in manifest order" }
            $LabResultPhases.image_preflight = "skipped_no_engine_probe_host"
            Write-Warning "lab-completao-orchestrate: completaoImageRefs set but no engine host for image inspect after skipping pi3b/mini-bt (non-blocking)."
        } elseif (-not (Test-CompletaoSshProbe -Alias $probeHost)) {
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "warning" -Message "ssh_probe_failed_nonblocking" -HostAlias $probeHost
            $LabResultPhases.image_preflight = "warning_ssh_probe_failed"
            Write-Warning "lab-completao-orchestrate: image preflight SSH probe failed for $probeHost (non-blocking)."
        } else {
            $missingList = New-Object System.Collections.Generic.List[string]
            foreach ($ir in $imgRefs) {
                if ($null -eq $ir) {
                    continue
                }
                $imageRef = [Convert]::ToString($ir, [System.Globalization.CultureInfo]::InvariantCulture).Trim()
                if (-not $imageRef) {
                    continue
                }
                if (-not (Test-CompletaoRemoteDockerImage -Alias $probeHost -ImageRef $imageRef)) {
                    [void]$missingList.Add($imageRef)
                }
            }
            if ($missingList.Count -gt 0) {
                $joined = ($missingList.ToArray() -join ",")
                Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "warning" -Message "image_missing_nonblocking" -HostAlias $probeHost -Detail @{ missing = $joined }
                $LabResultPhases.image_preflight = "warning_missing_images"
                Write-Warning "lab-completao-orchestrate: image(s) not on ${probeHost}: $joined (non-blocking). Pull/load on lab or use -SkipImagePreflight."
            } else {
                Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "ok" -Message "all_images_present" -HostAlias $probeHost -Detail @{ images = (($imgRefs | ForEach-Object { [Convert]::ToString($_, [System.Globalization.CultureInfo]::InvariantCulture) }) -join ",") }
                $LabResultPhases.image_preflight = "ok"
            }
        }
    }
    if ($LabResultPhases.image_preflight -eq "not_run") {
        $LabResultPhases.image_preflight = "not_configured"
    }
} else {
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "image_preflight" -Status "skipped" -Message "SkipImagePreflight_switch"
    $LabResultPhases.image_preflight = "skipped_switch"
}

$fping = Get-Command fping -ErrorAction SilentlyContinue

$privArg = ""
if ($Privileged) { $privArg = " --privileged" }

$completaoMainEngineSshHost = ""
if ($manifest.PSObject.Properties.Name -contains "completaoMainEngineSshHost" -and $manifest.completaoMainEngineSshHost) {
    $completaoMainEngineSshHost = [string]$manifest.completaoMainEngineSshHost
}

$master = [System.Text.StringBuilder]::new()
[void]$master.AppendLine("=== lab-completao-orchestrate $stamp ===")
[void]$master.AppendLine("repo: $RepoRoot")

$hostLoopStarted = Get-Date
$LabResultPhases.host_smoke_loop = "running"

foreach ($h in $manifest.hosts) {
    $alias = $h.sshHost
    if (-not $alias) { continue }

    try {
    $HostRecordAdded = $false
    $hostStopwatch = [Diagnostics.Stopwatch]::StartNew()

    $healthUrl = ""
    if ($h.PSObject.Properties.Name -contains "completaoHealthUrl" -and $h.completaoHealthUrl) {
        $healthUrl = [string]$h.completaoHealthUrl
    }

    $skipEngineImport = $false
    if ($h.PSObject.Properties.Name -contains "completaoSkipEngineImport") {
        $v = $h.completaoSkipEngineImport
        if ($v -eq $true -or "$v" -eq "true") { $skipEngineImport = $true }
    }
    if ($h.PSObject.Properties.Name -contains "completaoEngineMode") {
        $em = [string]$h.completaoEngineMode
        if ($em -eq "container") { $skipEngineImport = $true }
    }

    $hwProfile = Get-CompletaoHardwareProfile -HostEntry $h -Alias $alias
    if ($hwProfile -match '^mini-bt-void') {
        $skipEngineImport = $true
    }

    Write-Host "=== Host: $alias ===" -ForegroundColor Cyan
    $hostLogSb = [System.Text.StringBuilder]::new()
    [void]$hostLogSb.AppendLine("=== lab-completao-orchestrate $stamp host=$alias ===")
    [void]$master.AppendLine("")
    [void]$master.AppendLine("### SSH host: $alias ###")

    if (-not $SkipFping -and $fping) {
        $hn = Get-SshHostname -Alias $alias
        if ($hn) {
            $fp = & fping -c 1 -t 400 $hn 2>&1 | Out-String
            [void]$hostLogSb.AppendLine($fp)
            [void]$master.AppendLine($fp)
        }
    }

    if (-not (Test-CompletaoSshProbe -Alias $alias)) {
        Write-Warning "SSH probe failed for $alias - skip (skip-on-failure)."
        [void]$master.AppendLine("SSH probe FAILED (skip-on-failure)")
        [void]$hostLogSb.AppendLine("SSH probe FAILED (skip-on-failure)")
        $safe = ($alias -replace '[^\w\-\.]', '_')
        $logfn = "${safe}_${stamp}_completao_host_smoke.log"
        Set-Content -LiteralPath (Join-Path $outDir $logfn) -Value $hostLogSb.ToString() -Encoding utf8
        $hostStopwatch.Stop()
        Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $false -Outcome "ssh_unreachable" -LogFileName $logfn -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
        $HostRecordAdded = $true
        continue
    }

    $firstRepo = $null
    foreach ($rp in $h.repoPaths) {
        if ($rp) {
            $firstRepo = $rp
            break
        }
    }
    if ($firstRepo -and -not (Test-CompletaoSshRepoDir -Alias $alias -RepoPath $firstRepo)) {
        Write-Warning "Completao health check failed (repo dir missing or SSH error) for $alias path=$firstRepo - skip host (skip-on-failure)."
        [void]$master.AppendLine("REPO_HEALTH_FAIL skip-on-failure firstRepo=$firstRepo")
        [void]$hostLogSb.AppendLine("REPO_HEALTH_FAIL skip-on-failure firstRepo=$firstRepo")
        $safe = ($alias -replace '[^\w\-\.]', '_')
        $logfn = "${safe}_${stamp}_completao_host_smoke.log"
        Set-Content -LiteralPath (Join-Path $outDir $logfn) -Value $hostLogSb.ToString() -Encoding utf8
        $hostStopwatch.Stop()
        Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $true -Outcome "repo_path_unreachable" -LogFileName $logfn -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
        $HostRecordAdded = $true
        continue
    }

    if ($hwProfile -match '^mini-bt-void') {
        $voidNote = "LAB_NOTE mini-bt Void: run sudo xbps-install -S libmariadbclient-devel pkg-config if mysqlclient build fails; if uv sync still fails, use a private clone branch or gitignored local pyproject overlay on that host only (do not strip DB deps from the canonical Git repo); keep MariaDB/DB scan load on Latitude/T14; this host: filesystem + logs + skip-engine-import."
        [void]$hostLogSb.AppendLine($voidNote)
        [void]$master.AppendLine($voidNote)
        Write-Host $voidNote -ForegroundColor DarkYellow
    }

    if ($hwProfile -match '^pi3b') {
        $piRp = $firstRepo
        if (-not $piRp) {
            $piRp = "/home/leitao"
            $piNote = "PI3B_NOTE no repoPaths in manifest; using passive base $piRp (NFS/home or operator default)."
            Write-Host $piNote -ForegroundColor DarkYellow
            [void]$master.AppendLine($piNote)
            [void]$hostLogSb.AppendLine($piNote)
        }
        if (-not (Test-CompletaoSshRepoDir -Alias $alias -RepoPath $piRp)) {
            Write-Warning "Pi3B health: passive base missing or unreadable $piRp - skip host (skip-on-failure)."
            [void]$master.AppendLine("PI3B_HEALTH_FAIL skip-on-failure path=$piRp")
            [void]$hostLogSb.AppendLine("PI3B_HEALTH_FAIL skip-on-failure path=$piRp")
            $safe = ($alias -replace '[^\w\-\.]', '_')
            $logfn = "${safe}_${stamp}_completao_host_smoke.log"
            Set-Content -LiteralPath (Join-Path $outDir $logfn) -Value $hostLogSb.ToString() -Encoding utf8
            $hostStopwatch.Stop()
            Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $true -Outcome "pi3b_base_unreachable" -LogFileName $logfn -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
            $HostRecordAdded = $true
            continue
        }
        $rpEsc = $piRp -replace "'", "'\''"
        $piRemote = Build-Pi3bPassiveRemoteCmd -RepoPathEsc $rpEsc
        $piRemoteEsc = $piRemote.Replace('"', '\"')
        $piLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=180 -o ServerAliveInterval=15 -o ServerAliveCountMax=8 $alias `"$piRemoteEsc`" 2>&1"
        $piOut = Invoke-CmdCapture -CmdLine $piLine
        [void]$hostLogSb.AppendLine("--- pi3b passive (no Docker / no container smoke) repo: $piRp ---")
        [void]$hostLogSb.AppendLine($piOut)
        [void]$master.AppendLine("--- pi3b passive repo: $piRp ---")
        [void]$master.AppendLine($piOut)
        if ($healthUrl) {
            try {
                $r = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 15 -UseBasicParsing
                $curlLine = "dev-PC curl completaoHealthUrl: HTTP $($r.StatusCode) len=$($r.RawContentLength)"
                [void]$hostLogSb.AppendLine($curlLine)
                [void]$master.AppendLine($curlLine)
            } catch {
                $curlFail = "dev-PC curl completaoHealthUrl FAILED: $($_.Exception.Message)"
                [void]$hostLogSb.AppendLine($curlFail)
                [void]$master.AppendLine($curlFail)
            }
        }
        $safe = ($alias -replace '[^\w\-\.]', '_')
        $oneFile = Join-Path $outDir "${safe}_${stamp}_completao_host_smoke.log"
        Set-Content -LiteralPath $oneFile -Value $hostLogSb.ToString() -Encoding utf8
        Write-Host "Wrote $oneFile (pi3b passive path)" -ForegroundColor Green
        $hostStopwatch.Stop()
        $logfn = "${safe}_${stamp}_completao_host_smoke.log"
        Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $true -Outcome "pi3b_passive_completed" -LogFileName $logfn -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
        $HostRecordAdded = $true
        continue
    }

    foreach ($rp in $h.repoPaths) {
        if (-not $rp) { continue }
        $rpEsc = $rp -replace "'", "'\''"
        $healthEsc = ""
        if ($healthUrl) {
            $hu = $healthUrl -replace "'", "'\''"
            $healthEsc = " --health-url '$hu'"
        }
        $skipEsc = ""
        if ($skipEngineImport) { $skipEsc = " --skip-engine-import" }
        $benchEsc = ""
        if ($h.PSObject.Properties.Name -contains "completaoBenchTrack" -and $h.completaoBenchTrack) {
            $bt = [string]$h.completaoBenchTrack
            if ($bt -match "^(stable|beta)$") {
                $benchEsc = " --bench-track $bt"
            }
        }
        $mePrefix = ""
        if ($completaoMainEngineSshHost) {
            $meEsc = $completaoMainEngineSshHost -replace "'", "'\''"
            $mePrefix = "export LAB_COMPLETAO_MAIN_ENGINE_SSH_HOST='$meEsc'; "
        }
        $aliasEsc = $alias -replace "'", "'\''"
        $aliasExport = "export LAB_COMPLETAO_SSH_HOST_ALIAS='$aliasEsc'; "
        # Require an up-to-date clone (script ships on main); clear message if missing after git sync.
        $remoteCmd = "${mePrefix}${aliasExport}cd '$rpEsc' && if [ ! -f scripts/lab-completao-host-smoke.sh ]; then echo 'MISSING_SCRIPT: scripts/lab-completao-host-smoke.sh not in clone - on the host: cd to repo, git fetch origin && integrate origin/main (see docs/ops/LAB_COMPLETAO_RUNBOOK.md)'; exit 2; fi && bash scripts/lab-completao-host-smoke.sh$privArg$healthEsc$skipEsc$benchEsc 2>&1"
        $remoteCmdEsc = $remoteCmd.Replace('"', '\"')
        $remoteLine = "ssh.exe -o BatchMode=yes -o ConnectTimeout=180 -o ServerAliveInterval=15 -o ServerAliveCountMax=8 $alias `"$remoteCmdEsc`" 2>&1"
        $remoteOut = Invoke-CmdCapture -CmdLine $remoteLine
        Write-CompletaoHostSmokeEmbeddedJsonlLines -ReportPath $eventsPath -RemoteText $remoteOut
        [void]$hostLogSb.AppendLine("--- repo: $rp ---")
        [void]$hostLogSb.AppendLine($remoteOut)
        [void]$master.AppendLine("--- repo: $rp ---")
        [void]$master.AppendLine($remoteOut)
    }

    if ($healthUrl) {
        try {
            $r = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 15 -UseBasicParsing
            $curlLine = "dev-PC curl completaoHealthUrl: HTTP $($r.StatusCode) len=$($r.RawContentLength)"
            [void]$hostLogSb.AppendLine($curlLine)
            [void]$master.AppendLine($curlLine)
        } catch {
            $curlFail = "dev-PC curl completaoHealthUrl FAILED: $($_.Exception.Message)"
            [void]$hostLogSb.AppendLine($curlFail)
            [void]$master.AppendLine($curlFail)
        }
    }

    $safe = ($alias -replace '[^\w\-\.]', '_')
    $oneFile = Join-Path $outDir "${safe}_${stamp}_completao_host_smoke.log"
    Set-Content -LiteralPath $oneFile -Value $hostLogSb.ToString() -Encoding utf8
    Write-Host "Wrote $oneFile" -ForegroundColor Green
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "host_smoke" -Status "ok" -Message "host_log_written" -HostAlias $alias
    $hostStopwatch.Stop()
    $logfn = "${safe}_${stamp}_completao_host_smoke.log"
    Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $true -Outcome "smoke_log_written" -LogFileName $logfn -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
    $HostRecordAdded = $true

    } catch {
        if (-not $HostRecordAdded) {
            $hostStopwatch.Stop()
            Add-CompletaoHostConnectivityRecord -Records $LabHostRecords -Alias $alias -SshProbeOk $false -Outcome "host_exception" -LogFileName "" -ElapsedSec $hostStopwatch.Elapsed.TotalSeconds
        }
        Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "host_smoke" -Status "failed" -Message $_.Exception.Message -HostAlias $alias
        Write-Warning "lab-completao-orchestrate: unexpected error for host $alias : $($_.Exception.Message)"
        [void]$master.AppendLine("HOST_EXCEPTION $alias : $($_.Exception.Message)")
    }
}

$manifestHostCount = 0
if ($manifest.hosts) {
    $manifestHostCount = @($manifest.hosts).Count
}
Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "summary" -Status "ok" -Message "orchestrate_host_loop_finished" -Detail @{ hostsInManifest = $manifestHostCount; eventsPath = $eventsPath }

$allFile = Join-Path $outDir "completao_${stamp}_allhosts.log"
Set-Content -LiteralPath $allFile -Value $master.ToString() -Encoding utf8
Write-Host "Wrote consolidated $allFile" -ForegroundColor Green

$hostLoopSec = [math]::Round(((Get-Date) - $hostLoopStarted).TotalSeconds, 2)
$LabResultPhases.host_smoke_loop = "completed"
$withSkips = @($LabHostRecords | Where-Object { $_.outcome -ne "smoke_log_written" -and $_.outcome -ne "pi3b_passive_completed" })
if ($withSkips.Count -gt 0) {
    $LabResultPhases.host_smoke_loop = "completed_with_skips"
}

$connSummary = "no_host_records"
if ($LabHostRecords.Count -gt 0) {
    $bad = @($LabHostRecords | Where-Object { $_.outcome -match "unreachable|exception|repo_path|base_unreachable" })
    if ($bad.Count -eq 0) {
        $connSummary = "all_hosts_completed_paths_ok"
    } else {
        $connSummary = "degraded"
    }
}

$perHostSec = [ordered]@{}
foreach ($rec in $LabHostRecords) {
    if ($rec.sshHost) {
        $perHostSec[$rec.sshHost] = $rec.seconds_elapsed
    }
}

$wallAll = [math]::Round(((Get-Date) - $labResultStarted).TotalSeconds, 2)

$orchestrationChecks = New-Object System.Collections.Generic.List[object]
foreach ($stepName in @(
        "inventory_preflight",
        "lab_git_ensure_ref",
        "data_contract_preflight",
        "image_preflight",
        "host_smoke_loop"
    )) {
    $stepResult = [string]$LabResultPhases[$stepName]
    [void]$orchestrationChecks.Add([ordered]@{ step = $stepName; result = $stepResult })
}

$overallStatus = "completed"
if ($connSummary -eq "degraded") {
    $overallStatus = "degraded"
} elseif ($LabResultPhases.host_smoke_loop -eq "completed_with_skips") {
    $overallStatus = "completed_with_skips"
}

$semanticExit = 0
$semanticReason = "all_hosts_ok_no_degraded_connectivity"
if ($overallStatus -eq "degraded") {
    $semanticExit = 1
    $semanticReason = "connectivity_degraded_or_host_path_failure"
} elseif ($overallStatus -eq "completed_with_skips") {
    $semanticExit = 1
    $semanticReason = "completed_with_unreachable_or_skipped_hosts"
}

$invokerCorrelation = ""
if ($env:DATA_BOAR_COMPLETAO_INVOKER) {
    $invokerCorrelation = [string]$env:DATA_BOAR_COMPLETAO_INVOKER
}

$auditTrail = [ordered]@{
    schema                  = "DATA_BOAR_LAB_AUDIT_TRAIL_v1"
    recorded_at_utc         = (Get-Date).ToUniversalTime().ToString("o")
    windows_session_user    = $env:USERNAME
    windows_computer_name   = $env:COMPUTERNAME
    powershell_pid          = $PID
    invoker_correlation     = $invokerCorrelation
    invoker_correlation_env = "DATA_BOAR_COMPLETAO_INVOKER"
    note                    = "Lab orchestration traceability; not a legal attestation. Set DATA_BOAR_COMPLETAO_INVOKER for agent or ticket id when automating."
}

$exitSemantic = [ordered]@{
    contract = "DATA_BOAR_COMPLETAO_EXIT_v1"
    value    = $semanticExit
    reason   = $semanticReason
    meanings = [ordered]@{
        "0" = "full_success"
        "1" = "infrastructure_reachability_permission_or_partial_lab_skip"
        "2" = "data_contract_schema_repo_clone_or_config_shape"
        "3" = "compliance_violation_signal_reserved_for_scanners"
    }
}

$labPayload = [ordered]@{
    schemaVersion          = 1
    kind                   = "data_boar_lab_completao_orchestrate"
    run_stamp              = $stamp
    generated_at_utc       = (Get-Date).ToUniversalTime().ToString("o")
    repo_folder_name       = (Split-Path $RepoRoot -Leaf)
    manifest_file_name     = (Split-Path $ManifestPath -Leaf)
    audit_trail            = $auditTrail
    exit_code_semantic     = $exitSemantic
    overall_status         = $overallStatus
    phases                 = $LabResultPhases
    orchestration_checks   = @($orchestrationChecks.ToArray())
        idempotency            = @{
        latest_json_atomically_overwritten = @("lab_result.json", "lab_status.json", "GRC_EXECUTIVE_REPORT.json", "GRC_EXECUTIVE_REPORT_remediation.xlsx", "GRC_EXECUTIVE_REPORT_executive.pdf")
        stamped_artifacts_per_run            = @("completao_<stamp>_orchestrate_events.jsonl", "completao_<stamp>_allhosts.log", "completao_<stamp>_lab_result.json", "completao_<stamp>_GRC_EXECUTIVE_REPORT.json", "completao_<stamp>_GRC_EXECUTIVE_REPORT_remediation.xlsx", "completao_<stamp>_GRC_EXECUTIVE_REPORT_executive.pdf", "<host>_<stamp>_completao_host_smoke.log")
        note                                 = "Re-running with the same LAB state and flags yields the same phase keys; timestamps and stamped filenames always change. GRC JSON is best-effort after lab_result (see scripts/generate_grc_report.py). When GRC succeeds, scripts/export_reports.py writes GRC_EXECUTIVE_REPORT_remediation.xlsx and GRC_EXECUTIVE_REPORT_executive.pdf (stamped copies alongside). Remote git/inspect side effects are outside this script."
    }
    connectivity_status    = @{
        summary      = $connSummary
        host_records = @($LabHostRecords.ToArray())
    }
    vulnerabilities_found    = @()
    vulnerability_scan       = @{
        source = "not_run_by_orchestrator"
        note   = "No CVE scanner or product vulnerability aggregate in this orchestrator; extend with offline tools or future hooks."
    }
    performance_metrics      = @{
        orchestrate_wall_clock_sec       = $wallAll
        host_smoke_loop_wall_clock_sec   = $hostLoopSec
        per_host_seconds                 = [hashtable]$perHostSec
        privileged                       = [bool]$Privileged
    }
    run_flags                = [ordered]@{
        SkipInventoryPreflight     = [bool]$SkipInventoryPreflight
        SkipDataContractPreflight    = [bool]$SkipDataContractPreflight
        SkipImagePreflight           = [bool]$SkipImagePreflight
        SkipLabGitRefCheck           = [bool]$SkipLabGitRefCheck
        SkipFping                    = [bool]$SkipFping
        AlignLabClonesToLabGitRef    = [bool]$AlignLabClonesToLabGitRef
    }
    artifacts                = [ordered]@{
        orchestrate_events_jsonl = (Split-Path $eventsPath -Leaf)
        allhosts_log             = (Split-Path $allFile -Leaf)
        lab_result_latest        = "lab_result.json"
        lab_status_latest        = "lab_status.json"
        lab_result_stamped       = "completao_${stamp}_lab_result.json"
        grc_executive_latest     = "GRC_EXECUTIVE_REPORT.json"
        grc_executive_stamped    = "completao_${stamp}_GRC_EXECUTIVE_REPORT.json"
    }
    agent_readable_hint      = "Compare this file to a prior copy under docs/private/homelab/reports/; see docs/ops/LAB_COMPLETAO_RUNBOOK.md."
}

Write-CompletaoLabResultJsonFiles -OutDir $outDir -Stamp $stamp -Payload $labPayload
Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "lab_result" -Status "ok" -Message "wrote_lab_result_json" -Detail @{ lab_result_latest = "lab_result.json"; lab_status_latest = "lab_status.json"; lab_result_stamped = "completao_${stamp}_lab_result.json" }

Write-Host "[>] Generating GRC executive report..." -ForegroundColor Yellow
$scanResultsPrivate = Join-Path $RepoRoot "docs\private\homelab\data\raw_scan_results.json"
$grcReportLatest = Join-Path $outDir "GRC_EXECUTIVE_REPORT.json"
$grcReportStamped = Join-Path $outDir "completao_${stamp}_GRC_EXECUTIVE_REPORT.json"
$labResultLatest = Join-Path $outDir "lab_result.json"
$genScript = Join-Path $RepoRoot "scripts\generate_grc_report.py"
$dataDirPrivate = Join-Path $RepoRoot "docs\private\homelab\data"
if (-not (Test-Path -LiteralPath $dataDirPrivate)) {
    New-Item -ItemType Directory -Force -Path $dataDirPrivate | Out-Null
}
try {
    Push-Location $RepoRoot
    try {
        $pyArgs = @(
            $genScript,
            "--output",
            $grcReportLatest,
            "--lab-result",
            $labResultLatest
        )
        if (Test-Path -LiteralPath $scanResultsPrivate) {
            $pyArgs = @(
                $genScript,
                "--input",
                $scanResultsPrivate,
                "--output",
                $grcReportLatest,
                "--lab-result",
                $labResultLatest
            )
        }
        & uv run python @pyArgs
        if ($LASTEXITCODE -ne 0) {
            throw "generate_grc_report.py failed exit=$LASTEXITCODE"
        }
    } finally {
        Pop-Location
    }
    if (Test-Path -LiteralPath $grcReportLatest) {
        Copy-Item -LiteralPath $grcReportLatest -Destination $grcReportStamped -Force
    }
    Write-Host "[OK] GRC executive report generated." -ForegroundColor Green
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "grc_executive_report" -Status "ok" -Message "written" -Detail @{ latest = (Split-Path $grcReportLatest -Leaf); stamped = (Split-Path $grcReportStamped -Leaf) }

    if (Test-Path -LiteralPath $grcReportLatest) {
        try {
            $exportScript = Join-Path $RepoRoot "scripts\export_reports.py"
            Write-Host "[>] Exporting PDF and XLSX artifacts from GRC JSON..." -ForegroundColor Cyan
            Push-Location $RepoRoot
            try {
                & uv run python $exportScript --input $grcReportLatest
                if ($LASTEXITCODE -ne 0) {
                    throw "export_reports.py failed exit=$LASTEXITCODE"
                }
            } finally {
                Pop-Location
            }
            $grcXlsxLatest = Join-Path $outDir "GRC_EXECUTIVE_REPORT_remediation.xlsx"
            $grcPdfLatest = Join-Path $outDir "GRC_EXECUTIVE_REPORT_executive.pdf"
            $grcXlsxStamped = Join-Path $outDir "completao_${stamp}_GRC_EXECUTIVE_REPORT_remediation.xlsx"
            $grcPdfStamped = Join-Path $outDir "completao_${stamp}_GRC_EXECUTIVE_REPORT_executive.pdf"
            if (Test-Path -LiteralPath $grcXlsxLatest) {
                Copy-Item -LiteralPath $grcXlsxLatest -Destination $grcXlsxStamped -Force
            }
            if (Test-Path -LiteralPath $grcPdfLatest) {
                Copy-Item -LiteralPath $grcPdfLatest -Destination $grcPdfStamped -Force
            }
            Write-Host "[OK] GRC PDF and XLSX export finished." -ForegroundColor Green
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "grc_export_artifacts" -Status "ok" -Message "written" -Detail @{
                xlsx_latest  = (Split-Path $grcXlsxLatest -Leaf)
                pdf_latest   = (Split-Path $grcPdfLatest -Leaf)
                xlsx_stamped = (Split-Path $grcXlsxStamped -Leaf)
                pdf_stamped  = (Split-Path $grcPdfStamped -Leaf)
            }
        } catch {
            Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "grc_export_artifacts" -Status "failed" -Message $_.Exception.Message
            Write-Warning "GRC PDF/XLSX export skipped or failed: $($_.Exception.Message)"
        }
    }

    Write-Host "[i] Optional DashBOARd: set DATA_BOAR_GRC_JSON to the GRC JSON path, then streamlit run app\dashboard.py (uv sync --extra grc-dashboard)." -ForegroundColor Magenta
} catch {
    Write-CompletaoOrchestrateEvent -ReportPath $eventsPath -Phase "grc_executive_report" -Status "failed" -Message $_.Exception.Message
    Write-Warning "GRC executive report skipped or failed: $($_.Exception.Message)"
}
Write-Host "[FINISH] Completao cycle closed. Review reports (including GRC JSON) before commit." -ForegroundColor Cyan

Write-Host "Append lessons learned using docs/private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md" -ForegroundColor DarkGray

exit $semanticExit
