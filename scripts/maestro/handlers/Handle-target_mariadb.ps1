#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/handlers/Handle-target_mariadb.ps1

.SYNOPSIS
 Sub-orchestrator for persona 'target_mariadb'.

.DESCRIPTION
 Brings up the synthetic MariaDB service on the target host via Docker/Podman compose
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

Write-Host "   [Target-MariaDB] Provisionando MariaDB sintetico em $($Node.hostname)..." -ForegroundColor Magenta

$sentinelDir  = "/tmp/databoar_handler"
$sentinelFile = "$sentinelDir/target_mariadb_sentinel.txt"

$remoteCmd = @'
set -e
SENTINEL="__SENTINEL__"
mkdir -p "$(dirname "$SENTINEL")"
_rc=0
trap '_rc=$?; echo $_rc > "$SENTINEL"; exit $_rc' EXIT
cd __NODE_PATH__/deploy/lab-smoke-stack
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
DEFAULT_PORT="${LAB_MY_PORT:-33306}"
PORT_CANDIDATES="${LAB_MY_PORT_CANDIDATES:-$DEFAULT_PORT 33307 33308 33309}"
CHOSEN_PORT="$(pick_port "$DEFAULT_PORT" "$PORT_CANDIDATES")"
AUTOCLEAN="${LAB_TARGET_DB_AUTOCLEAN:-0}"
if [ "$AUTOCLEAN" = "1" ]; then
  trap 'docker rm -f lab-mariadb >/dev/null 2>&1 || podman rm -f lab-mariadb >/dev/null 2>&1 || true' EXIT
fi
if command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
  podman rm -f lab-mariadb >/dev/null 2>&1 || true
  podman run -d --name lab-mariadb \
    -p "${CHOSEN_PORT}:3306" \
    -e MARIADB_ROOT_PASSWORD="${LAB_MY_ROOT_PASSWORD:-lab_smoke_root_change_me}" \
    -e MARIADB_DATABASE="${LAB_MY_DATABASE:-lab_smoke_my}" \
    -e MARIADB_USER="${LAB_MY_USER:-lab_smoke}" \
    -e MARIADB_PASSWORD="${LAB_MY_PASSWORD:-lab_smoke_change_me}" \
    -v "$PWD/init/mariadb:/docker-entrypoint-initdb.d:ro" \
    docker.io/library/mariadb:11 >/dev/null
  podman ps --filter name=lab-mariadb --format "{{.Names}} {{.Status}}" || true
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  export LAB_MY_PORT="$CHOSEN_PORT"
  docker compose up -d lab-mariadb >/dev/null
  docker compose ps lab-mariadb || true
else
  echo "NO_ENGINE"
  exit 7
fi
echo "TARGET_MARIADB_READY port=${CHOSEN_PORT} at $(date +'%H:%M:%S')" > ~/.labop-status
echo "TARGET_MARIADB_READY port=${CHOSEN_PORT}"
'@
$remoteCmd = $remoteCmd.Replace("__SENTINEL__", $sentinelFile)
$remoteCmd = $remoteCmd.Replace("__NODE_PATH__", [string]$Node.path) -replace "`r", ""

$out = ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$($Node.user)@$($Node.hostname)" "$remoteCmd"
if ($LASTEXITCODE -eq 0 -and $out -match "TARGET_MARIADB_READY") {
    $portMatch = [regex]::Match(($out -join "`n"), "port=(\d+)")
    $portNum = if ($portMatch.Success) { [int]$portMatch.Groups[1].Value } else { 0 }
    if ($portMatch.Success) {
        Write-Host "      [SUCCESS] MariaDB sintetico pronto em $($Node.hostname) (porta $portNum)." -ForegroundColor Green
    } else {
        Write-Host "      [SUCCESS] MariaDB sintetico pronto em $($Node.hostname)." -ForegroundColor Green
    }
    $verify = Confirm-TargetDbSyntheticData -Node $Node -Engine mariadb -Port $portNum
    if (-not $verify.Ok) {
        Write-Warning "      [REAL FAIL] MariaDB up mas dados sinteticos ausentes: $($verify.Detail)"
        Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
        exit 1
    }
    Write-Host "      [VERIFY] lab_customers count=$($verify.Count) (synthetic seed OK)" -ForegroundColor Green
} else {
    Write-Warning "      [WARNING] Falha ao provisionar target_mariadb em $($Node.hostname)."
    Write-RemoteSentinel -Node $Node -SentinelFile $sentinelFile -ExitCode 1
    exit 1
}
