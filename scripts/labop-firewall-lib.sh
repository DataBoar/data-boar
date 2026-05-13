#!/usr/bin/env bash
# scripts/labop-firewall-lib.sh
# Shared firewall audit + ephemeral rule management for labop-*-ensure.sh scripts.
# Source this file: source "$(dirname "$0")/labop-firewall-lib.sh"
#
# Contract:
#   _fw_detect          -- sets FW_TYPE (ufw|nftables|iptables|firewalld|none)
#   _fw_port_allowed    -- checks if lab subnet can reach $1/$2 (port/proto)
#   _fw_open_ephemeral  -- opens port $1/$2 for LAB_OP_SUBNET; records in state file
#   _fw_cleanup         -- reverts rules added by this session (state file)
#   _port_listening     -- returns 0 if TCP port $1 is listening on the host
#
# Environment:
#   LAB_OP_SUBNET   -- CIDR of lab-op hosts (default: auto-detect from primary iface)
#   FW_STATE_FILE   -- path to ephemeral state JSON (default: ~/.labop-fw-ephemeral-$TAG.json)
#   FW_TAG          -- identifies the session for state file naming (set by caller)

# ---------------------------------------------------------------------------
# Detect lab-op subnet from environment or primary interface
# ---------------------------------------------------------------------------
_fw_detect_subnet() {
  if [[ -n "${LAB_OP_SUBNET:-}" ]]; then
    echo "$LAB_OP_SUBNET"
    return
  fi
  # Best-effort: find the primary non-loopback interface and derive /24 subnet
  local primary_ip
  primary_ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '/src/{print $7}' | head -1)
  if [[ -n "$primary_ip" ]]; then
    # Assume /24 subnet (typical for home/lab environments)
    echo "${primary_ip%.*}.0/24"
  else
    echo "192.168.0.0/16"  # wide fallback — operator should set LAB_OP_SUBNET
  fi
}

LAB_OP_SUBNET="${LAB_OP_SUBNET:-$(_fw_detect_subnet)}"

# ---------------------------------------------------------------------------
# Detect active firewall manager
# ---------------------------------------------------------------------------
_fw_detect() {
  FW_TYPE="none"
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
    FW_TYPE="ufw"
  elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state 2>/dev/null | grep -q "running"; then
    FW_TYPE="firewalld"
  elif command -v nft >/dev/null 2>&1 && nft list ruleset 2>/dev/null | grep -q "type filter"; then
    FW_TYPE="nftables"
  elif command -v iptables >/dev/null 2>&1 && iptables -L INPUT -n 2>/dev/null | grep -qv "Chain INPUT"; then
    FW_TYPE="iptables"
  fi
  echo "[FW] Detected firewall: $FW_TYPE (subnet: $LAB_OP_SUBNET)"
}

# ---------------------------------------------------------------------------
# Check if TCP port is listening
# ---------------------------------------------------------------------------
_port_listening() {
  local port="$1"
  ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE ":${port}$"
}

# ---------------------------------------------------------------------------
# Check if lab subnet is allowed to reach port (returns 0=ok, 1=blocked)
# ---------------------------------------------------------------------------
_fw_port_allowed() {
  local port="$1"
  local proto="${2:-tcp}"

  case "$FW_TYPE" in
    ufw)
      # ufw status numbered shows rules; check for port/subnet
      ufw status 2>/dev/null | grep -qE "^${port}/(${proto}|v6).*ALLOW" && return 0
      ufw status 2>/dev/null | grep -qE "^${port}.*ALLOW" && return 0
      return 1
      ;;
    nftables)
      nft list ruleset 2>/dev/null | grep -qE "dport ${port}.*accept" && return 0
      return 1
      ;;
    iptables)
      iptables -L INPUT -n 2>/dev/null | grep -qE "ACCEPT.*dpt:${port}" && return 0
      return 1
      ;;
    firewalld)
      firewall-cmd --list-ports 2>/dev/null | grep -qE "^${port}/${proto}" && return 0
      return 1
      ;;
    none)
      return 0  # no firewall = open
      ;;
  esac
  return 1
}

# ---------------------------------------------------------------------------
# Open port ephemerally for LAB_OP_SUBNET only
# Sets FW_EPHEMERAL_ADDED=1 if a new rule was added
# ---------------------------------------------------------------------------
FW_EPHEMERAL_ADDED=0
FW_EPHEMERAL_TAG=""

_fw_open_ephemeral() {
  local port="$1"
  local proto="${2:-tcp}"
  local comment="labop-smoke-ephemeral-${port}-$$"
  FW_EPHEMERAL_TAG="$comment"

  echo "[FW] Opening port $port/$proto for $LAB_OP_SUBNET (ephemeral, tag: $comment)"

  case "$FW_TYPE" in
    ufw)
      ufw allow proto "$proto" from "$LAB_OP_SUBNET" to any port "$port" comment "$comment" 2>&1
      ;;
    nftables)
      nft add rule inet filter input ip saddr "$LAB_OP_SUBNET" "$proto" dport "$port" accept comment "\"$comment\"" 2>&1
      ;;
    iptables)
      iptables -I INPUT -p "$proto" -s "$LAB_OP_SUBNET" --dport "$port" -j ACCEPT -m comment --comment "$comment" 2>&1
      ;;
    firewalld)
      firewall-cmd --add-rich-rule="rule family=ipv4 source address='$LAB_OP_SUBNET' port port='$port' protocol='$proto' accept" 2>&1
      ;;
    none)
      echo "[FW] No firewall active — no rule needed."
      return 0
      ;;
  esac

  if [[ $? -eq 0 ]]; then
    FW_EPHEMERAL_ADDED=1
    # Persist state for cleanup
    local state_file="${FW_STATE_FILE:-${HOME}/.labop-fw-ephemeral-${FW_TAG:-default}.json}"
    echo "{\"fw\":\"$FW_TYPE\",\"port\":$port,\"proto\":\"$proto\",\"subnet\":\"$LAB_OP_SUBNET\",\"tag\":\"$comment\"}" > "$state_file" 2>/dev/null || true
    echo "[FW] Ephemeral rule added. State saved to $state_file."
    return 0
  else
    echo "[FW] WARN: Failed to add ephemeral rule." >&2
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Revert ephemeral rules added by this session
# ---------------------------------------------------------------------------
_fw_cleanup_ephemeral() {
  local state_file="${FW_STATE_FILE:-${HOME}/.labop-fw-ephemeral-${FW_TAG:-default}.json}"

  if [[ ! -f "$state_file" ]]; then
    echo "[FW] No ephemeral state file found — nothing to clean up."
    return 0
  fi

  # Parse state (simple grep, no jq required)
  local fw port proto subnet tag
  fw=$(grep -o '"fw":"[^"]*"' "$state_file" | cut -d'"' -f4)
  port=$(grep -o '"port":[0-9]*' "$state_file" | cut -d: -f2)
  proto=$(grep -o '"proto":"[^"]*"' "$state_file" | cut -d'"' -f4)
  subnet=$(grep -o '"subnet":"[^"]*"' "$state_file" | cut -d'"' -f4)
  tag=$(grep -o '"tag":"[^"]*"' "$state_file" | cut -d'"' -f4)

  echo "[FW] Reverting ephemeral rule: $fw port=$port/$proto subnet=$subnet tag=$tag"

  case "$fw" in
    ufw)
      ufw delete allow proto "$proto" from "$subnet" to any port "$port" 2>&1 || true
      ;;
    nftables)
      # nftables doesn't easily delete by comment; delete by handle if known
      local handle
      handle=$(nft -a list ruleset 2>/dev/null | grep "$tag" | grep -o 'handle [0-9]*' | awk '{print $2}')
      if [[ -n "$handle" ]]; then
        nft delete rule inet filter input handle "$handle" 2>&1 || true
      else
        echo "[FW] WARN: Could not find nftables rule handle for tag $tag — manual cleanup may be needed." >&2
      fi
      ;;
    iptables)
      iptables -D INPUT -p "$proto" -s "$subnet" --dport "$port" -j ACCEPT -m comment --comment "$tag" 2>&1 || true
      ;;
    firewalld)
      firewall-cmd --remove-rich-rule="rule family=ipv4 source address='$subnet' port port='$port' protocol='$proto' accept" 2>&1 || true
      ;;
  esac

  rm -f "$state_file" 2>/dev/null || true
  echo "[FW] Ephemeral rule reverted and state file removed."
}

# ---------------------------------------------------------------------------
# Human-readable troubleshooting hint for a blocked port
# ---------------------------------------------------------------------------
_fw_troubleshoot_hint() {
  local port="$1"
  local proto="${2:-tcp}"
  local service_hint="${3:-service}"

  echo ""
  echo "[FW] >>> TROUBLESHOOTING: port $port/$proto blocked for $LAB_OP_SUBNET <<<"
  echo "[FW] To open manually (persistent), choose your firewall:"
  case "$FW_TYPE" in
    ufw)      echo "[FW]   sudo ufw allow proto $proto from $LAB_OP_SUBNET to any port $port" ;;
    nftables) echo "[FW]   sudo nft add rule inet filter input ip saddr $LAB_OP_SUBNET $proto dport $port accept" ;;
    iptables) echo "[FW]   sudo iptables -I INPUT -p $proto -s $LAB_OP_SUBNET --dport $port -j ACCEPT" ;;
    firewalld)echo "[FW]   sudo firewall-cmd --add-rich-rule=\"rule family=ipv4 source address='$LAB_OP_SUBNET' port port='$port' protocol='$proto' accept\" --permanent && sudo firewall-cmd --reload" ;;
    none)     echo "[FW]   No firewall detected — port may be blocked by a network device upstream." ;;
  esac
  echo "[FW] To auto-open ephemerally for this smoke run, use --apply flag (requires LABOP sudoers)."
  echo ""
}
