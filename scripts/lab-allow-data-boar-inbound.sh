#!/usr/bin/env bash
# Lab-only: allow inbound TCP 8088 (Data Boar) from LAB_LAN_CIDR (default 10.0.0.0/16).
# Run as root on the host that runs Data Boar. Adjust LAB_LAN_CIDR to your subnet.
# Usage: sudo LAB_LAN_CIDR=10.0.0.0/8 ./scripts/lab-allow-data-boar-inbound.sh
# Or:    sudo -E env LAB_LAN_CIDR=10.0.1.0/24 ./scripts/lab-allow-data-boar-inbound.sh

set -euo pipefail

PORT="${DATA_BOAR_PORT:-8088}"
CIDR="${LAB_LAN_CIDR:-10.0.0.0/16}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

if command -v ufw >/dev/null 2>&1; then
  # ufw: allow from LAN to port
  ufw allow from "${CIDR}" to any port "${PORT}" proto tcp comment 'Data Boar lab LAN'
  echo "ufw: allowed ${CIDR} -> :${PORT}/tcp"
elif command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=${CIDR} port port=${PORT} protocol=tcp accept"
  firewall-cmd --reload
  echo "firewalld: rich rule for ${CIDR} -> ${PORT}/tcp"
else
  echo "Neither ufw nor firewall-cmd found. Add a host rule manually (nftables/iptables) for ${CIDR} -> :${PORT}." >&2
  exit 1
fi
