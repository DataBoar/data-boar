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
    [switch]$Deep
)

Write-Host "   [Target-Postgres] Provisionando Postgres sintetico em $($Node.hostname)..." -ForegroundColor Magenta

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
    -v "$PWD/init/postgres:/docker-entrypoint-initdb.d:ro" \
    docker.io/library/postgres:16-alpine >/dev/null
  podman ps --filter name=lab-postgres --format "{{.Names}} {{.Status}}" || true
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  export LAB_PG_PORT="$CHOSEN_PORT"
  docker compose up -d lab-postgres >/dev/null
  docker compose ps lab-postgres || true
else
  echo "NO_ENGINE"
  exit 7
fi
echo "TARGET_POSTGRES_READY port=${CHOSEN_PORT} at $(date +'%H:%M:%S')" > ~/.labop-status
echo "TARGET_POSTGRES_READY port=${CHOSEN_PORT}"
'@
$remoteCmd = $remoteCmd.Replace("__NODE_PATH__", [string]$Node.path) -replace "`r", ""

$out = ssh -q -o BatchMode=yes "$($Node.user)@$($Node.hostname)" "$remoteCmd"
if ($LASTEXITCODE -eq 0 -and $out -match "TARGET_POSTGRES_READY") {
    $portMatch = [regex]::Match(($out -join "`n"), "port=(\d+)")
    if ($portMatch.Success) {
        Write-Host "      [SUCCESS] Postgres sintetico pronto em $($Node.hostname) (porta $($portMatch.Groups[1].Value))." -ForegroundColor Green
    } else {
        Write-Host "      [SUCCESS] Postgres sintetico pronto em $($Node.hostname)." -ForegroundColor Green
    }
} else {
    Write-Warning "      [WARNING] Falha ao provisionar target_postgres em $($Node.hostname)."
}
