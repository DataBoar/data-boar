#!/usr/bin/env bash
# scripts/labop-fw-guard-ensure.sh
# Validates (and optionally remediates) fail2ban/sshguard ignore lists for lab-op subnet.
# Run via narrow sudoers from labop-gate-readiness.sh / Maestro -Deep (#957).
#
# Usage: sudo -n bash labop-fw-guard-ensure.sh [--check | --apply]
#   Env: LAB_OP_SUBNET (required, e.g. RFC1918 CIDR from inventory)
#
# Exit: 0=healthy or remediated; 1=needs fix (check) or remediation failed; 2=bad args

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --check) APPLY=0 ;;
    --help|-h)
      echo "Usage: $0 [--check | --apply]  (LAB_OP_SUBNET required)"
      exit 0
      ;;
    *) echo "[FW-Guard] Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SUBNET="${LAB_OP_SUBNET:-}"
if [[ -z "$SUBNET" ]]; then
  echo "[FW-Guard] FAIL: LAB_OP_SUBNET unset" >&2
  exit 2
fi

_log() { echo "[FW-Guard $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[FW-Guard] OK: $*"; }
_warn(){ echo "[FW-Guard] WARN: $*" >&2; }
_fail(){ echo "[FW-Guard] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (apply=$APPLY subnet=$SUBNET)"

NEED_FIX=0
F2B_PRESENT=0
SG_PRESENT=0

_subnet_in_list() {
  local list="$1"
  [[ -z "$list" ]] && return 1
  # Word-boundary style: subnet appears as token in ignoreip/whitelist string
  grep -qE "(^|[[:space:]])${SUBNET}([[:space:]]|$)" <<<"$list"
}

# --- fail2ban ---
if command -v fail2ban-client >/dev/null 2>&1; then
  F2B_PRESENT=1
  IGNOREIP=""
  if fail2ban-client ping >/dev/null 2>&1; then
    IGNOREIP="$(fail2ban-client get sshd ignoreip 2>/dev/null || true)"
    if [[ -z "$IGNOREIP" ]]; then
      IGNOREIP="$(fail2ban-client status sshd 2>/dev/null | grep -i 'ignore ip list' | sed 's/.*://' || true)"
    fi
  fi
  if _subnet_in_list "$IGNOREIP"; then
    _ok "fail2ban sshd ignoreip includes $SUBNET"
  else
    _warn "fail2ban sshd ignoreip missing lab subnet (have: ${IGNOREIP:-<empty>})"
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      JAIL_LOCAL="/etc/fail2ban/jail.local"
      DROPIN="/etc/fail2ban/jail.d/labop-ignoreip.local"
      if [[ -w /etc/fail2ban ]] || [[ -w "$(dirname "$DROPIN")" ]]; then
        if [[ ! -f "$DROPIN" ]] || ! grep -qF "$SUBNET" "$DROPIN" 2>/dev/null; then
          {
            echo "# labop-fw-guard-ensure.sh (leave-no-trace: remove this file to revert)"
            echo "[sshd]"
            echo "ignoreip = 127.0.0.1/8 ::1 $SUBNET"
          } >"$DROPIN"
          _log "Wrote $DROPIN"
        fi
        if fail2ban-client reload >/dev/null 2>&1 || systemctl reload fail2ban >/dev/null 2>&1; then
          _ok "fail2ban reloaded after ignoreip remediation"
          NEED_FIX=0
        else
          _fail "fail2ban reload failed after writing drop-in"
        fi
      else
        _fail "Cannot write fail2ban drop-in (no grant or read-only)"
      fi
    fi
  fi
else
  _log "fail2ban-client absent (skip)"
fi

# --- sshguard ---
if command -v sshguard >/dev/null 2>&1 || [[ -f /etc/sshguard/whitelist ]]; then
  SG_PRESENT=1
  WL=""
  for f in /etc/sshguard/whitelist /etc/sshguard.whitelist; do
    if [[ -f "$f" ]]; then
      WL="$(grep -v '^#' "$f" | tr '\n' ' ')"
      break
    fi
  done
  if _subnet_in_list "$WL"; then
    _ok "sshguard whitelist includes $SUBNET"
  elif [[ -z "$WL" && $F2B_PRESENT -eq 1 ]]; then
    _log "sshguard whitelist empty/unreadable; fail2ban present - advisory only"
  else
    _warn "sshguard whitelist missing lab subnet (have: ${WL:-<empty>})"
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      WL_FILE="/etc/sshguard/whitelist"
      if [[ ! -f "$WL_FILE" ]]; then WL_FILE="/etc/sshguard.whitelist"; fi
      if [[ -w "$WL_FILE" ]] || [[ ! -f "$WL_FILE" && -w "$(dirname "$WL_FILE")" ]]; then
        if ! grep -qF "$SUBNET" "$WL_FILE" 2>/dev/null; then
          echo "$SUBNET" >>"$WL_FILE"
          _log "Appended $SUBNET to $WL_FILE"
        fi
        if command -v rc-service >/dev/null 2>&1; then
          rc-service sshguard restart >/dev/null 2>&1 || true
        elif command -v systemctl >/dev/null 2>&1; then
          systemctl reload sshguard >/dev/null 2>&1 || systemctl restart sshguard >/dev/null 2>&1 || true
        fi
        _ok "sshguard whitelist remediated (best-effort reload)"
        NEED_FIX=0
      else
        _fail "Cannot write sshguard whitelist (no grant)"
      fi
    fi
  fi
fi

if [[ $F2B_PRESENT -eq 0 && $SG_PRESENT -eq 0 ]]; then
  _log "No fail2ban/sshguard detected - skip fw guard"
  exit 0
fi

if [[ $NEED_FIX -eq 0 ]]; then
  exit 0
fi
exit 1
