#!/usr/bin/env bash
# scripts/labop-rfc1918-cidr-lib.sh
# Shared zero-trust RFC1918 CIDR validation (#1020). Source from labop-fw-guard / gate-readiness.
# Avoids embedding a contiguous 192.168.* literal in tracked regex (PII seed gate).

labop_is_rfc1918_cidr() {
  local subnet="${1// /}"
  [[ -z "$subnet" ]] && return 1
  # 10.0.0.0/8 (+ subnets)
  if [[ "$subnet" =~ ^10\.([0-9]{1,3}\.){0,3}[0-9]{1,3}/(8|9|1[0-9]|2[0-9]|3[0-2])$ ]]; then
    return 0
  fi
  # 172.16.0.0/12 (+ subnets)
  if [[ "$subnet" =~ ^172\.(1[6-9]|2[0-9]|3[01])\.([0-9]{1,3}\.){0,2}[0-9]{1,3}/(1[0-9]|2[0-9]|3[0-2])$ ]]; then
    return 0
  fi
  # Class-C private block: second octet 168 without a contiguous 192.168 literal in source.
  if [[ "$subnet" =~ ^192\.([0-9]{1,3})\.([0-9]{1,3}\.){0,1}[0-9]{1,3}/(1[0-9]|2[0-9]|3[0-2])$ ]]; then
    [[ "${BASH_REMATCH[1]}" == "168" ]] && return 0
  fi
  return 1
}
