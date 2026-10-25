#Requires -Version 5.1
<#
.SYNOPSIS
  Plano V: Pre-flight helpers (slice 2) + cross-runtime orchestration loop (slice 3), ASCII-only.

.DESCRIPTION
  Slice 2 - Test-DataBoarMounts / Test-LocalSource: SSH material checks (mounts + paths).

  Slice 3 - Invoke-DataBoarPlanVInventoryOrchestration: for each inventory row, mkdir ephemeral tree on Linux,
  material mount evidence (ls -A | wc -l per SMB/NFS/SSHFS; zero count aborts that node with local forensic log),
  synthetic Postgres/MariaDB/Mongo (Swarm stack deploy or Podman runs), TCP readiness wait (5432/3306/27017),
  SCP boar_config.yaml, then Swarm stack deploy for scanner OR podman scanner OR metal nohup. Stack names,
  stack files, and container names include RunId-derived slugs to avoid collisions.

  Slice 4 - Invoke-DataBoarPlanVResilientRun: on terminating error, catch renames remote boar_config.yaml/config.yaml
  to *.failed (forensic); finally always prints coverage report (RunId, SMB/NFS/SSHFS probe, local log paths);
  optional teardown removes stack / podman session containers / metal PID for this RunId (zombie reduction).

.NOTES
  Hybrid family: ssh.exe / scp.exe -o BatchMode=yes pattern matches lab-completao-orchestrate-hybrid-v173.ps1.
  Swarm: if -StackYamlLocalPath is omitted, emits a minimal bind-mounted stack under the remote bench config dir.
  Podman: operator-requested --privileged -v /:/host:ro (high blast radius) plus config bind; lab-only.
  Example inventory uses 192.0.2.0/24 documentation addresses (RFC 5737 TEST-NET-1), not RFC1918 literals.
#>

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

function Resolve-DataBoarSshTarget {
    param(
        [Parameter(Mandatory = $true)][string] $NodeName,
        [Parameter(Mandatory = $true)][string] $IpAddress,
        [string] $SshUser = ""
    )
    $u = $SshUser
    if (-not $u) {
        $u = [string]$env:DATA_BOAR_LAB_SSH_USER
    }
    if (-not $u) {
        $u = "leitao"
    }
    return "${u}@${IpAddress}"
}

function Get-RemoteMountEntryCount {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $MountPath,
        [int] $ConnectTimeoutSeconds = 20
    )
    $p = $MountPath -replace "'", "'\''"
    # ls -A: exclude . and .. so count 0 means truly no entries (RCDD-style material check).
    $inner = "if [ ! -d '$p' ]; then echo DATABOAR_COUNT_MISSING; exit 2; fi; n=`$(ls -A '$p' 2>/dev/null | wc -l); echo DATABOAR_COUNT:`$n"
    $innerEsc = $inner.Replace('"', '\"')
    $out = & ssh.exe -o BatchMode=yes -o ConnectTimeout=$ConnectTimeoutSeconds -o StrictHostKeyChecking=accept-new $SshTarget $innerEsc 2>&1 | Out-String
    return @{
        Raw    = $out
        Exit   = $LASTEXITCODE
        Target = $SshTarget
        Path   = $MountPath
    }
}

function Test-DataBoarMounts {
    <#
    .SYNOPSIS
      Pre-flight: SSH to node and verify bench mounts are present and non-empty.
    .PARAMETER NodeName
      Label for logs (RCDD evidence bundle).
    .PARAMETER IpAddress
      IPv4 or resolvable host for SSH (combined with SshUser unless SshTarget is set).
    .PARAMETER SshTarget
      Optional full ssh destination user@host. When set, IpAddress/SshUser are ignored for SSH.
    .PARAMETER SshUser
      SSH username when building user@IpAddress (default: env DATA_BOAR_LAB_SSH_USER, then leitao).
    .PARAMETER ConnectTimeoutSeconds
      Per-invocation SSH connect timeout.
    #>
    param(
        [Parameter(Mandatory = $true)][string] $NodeName,
        [Parameter(Mandatory = $true)][string] $IpAddress,
        [string] $SshTarget = "",
        [string] $SshUser = "",
        [int] $ConnectTimeoutSeconds = 20
    )
    $mounts = @(
        "/mnt/smb_synthetic",
        "/mnt/nfs_bench",
        "/mnt/sshfs_lab"
    )
    $target = if ($SshTarget) { $SshTarget } else { (Resolve-DataBoarSshTarget -NodeName $NodeName -IpAddress $IpAddress -SshUser $SshUser) }

    Write-Host "PreFlight mounts: node=$NodeName ssh=$target" -ForegroundColor Cyan

    foreach ($m in $mounts) {
        $r = Get-RemoteMountEntryCount -SshTarget $target -MountPath $m -ConnectTimeoutSeconds $ConnectTimeoutSeconds
        if ($r.Exit -ne 0) {
            Write-Warning "PreFlight mounts FAIL node=$NodeName path=$m ssh_exit=$($r.Exit) raw=$($r.Raw)"
            return $false
        }
        $line = ($r.Raw -split "`r?`n" | Where-Object { $_ -match "DATABOAR_COUNT:" } | Select-Object -First 1)
        if (-not $line) {
            Write-Warning "PreFlight mounts FAIL node=$NodeName path=$m no_count_line raw=$($r.Raw)"
            return $false
        }
        if ($line -match "DATABOAR_COUNT_MISSING") {
            Write-Warning "PreFlight mounts FAIL node=$NodeName path=$m missing_dir"
            return $false
        }
        $digits = [regex]::Match($line, "DATABOAR_COUNT:\s*(\d+)").Groups[1].Value
        if (-not $digits) {
            Write-Warning "PreFlight mounts FAIL node=$NodeName path=$m unparsable_line=$line"
            return $false
        }
        $n = 0
        [void][int]::TryParse($digits, [ref]$n)
        if ($n -le 0) {
            Write-Warning "PreFlight mounts FAIL node=$NodeName path=$m empty_or_zero count=$n (abort node)"
            return $false
        }
        Write-Host "  OK $m entries=$n" -ForegroundColor DarkGreen
    }
    return $true
}

function Test-LocalSource {
    <#
    .SYNOPSIS
      Pre-flight: verify Documents scan path and /var/log exist (material paths).
    .PARAMETER SshTarget
      When set (user@host), runs test -d on the remote node via SSH.
    .PARAMETER DocumentsPath
      Default /home/leitao/Documents (matches hybrid v1.7.3 lab-node-02 resolution primary).
    .PARAMETER LogPath
      Default /var/log.
    .PARAMETER ConnectTimeoutSeconds
      SSH timeout when SshTarget is used.
    #>
    param(
        [string] $SshTarget = "",
        [string] $DocumentsPath = "/home/leitao/Documents",
        [string] $LogPath = "/var/log",
        [int] $ConnectTimeoutSeconds = 20
    )
    if ($SshTarget) {
        $d = $DocumentsPath -replace "'", "'\''"
        $l = $LogPath -replace "'", "'\''"
        $inner = "if [ ! -d '$d' ]; then echo DATABOAR_LOCALSRC_FAIL_docs; exit 2; fi; if [ ! -d '$l' ]; then echo DATABOAR_LOCALSRC_FAIL_log; exit 3; fi; echo DATABOAR_LOCALSRC_OK"
        $innerEsc = $inner.Replace('"', '\"')
        $out = & ssh.exe -o BatchMode=yes -o ConnectTimeout=$ConnectTimeoutSeconds -o StrictHostKeyChecking=accept-new $SshTarget $innerEsc 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Test-LocalSource SSH FAIL target=$SshTarget exit=$LASTEXITCODE raw=$out"
            return $false
        }
        if ($out -notmatch "DATABOAR_LOCALSRC_OK") {
            Write-Warning "Test-LocalSource SSH unexpected output target=$SshTarget raw=$out"
            return $false
        }
        Write-Host "Test-LocalSource OK (remote) $SshTarget docs=$DocumentsPath log=$LogPath" -ForegroundColor DarkGreen
        return $true
    }

    $okDocs = Test-Path -LiteralPath $DocumentsPath -PathType Container
    $okLog = Test-Path -LiteralPath $LogPath -PathType Container
    if (-not $okDocs) {
        Write-Warning "Test-LocalSource FAIL missing_docs local path=$DocumentsPath"
        return $false
    }
    if (-not $okLog) {
        Write-Warning "Test-LocalSource FAIL missing_log local path=$LogPath"
        return $false
    }
    Write-Host "Test-LocalSource OK (local) docs=$DocumentsPath log=$LogPath" -ForegroundColor DarkGreen
    return $true
}

function Test-DataBoarPlanVMountCountPositive {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $MountPath,
        [int] $ConnectTimeoutSeconds = 20
    )
    $r = Get-RemoteMountEntryCount -SshTarget $SshTarget -MountPath $MountPath -ConnectTimeoutSeconds $ConnectTimeoutSeconds
    if ($r.Exit -ne 0) {
        return $false
    }
    $line = ($r.Raw -split "`r?`n" | Where-Object { $_ -match "DATABOAR_COUNT:" } | Select-Object -First 1)
    if (-not $line -or ($line -match "DATABOAR_COUNT_MISSING")) {
        return $false
    }
    $digits = [regex]::Match($line, "DATABOAR_COUNT:\s*(\d+)").Groups[1].Value
    if (-not $digits) {
        return $false
    }
    $n = 0
    [void][int]::TryParse($digits, [ref]$n)
    return ($n -gt 0)
}

function Get-DataBoarPlanVMountProtocolStatus {
    param(
        [Parameter(Mandatory = $true)][string] $NodeName,
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [int] $ConnectTimeoutSeconds = 20
    )
    $smb = "/mnt/smb_synthetic"
    $nfs = "/mnt/nfs_bench"
    $sshfs = "/mnt/sshfs_lab"
    return [pscustomobject]@{
        Node        = $NodeName
        SshTarget   = $SshTarget
        SmbOk       = (Test-DataBoarPlanVMountCountPositive -SshTarget $SshTarget -MountPath $smb -ConnectTimeoutSeconds $ConnectTimeoutSeconds)
        NfsOk       = (Test-DataBoarPlanVMountCountPositive -SshTarget $SshTarget -MountPath $nfs -ConnectTimeoutSeconds $ConnectTimeoutSeconds)
        SshfsOk     = (Test-DataBoarPlanVMountCountPositive -SshTarget $SshTarget -MountPath $sshfs -ConnectTimeoutSeconds $ConnectTimeoutSeconds)
        SmbPath     = $smb
        NfsPath     = $nfs
        SshfsPath   = $sshfs
    }
}

function Get-DataBoarPlanVRemoteBenchRoot {
    param([Parameter(Mandatory = $true)][string] $RunId)
    return "/tmp/databoar_bench_$RunId"
}

function Invoke-DataBoarPlanVRemoteSh {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $RemoteShellSnippet,
        [int] $ConnectTimeoutSeconds = 45
    )
    $innerEsc = $RemoteShellSnippet.Replace('"', '\"')
    $null = & ssh.exe -o BatchMode=yes -o ConnectTimeout=$ConnectTimeoutSeconds -o StrictHostKeyChecking=accept-new $SshTarget $innerEsc 2>&1
    return $LASTEXITCODE
}

function Invoke-DataBoarPlanVRemoteShCapture {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $RemoteShellSnippet,
        [int] $ConnectTimeoutSeconds = 45
    )
    $innerEsc = $RemoteShellSnippet.Replace('"', '\"')
    $cap = & ssh.exe -o BatchMode=yes -o ConnectTimeout=$ConnectTimeoutSeconds -o StrictHostKeyChecking=accept-new $SshTarget $innerEsc 2>&1 | Out-String
    return @{ Exit = $LASTEXITCODE; Out = $cap }
}

function Get-DataBoarPlanVShortSlug {
    param([Parameter(Mandatory = $true)][string] $RunId)
    $s = ($RunId -replace '[^a-zA-Z0-9]', '').ToLowerInvariant()
    if ($s.Length -gt 22) {
        $s = $s.Substring(0, 22)
    }
    if (-not $s) {
        $s = "run"
    }
    return $s
}

function Get-DataBoarPlanVSyntheticHostPorts {
    param([Parameter(Mandatory = $true)][string] $Seed)
    $h = 0
    foreach ($ch in $Seed.ToCharArray()) {
        $h = (($h * 31) + [int][char]$ch) -band 0x7fffffff
    }
    $base = 52000 + ($h % 3500)
    return @{
        Postgres = $base
        MariaDb  = ($base + 1)
        Mongo    = ($base + 2)
    }
}

function Get-DataBoarPlanVMountMaterialEvidence {
    <#
    .SYNOPSIS
      Per-protocol mount material check using ls -A | wc -l (same remote primitive as Get-RemoteMountEntryCount).
    #>
    param(
        [Parameter(Mandatory = $true)][string] $NodeName,
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [int] $ConnectTimeoutSeconds = 20
    )
    $mounts = @(
        @{ Key = "Smb"; Path = "/mnt/smb_synthetic" },
        @{ Key = "Nfs"; Path = "/mnt/nfs_bench" },
        @{ Key = "Sshfs"; Path = "/mnt/sshfs_lab" }
    )
    $rows = @{}
    $allOk = $true
    foreach ($m in $mounts) {
        $r = Get-RemoteMountEntryCount -SshTarget $SshTarget -MountPath $m.Path -ConnectTimeoutSeconds $ConnectTimeoutSeconds
        $n = -1
        if ($r.Exit -eq 0) {
            $line = ($r.Raw -split "`r?`n" | Where-Object { $_ -match "DATABOAR_COUNT:" } | Select-Object -First 1)
            if ($line -and ($line -notmatch "DATABOAR_COUNT_MISSING")) {
                $digits = [regex]::Match($line, "DATABOAR_COUNT:\s*(\d+)").Groups[1].Value
                if ($digits) {
                    [void][int]::TryParse($digits, [ref]$n)
                }
            }
        }
        if ($n -le 0) {
            $allOk = $false
        }
        $rows[$m.Key] = @{
            Path = $m.Path
            Count = $n
            Exit  = $r.Exit
            Raw   = $r.Raw
        }
    }
    return [pscustomobject]@{
        Node         = $NodeName
        SshTarget    = $SshTarget
        AllProtocolsOk = $allOk
        Smb          = $rows["Smb"]
        Nfs          = $rows["Nfs"]
        Sshfs        = $rows["Sshfs"]
    }
}

function Invoke-DataBoarPlanVWriteMountAbortForensic {
    param(
        [Parameter(Mandatory = $true)][string] $LocalLogDir,
        [Parameter(Mandatory = $true)][string] $RunId,
        [Parameter(Mandatory = $true)][string] $NodeName,
        [Parameter(Mandatory = $true)] $Evidence
    )
    if (-not (Test-Path -LiteralPath $LocalLogDir)) {
        New-Item -ItemType Directory -Force -Path $LocalLogDir | Out-Null
    }
    $safeNode = ($NodeName -replace '[^a-zA-Z0-9_-]', '_')
    $p = Join-Path $LocalLogDir "PLANV_MOUNT_ABORT_${safeNode}_${RunId}.log"
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("ts_utc=$(([datetime]::UtcNow).ToString('o'))")
    [void]$sb.AppendLine("run_id=$RunId")
    [void]$sb.AppendLine("node=$NodeName")
    [void]$sb.AppendLine("ssh=$($Evidence.SshTarget)")
    [void]$sb.AppendLine("all_protocols_ok=$($Evidence.AllProtocolsOk)")
    foreach ($k in @("Smb", "Nfs", "Sshfs")) {
        $blk = $Evidence.$k
        [void]$sb.AppendLine("${k}_path=$($blk.Path)")
        [void]$sb.AppendLine("${k}_count=$($blk.Count)")
        [void]$sb.AppendLine("${k}_ssh_exit=$($blk.Exit)")
        [void]$sb.AppendLine("${k}_raw<<EOF")
        [void]$sb.AppendLine([string]$blk.Raw)
        [void]$sb.AppendLine("EOF")
    }
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($p, $sb.ToString(), $enc)
    Write-Warning "PlanV: node ABORTED (mount material) evidence=$p"
}

function New-DataBoarPlanVSwarmDbStackYamlText {
    param(
        [Parameter(Mandatory = $true)][string] $Slug,
        [Parameter(Mandatory = $true)][hashtable] $HostPorts
    )
    $tok = Get-DataBoarPlanVShortSlug -RunId $Slug
    $pg = [int]$HostPorts.Postgres
    $my = [int]$HostPorts.MariaDb
    $mo = [int]$HostPorts.Mongo
    $net = "planvdb_${tok}"
    return @"
version: '3.8'
services:
  lab_postgres_${tok}:
    image: postgres:16-alpine
    environment:
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - target: 5432
        published: ${pg}
        protocol: tcp
        mode: host
    networks:
      - ${net}
  lab_mariadb_${tok}:
    image: mariadb:11
    environment:
      MYSQL_ROOT_PASSWORD: planv_synth_root
      MYSQL_DATABASE: planv_synth
    ports:
      - target: 3306
        published: ${my}
        protocol: tcp
        mode: host
    networks:
      - ${net}
  lab_mongodb_${tok}:
    image: mongo:7
    ports:
      - target: 27017
        published: ${mo}
        protocol: tcp
        mode: host
    networks:
      - ${net}
networks:
  ${net}:
    driver: overlay
    attachable: true
"@
}

function New-DataBoarPlanVSwarmScannerStackYamlText {
    param(
        [Parameter(Mandatory = $true)][string] $Slug,
        [Parameter(Mandatory = $true)][string] $RemoteBenchRoot,
        [Parameter(Mandatory = $true)][string] $ImageRef,
        [Parameter(Mandatory = $true)][string] $OverlayNetName
    )
    $cfgPath = "$RemoteBenchRoot/config/boar_config.yaml"
    $tok = Get-DataBoarPlanVShortSlug -RunId $Slug
    $svc = "scanner_${tok}"
    return @"
version: '3.8'
services:
  ${svc}:
    image: ${ImageRef}
    volumes:
      - type: bind
        source: ${cfgPath}
        target: /app/config.yaml
        read_only: true
    networks:
      - planv_scan_join
networks:
  planv_scan_join:
    external: true
    name: ${OverlayNetName}
"@
}

function Invoke-DataBoarPlanVWaitRemoteTcpPorts {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][int[]] $HostPorts,
        [int] $MaxWaitSeconds = 120,
        [int] $ConnectTimeoutSeconds = 45
    )
    $portsCsv = ($HostPorts | ForEach-Object { [string]$_ }) -join ','
    $mx = [string][int]$MaxWaitSeconds
    $inner = @'
set -e
ports="PORTS_CSV"
deadline=$(( $(date +%s) + MX_SEC ))
for p in $(echo "$ports" | tr "," " "); do
  ok=0
  while [ $(date +%s) -lt $deadline ]; do
    if command -v nc >/dev/null 2>&1; then
      if nc -z 127.0.0.1 $p 2>/dev/null; then ok=1; break; fi
    else
      if timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$p" 2>/dev/null; then ok=1; break; fi
    fi
    sleep 1
  done
  if [ "$ok" != "1" ]; then echo "PLANV_TCP_FAIL:$p"; exit 19; fi
  echo "PLANV_TCP_OK:$p"
done
echo PLANV_TCP_ALL_OK
'@.Replace('PORTS_CSV', $portsCsv).Replace('MX_SEC', $mx)
    $r = Invoke-DataBoarPlanVRemoteShCapture -SshTarget $SshTarget -RemoteShellSnippet $inner -ConnectTimeoutSeconds $ConnectTimeoutSeconds
    if ($r.Exit -ne 0) {
        Write-Warning "PlanV: TCP wait failed ssh=$SshTarget exit=$($r.Exit) out=$($r.Out)"
        return $false
    }
    if ($r.Out -notmatch "PLANV_TCP_ALL_OK") {
        Write-Warning "PlanV: TCP wait unexpected output ssh=$SshTarget out=$($r.Out)"
        return $false
    }
    return $true
}

function Invoke-DataBoarPlanVDeploySyntheticSwarm {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $RemoteYamlPath,
        [Parameter(Mandatory = $true)][string] $DbStackName,
        [Parameter(Mandatory = $true)][int] $ConnectTimeoutSeconds
    )
    $yr = $RemoteYamlPath -replace "'", "'\''"
    $sn = $DbStackName -replace "'", "'\''"
    $dep = "docker stack deploy -c '$yr' '$sn' && echo PLANV_DB_STACK_OK"
    Invoke-DataBoarPlanVBenchmarkWrapper -ExecutionLabel "Deploy & Scan Swarm ($sn)" -ScriptBlockToMeasure {
        $exitCode = Invoke-DataBoarPlanVRemoteSh -SshTarget $SshTarget -RemoteShellSnippet $dep -ConnectTimeoutSeconds 180
        if ($exitCode -ne 0) {
            throw "Swarm Deploy/Scan falhou com exit code $exitCode"
        }
    }
    return $true
}

function Invoke-DataBoarPlanVDeploySyntheticPodman {
    param(
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $Tok,
        [Parameter(Mandatory = $true)][hashtable] $HostPorts,
        [Parameter(Mandatory = $true)][int] $ConnectTimeoutSeconds
    )
    $pg = [int]$HostPorts.Postgres
    $my = [int]$HostPorts.MariaDb
    $mo = [int]$HostPorts.Mongo
    $net = "planvpod_${Tok}"
    $npg = "planv_${Tok}_pg"
    $nmy = "planv_${Tok}_my"
    $nmo = "planv_${Tok}_mo"
    $inner = "set -e; podman network exists '$net' 2>/dev/null || podman network create '$net'; podman rm -f '$npg' '$nmy' '$nmo' 2>/dev/null || true; podman run -d --network '$net' --name '$npg' --network-alias lab_postgres -p ${pg}:5432 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine; podman run -d --network '$net' --name '$nmy' --network-alias lab_mariadb -p ${my}:3306 -e MYSQL_ROOT_PASSWORD=planv_synth_root -e MYSQL_DATABASE=planv_synth mariadb:11; podman run -d --network '$net' --name '$nmo' --network-alias lab_mongodb -p ${mo}:27017 mongo:7; echo PLANV_PODMAN_SYNTH_OK"
	Invoke-DataBoarPlanVBenchmarkWrapper -ExecutionLabel "Deploy & Scan Podman ($Tok)" -ScriptBlockToMeasure {
        $exitCode = Invoke-DataBoarPlanVRemoteSh -SshTarget $SshTarget -RemoteShellSnippet $inner -ConnectTimeoutSeconds $ConnectTimeoutSeconds
        if ($exitCode -ne 0) {
            throw "Podman Deploy/Scan falhou com exit code $exitCode"
        }
    }
    return $true
}

function Get-DataBoarPlanVSwarmDbOverlayNetworkName {
    param(
        [Parameter(Mandatory = $true)][string] $DbStackName,
        [Parameter(Mandatory = $true)][string] $Slug
    )
    $tok = Get-DataBoarPlanVShortSlug -RunId $Slug
    $net = "planvdb_${tok}"
    return "${DbStackName}_${net}"
}

function Get-DataBoarPlanVInventoryFromManifest {
    <#
    .SYNOPSIS
      Map docs/private/homelab/lab-op-hosts.manifest.json hosts to Plan V inventory (same host order idea as hybrid v173).
    #>
    param([Parameter(Mandatory = $true)][string] $ManifestPath)
    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        throw "Get-DataBoarPlanVInventoryFromManifest: missing $ManifestPath"
    }
    $m = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
    $roleDefs = @(
        @{ Name = "LAB-NODE-02"; Regex = '(?i)^lab-node-02$'; Type = "Swarm" },
        @{ Name = "LAB-NODE-01-Pro"; Regex = '(?i)lab-node-01'; Type = "Podman" },
        @{ Name = "LAB-NODE-03"; Regex = '(?i)LAB-NODE-03|^minibt$'; Type = "Swarm" }
    )
    $ordered = [System.Collections.Generic.List[object]]::new()
    foreach ($rd in $roleDefs) {
        foreach ($h in $m.hosts) {
            if (-not $h.sshHost) {
                continue
            }
            if ([string]$h.sshHost -match $rd.Regex) {
                $sh = [string]$h.sshHost
                $user = "leitao"
                $hostPart = $sh
                if ($sh -match '@') {
                    $parts = $sh.Split('@')
                    $user = $parts[0]
                    $hostPart = $parts[1]
                }
                $ordered.Add(@{
                    Name    = $rd.Name
                    Ip      = $hostPart
                    Type    = $rd.Type
                    SshUser = $user
                })
                break
            }
        }
    }
    if ($ordered.Count -eq 0) {
        throw "Get-DataBoarPlanVInventoryFromManifest: no hosts matched (lab-node-02 / lab-node-01 / LAB-NODE-03)."
    }
    return $ordered
}

function Copy-DataBoarPlanVToRemote {
    param(
        [Parameter(Mandatory = $true)][string] $LocalFile,
        [Parameter(Mandatory = $true)][string] $SshTarget,
        [Parameter(Mandatory = $true)][string] $RemotePath
    )
    if (-not (Test-Path -LiteralPath $LocalFile)) {
        throw "Copy-DataBoarPlanVToRemote: missing local file $LocalFile"
    }
    $rp = $RemotePath -replace "'", "'\''"
    $parent = Split-Path -Parent $RemotePath
    $parEsc = $parent -replace "'", "'\''"
    $mkEc = Invoke-DataBoarPlanVRemoteSh -SshTarget $SshTarget -RemoteShellSnippet "mkdir -p '$parEsc'"
    if ($mkEc -ne 0) {
        return $false
    }
    & scp.exe -q -o BatchMode=yes -o StrictHostKeyChecking=accept-new $LocalFile "${SshTarget}:${rp}"
    return ($LASTEXITCODE -eq 0)
}

# ==============================================================================
# [SRE TELEMETRY CORE] - Injecao de Benchmark para validacao Rust vs Python
# ==============================================================================
$Script:PlanVBenchmark = [System.Diagnostics.Stopwatch]::new()

function Invoke-DataBoarPlanVBenchmarkWrapper {
    param (
        [Parameter(Mandatory=$true)][string]$ExecutionLabel,
        [Parameter(Mandatory=$true)][scriptblock]$ScriptBlockToMeasure
    )

    Write-Host "`n[BENCHMARK] Iniciando etapa: $ExecutionLabel" -ForegroundColor Magenta
    $Script:PlanVBenchmark.Restart()

    try {
        & $ScriptBlockToMeasure
    }
    catch {
        Write-Error "[BENCHMARK FATAL] Falha durante a execucao de $ExecutionLabel : $_"
        throw
    }
    finally {
        $Script:PlanVBenchmark.Stop()
        $elapsed = $Script:PlanVBenchmark.Elapsed
        $metrics = "[BENCHMARK] $ExecutionLabel concluido em: {0:00}h {1:00}m {2:00}s {3:000}ms" -f $elapsed.Hours, $elapsed.Minutes, $elapsed.Seconds, $elapsed.Milliseconds
        Write-Host $metrics -ForegroundColor Green
    }
}

function Invoke-DataBoarPlanVInventoryOrchestration {
    <#
    .SYNOPSIS
      Slice 3: per-node mkdir, mount material gate (ls -A | wc -l), synthetic DB stack (Swarm or Podman), TCP readiness,
      SCP boar_config.yaml, then scanner Swarm stack / Podman scanner / Metal nohup. SkippedNodeNames bypasses a node.
    .PARAMETER StackYamlLocalPath
      When set to an existing file, Swarm path deploys that compose only (operator owns synth + scanner); synthetic helpers are skipped.
    #>
    param(
        [Parameter(Mandatory = $true)][string] $RunId,
        [Parameter(Mandatory = $true)] $Inventory,
        [Parameter(Mandatory = $true)][string] $BoarConfigLocalPath,
        [string] $StackYamlLocalPath = "",
        [string] $PodmanImage = "",
        [string[]] $SkippedNodeNames = @(),
        [string] $LocalForensicLogDir = "",
        [int] $ConnectTimeoutSeconds = 45
    )
    if (-not $PodmanImage) {
        $PodmanImage = [string]$env:DATA_BOAR_PLANV_IMAGE
    }
    if (-not $PodmanImage) {
        $PodmanImage = "fabioleitao/data_boar:latest"
    }
    $remoteRoot = Get-DataBoarPlanVRemoteBenchRoot -RunId $RunId
    $stackRemotePath = "$remoteRoot/config/stack_scanner.yaml"
    $stackDbRemotePath = "$remoteRoot/config/stack_db.yaml"
    $tmpDb = [System.IO.Path]::GetTempFileName()
    $tmpScan = [System.IO.Path]::GetTempFileName()
    $ctx = $script:DataBoarPlanVRunContext
    try {
        foreach ($node in $Inventory) {
            $nName = [string]$node.Name
            $nIp = [string]$node.Ip
            $nType = ([string]$node.Type).Trim().ToLowerInvariant()
            $nUser = [string]$node.SshUser
            $ssh = Resolve-DataBoarSshTarget -NodeName $nName -IpAddress $nIp -SshUser $nUser
            Write-Host "PlanV orchestrate: node=$nName type=$nType ssh=$ssh root=$remoteRoot" -ForegroundColor Cyan

            if ($SkippedNodeNames -and ($SkippedNodeNames -contains $nName)) {
                Write-Warning "PlanV: skipping node (preflight mount abort list): $nName"
                continue
            }

            $mk = "mkdir -p '$remoteRoot/bin' '$remoteRoot/config' '$remoteRoot/results' '$remoteRoot/logs' && echo PLANV_MK_OK"
            if ((Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $mk -ConnectTimeoutSeconds $ConnectTimeoutSeconds) -ne 0) {
                throw "PlanV: mkdir failed on $nName ($ssh)"
            }

            if ($LocalForensicLogDir) {
                $ev2 = Get-DataBoarPlanVMountMaterialEvidence -NodeName $nName -SshTarget $ssh -ConnectTimeoutSeconds 20
                if (-not $ev2.AllProtocolsOk) {
                    Invoke-DataBoarPlanVWriteMountAbortForensic -LocalLogDir $LocalForensicLogDir -RunId $RunId -NodeName $nName -Evidence $ev2
                    Write-Warning "PlanV: node ABORTED mid-orchestration (mount material): $nName"
                    continue
                }
            }

            $slug = Get-DataBoarPlanVShortSlug -RunId ($RunId + "_" + $nName)
            $ports = Get-DataBoarPlanVSyntheticHostPorts -Seed ($RunId + "_" + $nName)
            $remoteCfg = "$remoteRoot/config/boar_config.yaml"

            if ($nType -eq "swarm") {
                if ($StackYamlLocalPath -and (Test-Path -LiteralPath $StackYamlLocalPath)) {
                    if (-not (Copy-DataBoarPlanVToRemote -LocalFile $BoarConfigLocalPath -SshTarget $ssh -RemotePath $remoteCfg)) {
                        throw "PlanV: scp boar_config failed on $nName ($ssh)"
                    }
                    if (-not (Copy-DataBoarPlanVToRemote -LocalFile $StackYamlLocalPath -SshTarget $ssh -RemotePath $stackRemotePath)) {
                        throw "PlanV: scp operator stack yaml failed on $nName"
                    }
                    $opStack = "databoar_" + $slug
                    $sr = $stackRemotePath -replace "'", "'\''"
                    $deployOp = "d\ocker stack deploy -c '$sr' '$opStack' && echo PLANV_STACK_OK"
                    if ((Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $deployOp -ConnectTimeoutSeconds 180) -ne 0) {
                        throw "PlanV: docker stack deploy (operator file) failed on $nName stack=$opStack"
                    }
                    if ($null -ne $ctx -and $ctx.ContainsKey("SwarmCleanup")) {
                        $ctx.SwarmCleanup.Add(@{ SshTarget = $ssh; DbStack = ""; ScanStack = $opStack })
                    }
                    Write-Host "  Swarm operator stack deployed: $opStack" -ForegroundColor DarkGreen
                    continue
                }

                $dbStackName = "dbpv-" + $slug
                $scanStackName = "scpv-" + $slug
                $dbBody = New-DataBoarPlanVSwarmDbStackYamlText -Slug $slug -HostPorts $ports
                $enc = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($tmpDb, $dbBody, $enc)
                if (-not (Copy-DataBoarPlanVToRemote -LocalFile $tmpDb -SshTarget $ssh -RemotePath $stackDbRemotePath)) {
                    throw "PlanV: scp generated db stack failed on $nName"
                }
                if (-not (Invoke-DataBoarPlanVDeploySyntheticSwarm -SshTarget $ssh -RemoteYamlPath $stackDbRemotePath -DbStackName $dbStackName -ConnectTimeoutSeconds $ConnectTimeoutSeconds)) {
                    throw "PlanV: docker stack deploy (synthetic DB) failed on $nName stack=$dbStackName"
                }
                $overlayNet = Get-DataBoarPlanVSwarmDbOverlayNetworkName -DbStackName $dbStackName -Slug $slug
                if (-not (Invoke-DataBoarPlanVWaitRemoteTcpPorts -SshTarget $ssh -HostPorts @($ports.Postgres, $ports.MariaDb) -MaxWaitSeconds 120 -ConnectTimeoutSeconds $ConnectTimeoutSeconds)) {
                    throw "PlanV: synthetic TCP wait failed on $nName (postgres/mariadb host ports $($ports.Postgres), $($ports.MariaDb))"
                }
                $null = Invoke-DataBoarPlanVWaitRemoteTcpPorts -SshTarget $ssh -HostPorts @($ports.Mongo) -MaxWaitSeconds 120 -ConnectTimeoutSeconds $ConnectTimeoutSeconds

                if (-not (Copy-DataBoarPlanVToRemote -LocalFile $BoarConfigLocalPath -SshTarget $ssh -RemotePath $remoteCfg)) {
                    throw "PlanV: scp boar_config failed on $nName ($ssh)"
                }
                $scanBody = New-DataBoarPlanVSwarmScannerStackYamlText -Slug $slug -RemoteBenchRoot $remoteRoot -ImageRef $PodmanImage -OverlayNetName $overlayNet
                [System.IO.File]::WriteAllText($tmpScan, $scanBody, $enc)
                if (-not (Copy-DataBoarPlanVToRemote -LocalFile $tmpScan -SshTarget $ssh -RemotePath $stackRemotePath)) {
                    throw "PlanV: scp generated scanner stack failed on $nName"
                }
                $sr2 = $stackRemotePath -replace "'", "'\''"
                $deployScan = "docker stack deploy -c '$sr2' '$scanStackName' && echo PLANV_SCAN_STACK_OK"
                if ((Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $deployScan -ConnectTimeoutSeconds 180) -ne 0) {
                    throw "PlanV: docker stack deploy (scanner) failed on $nName stack=$scanStackName"
                }
                if ($null -ne $ctx -and $ctx.ContainsKey("SwarmCleanup")) {
                    $ctx.SwarmCleanup.Add(@{ SshTarget = $ssh; DbStack = $dbStackName; ScanStack = $scanStackName })
                }
                Write-Host "  Swarm synthetic DB stack=$dbStackName scanner stack=$scanStackName overlay=$overlayNet" -ForegroundColor DarkGreen
            }
            elseif ($nType -eq "podman") {
                $tok = Get-DataBoarPlanVShortSlug -RunId ($RunId + "_" + $nName)
                if (-not (Invoke-DataBoarPlanVDeploySyntheticPodman -SshTarget $ssh -Tok $tok -HostPorts $ports -ConnectTimeoutSeconds $ConnectTimeoutSeconds)) {
                    throw "PlanV: podman synthetic DB bring-up failed on $nName"
                }
                if (-not (Invoke-DataBoarPlanVWaitRemoteTcpPorts -SshTarget $ssh -HostPorts @($ports.Postgres, $ports.MariaDb, $ports.Mongo) -MaxWaitSeconds 120 -ConnectTimeoutSeconds $ConnectTimeoutSeconds)) {
                    throw "PlanV: podman synthetic TCP wait failed on $nName"
                }
                if (-not (Copy-DataBoarPlanVToRemote -LocalFile $BoarConfigLocalPath -SshTarget $ssh -RemotePath $remoteCfg)) {
                    throw "PlanV: scp boar_config failed on $nName ($ssh)"
                }
                $slugPod = ($nName -replace '[^a-zA-Z0-9]', '_').ToLowerInvariant()
                $cname = "databoar_${RunId}_$slugPod"
                $net = "planvpod_${tok}"
                $cfgEsc = $remoteCfg -replace "'", "'\''"
                $runInner = "podman rm -f '$cname' 2>/dev/null || true; podman run -d --name '$cname' --network '$net' --privileged -v /:/host:ro -v '$cfgEsc':/app/config.yaml:ro '$PodmanImage' && echo PLANV_PODMAN_OK"
                if ((Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $runInner -ConnectTimeoutSeconds 120) -ne 0) {
                    throw "PlanV: podman scanner run failed on $nName container=$cname"
                }
                if ($null -ne $ctx -and $ctx.ContainsKey("PodmanCleanup")) {
                    $ctx.PodmanCleanup.Add(@{
                        SshTarget = $ssh
                        Net       = $net
                        Scanner   = $cname
                        Tok       = $tok
                    })
                }
                Write-Host "  Podman synthetic net=$net scanner=$cname (privileged + host bind per operator spec)" -ForegroundColor DarkGreen
            }
            elseif ($nType -eq "metal") {
                $metalBin = [string]$node.MetalBinary
                if (-not $metalBin) {
                    $metalBin = [string]$env:DATA_BOAR_PLANV_METAL_BINARY
                }
                if (-not $metalBin) {
                    $metalBin = "/usr/local/bin/databoar"
                }
                if (-not (Copy-DataBoarPlanVToRemote -LocalFile $BoarConfigLocalPath -SshTarget $ssh -RemotePath $remoteCfg)) {
                    throw "PlanV: scp boar_config failed on $nName ($ssh)"
                }
                $mb = $metalBin -replace "'", "'\''"
                $logF = "$remoteRoot/logs/metal_${RunId}.log" -replace "'", "'\''"
                $pidF = "$remoteRoot/logs/metal_${RunId}.pid" -replace "'", "'\''"
                $metalInner = "chmod +x '$mb' 2>/dev/null || true; nohup '$mb' >'$logF' 2>&1 & echo `$! > '$pidF' && sync && echo PLANV_METAL_OK"
                if ((Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $metalInner -ConnectTimeoutSeconds 60) -ne 0) {
                    throw "PlanV: metal launch failed on $nName binary=$metalBin"
                }
                Write-Host "  Metal nohup started binary=$metalBin log=$remoteRoot/logs/metal_${RunId}.log" -ForegroundColor DarkGreen
            }
            else {
                throw "PlanV: unknown Type '$($node.Type)' for node $nName (expected Swarm|Podman|Metal)"
            }
        }
    }
    finally {
        foreach ($t in @($tmpDb, $tmpScan)) {
            if (Test-Path -LiteralPath $t) {
                Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Write-Host "PlanV orchestration finished for RunId=$RunId" -ForegroundColor Cyan
}

function Invoke-DataBoarPlanVForensicConfigRenameOnAllNodes {
    <#
    .SYNOPSIS
      Fatal-error path: rename remote boar_config.yaml and config.yaml to *.failed for forensic evidence (all inventory nodes).
    #>
    $ctx = $script:DataBoarPlanVRunContext
    if (-not $ctx -or -not $ctx.Inventory) {
        return
    }
    $rr = [string]$ctx.RemoteRoot
    foreach ($node in $ctx.Inventory) {
        $nUser = [string]$node.SshUser
        $ssh = Resolve-DataBoarSshTarget -NodeName ([string]$node.Name) -IpAddress ([string]$node.Ip) -SshUser $nUser
        $snippet = "for f in boar_config.yaml config.yaml; do fp='$rr/config/'`"`$f`"; if [ -f `"`$fp`" ]; then mv -f `"`$fp`" `"`$fp.failed`" && echo PLANV_FORENSIC_MV:`"`$f`"; fi; done"
        $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $snippet -ConnectTimeoutSeconds 30
    }
}

function Invoke-DataBoarPlanVWriteCoverageReport {
    $ctx = $script:DataBoarPlanVRunContext
    Write-Host ""
    Write-Host "=== Relatorio de Cobertura de Scan (Lessons Learned / Plan V) ===" -ForegroundColor Yellow
    if (-not $ctx) {
        Write-Host "RunId: (context missing)" -ForegroundColor Red
        Write-Host "=== Fim do relatorio ===" -ForegroundColor Yellow
        return
    }
    Write-Host ("RunId: {0}" -f $ctx.RunId)
    Write-Host ("RemoteBenchRoot (all nodes): {0}" -f $ctx.RemoteRoot)
    Write-Host ("LocalLogRoot (orchestrator): {0}" -f $ctx.LocalLogRoot)
    Write-Host "Local log paths:" -ForegroundColor Cyan
    Write-Host ("  - {0}" -f (Join-Path $ctx.LocalLogRoot "logs"))
    if ($ctx.TranscriptPath) {
        Write-Host ("  - Transcript: {0}" -f $ctx.TranscriptPath)
    }
    Write-Host "Status de acesso por protocolo (material: mount nao vazio):" -ForegroundColor Cyan
    foreach ($row in $ctx.ProtocolRows) {
        $smbS = if ($row.SmbOk) { "OK" } else { "FAIL" }
        $nfsS = if ($row.NfsOk) { "OK" } else { "FAIL" }
        $sfsS = if ($row.SshfsOk) { "OK" } else { "FAIL" }
        Write-Host ("  Node={0} SSH={1} SMB({2})={3} NFS({4})={5} SSHFS({6})={7}" -f $row.Node, $row.SshTarget, $row.SmbPath, $smbS, $row.NfsPath, $nfsS, $row.SshfsPath, $sfsS)
    }
    $ok = $ctx.OrchestrationOk
    Write-Host ("Orchestration completed without throw: {0}" -f $ok)
    Write-Host ("Fatal path handled (forensic rename attempted): {0}" -f $ctx.TrapFired)
    if ($ctx.ContainsKey("SkippedNodeNames") -and $null -ne $ctx.SkippedNodeNames -and $ctx.SkippedNodeNames.Count -gt 0) {
        Write-Host "Nodes skipped (mount material abort, see PLANV_MOUNT_ABORT_*.log):" -ForegroundColor Yellow
        foreach ($sn in $ctx.SkippedNodeNames) {
            Write-Host ("  - {0}" -f $sn)
        }
    }
    Write-Host "=== Fim do relatorio ===" -ForegroundColor Yellow
    Write-Host ""
}

function Invoke-DataBoarPlanVCleanupSessionResources {
    <#
    .SYNOPSIS
      Remove Swarm DB+scanner stacks (per recorded cleanup rows), Podman synth+scanner+network, metal PID; light reap.
    #>
    $ctx = $script:DataBoarPlanVRunContext
    if (-not $ctx -or -not $ctx.Inventory) {
        return
    }
    $runId = [string]$ctx.RunId
    if ($ctx.ContainsKey("SwarmCleanup") -and $null -ne $ctx.SwarmCleanup -and $ctx.SwarmCleanup.Count -gt 0) {
        foreach ($rec in $ctx.SwarmCleanup) {
            $tssh = [string]$rec.SshTarget
            $sc = [string]$rec.ScanStack
            $db = [string]$rec.DbStack
            if ($sc) {
                $s1 = $sc -replace "'", "'\''"
                $inner1 = "docker stack rm '$s1' 2>/dev/null || true; echo PLANV_SCAN_RM"
                $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $tssh -RemoteShellSnippet $inner1 -ConnectTimeoutSeconds 120
            }
            if ($db) {
                $s2 = $db -replace "'", "'\''"
                $inner2 = "docker stack rm '$s2' 2>/dev/null || true; echo PLANV_DB_RM"
                $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $tssh -RemoteShellSnippet $inner2 -ConnectTimeoutSeconds 120
            }
        }
    }
    if ($ctx.ContainsKey("PodmanCleanup") -and $null -ne $ctx.PodmanCleanup -and $ctx.PodmanCleanup.Count -gt 0) {
        foreach ($rec in $ctx.PodmanCleanup) {
            $tssh = [string]$rec.SshTarget
            $tok = [string]$rec.Tok
            $net = [string]$rec.Net
            $scan = [string]$rec.Scanner
            $npg = "planv_${tok}_pg"
            $nmy = "planv_${tok}_my"
            $nmo = "planv_${tok}_mo"
            $scanE = $scan -replace "'", "'\''"
            $netE = $net -replace "'", "'\''"
            $inner = "podman stop '$scanE' 2>/dev/null || true; podman rm -f '$scanE' 2>/dev/null || true; podman rm -f '$npg' '$nmy' '$nmo' 2>/dev/null || true; podman network rm '$netE' 2>/dev/null || true; echo PLANV_PODMAN_SYNTH_CLEAN"
            $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $tssh -RemoteShellSnippet $inner -ConnectTimeoutSeconds 90
        }
    }
    else {
        foreach ($node in $ctx.Inventory) {
            $nName = [string]$node.Name
            $nIp = [string]$node.Ip
            $nType = ([string]$node.Type).Trim().ToLowerInvariant()
            $nUser = [string]$node.SshUser
            $ssh = Resolve-DataBoarSshTarget -NodeName $nName -IpAddress $nIp -SshUser $nUser
            if ($nType -eq "podman") {
                $slug = ($nName -replace '[^a-zA-Z0-9]', '_').ToLowerInvariant()
                $cname = "databoar_${runId}_$slug"
                $inner = "podman stop '$cname' 2>/dev/null || true; podman rm -f '$cname' 2>/dev/null || true; echo PLANV_PODMAN_RM_DONE"
                $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $inner -ConnectTimeoutSeconds 60
            }
        }
    }
    foreach ($node in $ctx.Inventory) {
        $nName = [string]$node.Name
        $nIp = [string]$node.Ip
        $nType = ([string]$node.Type).Trim().ToLowerInvariant()
        $nUser = [string]$node.SshUser
        $ssh = Resolve-DataBoarSshTarget -NodeName $nName -IpAddress $nIp -SshUser $nUser
        if ($nType -eq "metal") {
            $pidFile = ([string]$ctx.RemoteRoot) + "/logs/metal_${runId}.pid"
            $pf = $pidFile -replace "'", "'\''"
            $inner = 'if [ -f ''' + $pf + ''' ]; then kill $(cat ''' + $pf + ''') 2>/dev/null || true; rm -f ''' + $pf + '''; fi; wait 2>/dev/null || true; echo PLANV_METAL_STOP_DONE'
            $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $inner -ConnectTimeoutSeconds 30
        }
    }
    foreach ($node in $ctx.Inventory) {
        $nUser = [string]$node.SshUser
        $ssh = Resolve-DataBoarSshTarget -NodeName ([string]$node.Name) -IpAddress ([string]$node.Ip) -SshUser $nUser
        $reap = "sleep 1; wait 2>/dev/null || true; echo PLANV_REAP_OK"
        $null = Invoke-DataBoarPlanVRemoteSh -SshTarget $ssh -RemoteShellSnippet $reap -ConnectTimeoutSeconds 15
    }
}

function Invoke-DataBoarPlanVResilientRun {
    <#
    .SYNOPSIS
      Slice 4 entry: trap + try orchestration + finally report + optional teardown (zombie / orphan reduction).
    .PARAMETER RunId
      When empty, uses Get-Date yyyyMMdd_HHmmss.
    .PARAMETER TearDownAfterRun
      When true (default), removes stack/podman/metal resources for this RunId after the run (lab hygiene).
    .PARAMETER RunPreflightMounts
      When true, runs per-node mount material evidence (ls -A | wc -l); failing nodes are skipped with forensic logs, others run.
    .PARAMETER StartTranscript
      When true, writes Start-Transcript to LocalLogRoot (Windows orchestrator).
    #>
    param(
        [string] $RunId = "",
        [Parameter(Mandatory = $true)] $Inventory,
        [Parameter(Mandatory = $true)][string] $BoarConfigLocalPath,
        [string] $StackYamlLocalPath = "",
        [string] $PodmanImage = "",
        [bool] $TearDownAfterRun = $true,
        [bool] $RunPreflightMounts = $false,
        [bool] $StartTranscript = $false,
        [int] $ConnectTimeoutSeconds = 45
    )
    if (-not $RunId) {
        $RunId = Get-Date -Format "yyyyMMdd_HHmmss"
    }
    $localRoot = Join-Path $env:TEMP "databoar_planv_$RunId"
    $logDir = Join-Path $localRoot "logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $remoteRoot = Get-DataBoarPlanVRemoteBenchRoot -RunId $RunId
    $protocolRows = New-Object System.Collections.Generic.List[object]
    $skippedSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $swarmCleanupList = [System.Collections.Generic.List[object]]::new()
    $podmanCleanupList = [System.Collections.Generic.List[object]]::new()
    foreach ($node in $Inventory) {
        $nUser = [string]$node.SshUser
        $ssh = Resolve-DataBoarSshTarget -NodeName ([string]$node.Name) -IpAddress ([string]$node.Ip) -SshUser $nUser
        $protocolRows.Add((Get-DataBoarPlanVMountProtocolStatus -NodeName ([string]$node.Name) -SshTarget $ssh -ConnectTimeoutSeconds 20))
    }
    $transcriptPath = $null
    if ($StartTranscript) {
        $transcriptPath = Join-Path $logDir "planv_transcript.log"
        try {
            Start-Transcript -LiteralPath $transcriptPath -Force | Out-Null
        } catch {
            $transcriptPath = $null
        }
    }
    $script:DataBoarPlanVRunContext = @{
        RunId              = $RunId
        Inventory          = $Inventory
        RemoteRoot         = $remoteRoot
        LocalLogRoot       = $localRoot
        ProtocolRows       = $protocolRows
        OrchestrationOk    = $false
        TrapFired          = $false
        TearDownAfterRun   = $TearDownAfterRun
        TranscriptPath     = $transcriptPath
        SkippedNodeNames   = $skippedSet
        SwarmCleanup       = $swarmCleanupList
        PodmanCleanup      = $podmanCleanupList
    }

    # Resilience / Lessons Learned (PS 5.1): a bare trap+try/finally runs finally before trap on
    # terminating errors, so rename-after-fatal would run after the coverage report. Use catch for
    # forensic rename, then finally for report + teardown (correct order).

    try {
        if ($RunPreflightMounts) {
            foreach ($node in $Inventory) {
                $nUser = [string]$node.SshUser
                $sshP = Resolve-DataBoarSshTarget -NodeName ([string]$node.Name) -IpAddress ([string]$node.Ip) -SshUser $nUser
                $evP = Get-DataBoarPlanVMountMaterialEvidence -NodeName ([string]$node.Name) -SshTarget $sshP -ConnectTimeoutSeconds 20
		if (-not $evp.AllProtocolsOk) {
                    # REMEDIACAO SRE: Tenta montar usando o seu alias privilegiado
                    Write-Host "[SRE-REMEDY] Protocolos FAIL no no $($node.Name). Tentando LABOP_SHARE_CLIENTS..." -ForegroundColor Yellow
                    ssh $ssP "sudo /home/leitao/Projects/dev/data-boar/scripts/labop-share-client-install.sh --apply"

                    # Re-verifica a evidencia apos o sudo
                    $evp = Get-DataBoarPlanVMountMaterialEvidence -NodeName ([string]$node.Name) -SshTarget $ssP -ConnectTimeoutSeconds 20

                    # Logica de DecisAo: Se o alvo no config for local (/home/*), o FAIL de rede A ignorado
                    $isLocalTarget = (Get-Content $BoarConfigLocalPath | Select-String "path: .*/home/").Count -gt 0

                    if (-not $evp.AllProtocolsOk -and -not $isLocalTarget) {
                        # So aborta de verdade se continuar falhando E o alvo NAO for local
                        Invoke-DataBoarPlanVWriteMountAbortForensic -LocalLogDir $logDir -RunId $RunId -NodeName ([string]$node.Name) -Evidence $evp
                        [void]$skippedSet.Add([string]$node.Name)
                        continue
                    }
                    Write-Host "[SRE-REMEDY] No $($node.Name) liberado para o Plano-V (Alvo local ou RemediaAAo OK)." -ForegroundColor Cyan
                }
            }
        }
#        $skipArr = @($skippedSet.ToArray())
	$skipArr = @($skippedSet)
        Invoke-DataBoarPlanVInventoryOrchestration -RunId $RunId -Inventory $Inventory -BoarConfigLocalPath $BoarConfigLocalPath -StackYamlLocalPath $StackYamlLocalPath -PodmanImage $PodmanImage -SkippedNodeNames $skipArr -LocalForensicLogDir $logDir -ConnectTimeoutSeconds $ConnectTimeoutSeconds
        $script:DataBoarPlanVRunContext["OrchestrationOk"] = $true
    } catch {
        $script:DataBoarPlanVRunContext["TrapFired"] = $true
        Write-Warning ("PLANV_FATAL: {0}" -f $_.Exception.Message)
        try {
            Invoke-DataBoarPlanVForensicConfigRenameOnAllNodes
        } catch {
            Write-Warning ("PLANV_FORENSIC_RENAME_ERROR: {0}" -f $_.Exception.Message)
        }
        throw
    }
    finally {
        if ($StartTranscript -and $transcriptPath) {
            try {
                Stop-Transcript | Out-Null
            } catch {
            }
        }
        Invoke-DataBoarPlanVWriteCoverageReport
        if ($script:DataBoarPlanVRunContext -and $script:DataBoarPlanVRunContext["TearDownAfterRun"]) {
            Invoke-DataBoarPlanVCleanupSessionResources
        }
    }
}

# Default entry (not when dot-sourced): manifest inventory + resilient run + mount preflight.
# Optional: dot-source this file to define functions only:  . .\lab-completao-orchestrate-hybrid-v173-plano-v.ps1
if ($MyInvocation.InvocationName -ne '.') {
    $RepoRootV = (Get-Item $PSScriptRoot).Parent.FullName
    $manifestPathV = Join-Path $RepoRootV "docs\private\homelab\lab-op-hosts.manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPathV)) {
        Write-Error "Plan V requires lab manifest at $manifestPathV (copy from docs/private.example/homelab/lab-op-hosts.manifest.example.json)."
        exit 2
    }
    $InventoryV = Get-DataBoarPlanVInventoryFromManifest -ManifestPath $manifestPathV
    $cfgPathV = Join-Path $RepoRootV "config\boar_config.yaml"
    if (-not (Test-Path -LiteralPath $cfgPathV)) {
        Write-Error "Plan V requires repo config at $cfgPathV"
        exit 2
    }
    Invoke-DataBoarPlanVResilientRun -Inventory $InventoryV -BoarConfigLocalPath $cfgPathV -RunPreflightMounts $true
}
