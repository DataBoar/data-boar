#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Lab-MaestroCommon.ps1

.SYNOPSIS
 Shared helpers for Maestro handlers (#955 tmux isolation, #954 doas/sudo + env, sentinel contract).

.DESCRIPTION
 Dot-source from handlers: . "$PSScriptRoot/../Lab-MaestroCommon.ps1" (handlers) or
 . "$PSScriptRoot/Lab-MaestroCommon.ps1" (Maestro.ps1).
#>

Set-StrictMode -Version 2

function Initialize-MaestroLoginToolPath {
    <#
    #1003: Non-interactive shells often omit ~/.local/bin and ~/.cargo/env from PATH.
    Prepend operator tool paths before local uv/cargo/maturin invocations on the dev PC.
    #>
    $homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    if (-not $homeDir) { return }
    $cargoEnv = Join-Path $homeDir ".cargo" "env"
    if (Test-Path -LiteralPath $cargoEnv) { . $cargoEnv }
    foreach ($dir in @(
            (Join-Path $homeDir ".local" "bin"),
            (Join-Path $homeDir ".cargo" "bin")
        )) {
        if (Test-Path -LiteralPath $dir) {
            $env:PATH = "$dir$([IO.Path]::PathSeparator)$env:PATH"
        }
    }
}

function Get-MaestroRemoteLoginPathPrelude {
    <#
    #1003: Bash prelude for SSH/tmux payloads (parity with lab-completao-host-smoke.sh).
    #>
    return 'export PATH="${HOME}/.local/bin:${PATH}"; [ -f "${HOME}/.cargo/env" ] && . "${HOME}/.cargo/env"; '
}

function Get-HandlerTmuxSessionName {
    param([Parameter(Mandatory = $true)][string]$Persona)
    # Per-persona session avoids C-c clobber on multi-persona nodes (#955).
    return "completao_$Persona"
}

function Get-EnsureAlarmFromOutput {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Lines,
        [Parameter(Mandatory = $true)][string]$LogTag
    )
    foreach ($line in @($Lines)) {
        if ($line -match "\[$LogTag\] ALARM=([a-z_]+)(?: hint=([^\s]+))?") {
            return [pscustomobject]@{
                Alarm = $Matches[1]
                Hint  = $Matches[2]
            }
        }
    }
    return $null
}

function Add-MaestroHandlerExitTally {
    <#
    #1021 R9b: passou (0) vs degradou (3) vs falhou (other). Exit 3 is ALARM, not REAL FAIL.
    #>
    param(
        [Parameter(Mandatory = $true)][int]$ExitCode,
        [ref]$FailCount,
        [ref]$AlarmCount
    )
    if ($ExitCode -eq 0) { return }
    if ($ExitCode -eq 3) {
        $AlarmCount.Value++
        return
    }
    $FailCount.Value++
}

function Format-MaestroHandlersSummary {
    <#
    Per-host handler rollup for Deep smoke / gate reports (#1021 R9b).
    #>
    param(
        [bool]$GateOk,
        [int]$HandlerRan = 0,
        [int]$HandlerFails = 0,
        [int]$HandlerAlarms = 0
    )
    if (-not $GateOk) { return 'SKIP' }
    if ($HandlerRan -eq 0) { return 'NONE' }
    if ($HandlerFails -gt 0) { return "FAIL:$HandlerFails" }
    if ($HandlerAlarms -gt 0) { return "ALARM:$HandlerAlarms" }
    return 'OK'
}

function Get-LabDbInitStageBash {
    <#
    #1021 R11: SCP/rsync often leaves init SQL at 660; rootless podman cannot read bind mount.
    Stage to /tmp with a+rX before podman run (see LAB_SMOKE_MULTI_HOST.md / ADR-0029).
    #>
    return @'
stage_lab_db_init() {
  local src="$1"
  local label="$2"
  local dest="/tmp/databoar-lab-init/${label}"
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -a "${src}/." "$dest/"
  chmod -R a+rX "$dest"
  printf '%s' "$dest"
}
ensure_lab_smoke_init_readable() {
  local dir
  for dir in "$@"; do
    if [ -d "$dir" ]; then
      chmod -R a+rX "$dir" 2>/dev/null || true
    fi
  done
}
'@.Trim()
}

function Confirm-TargetDbSyntheticData {
    <#
    #1021 R9c: after container READY, prove init seed rows exist (not just port open).
    Uses podman/docker exec against lab-* containers; retries while entrypoint init runs.
    #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][ValidateSet('postgres', 'mariadb', 'mongodb')]
        [string]$Engine,
        [int]$Port = 0,
        [int]$MaxAttempts = 15,
        [int]$WaitSeconds = 2
    )

    $repoPath = Get-MaestroRemoteRepoPath -RepoPath ([string]$Node.path)
    $stackDir = "$repoPath/deploy/lab-smoke-stack"

    $engineBody = switch ($Engine) {
        'postgres' {
            @'
cd __STACK_DIR__
_pg_container_state() {
  if command -v podman >/dev/null 2>&1 && podman ps -a --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-postgres'; then
    podman inspect -f '{{.State.Status}}' lab-postgres 2>/dev/null || echo missing
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose ps lab-postgres 2>/dev/null | grep -q 'Up'; then
    echo running
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose ps -a lab-postgres 2>/dev/null | grep -q lab-postgres; then
    echo exited
    return
  fi
  echo missing
}
_count_pg() {
  if command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-postgres'; then
    podman exec lab-postgres psql -U "${LAB_PG_USER:-lab_smoke}" -d "${LAB_PG_DATABASE:-lab_smoke_pg}" -tAc "SELECT count(*) FROM lab_customers;"
  elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker compose exec -T lab-postgres psql -U "${LAB_PG_USER:-lab_smoke}" -d "${LAB_PG_DATABASE:-lab_smoke_pg}" -tAc "SELECT count(*) FROM lab_customers;"
  else
    return 2
  fi
}
st=$(_pg_container_state)
if [ "$st" != "running" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=postgres reason=confirm_unreachable container=$st"
  command -v podman >/dev/null 2>&1 && podman logs --tail 5 lab-postgres 2>&1 || true
  exit 1
fi
attempt=0
last_err=""
while [ "$attempt" -lt __MAX_ATTEMPTS__ ]; do
  cnt=$(_count_pg 2>"/tmp/databoar-pg-count.err") || cnt=""
  last_err=$(tail -1 /tmp/databoar-pg-count.err 2>/dev/null || true)
  cnt=$(printf '%s' "$cnt" | tr -d '[:space:]')
  if printf '%s' "$cnt" | grep -Eq '^[0-9]+$' && [ "$cnt" -gt 0 ]; then
    echo "SYNTHETIC_DATA_OK engine=postgres table=lab_customers count=$cnt"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep __WAIT_SECONDS__
done
if [ -n "$last_err" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=postgres reason=confirm_exec_failed detail=${last_err}"
else
  echo "SYNTHETIC_DATA_FAIL engine=postgres reason=seed_empty container=running"
fi
exit 1
'@
        }
        'mariadb' {
            @'
cd __STACK_DIR__
_my_container_state() {
  if command -v podman >/dev/null 2>&1 && podman ps -a --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-mariadb'; then
    podman inspect -f '{{.State.Status}}' lab-mariadb 2>/dev/null || echo missing
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose ps lab-mariadb 2>/dev/null | grep -q 'Up'; then
    echo running
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose ps -a lab-mariadb 2>/dev/null | grep -q lab-mariadb; then
    echo exited
    return
  fi
  echo missing
}
_count_my() {
  if command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-mariadb'; then
    podman exec lab-mariadb mariadb -u"${LAB_MY_USER:-lab_smoke}" -p"${LAB_MY_PASSWORD:-lab_smoke_change_me}" -N -e "SELECT count(*) FROM lab_customers;" "${LAB_MY_DATABASE:-lab_smoke_my}"
  elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker compose exec -T lab-mariadb mariadb -u"${LAB_MY_USER:-lab_smoke}" -p"${LAB_MY_PASSWORD:-lab_smoke_change_me}" -N -e "SELECT count(*) FROM lab_customers;" "${LAB_MY_DATABASE:-lab_smoke_my}"
  else
    return 2
  fi
}
st=$(_my_container_state)
if [ "$st" != "running" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=mariadb reason=confirm_unreachable container=$st"
  command -v podman >/dev/null 2>&1 && podman logs --tail 5 lab-mariadb 2>&1 || true
  exit 1
fi
attempt=0
last_err=""
while [ "$attempt" -lt __MAX_ATTEMPTS__ ]; do
  cnt=$(_count_my 2>"/tmp/databoar-my-count.err") || cnt=""
  last_err=$(tail -1 /tmp/databoar-my-count.err 2>/dev/null || true)
  cnt=$(printf '%s' "$cnt" | tr -d '[:space:]')
  if printf '%s' "$cnt" | grep -Eq '^[0-9]+$' && [ "$cnt" -gt 0 ]; then
    echo "SYNTHETIC_DATA_OK engine=mariadb table=lab_customers count=$cnt"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep __WAIT_SECONDS__
done
if [ -n "$last_err" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=mariadb reason=confirm_exec_failed detail=${last_err}"
else
  echo "SYNTHETIC_DATA_FAIL engine=mariadb reason=seed_empty container=running"
fi
exit 1
'@
        }
        'mongodb' {
            @'
cd __STACK_DIR__
_mongo_container_state() {
  if command -v podman >/dev/null 2>&1 && podman ps -a --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-mongodb'; then
    podman inspect -f '{{.State.Status}}' lab-mongodb 2>/dev/null || echo missing
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose -f docker-compose.mongo.yml ps lab-mongodb 2>/dev/null | grep -q 'Up'; then
    echo running
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose -f docker-compose.mongo.yml ps -a lab-mongodb 2>/dev/null | grep -q lab-mongodb; then
    echo exited
    return
  fi
  echo missing
}
_count_mongo() {
  if command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' 2>/dev/null | grep -qx 'lab-mongodb'; then
    podman exec lab-mongodb mongosh --quiet --eval 'db.getSiblingDB("lab_smoke_mongo").lab_people.countDocuments()'
  elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker compose -f docker-compose.mongo.yml exec -T lab-mongodb mongosh --quiet --eval 'db.getSiblingDB("lab_smoke_mongo").lab_people.countDocuments()'
  else
    return 2
  fi
}
st=$(_mongo_container_state)
if [ "$st" != "running" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=mongodb reason=confirm_unreachable container=$st"
  command -v podman >/dev/null 2>&1 && podman logs --tail 5 lab-mongodb 2>&1 || true
  exit 1
fi
attempt=0
last_err=""
while [ "$attempt" -lt __MAX_ATTEMPTS__ ]; do
  cnt=$(_count_mongo 2>"/tmp/databoar-mongo-count.err") || cnt=""
  last_err=$(tail -1 /tmp/databoar-mongo-count.err 2>/dev/null || true)
  cnt=$(printf '%s' "$cnt" | tr -d '[:space:]')
  if printf '%s' "$cnt" | grep -Eq '^[0-9]+$' && [ "$cnt" -gt 0 ]; then
    echo "SYNTHETIC_DATA_OK engine=mongodb collection=lab_people count=$cnt"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep __WAIT_SECONDS__
done
if [ -n "$last_err" ]; then
  echo "SYNTHETIC_DATA_FAIL engine=mongodb reason=confirm_exec_failed detail=${last_err}"
else
  echo "SYNTHETIC_DATA_FAIL engine=mongodb reason=seed_empty container=running"
fi
exit 1
'@
        }
    }

    $remoteCmd = $engineBody.Replace('__STACK_DIR__', $stackDir).Replace('__MAX_ATTEMPTS__', [string]$MaxAttempts).Replace('__WAIT_SECONDS__', [string]$WaitSeconds) -replace "`r", ""

    $out = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
        "$($Node.user)@$($Node.hostname)" "$remoteCmd" 2>&1
    $text = ($out | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $text -match 'SYNTHETIC_DATA_OK') {
        $countMatch = [regex]::Match($text, 'count=(\d+)')
        $count = if ($countMatch.Success) { [int]$countMatch.Groups[1].Value } else { 0 }
        return [pscustomobject]@{ Ok = $true; Count = $count; Detail = $text }
    }
    $failDetail = if ($text) { $text } else { "ssh_exit=$LASTEXITCODE engine=$Engine port=$Port" }
    return [pscustomobject]@{ Ok = $false; Count = 0; Detail = $failDetail }
}

function Get-LabPrivilegeInvoker {
    <#
    Returns the non-interactive privilege prefix for remote ensure scripts (#954).
    #1021 R8: env vars go to .labop-gate/ context files (Plano B); privileged argv is
    canonical bash + script only so narrow sudoers/doas grants match literally.
    #>
    return @'
if command -v doas >/dev/null 2>&1; then echo "doas -n"; elif command -v sudo >/dev/null 2>&1; then echo "sudo -n"; else echo "NO_PRIV"; fi
'@.Trim()
}

function Get-LabCanonicalBashProbe {
    <#
    #1021 R8: prefer /usr/bin/bash and /bin/bash before command -v (usrmerge secure_path).
    #>
    return @'
BASH_BIN=""; for _b in /usr/bin/bash /bin/bash; do if [ -x "$_b" ]; then BASH_BIN="$_b"; break; fi; done; if [ -z "$BASH_BIN" ]; then echo "[Ensure] bash_bin_unresolved" >&2; exit 2; fi
'@.Trim()
}

function Build-EnsureRemoteCommand {
    param(
        [Parameter(Mandatory = $true)][string]$EnsureScript,
        [Parameter(Mandatory = $true)][string]$EnsureMode,
        [hashtable]$EnvVars = @{}
    )
    $privProbe = Get-LabPrivilegeInvoker
    $bashProbe = Get-LabCanonicalBashProbe
    $ctxFileByKey = @{
        LAB_OP_SUBNET = 'LAB_OP_SUBNET'
        LAB_NFS_SVC   = 'LAB_NFS_SVC'
        LAB_PKG_MGR   = 'LAB_PKG_MGR'
    }
    $ctxWrites = @()
    foreach ($k in $EnvVars.Keys) {
        $v = [string]$EnvVars[$k]
        if ($v -match "[\s'`"$\\]") {
            throw "Build-EnsureRemoteCommand: unsafe env value for $k"
        }
        if (-not $ctxFileByKey.ContainsKey($k)) {
            throw "Build-EnsureRemoteCommand: unsupported context key $k (use .labop-gate files)"
        }
        $fname = $ctxFileByKey[$k]
        $ctxWrites += "printf '%s\n' '$v' >`"`$GATE_DIR/$fname`""
    }
    $ctxBlock = if ($ctxWrites.Count -gt 0) {
        "ENSURE_SCRIPT=$EnsureScript; GATE_DIR=`"`$(cd `"`$(dirname `"`$ENSURE_SCRIPT`")/..`" && pwd)/.labop-gate`"; mkdir -p `"`$GATE_DIR`"; $($ctxWrites -join '; '); "
    } else {
        "ENSURE_SCRIPT=$EnsureScript; "
    }
    return "${ctxBlock}PRIV=`$($privProbe)` ; if [ `"`$PRIV`" = NO_PRIV ]; then echo '[Ensure] NO doas/sudo on host' >&2; exit 2; fi; $bashProbe; `$PRIV `"`$BASH_BIN`" `"`$ENSURE_SCRIPT`" '$EnsureMode' 2>&1"
}

function Invoke-HandlerTmuxPayload {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$Persona,
        [Parameter(Mandatory = $true)][string]$PayloadB64,
        [switch]$SkipSessionCreate
    )
    $session = Get-HandlerTmuxSessionName -Persona $Persona
    $create = if ($SkipSessionCreate) { "" } else {
        "tmux has-session -t $session 2>/dev/null || tmux new-session -d -s $session ; "
    }
    # No C-c: dedicated session per persona (#955).
    # #1003: login-env PATH before decoded payload (non-interactive tmux lacks ~/.local/bin).
    $prelude = Get-MaestroRemoteLoginPathPrelude
    $tmuxCmd = "${create}tmux send-keys -t $session '${prelude}echo $PayloadB64 | base64 -d | bash' Enter"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
        "$($Node.user)@$($Node.hostname)" "$tmuxCmd"
    return $LASTEXITCODE
}

function Write-RemoteSentinel {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$SentinelFile,
        [Parameter(Mandatory = $true)][int]$ExitCode
    )
    $dir = Split-Path -Parent $SentinelFile
    $cmd = "mkdir -p $dir && echo $ExitCode > $SentinelFile"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
}

function Clear-RemoteSentinel {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$SentinelFile
    )
    $cmd = "rm -f $SentinelFile"
    ssh -q -o BatchMode=yes -o ConnectTimeout=15 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
}

function Reset-LabOpStatus {
    <#
    #969: clear stale ~/.labop-status at the start of each Maestro turn so yesterday's
    DONE_FAILED does not masquerade as the current run outcome.
    #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$RunMarker
    )
    $safeMarker = $RunMarker -replace "'", ""
    $cmd = "echo 'NOT_RUN maestro=$safeMarker at '`$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)' > ~/.labop-status"
    ssh -q -o BatchMode=yes -o ConnectTimeout=8 "$($Node.user)@$($Node.hostname)" "$cmd" > $null 2>&1
    return ($LASTEXITCODE -eq 0)
}

function Get-MaestroCanonicalRepoPath {
    param([Parameter(Mandatory = $true)][string]$RepoPath)
    # Same suffix strip as Handle-target_nfs.ps1 / Handle-target_cifs.ps1 (#99b6fdc).
    return ($RepoPath -replace "-v[0-9]+\.[0-9]+\.[0-9]+[^/\\]*$", "")
}

function Get-MaestroRemoteRepoPath {
    param([Parameter(Mandatory = $true)][string]$RepoPath)
    $canonical = Get-MaestroCanonicalRepoPath -RepoPath $RepoPath
    if ($canonical -match '^~(/.*)$') {
        return "`$HOME$($Matches[1])"
    }
    return $canonical
}

function Invoke-LabopGateReadiness {
    <#
    #960: ALARM (--check) skips handlers; REMEDIATE (-Deep / --apply) uses narrow grants.
    #>
    param(
        [Parameter(Mandatory = $true)]$Node,
        [switch]$Deep
    )
    $personaList = @($Node.personas)
    if (-not $personaList -or $personaList.Count -eq 0) {
        return $true
    }
    $personaCsv = ($personaList -join ',')
    $repoPath = Get-MaestroRemoteRepoPath -RepoPath ([string]$Node.path)
    $mode = if ($Deep) { '--apply' } else { '--check' }
    $ctxSetup = ""
    if ($Node.PSObject.Properties.Name -contains 'lab_op_subnet' -and $Node.lab_op_subnet) {
        $subnet = [string]$Node.lab_op_subnet
        if ($subnet -match "[\s'`"$\\]") {
            throw "Invoke-LabopGateReadiness: unsafe lab_op_subnet on $($Node.hostname)"
        }
        $ctxSetup = "mkdir -p .labop-gate && printf '%s\n' '$subnet' > .labop-gate/LAB_OP_SUBNET && "
    }
    $bashProbe = Get-LabCanonicalBashProbe
    $gateScript = "$repoPath/scripts/labop-gate-readiness.sh"
    $remoteCmd = "cd $repoPath && ${ctxSetup}${bashProbe}; `"`$BASH_BIN`" $gateScript $mode --personas '$personaCsv' 2>&1"
    Write-Host "      [GateReadiness] $mode on $($Node.hostname) personas=$personaCsv" -ForegroundColor DarkCyan
    $output = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 `
        "$($Node.user)@$($Node.hostname)" $remoteCmd 2>&1
    foreach ($line in @($output)) {
        if ($line) { Write-Host "      $line" }
    }
    if ($LASTEXITCODE -ne 0) {
        if ($Deep) {
            Write-Warning "      [REAL FAIL] Gate readiness --apply failed on $($Node.hostname)"
        } else {
            Write-Warning "      [ALARM] Gate readiness failed on $($Node.hostname). Handlers skipped. Use -Deep to remediate."
        }
        return $false
    }
    return $true
}
