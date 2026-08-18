#!/usr/bin/env bash
# One-shot: fix docker.list permissions so user-space tools stop Errno 13 (see ansible lab_node_01_docker_ce).
# Run on the LAB-NODE-01: bash scripts/lab-node-01-fix-docker-list.sh
set -eu
DOCKER_LIST="/etc/apt/sources.list.d/docker.list"
if [[ ! -f "${DOCKER_LIST}" ]]; then
  echo "INFO: ${DOCKER_LIST} not found — nothing to fix (Docker CE role not applied yet)."
  exit 0
fi
echo "Fixing ${DOCKER_LIST} -> root:root 0644 (requires sudo)..."
sudo chown root:root "${DOCKER_LIST}"
sudo chmod 644 "${DOCKER_LIST}"
stat -c '%a %U:%G %n' "${DOCKER_LIST}"
