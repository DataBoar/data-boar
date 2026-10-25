#!/usr/bin/env bash
# Data Boar — homelab inventory helper (run ON each Linux host; redact output before sharing).
# Usage: bash scripts/homelab-host-report.sh
# After clone: chmod +x scripts/homelab-host-report.sh   (typos: chmos / chmosd → chmod)
# See: docs/ops/HOMELAB_HOST_PACKAGE_INVENTORY.md

set -u

# Non-interactive shells (SSH/batch) may miss sbin paths; normalize early to reduce false negatives
# (e.g. ufw, auditctl, iptables/nft may live under /usr/sbin).
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

HR_PRIVILEGED=0
HR_DEEP=0
for arg in "$@"; do
  case "$arg" in
    --privileged) HR_PRIVILEGED=1 ;;
    --deep) HR_DEEP=1 ;;
    --help|-h)
      cat <<'EOF'
Usage: bash scripts/homelab-host-report.sh [--privileged] [--deep]

Default mode runs read-only checks without sudo.

--privileged:
  Enables best-effort privileged probes using `sudo -n` (non-interactive).
  If sudo requires a password, privileged probes will be skipped.

--deep:
  Enables heavier checks (best-effort). Intended for operator-driven runs.
  May increase runtime/noise. Requires --privileged for most probes.
EOF
      exit 0
      ;;
  esac
done

_hr_section() { echo "--- $* ---"; }
_hr_cmd() { command -v "$1" >/dev/null 2>&1; }
_hr_try() { "$@" 2>/dev/null || true; }
_hr_sudo() {
  if [[ "$HR_PRIVILEGED" == "1" ]] && _hr_cmd sudo; then
    sudo -n "$@" 2>/dev/null || true
  fi
}
_hr_timeout() {
  local secs="$1"; shift
  if _hr_cmd timeout; then
    timeout "$secs" "$@" 2>/dev/null || true
  else
    "$@" 2>/dev/null || true
  fi
}

_hr_os_id() {
  if [[ -r /etc/os-release ]]; then
    . /etc/os-release
    echo "${ID:-unknown}"
  else
    echo unknown
  fi
}

_hr_svc_is_active() {
  local name="$1"
  if _hr_cmd systemctl; then
    systemctl is-active "$name" 2>/dev/null || true
  elif _hr_cmd sv; then
    sv status "$name" 2>/dev/null || true
  else
    echo "(no service manager)"
  fi
}

echo "=== homelab-host-report $(date -Iseconds 2>/dev/null || date) ==="
echo "HOST: $(hostname -f 2>/dev/null || hostname 2>/dev/null || echo unknown)"
_hr_section "uname"
uname -a 2>/dev/null || true

_hr_section "/etc/os-release"
if [[ -f /etc/os-release ]]; then
  cat /etc/os-release
else
  echo "(no /etc/os-release)"
fi

_hr_section "CPU / RAM"
command -v nproc >/dev/null && echo "nproc: $(nproc)" || true
command -v free >/dev/null && free -h || true
_hr_try swapon --show 2>/dev/null
_hr_try zramctl 2>/dev/null | head -40

_hr_section "Python"
if command -v python3 >/dev/null; then
  command -v python3
  python3 --version
else
  echo "python3: not in PATH"
fi

_hr_section "uv"
if command -v uv >/dev/null; then
  uv --version
else
  echo "uv: not in PATH"
fi

_hr_section "pip (user warning: may be system pip)"
if command -v pip3 >/dev/null; then
  pip3 --version
elif command -v python3 >/dev/null && python3 -m pip --version >/dev/null 2>&1; then
  python3 -m pip --version
else
  echo "pip3: not in PATH (try: python3 -m pip --version)"
fi

_hr_section "Docker"
if command -v docker >/dev/null; then
  docker --version
  docker info 2>/dev/null | head -40 || echo "(docker info failed — permissions or daemon down)"
  echo "(swarm line)"
  docker info 2>/dev/null | grep -i '^ Swarm:' || true
else
  echo "docker: not in PATH"
fi

_hr_section "Bitwarden CLI (bw)"
if command -v bw >/dev/null; then
  command -v bw
  bw --version 2>/dev/null || echo "(bw --version failed)"
else
  echo "bw: not in PATH (install via apt bitwarden-cli, npm -g @bitwarden/cli, or GitHub release; ensure PATH)"
fi

_hr_section "dpkg: suggested Data Boar-related packages (Debian/Ubuntu)"
if command -v dpkg-query >/dev/null; then
  pkgs=(python3.12 python3.12-venv python3.12-dev build-essential libpq-dev libssl-dev libffi-dev unixodbc-dev
        docker-ce docker.io containerd.io podman lynis bitwarden-cli)
  for p in "${pkgs[@]}"; do
    dpkg-query -W -f='${Status}\t${Package}\t${Version}\n' "$p" 2>/dev/null | grep -v '^not-installed' || true
  done
  echo "(dpkg full count: $(dpkg -l 2>/dev/null | wc -l) lines — use dpkg -l > file if you need full export)"
else
  echo "dpkg-query: not available (not Debian/Ubuntu?)"
fi

_hr_section "xbps (Void): name match sample"
if command -v xbps-query >/dev/null; then
  xbps-query -l | grep -iE 'python3|docker|uv|lynis|openssl|gcc' | head -60 || true
else
  echo "xbps-query: not available"
fi

_hr_section "apk (Alpine): world head"
if command -v apk >/dev/null; then
  apk list -I 2>/dev/null | head -40 || true
else
  echo "apk: not available"
fi

_hr_section "Lynis (if installed)"
# Debian/Ubuntu install to /usr/sbin/lynis — often missing from PATH in non-login scripts.
# Run from /tmp + sanitized env: some builds mis-resolve language/DB paths when cwd is the repo
# or when stale LYNIS_* / PWD leaks from the shell.
_lynis_resolve_bin() {
  local p deb_paths
  for p in /usr/sbin/lynis /usr/bin/lynis /usr/local/sbin/lynis; do
    if [[ -f "$p" ]] && [[ -r "$p" ]]; then
      if [[ -x "$p" ]]; then echo "$p"; return 0; fi
    fi
  done
  if command -v dpkg-query >/dev/null; then
    while IFS= read -r deb_paths; do
      [[ -z "$deb_paths" ]] && continue
      if [[ -f "$deb_paths" && -x "$deb_paths" ]]; then
        echo "$deb_paths"
        return 0
      fi
    done < <(dpkg-query -L lynis 2>/dev/null | grep -E '^/(usr/)?(s)?bin/lynis$' || true)
  fi
  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  command -v lynis 2>/dev/null || true
}

_lynis_show_version() {
  local bin="$1"
  [[ -n "$bin" ]] || return 1
  [[ -f "$bin" ]] || return 1
  (
    cd /tmp 2>/dev/null || cd / 2>/dev/null || true
    unset OLDPWD LYNIS_HOME LYNIS_CONFIG_DIR 2>/dev/null || true
    # `show version` avoids some full-init code paths; fall back to --version.
    env -i \
      HOME="${HOME:-/tmp}" \
      PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
      LANG="${LANG:-C.UTF-8}" \
      LC_ALL="${LC_ALL:-C.UTF-8}" \
      TERM="${TERM:-dumb}" \
      USER="${USER:-}" \
      "$bin" show version 2>&1 \
      || env -i \
        HOME="${HOME:-/tmp}" \
        PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        LANG="${LANG:-C.UTF-8}" \
        LC_ALL="${LC_ALL:-C.UTF-8}" \
        TERM="${TERM:-dumb}" \
        USER="${USER:-}" \
        "$bin" --version 2>&1
  )
}

LYNIS_BIN="$(_lynis_resolve_bin)"
if [[ -n "$LYNIS_BIN" ]]; then
  if ! _lynis_show_version "$LYNIS_BIN"; then
    echo "lynis: binary at $LYNIS_BIN but version query failed (try: sudo apt install --reinstall lynis; type -a lynis)"
  fi
else
  echo "lynis: not installed or not found under /usr/sbin, /usr/bin, dpkg -L lynis, or standard PATH"
fi

_hr_section "banners (issue/banner.net)"
_hr_try sed -n '1,40p' /etc/issue
_hr_try sed -n '1,80p' /etc/issue.net
_hr_try sed -n '1,120p' /etc/banner.net

_hr_section "package updates (best-effort)"
os_id="$(_hr_os_id)"
if [[ "$os_id" == "debian" || "$os_id" == "ubuntu" || "$os_id" == "linuxmint" ]]; then
  if _hr_cmd apt-get; then
    echo "(apt-get -s upgrade summary)"
    _hr_timeout 20 _hr_sudo apt-get -s upgrade | grep -E '^(Inst|Conf|Remv|Upg|0 upgraded|[0-9]+ upgraded)' | head -60 || true
  fi
elif [[ "$os_id" == "void" ]]; then
  if _hr_cmd xbps-install; then
    echo "(xbps-install -Mun output head; updates available if any lines shown)"
    _hr_timeout 20 xbps-install -Mun | head -60
  fi
fi

_hr_section "OpenSSH (client/server + effective config)"
_hr_try ssh -V 2>&1 | head -2
_hr_try sshd -V 2>&1 | head -2
if _hr_cmd sshd; then
  # sshd -T may need root for full visibility; try both.
  echo "(sshd -T banner/passwordauth/permitrootlogin subset)"
  _hr_try sshd -T 2>/dev/null | grep -iE '^(banner|passwordauthentication|permitrootlogin|pubkeyauthentication|kbdinteractiveauthentication|challengeresponseauthentication|usepam|x11forwarding|allowtcpforwarding|allowagentforwarding)\b' | head -80
  _hr_sudo sshd -T 2>/dev/null | grep -iE '^(banner|passwordauthentication|permitrootlogin|pubkeyauthentication|kbdinteractiveauthentication|challengeresponseauthentication|usepam|x11forwarding|allowtcpforwarding|allowagentforwarding)\b' | head -80
fi

_hr_section "UFW / nftables (firewall posture)"
if _hr_cmd ufw; then
  _hr_sudo ufw status verbose
  _hr_sudo ufw status numbered
  _hr_try ufw status verbose
elif _hr_cmd nft; then
  echo "(nft ruleset head)"
  _hr_sudo nft list ruleset | head -120
  _hr_try nft list ruleset | head -120
else
  echo "firewall: neither ufw nor nft found"
fi

_hr_section "Fail2ban"
if _hr_cmd fail2ban-client; then
  _hr_sudo fail2ban-client status
  _hr_sudo fail2ban-client status sshd
  _hr_try fail2ban-client status
fi

_hr_section "sshguard"
if _hr_cmd sshguard; then
  _hr_sudo sed -n '1,120p' /etc/sshguard/whitelist
  _hr_svc_is_active sshguard
fi

_hr_section "USBGuard"
if _hr_cmd usbguard; then
  _hr_sudo sed -n '1,120p' /etc/usbguard/rules.conf
  _hr_sudo usbguard list-rules | head -80
  _hr_sudo usbguard list-devices | head -80
  _hr_svc_is_active usbguard
fi

_hr_section "auditd"
if _hr_cmd auditctl; then
  _hr_sudo auditctl -v
  _hr_sudo sed -n '1,260p' /etc/audit/rules.d/*.rules
  _hr_svc_is_active auditd
fi

_hr_section "AIDE"
if _hr_cmd aide; then
  _hr_try aide --version | head -80
  _hr_sudo sed -n '1,120p' /etc/aide/aide.conf
  _hr_try ls -la /etc/aide 2>/dev/null | head -40 || true
fi

_hr_section "Tripwire (if installed)"
_hr_try tripwire --version

_hr_section "deep: Lynis quick audit (best-effort)"
if [[ "$HR_DEEP" == "1" ]]; then
  if [[ -n "${LYNIS_BIN:-}" ]] && [[ "$HR_PRIVILEGED" == "1" ]]; then
    # Avoid heavy audits on tiny hosts (e.g. Raspberry Pi class).
    mem_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
    if [[ "$mem_kb" -lt 1500000 ]]; then
      echo "(skipped: low memory host; run lynis manually if desired)"
    else
      echo "(running: sudo -n lynis audit system --quick; timeout 180s)"
      # Run with a minimal environment and safe cwd to avoid path-resolution quirks
      # (some Lynis builds may mis-resolve language/DB paths when invoked from a project repo).
      _hr_timeout 180 sudo -n env -i \
        HOME="${HOME:-/tmp}" \
        PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        LANG="${LANG:-C.UTF-8}" \
        LC_ALL="${LC_ALL:-C.UTF-8}" \
        TERM="${TERM:-dumb}" \
        USER="${USER:-}" \
        bash -lc "cd /tmp 2>/dev/null || cd / 2>/dev/null || true; \"$LYNIS_BIN\" audit system --quick" \
        2>&1 | tail -n 120 || true
    fi
  else
    echo "(skipped: needs --privileged and lynis installed)"
  fi
fi

_hr_section "kernel / sysctl / block (read-only sample)"
# Helps trace lab tuning (vm dirty ratios, schedulers, rotational flags) without dumping full sysctl -a.
_hr_section "/proc/cmdline (kernel boot params)"
_hr_try sed -n '1,1p' /proc/cmdline

if command -v sysctl >/dev/null; then
  sysctl vm.swappiness vm.dirty_ratio vm.dirty_background_ratio 2>/dev/null || true
  sysctl vm.dirty_expire_centisecs vm.dirty_writeback_centisecs 2>/dev/null || true
  sysctl kernel.randomize_va_space 2>/dev/null || true
  sysctl fs.protected_hardlinks fs.protected_symlinks 2>/dev/null || true
  sysctl fs.protected_fifos fs.protected_regular 2>/dev/null || true
  sysctl kernel.yama.ptrace_scope 2>/dev/null || true
  sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc 2>/dev/null || true
fi
if [[ -r /proc/sys/vm/min_free_kbytes ]]; then
  echo "vm.min_free_kbytes: $(cat /proc/sys/vm/min_free_kbytes 2>/dev/null)"
fi

_hr_section "sysctl config files (head)"
_hr_try sed -n '1,200p' /etc/sysctl.conf
if [[ -d /etc/sysctl.d ]]; then
  for f in /etc/sysctl.d/*.conf; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"
    _hr_try sed -n '1,200p' "$f"
  done
fi

_hr_section "limits (ulimit + /etc/security/limits*)"
_hr_try bash -lc 'ulimit -a'
_hr_try sed -n '1,200p' /etc/security/limits.conf
if [[ -d /etc/security/limits.d ]]; then
  for f in /etc/security/limits.d/*.conf; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"
    _hr_try sed -n '1,200p' "$f"
  done
fi

if command -v lsblk >/dev/null; then
  _hr_section "lsblk (summary)"
  lsblk -o NAME,SIZE,TYPE,ROTA,RM,TRAN,MOUNTPOINTS 2>/dev/null | head -40 || true
fi

_hr_section "/sys/block/*/queue (scheduler, rotational, nr_requests sample)"
for q in /sys/block/*/queue; do
  [[ -d "$q" ]] || continue
  dev="${q#/sys/block/}"
  dev="${dev%/queue}"
  [[ "$dev" == loop* ]] && continue
  if [[ -f "$q/scheduler" ]]; then
    echo "$dev scheduler: $(tr -d '\n' <"$q/scheduler" 2>/dev/null)"
  fi
  if [[ -f "$q/rotational" ]]; then
    echo "$dev rotational: $(tr -d '\n' <"$q/rotational" 2>/dev/null)"
  fi
  if [[ -f "$q/nr_requests" ]]; then
    echo "$dev nr_requests: $(tr -d '\n' <"$q/nr_requests" 2>/dev/null)"
  fi
  if [[ -f "$q/read_ahead_kb" ]]; then
    echo "$dev read_ahead_kb: $(tr -d '\n' <"$q/read_ahead_kb" 2>/dev/null)"
  fi
  if [[ -f "$q/rq_affinity" ]]; then
    echo "$dev rq_affinity: $(tr -d '\n' <"$q/rq_affinity" 2>/dev/null)"
  fi
  if [[ -f "$q/nomerges" ]]; then
    echo "$dev nomerges: $(tr -d '\n' <"$q/nomerges" 2>/dev/null)"
  fi
done 2>/dev/null | head -80

_hr_section "udev rules (head)"
if [[ -d /etc/udev/rules.d ]]; then
  for f in /etc/udev/rules.d/*.rules; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"
    _hr_try sed -n '1,200p' "$f"
  done
fi

_hr_section "cpufreq (if present)"
if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
  for f in scaling_governor energy_performance_preference; do
    p="/sys/devices/system/cpu/cpu0/cpufreq/$f"
    [[ -r "$p" ]] && echo "cpu0 $f: $(tr -d '\n' <"$p" 2>/dev/null)"
  done
else
  echo "(no cpufreq sysfs — VM or older kernel?)"
fi

_hr_section "Optional dev toolchains (not required for Data Boar)"
command -v go >/dev/null && go version || echo "go: not in PATH"
command -v rustc >/dev/null && rustc --version || echo "rustc: not in PATH"
command -v zig >/dev/null && zig version || echo "zig: not in PATH"
command -v odin >/dev/null && odin version 2>/dev/null || echo "odin: not in PATH"
command -v brew >/dev/null && brew --version 2>/dev/null | head -3 || echo "brew: not in PATH"

echo "=== end ==="
