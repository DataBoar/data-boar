#!/usr/bin/env bash
# Run ON the lab host (e.g. LAB-NODE-01) with sudo when Docker fails with:
#   failed to start cluster component: --live-restore daemon configuration is incompatible with swarm mode
# Swarm (single-node) and live-restore cannot both be enabled on Docker 29+.
set -euo pipefail
DAEMON_JSON="${1:-/etc/docker/daemon.json}"
if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (apt install jq)." >&2
  exit 1
fi
if [[ ! -f "$DAEMON_JSON" ]]; then
  echo "Missing $DAEMON_JSON" >&2
  exit 1
fi
backup="${DAEMON_JSON}.bak.$(date +%Y%m%d%H%M%S)"
cp -a "$DAEMON_JSON" "$backup"
echo "Backed up to $backup"
tmp="$(mktemp)"
jq 'del(."live-restore")' "$DAEMON_JSON" >"$tmp"
install -m 0644 -o root -g root "$tmp" "$DAEMON_JSON"
rm -f "$tmp"
echo "Removed live-restore from $DAEMON_JSON (if present)."
systemctl restart docker
systemctl --no-pager --full status docker || true
docker info >/dev/null && echo "Docker OK: $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo running)"
