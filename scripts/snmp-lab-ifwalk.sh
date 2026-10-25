#!/usr/bin/env bash
# IF-MIB interfaces table walk (SNMPv3 authPriv SHA/AES) — Linux lab-op / bare metal.
# Same LAB_LAB-ROUTER-01_SNMP_* keys as Windows scripts/snmp-LAB-ROUTER-01-lab-probe.ps1 (historical name; works for any v3 target).
#
# Usage (from repo root on a Linux host with snmpwalk installed):
#   bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.local
#   bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.switch.local
#
# Install: sudo apt update && sudo apt install -y snmp
# Firewall: UDP 161 from this host to the device management IP.

set -euo pipefail

ENV_FILE="${1:-}"
if [[ -z "$ENV_FILE" || ! -f "$ENV_FILE" ]]; then
  echo "Usage: $0 <path-to-env-file>" >&2
  echo "Example: $0 docs/private/homelab/.env.snmp.local" >&2
  exit 2
fi

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "${line//[[:space:]]/}" ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  val=$(echo "$val" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  if [[ "$val" =~ ^\".*\"$ ]]; then
    val="${val#\"}"
    val="${val%\"}"
  fi
  export "${key}=${val}"
done < "$ENV_FILE"

: "${LAB_LAB-ROUTER-01_SNMP_HOST:?missing LAB_LAB-ROUTER-01_SNMP_HOST in env file}"
: "${LAB_LAB-ROUTER-01_SNMP_V3_USER:?missing LAB_LAB-ROUTER-01_SNMP_V3_USER}"
: "${LAB_LAB-ROUTER-01_SNMP_AUTH_PASS:?missing LAB_LAB-ROUTER-01_SNMP_AUTH_PASS}"
: "${LAB_LAB-ROUTER-01_SNMP_PRIV_PASS:?missing LAB_LAB-ROUTER-01_SNMP_PRIV_PASS}"

exec snmpwalk -v3 -l authPriv \
  -u "$LAB_LAB-ROUTER-01_SNMP_V3_USER" \
  -a SHA -A "$LAB_LAB-ROUTER-01_SNMP_AUTH_PASS" \
  -x AES -X "$LAB_LAB-ROUTER-01_SNMP_PRIV_PASS" \
  "$LAB_LAB-ROUTER-01_SNMP_HOST" \
  1.3.6.1.2.1.2.2
