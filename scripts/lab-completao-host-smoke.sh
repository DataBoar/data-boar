#!/usr/bin/env bash
# Data Boar -- per-host "completao" lab smoke (NOT pytest).
# Exercises runtime surfaces: uv, optional Docker/Podman, optional lab DB stack, optional HTTP /health.
# Run from repo root: bash scripts/lab-completao-host-smoke.sh [--privileged] [--health-url URL]
# See docs/ops/LAB_COMPLETAO_RUNBOOK.md and docs/ops/LAB_SMOKE_MULTI_HOST.md.
#
# Exit codes (DATA_BOAR_COMPLETAO_EXIT_v1 -- same contract as docs/ops/LAB_COMPLETAO_RUNBOOK.md):
#   0 -- completed diagnostic bundle (success; individual steps may log FAILED inside the transcript).
#   1 -- reserved for future infra-hard-fail fast-path (network/tool missing when a gate requires it).
#   2 -- invalid invocation / unknown CLI argument (contract violation).
#   3 -- reserved for compliance-violation signals when a scanner hook is wired to this script.
#
# Privileged mode uses sudo -n for read-only snapshots (firewall/security tools) when available.
# For non-interactive SSH, configure NOPASSWD narrowly -- docs/private/homelab/LABOP_COMPLETAO_SUDOERS.pt_BR.md
# (Cmnd_Alias for homelab-host-report.sh / lab-completao-host-smoke.sh --privileged paths must match sudoers literally.)

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"
# uv is often installed to ~/.local/bin (login shells add it; non-interactive SSH may not).
if [[ -d "${HOME}/.local/bin" ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

LC_PRIV=0
LC_SKIP_ENGINE=0
LC_EMIT_JSONL_ONLY=0
LC_LAB_STACK_UP=0
LC_HEALTH_URL="${LAB_COMPLETAO_HEALTH_URL:-}"
LC_REPO_ROOT=""
LC_BENCH_TRACK=""
LC_BENCH_ROOT=""
# LC_BENCH_RUN_ID is forwarded via Maestro persona handlers (Handle-*.ps1) so completão A/B
# sessions can correlate this smoke invocation with the wrapper RunId for audit/labeling.
LC_BENCH_RUN_ID=""

_lc_emit_host_env_audit_line() {
  local _uv="uv_missing"
  command -v uv >/dev/null 2>&1 && _uv=$(uv --version 2>/dev/null | head -n1 | tr -d '\r')
  local _py="python_missing"
  if command -v python3 >/dev/null 2>&1; then
    _py=$(python3 --version 2>&1 | tr -d '\r')
  elif command -v python >/dev/null 2>&1; then
    _py=$(python --version 2>&1 | tr -d '\r')
  fi
  local _alias="${LAB_COMPLETAO_SSH_HOST_ALIAS:-}"
  local _hn
  _hn="$(hostname 2>/dev/null || echo unknown)"
  if command -v python3 >/dev/null 2>&1; then
    UV_JSON="$_uv" PY_JSON="$_py" HOST_JSON="$_alias" HN_JSON="$_hn" python3 -c "import json, os, datetime
ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
kv = os.environ
d = {'v': 1, 'ts': ts, 'phase': 'host_env_audit', 'status': 'ok', 'message': 'runtime_versions', 'host': kv.get('HOST_JSON', ''), 'detail': {'ssh_alias': kv.get('HOST_JSON', ''), 'hostname': kv.get('HN_JSON', ''), 'uv_version': kv.get('UV_JSON', ''), 'python_version': kv.get('PY_JSON', '')}}
print('DATA_BOAR_COMPLETAO_JSONL_MIN_EVENT:' + json.dumps(d, separators=(',', ':')))"
  else
    echo "DATA_BOAR_COMPLETAO_JSONL_MIN_EVENT:{\"v\":1,\"phase\":\"host_env_audit\",\"status\":\"warning\",\"message\":\"no_python3_for_json\",\"host\":\"${_alias}\",\"detail\":{\"uv_version\":\"${_uv}\",\"python_version\":\"${_py}\"}}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --privileged) LC_PRIV=1 ;;
    --skip-engine-import) LC_SKIP_ENGINE=1 ;;
    --lab-stack-up) LC_LAB_STACK_UP=1 ;;
    --emit-jsonl-host-env-and-exit) LC_EMIT_JSONL_ONLY=1 ;;
    --bench-track)
      LC_BENCH_TRACK="${2:-}"
      shift
      ;;
    --bench-run-id)
      # Forwarded by Maestro persona handlers (Handle-*.ps1) so completão A/B sessions can
      # correlate this smoke invocation with the wrapper RunId. Stored for audit/labeling
      # only; downstream sections may surface it via $LC_BENCH_RUN_ID when desired.
      LC_BENCH_RUN_ID="${2:-}"
      shift
      ;;
    --health-url)
      LC_HEALTH_URL="${2:-}"
      shift
      ;;
    --repo-root)
      LC_REPO_ROOT="${2:-}"
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage: bash scripts/lab-completao-host-smoke.sh [--privileged] [--skip-engine-import] [--bench-track stable|beta] [--bench-run-id ID] [--health-url URL] [--repo-root PATH]

  --privileged          Best-effort read-only probes via sudo -n (iptables/nft/ufw/fail2ban status).
  --skip-engine-import  Skip uv / import core.engine (hosts that run Data Boar only via Docker/Swarm/Podman).
  --lab-stack-up        Try to bring up deploy/lab-smoke-stack (and optional Mongo compose overlay) before checks.
  --emit-jsonl-host-env-and-exit  Print one DATA_BOAR_COMPLETAO_JSONL_MIN_EVENT line (uv/python versions) and exit 0.
  --bench-track         Ephemeral A/B workdir under /tmp/databoar_bench/<stable|beta> (checkpoint isolation).
  --bench-run-id        Run-id forwarded by Maestro A/B wrapper for audit correlation (no-op semantics; label only).
  --health-url          Override LAB_COMPLETAO_HEALTH_URL (e.g. http://127.0.0.1:8088/health).
  --repo-root           Repo root (default: infer from script location).

Environment:
  LAB_COMPLETAO_HEALTH_URL              Optional URL for curl -sf (Data Boar /health or similar).
  LAB_COMPLETAO_LAB_STACK_UP            If 1, same as --lab-stack-up.
  LAB_COMPLETAO_SKIP_ENGINE_IMPORT      If set to 1, same as --skip-engine-import (manifest / container-only hosts).
  LAB_COMPLETAO_SSH_HOST_ALIAS          Set by lab-completao-orchestrate.ps1 (manifest sshHost) for power warnings.
  LAB_COMPLETAO_MAIN_ENGINE_SSH_HOST    Optional manifest completaoMainEngineSshHost; undervoltage on other hosts is warning-only.
  LAB_COMPLETAO_SKIP_UNDERVOLTAGE_CHECK If 1, skip vcgencmd/journal undervoltage section (LAB-NODE-04 passive / operator override).
  LAB_COMPLETAO_BENCH_TRACK             stable|beta when --bench-track not passed.
  LAB_COMPLETAO_BENCH_COMPARE           If 1, emit coarse wall-clock import probe (stable: core.engine; beta: boar_fast_filter).
EOF
      exit 0
      ;;
    *)
      echo "lab-completao-host-smoke: unknown arg: $1 (try --help)" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "${LAB_COMPLETAO_LAB_STACK_UP:-}" == "1" ]]; then
  LC_LAB_STACK_UP=1
fi

if [[ "$LC_EMIT_JSONL_ONLY" == "1" ]]; then
  _lc_emit_host_env_audit_line
  exit 0
fi

if [[ -z "$LC_REPO_ROOT" ]]; then
  _here=$(cd "$(dirname "$0")/.." && pwd)
  LC_REPO_ROOT="$_here"
fi

if [[ -z "$LC_BENCH_TRACK" && -n "${LAB_COMPLETAO_BENCH_TRACK:-}" ]]; then
  LC_BENCH_TRACK="${LAB_COMPLETAO_BENCH_TRACK}"
fi

_lc_section() { echo "--- $* ---"; }
_lc_cmd() { command -v "$1" >/dev/null 2>&1; }
_lc_try() { "$@" 2>/dev/null || true; }
_lc_sudo() {
  if [[ "$LC_PRIV" != "1" ]] || ! _lc_cmd sudo; then
    return 0
  fi
  sudo -n "$@" 2>/dev/null || echo "(sudo -n failed or denied for: $*)"
}

_lc_init_bench_workdir() {
  if [[ -z "$LC_BENCH_TRACK" ]]; then
    return 0
  fi
  if [[ "$LC_BENCH_TRACK" != "stable" && "$LC_BENCH_TRACK" != "beta" ]]; then
    echo "lab-completao-host-smoke: --bench-track must be stable or beta" >&2
    exit 2
  fi
  LC_BENCH_ROOT="/tmp/databoar_bench/$LC_BENCH_TRACK"
  mkdir -p "$LC_BENCH_ROOT" 2>/dev/null || true
  echo "databoar_bench_track=$LC_BENCH_TRACK" >"$LC_BENCH_ROOT/.checkpoint_isolation_marker" 2>/dev/null || true
  echo "BENCH_WORKDIR: $LC_BENCH_ROOT (isolated; do not share checkpoints between stable and beta)"
}

_lc_undervoltage_check() {
  if [[ "${LAB_COMPLETAO_SKIP_UNDERVOLTAGE_CHECK:-}" == "1" ]]; then
    _lc_section "power / undervoltage (skipped: LAB_COMPLETAO_SKIP_UNDERVOLTAGE_CHECK)"
    return 0
  fi
  _hn="$(hostname 2>/dev/null || true)"
  if [[ "$_hn" == *[Pp][Ii]3[Bb]* ]]; then
    _lc_section "power / undervoltage (skipped: LAB-NODE-04 passive target)"
    return 0
  fi
  _lc_section "power / undervoltage (non-fatal)"
  local th="0x0"
  if _lc_cmd vcgencmd; then
    th="$(vcgencmd get_throttled 2>/dev/null | sed -n 's/^throttled=//p' || echo "0x0")"
    echo "vcgencmd get_throttled: ${th:-unknown}"
  else
    echo "vcgencmd: not available (skip Pi-specific undervoltage)"
  fi
  if [[ -n "$th" && "$th" != "0x0" ]]; then
    if [[ -n "${LAB_COMPLETAO_MAIN_ENGINE_SSH_HOST:-}" && -n "${LAB_COMPLETAO_SSH_HOST_ALIAS:-}" && "$LAB_COMPLETAO_SSH_HOST_ALIAS" != "${LAB_COMPLETAO_MAIN_ENGINE_SSH_HOST}" ]]; then
      echo "WARNING: throttle/undervoltage on non-main-engine host (alias=${LAB_COMPLETAO_SSH_HOST_ALIAS} main=${LAB_COMPLETAO_MAIN_ENGINE_SSH_HOST}). Orchestration must not treat this as hard-fail."
    else
      echo "WARNING: throttle or undervoltage flags ($th). Review PSU; not a host-smoke exit failure."
    fi
  fi
  if [[ "$LC_PRIV" == "1" ]]; then
    _lc_try journalctl -k --since "2 hours ago" --no-pager 2>/dev/null | grep -iE 'under-?voltage|throttl' | tail -n 8 || true
  fi
}

_lc_bench_compare() {
  if [[ "${LAB_COMPLETAO_BENCH_COMPARE:-}" != "1" ]]; then
    return 0
  fi
  _lc_section "bench_compare (LAB_COMPLETAO_BENCH_COMPARE=1)"
  if [[ "$LC_SKIP_ENGINE" == "1" ]]; then
    echo "(skip bench_compare: skip-engine-import)"
    return 0
  fi
  if [[ ! -f "$LC_REPO_ROOT/pyproject.toml" ]] || ! _lc_cmd uv; then
    echo "(skip bench_compare: no uv or pyproject.toml)"
    return 0
  fi
  if [[ "$LC_BENCH_TRACK" == "stable" ]]; then
    echo "--- stable track: core.engine import wall seconds ---"
    _t0=$(date +%s)
    (cd "$LC_REPO_ROOT" && uv run python -c "import core.engine; print('engine_ok')") || true
    _t1=$(date +%s)
    echo "BENCH_STABLE_IMPORT_SEC=$((_t1 - _t0))"
  elif [[ "$LC_BENCH_TRACK" == "beta" ]]; then
    echo "--- beta track: boar_fast_filter (FFI) import wall seconds ---"
    _t0=$(date +%s)
    (cd "$LC_REPO_ROOT" && uv run python -c "import importlib.util as u; print('boar_fast_filter_ok' if u.find_spec('boar_fast_filter') else 'boar_fast_filter_missing')") || true
    _t1=$(date +%s)
    echo "BENCH_BETA_FFI_IMPORT_SEC=$((_t1 - _t0))"
  else
    echo "(bench_compare: set --bench-track stable|beta for labeled A/B timing)"
  fi
}

_lc_init_bench_workdir

echo "=== lab-completao-host-smoke $(date -Iseconds 2>/dev/null || date) ==="
echo "REPO_ROOT: $LC_REPO_ROOT"
echo "HOST: $(hostname -f 2>/dev/null || hostname 2>/dev/null || echo unknown)"
echo "PRIVILEGED: $LC_PRIV"
if [[ -n "$LC_BENCH_TRACK" ]]; then
  echo "BENCH_TRACK: $LC_BENCH_TRACK ROOT: ${LC_BENCH_ROOT:-}"
fi

_lc_emit_host_env_audit_line

_lc_undervoltage_check

_lc_section "uname"
uname -a 2>/dev/null || true

_lc_section "uv"
if _lc_cmd uv; then
  uv --version
else
  echo "uv: not in PATH"
fi

_lc_section "Python import (engine)"
if [[ "$LC_SKIP_ENGINE" == "1" ]]; then
  echo "(skipped: container-only host -- expect Data Boar via Docker / Podman / Swarm stack, not bare-metal uv; see docs/ops/LAB_COMPLETAO_RUNBOOK.md)"
elif [[ -f "$LC_REPO_ROOT/pyproject.toml" ]] && _lc_cmd uv; then
  (cd "$LC_REPO_ROOT" && uv run python -c "import core.engine; print('import core.engine: OK')" 2>&1) || echo "import core.engine: FAILED"
else
  echo "(skip: no uv or no pyproject.toml)"
fi

_lc_section "Data Boar Engine (Baremetal RC)"
# Se o Maestro enviou um config via argumento $1 ou se benchmark-rc existe
CONFIG_RC="${1:-tests/config/benchmark-rc.yaml}"

if [[ -f "$LC_REPO_ROOT/$CONFIG_RC" ]] && _lc_cmd uv; then
  do_log_ INFO "Iniciando Scan de Performance Baremetal com $CONFIG_RC..."

  # SRE FIX: Avisa o Maestro que o motor pesado iniciou
  echo "SCANNING_BAREMETAL_RC at $(date +'%H:%M:%S')" > "${HOME}/.labop-status"

  (cd "$LC_REPO_ROOT" && uv run data-boar scan --config "$CONFIG_RC")
else
  # Fallback para o smoke original se não houver config de benchmark
  (cd "$LC_REPO_ROOT" && uv run python -c "import core.engine; print('import core.engine: OK')" 2>&1) || echo "import core.engine: FAILED"
fi

_lc_section "Docker / Podman"
if _lc_cmd docker; then
  docker --version
  _lc_try docker info 2>&1 | head -n 20
  _lc_try docker compose version
else
  echo "docker: not in PATH"
fi
if _lc_cmd podman; then
  podman --version
  _lc_try podman info 2>&1 | head -n 15
else
  echo "podman: not in PATH (optional)"
fi

_lc_section "lab-smoke-stack (deploy/lab-smoke-stack)"
LSS="$LC_REPO_ROOT/deploy/lab-smoke-stack"
if [[ -d "$LSS" ]] && [[ -f "$LSS/docker-compose.yml" ]]; then
  if [[ "$LC_LAB_STACK_UP" == "1" ]]; then
    echo "(requested) bringing up synthetic DB stack..."
    if _lc_cmd docker; then
      if [[ -f "$LSS/docker-compose.mongo.yml" ]]; then
        (cd "$LSS" && _lc_try docker compose -f docker-compose.yml -f docker-compose.mongo.yml up -d 2>&1 | tail -n 40) || true
      else
        (cd "$LSS" && _lc_try docker compose up -d 2>&1 | tail -n 40) || true
      fi
    elif _lc_cmd podman; then
      if [[ -f "$LSS/docker-compose.mongo.yml" ]]; then
        (cd "$LSS" && _lc_try podman compose -f docker-compose.yml -f docker-compose.mongo.yml up -d 2>&1 | tail -n 40) || true
      else
        (cd "$LSS" && _lc_try podman compose up -d 2>&1 | tail -n 40) || true
      fi
    else
      echo "(lab stack up skipped: no docker/podman available)"
    fi
  fi

  if _lc_cmd docker; then
    (cd "$LSS" && _lc_try docker compose ps 2>&1) || true
  elif _lc_cmd podman; then
    (cd "$LSS" && _lc_try podman compose ps 2>&1) || true
  else
    echo "(no docker/podman for stack status)"
  fi
else
  echo "(no deploy/lab-smoke-stack on this clone)"
fi

_lc_section "HTTP health (optional)"
if [[ -n "$LC_HEALTH_URL" ]]; then
  echo "URL: $LC_HEALTH_URL"
  if _lc_cmd curl; then
    curl -sS -m 15 -w "\nHTTP_CODE:%{http_code}\n" "$LC_HEALTH_URL" 2>&1 | tail -n 30
  else
    echo "curl: not in PATH"
  fi
else
  echo "(LAB_COMPLETAO_HEALTH_URL / --health-url not set)"
fi

if [[ "$LC_PRIV" == "1" ]]; then
  _lc_section "privileged read-only (sudo -n)"
  _lc_sudo iptables-save 2>/dev/null | head -n 40
  _lc_sudo nft list ruleset 2>/dev/null | head -n 40
  if _lc_cmd ufw; then
    _lc_sudo ufw status verbose 2>/dev/null || true
  fi
  for svc in fail2ban sshguard auditd; do
    if _lc_cmd systemctl; then
      echo -n "$svc: "
      systemctl is-active "$svc" 2>/dev/null || echo "n/a"
    fi
  done
fi

_lc_bench_compare

# Adicionar no final de scripts/lab-completao-host-smoke.sh
_lc_section "Telemetria"
FINAL_TS=$(date +"%H:%M:%S")
echo "DONE_SUCCESS_BAREMETAL at ${FINAL_TS}" > "${HOME}/.labop-status"
echo "Status persistido em ${HOME}/.labop-status"

echo "=== lab-completao-host-smoke END ==="
exit 0
