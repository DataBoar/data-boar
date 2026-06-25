#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_mongodb.ps1

.SYNOPSIS
 Sub-orchestrator for persona 'target_mongodb'.

.DESCRIPTION
 Brings up the synthetic MongoDB service on the target host via Docker/Podman compose
 using docker-compose.mongo.yml and emits readiness signals for cross-host scans.
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

Write-Host "   [Target-MongoDB] Provisionando MongoDB sintetico em $($Node.hostname)..." -ForegroundColor Magenta

$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_mongodb_sentinel.txt"

$remoteCmd = @'
set -e
SENTINEL="__SENTINEL__"
mkdir -p "$(dirname "$SENTINEL")"
_rc=0
trap '_rc=$?; echo $_rc > "$SENTINEL"; exit $_rc' EXIT
cd __NODE_PATH__/deploy/lab-smoke-stack
__DB_INIT_STAGE__
ensure_lab_smoke_init_readable "$PWD/init/mongodb"
MONGO_INIT="$(stage_lab_db_init "$PWD/init/mongodb" mongodb)"
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
DEFAULT_PORT="${LAB_MONGO_PORT:-27018}"
PORT_CANDIDATES="${LAB_MONGO_PORT_CANDIDATES:-$DEFAULT_PORT 27019 27020 27021}"
CHOSEN_PORT="$(pick_port "$DEFAULT_PORT" "$PORT_CANDIDATES")"
AUTOCLEAN="${LAB_TARGET_DB_AUTOCLEAN:-0}"
if [ "$AUTOCLEAN" = "1" ]; then
  trap 'docker rm -f lab-mongodb >/dev/null 2>&1 || podman rm -f lab-mongodb >/dev/null 2>&1 || true' EXIT
fi
if command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
  podman rm -f lab-mongodb >/dev/null 2>&1 || true
  podman run -d --name lab-mongodb \
    -p "${CHOSEN_PORT}:27017" \
    -v "${MONGO_INIT}:/docker-entrypoint-initdb.d:ro" \
    docker.io/library/mongo:7 >/dev/null
  for _w in $(seq 1 90); do
    if podman inspect -f '{{.State.Status}}' lab-mongodb 2>/dev/null | grep -qx running; then
      break
    fi
    if podman inspect -f '{{.State.Status}}' lab-mongodb 2>/dev/null | grep -qx exited; then
      echo "TARGET_MONGODB_INIT_FAIL"
      podman logs --tail 8 lab-mongodb 2>&1 || true
      exit 1
    fi
    sleep 1
  done
  podman ps --filter name=lab-mongodb --format "{{.Names}} {{.Status}}" || true
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  export LAB_MONGO_PORT="$CHOSEN_PORT"
  ensure_lab_smoke_init_readable "$PWD/init/mongodb"
  docker compose -f docker-compose.mongo.yml up -d lab-mongodb >/dev/null
  docker compose -f docker-compose.mongo.yml ps lab-mongodb || true
else
  echo "NO_ENGINE"
  exit 7
fi
echo "TARGET_MONGODB_READY port=${CHOSEN_PORT} at $(date +'%H:%M:%S')" > ~/.labop-status
echo "TARGET_MONGODB_READY port=${CHOSEN_PORT}"
'@
$remoteCmd = $remoteCmd.Replace("__SENTINEL__", $sentinelFile)
$remoteCmd = $remoteCmd.Replace("__NODE_PATH__", [string]$Node.path)
$remoteCmd = $remoteCmd.Replace("__DB_INIT_STAGE__", (Get-LabDbInitStageBash))
$remoteCmd = $remoteCmd -replace "`r", ""

$out = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$remoteCmd"
if ($LASTEXITCODE -eq 0 -and $out -match "TARGET_MONGODB_READY") {
    $portMatch = [regex]::Match(($out -join "`n"), "port=(\d+)")
    $portNum = if ($portMatch.Success) { [int]$portMatch.Groups[1].Value } else { 0 }
    if ($portMatch.Success) {
        Write-Host "      [SUCCESS] MongoDB sintetico pronto em $($Node.hostname) (porta $portNum)." -ForegroundColor Green
    } else {
        Write-Host "      [SUCCESS] MongoDB sintetico pronto em $($Node.hostname)." -ForegroundColor Green
    }
    $verify = Confirm-TargetDbSyntheticData -Node $Node -Engine mongodb -Port $portNum
    if (-not $verify.Ok) {
        Write-Warning "      [REAL FAIL] MongoDB up mas dados sinteticos ausentes: $($verify.Detail)"
        Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
        exit 1
    }
    Write-Host "      [VERIFY] lab_people count=$($verify.Count) (synthetic seed OK)" -ForegroundColor Green
} else {
    Write-Warning "      [WARNING] Falha ao provisionar target_mongodb em $($Node.hostname)."
    Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
    exit 1
}
