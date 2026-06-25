#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_postgres.ps1

.SYNOPSIS
 Sub-orchestrator for persona 'target_postgres'.

.DESCRIPTION
 Brings up the synthetic PostgreSQL service on the target host via Docker/Podman compose
 and emits readiness signals for cross-host Data Boar scans.
#>

param(
    [Parameter(Mandatory = $true)]$Node,
    [string]$Ref = "WorkingTree",
    [switch]$Deep,
    [string]$BenchTrack = "",
    [string]$BenchRunId = "",
    [switch]$BenchCompare,
    [int]$BenchWebPort = 0,
    [string]$BenchHealthUrl = ""
)

. "$PSScriptRoot/../Lab-MaestroCommon.ps1"

Write-Host "   [Target-Postgres] Provisionando Postgres sintetico em $($Node.hostname)..." -ForegroundColor Magenta

$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_postgres_sentinel.txt"

$remoteCmd = @'
set -e
SENTINEL="__SENTINEL__"
mkdir -p "$(dirname "$SENTINEL")"
_rc=0
trap '_rc=$?; echo $_rc > "$SENTINEL"; exit $_rc' EXIT
cd __NODE_PATH__/deploy/lab-smoke-stack
__DB_INIT_STAGE__
ensure_lab_smoke_init_readable "$PWD/init/postgres"
PG_INIT="$(stage_lab_db_init "$PWD/init/postgres" postgres)"
pick_port() {
  local default_port="$1"
  local candidates="$2"
  local p
  for p in $candidates; do
    if ! ss -ltn 2>/dev/null | grep -q ":${p}\b"; then
      echo "$p"
      return 0
    fi
  done
  echo "$default_port"
}
DEFAULT_PORT="${LAB_PG_PORT:-55432}"
PORT_CANDIDATES="${LAB_PG_PORT_CANDIDATES:-$DEFAULT_PORT 55433 55434 55435}"
CHOSEN_PORT="$(pick_port "$DEFAULT_PORT" "$PORT_CANDIDATES")"
AUTOCLEAN="${LAB_TARGET_DB_AUTOCLEAN:-0}"
if [ "$AUTOCLEAN" = "1" ]; then
  trap 'docker rm -f lab-postgres >/dev/null 2>&1 || podman rm -f lab-postgres >/dev/null 2>&1 || true' EXIT
fi
if command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
  podman rm -f lab-postgres >/dev/null 2>&1 || true
  podman run -d --name lab-postgres \
    -p "${CHOSEN_PORT}:5432" \
    -e POSTGRES_USER="${LAB_PG_USER:-lab_smoke}" \
    -e POSTGRES_PASSWORD="${LAB_PG_PASSWORD:-lab_smoke_change_me}" \
    -e POSTGRES_DB="${LAB_PG_DATABASE:-lab_smoke_pg}" \
    -v "${PG_INIT}:/docker-entrypoint-initdb.d:ro" \
    docker.io/library/postgres:16-alpine >/dev/null
  for _w in $(seq 1 60); do
    if podman inspect -f '{{.State.Status}}' lab-postgres 2>/dev/null | grep -qx running; then
      break
    fi
    if podman inspect -f '{{.State.Status}}' lab-postgres 2>/dev/null | grep -qx exited; then
      echo "TARGET_POSTGRES_INIT_FAIL"
      podman logs --tail 8 lab-postgres 2>&1 || true
      exit 1
    fi
    sleep 1
  done
  podman ps --filter name=lab-postgres --format "{{.Names}} {{.Status}}" || true
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  export LAB_PG_PORT="$CHOSEN_PORT"
  ensure_lab_smoke_init_readable "$PWD/init/postgres"
  docker compose up -d lab-postgres >/dev/null
  docker compose ps lab-postgres || true
else
  echo "NO_ENGINE"
  exit 7
fi
echo "TARGET_POSTGRES_READY port=${CHOSEN_PORT} at $(date +'%H:%M:%S')" > ~/.labop-status
echo "TARGET_POSTGRES_READY port=${CHOSEN_PORT}"
'@
$remoteCmd = $remoteCmd.Replace("__SENTINEL__", $sentinelFile)
$remoteCmd = $remoteCmd.Replace("__NODE_PATH__", [string]$Node.path)
$remoteCmd = $remoteCmd.Replace("__DB_INIT_STAGE__", (Get-LabDbInitStageBash))
$remoteCmd = $remoteCmd -replace "`r", ""

$out = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$remoteCmd"
if ($LASTEXITCODE -eq 0 -and $out -match "TARGET_POSTGRES_READY") {
    $portMatch = [regex]::Match(($out -join "`n"), "port=(\d+)")
    $portNum = if ($portMatch.Success) { [int]$portMatch.Groups[1].Value } else { 0 }
    if ($portMatch.Success) {
        Write-Host "      [SUCCESS] Postgres sintetico pronto em $($Node.hostname) (porta $portNum)." -ForegroundColor Green
    } else {
        Write-Host "      [SUCCESS] Postgres sintetico pronto em $($Node.hostname)." -ForegroundColor Green
    }
    $verify = Confirm-TargetDbSyntheticData -Node $Node -Engine postgres -Port $portNum
    if (-not $verify.Ok) {
        Write-Warning "      [REAL FAIL] Postgres up mas dados sinteticos ausentes: $($verify.Detail)"
        Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
        exit 1
    }
    Write-Host "      [VERIFY] lab_customers count=$($verify.Count) (synthetic seed OK)" -ForegroundColor Green
} else {
    Write-Warning "      [WARNING] Falha ao provisionar target_postgres em $($Node.hostname)."
    Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
    exit 1
}
