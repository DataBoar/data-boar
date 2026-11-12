# shellcheck shell=bash
# Shared helpers for the local demo harness (#1447). Sourced, never executed.
# Linux host-only (rootless Podman). No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).

DL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DL_DIR/../.." && pwd)"
# shellcheck source=images.env
. "$DL_DIR/images.env"

# State (corpus, ephemeral secrets, logs, sqlite) lives OUTSIDE the repo.
STATE="${DEMO_LOCAL_STATE:-$HOME/.local/state/databoar-demo-local}"
SECRETS="$STATE/secrets.env"
# /extras overlay for the container image (a cache: down.sh does not delete it).
EXTRAS_DIR="${DEMO_LOCAL_EXTRAS_DIR:-$HOME/.cache/databoar-demo-local/extras}"
# Optional real Supabase target, kept outside the repo (pass_from_env only).
SUPABASE_TARGET="${DEMO_LOCAL_SUPABASE_TARGET:-$HOME/.config/databoar-demo/supabase.target.yaml}"

PORT_SMB="${DEMO_LOCAL_SMB_PORT:-4450}"
PORT_PG="${DEMO_LOCAL_PG_PORT:-55433}"
PORT_REDIS="${DEMO_LOCAL_REDIS_PORT:-56380}"
PORT_MONGO="${DEMO_LOCAL_MONGO_PORT:-27019}"
PORT_WEB="${DEMO_LOCAL_WEB_PORT:-8077}"
PORT_BOAR="${DEMO_LOCAL_BOAR_PORT:-8099}"
export DEMO_LOCAL_SMB_PORT="$PORT_SMB" DEMO_LOCAL_PG_PORT="$PORT_PG" \
  DEMO_LOCAL_REDIS_PORT="$PORT_REDIS" DEMO_LOCAL_MONGO_PORT="$PORT_MONGO" \
  DEMO_LOCAL_WEB_PORT="$PORT_WEB" DEMO_LOCAL_BOAR_PORT="$PORT_BOAR"

C_SMB=dbdl-smb C_PG=dbdl-pg C_REDIS=dbdl-redis C_MONGO=dbdl-mongo C_WEB=dbdl-web
C_BOAR=dbdl-boar
BOAR_URL="http://127.0.0.1:$PORT_BOAR"
# Operator allowlist for credential destinations (add the real Supabase host here).
ALLOWED_HOSTS="127.0.0.1${DEMO_LOCAL_EXTRA_ALLOWED_HOSTS:+,$DEMO_LOCAL_EXTRA_ALLOWED_HOSTS}"

# Hardening shared by every container: no capability unless the caller adds one.
HARDEN=(--cap-drop all --security-opt no-new-privileges)

die() { echo "demo-local: $*" >&2; exit 1; }

# Podman: native `podman`, or `wsl podman` is NOT supported (Linux host-only).
command -v podman >/dev/null 2>&1 || die "podman not found (Linux host-only)"
command -v uv >/dev/null 2>&1 || die "uv not found in PATH"

load_secrets() {
  [ -f "$SECRETS" ] || die "no secrets file; run up.sh first"
  set -a
  # shellcheck disable=SC1090
  . "$SECRETS"
  set +a
}

wait_port() { # host port seconds
  local i=0
  while ! (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null; do
    i=$((i + 1))
    [ "$i" -ge "$(($3 * 4))" ] && return 1
    sleep 0.25
  done
  return 0
}

wait_http() { # url seconds
  local i=0
  while ! curl -fsS -o /dev/null --max-time 2 "$1" 2>/dev/null; do
    i=$((i + 1))
    [ "$i" -ge "$(($2 * 2))" ] && return 1
    sleep 0.5
  done
  return 0
}

# Rendered Boar config. Container mode sees the state dir at /data.
render_config() { # mode out [only] [variant]
  local mode="$1" out="$2" only="${3:-}" variant="${4:-}" datadir
  datadir="$STATE/data"
  [ "$mode" = container ] && datadir=/data
  local args=(--template "$DL_DIR/config.demo-local.yaml" --out "$out"
    --data-dir "$datadir")
  [ -f "$SUPABASE_TARGET" ] && args+=(--supabase-file "$SUPABASE_TARGET")
  podman container exists "$C_WEB" 2>/dev/null || args+=(--no-web)
  [ -n "$only" ] && args+=(--only "$only")
  [ -n "$variant" ] && args+=(--variant "$variant")
  uv run --no-sync python -I "$DL_DIR/render_config.py" "${args[@]}"
}

# Names of env vars the rendered config reads (pass_from_env etc.).
config_env_names() { # config
  uv run --no-sync python -I "$DL_DIR/render_config.py" --list-env "$1"
}

# The published image 1.8.0 predates "fix(smb): pass the target port to walk,
# scandir and open_file" (0f9e931f), so it always dials 445 and cannot scan the
# harness SMB share on a high port. While that is true, container mode mounts the
# repo's fixed connector over the image file (read-only). Set
# DEMO_LOCAL_NO_SMB_PATCH=1 to run the unpatched image.
smb_patch_args() {
  [ -z "${DEMO_LOCAL_NO_SMB_PATCH:-}" ] || return 0
  local fixed='open_file(unc_file, mode="rb", port=port)'
  grep -qF "$fixed" "$REPO_ROOT/connectors/smb_connector.py" || return 0
  if podman run --rm --entrypoint python "$IMG_BOAR" -c \
    "import sys; sys.exit(0 if '$fixed' in open('/app/connectors/smb_connector.py').read() else 1)" \
    >/dev/null 2>&1; then
    return 0
  fi
  echo "-v"
  echo "$REPO_ROOT/connectors/smb_connector.py:/app/connectors/smb_connector.py:ro"
}

boar_mode() { cat "$STATE/boar.mode" 2>/dev/null || true; }

boar_stop() {
  case "$(boar_mode)" in
    container) podman rm -f -t 5 "$C_BOAR" >/dev/null 2>&1 || true ;;
    native)
      if [ -f "$STATE/boar.pid" ]; then
        local pid
        pid="$(cat "$STATE/boar.pid")"
        # Only the PID this harness started (recorded at launch).
        kill "$pid" 2>/dev/null || true
        for _ in $(seq 1 40); do kill -0 "$pid" 2>/dev/null || break; sleep 0.25; done
        kill -9 "$pid" 2>/dev/null || true
        rm -f "$STATE/boar.pid"
      fi
      ;;
  esac
}

# Start Boar for a rendered config (state/data/config.yaml) in the saved mode.
boar_start() { # mode
  local mode="$1"
  load_secrets
  mkdir -p "$STATE/data" "$STATE/logs"
  rm -f "$STATE/data/audit_results.db"*
  local names=() n
  mapfile -t names < <(config_env_names "$STATE/data/config.yaml")
  echo "$mode" >"$STATE/boar.mode"
  if [ "$mode" = container ]; then
    local envargs=() patch=()
    mapfile -t patch < <(smb_patch_args)
    for n in "${names[@]}"; do [ -n "$n" ] && [ -n "${!n:-}" ] && envargs+=(-e "$n"); done
    podman run -d --name "$C_BOAR" --network host --memory 700m "${HARDEN[@]}" \
      --userns "keep-id:uid=65532,gid=65532" \
      "${envargs[@]}" "${patch[@]}" \
      -e API_HOST=127.0.0.1 -e DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS="$ALLOWED_HOSTS" \
      -v "$STATE/data:/data" -v "$EXTRAS_DIR:/extras:ro" \
      "$IMG_BOAR" main.py --config /data/config.yaml --web --host 127.0.0.1 \
      --port "$PORT_BOAR" --allow-insecure-http >"$STATE/logs/boar-start.log" 2>&1 \
      || die "boar container failed to start (see $STATE/logs/boar-start.log)"
  else
    (
      cd "$REPO_ROOT"
      export API_HOST=127.0.0.1 DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS="$ALLOWED_HOSTS"
      setsid uv run --no-sync python main.py --config "$STATE/data/config.yaml" \
        --web --host 127.0.0.1 --port "$PORT_BOAR" --allow-insecure-http \
        >"$STATE/logs/boar-native.log" 2>&1 &
      echo $! >"$STATE/boar.pid"
    )
  fi
  wait_http "$BOAR_URL/health" 90 || die "boar did not answer /health"
}
