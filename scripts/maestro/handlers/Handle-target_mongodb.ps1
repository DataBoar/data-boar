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
    [switch]$Deep
)

Write-Host "   [Target-MongoDB] Provisionando MongoDB sintetico em $($Node.hostname)..." -ForegroundColor Magenta

$remoteCmd = @'
set -e
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
    -v "$PWD/init/mongodb:/docker-entrypoint-initdb.d:ro" \
    docker.io/library/mongo:7 >/dev/null
  podman ps --filter name=lab-mongodb --format "{{.Names}} {{.Status}}" || true
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  export LAB_MONGO_PORT="$CHOSEN_PORT"
  docker compose -f docker-compose.mongo.yml up -d lab-mongodb >/dev/null
  docker compose -f docker-compose.mongo.yml ps lab-mongodb || true
else
  echo "NO_ENGINE"
  exit 7
fi
echo "TARGET_MONGODB_READY port=${CHOSEN_PORT} at $(date +'%H:%M:%S')" > ~/.labop-status
echo "TARGET_MONGODB_READY port=${CHOSEN_PORT}"
'@
$remoteCmd = $remoteCmd.Replace("__NODE_PATH__", [string]$Node.path) -replace "`r", ""

$out = ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$remoteCmd"
if ($LASTEXITCODE -eq 0 -and $out -match "TARGET_MONGODB_READY") {
    $portMatch = [regex]::Match(($out -join "`n"), "port=(\d+)")
    if ($portMatch.Success) {
        Write-Host "      [SUCCESS] MongoDB sintetico pronto em $($Node.hostname) (porta $($portMatch.Groups[1].Value))." -ForegroundColor Green
    } else {
        Write-Host "      [SUCCESS] MongoDB sintetico pronto em $($Node.hostname)." -ForegroundColor Green
    }
} else {
    Write-Warning "      [WARNING] Falha ao provisionar target_mongodb em $($Node.hostname)."
}
