#!/usr/bin/env bash
# Bring up the LOCAL demo scenario (#1447): 5 loopback targets + Data Boar.
# Linux host-only (rootless Podman). No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
#
# Usage: up.sh [--mode container|native] [--no-web]
# Prints only the startup time and the dashboard URL. Secrets are random,
# ephemeral and kept in $STATE/secrets.env (mode 600), never printed.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

MODE=container
WITH_WEB=1
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:?--mode needs container|native}"; shift 2 ;;
    --no-web) WITH_WEB=0; shift ;;
    *) die "usage: up.sh [--mode container|native] [--no-web]" ;;
  esac
done
case "$MODE" in container | native) ;; *) die "bad --mode: $MODE" ;; esac

T0=$(date +%s.%N)
OK=0
cleanup() {
  { [ "$OK" = 1 ] || [ -n "${DEMO_LOCAL_KEEP_ON_FAIL:-}" ]; } && return 0
  echo "demo-local: up failed, rolling back" >&2
  "$DL_DIR/down.sh" >/dev/null 2>&1 || true
}
trap cleanup EXIT

umask 077
mkdir -p "$STATE" "$STATE/logs" "$STATE/data" "$STATE/samba"
chmod 700 "$STATE"

# --- ephemeral secrets (never printed) ---------------------------------------
gen() { python3 -c 'import secrets; print(secrets.token_urlsafe(18))'; }
{
  echo "DATA_BOAR_DEMO_PG_PASS=$(gen)"
  echo "DATA_BOAR_DEMO_SMB_PASS=$(gen)"
  echo "DATA_BOAR_DEMO_REDIS_PASS=$(gen)"
  echo "DATA_BOAR_DEMO_MONGO_PASS=$(gen)"
  echo "DATA_BOAR_DEMO_MONGO_ROOT_PASS=$(gen)"
} >"$SECRETS"
chmod 600 "$SECRETS"
load_secrets

# --- project env + corpus ----------------------------------------------------
cd "$REPO_ROOT"
uv sync -q --extra postgres --extra nosql --extra shares --extra compressed
rm -rf "${STATE:?}/corpus"
uv run --no-sync python -I -c 'from core.demo.synthetic_corpus import generate_corpus; import sys; generate_corpus(sys.argv[1], ["compressed_smb"])' \
  "$STATE/corpus" >/dev/null
chmod -R o+rX "$STATE/corpus"

# --- SMB (compressed corpus) -------------------------------------------------
cp "$REPO_ROOT/deploy/demo/samba/container.json" "$STATE/samba/container.json"
python3 - "$REPO_ROOT/deploy/demo/samba/users.example.json" "$STATE/samba/users.json" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1]))
d["users"]["all_entries"][0]["password"] = os.environ["DATA_BOAR_DEMO_SMB_PASS"]
json.dump(d, open(sys.argv[2], "w"))
PY
chmod 600 "$STATE/samba/users.json"
# Same flags as deploy/demo/quadlet/samba.container (measured on Podman 5.4).
podman run -d --name "$C_SMB" --userns host --memory 96m --cap-drop all \
  --cap-add SETUID --cap-add SETGID --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges -p "127.0.0.1:$PORT_SMB:445" \
  -e SAMBA_CONTAINER_ID=boardemo \
  -e SAMBACC_CONFIG=/etc/samba-demo/container.json:/etc/samba-demo/users.json \
  -v "$STATE/samba/container.json:/etc/samba-demo/container.json:ro" \
  -v "$STATE/samba/users.json:/etc/samba-demo/users.json:ro" \
  -v "$STATE/corpus:/share:ro" \
  "$IMG_SAMBA" >/dev/null

# --- PostgreSQL 17: lab + supa_sim (simulated Supabase) ----------------------
podman run -d --name "$C_PG" --user 70:70 --userns keep-id:uid=70,gid=70 --memory 128m "${HARDEN[@]}" \
  -p "127.0.0.1:$PORT_PG:5432" -e POSTGRES_USER=demo -e POSTGRES_DB=lab \
  -e POSTGRES_PASSWORD="$DATA_BOAR_DEMO_PG_PASS" \
  -v "$REPO_ROOT/deploy/lab-smoke-stack/init/postgres:/docker-entrypoint-initdb.d:ro" \
  "$IMG_POSTGRES" -c shared_buffers=32MB -c max_connections=20 >/dev/null

# --- Redis 7.4 ---------------------------------------------------------------
podman run -d --name "$C_REDIS" --user 999:1000 --userns keep-id:uid=999,gid=1000 --memory 48m "${HARDEN[@]}" \
  -p "127.0.0.1:$PORT_REDIS:6379" "$IMG_REDIS" \
  redis-server --requirepass "$DATA_BOAR_DEMO_REDIS_PASS" --save "" \
  --appendonly no --maxmemory 32mb >/dev/null

# --- MongoDB 7.0 (WiredTiger cache capped at 0.25 GB, the minimum) -----------
podman run -d --name "$C_MONGO" --user 999:999 --userns keep-id:uid=999,gid=999 --memory 256m "${HARDEN[@]}" \
  -p "127.0.0.1:$PORT_MONGO:27017" -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD="$DATA_BOAR_DEMO_MONGO_ROOT_PASS" \
  -v "$REPO_ROOT/deploy/lab-smoke-stack/init/mongodb:/docker-entrypoint-initdb.d:ro" \
  "$IMG_MONGO" --wiredTigerCacheSizeGB 0.25 --bind_ip_all >/dev/null

# --- optional WebDAV + REST (single httpd container) -------------------------
if [ "$WITH_WEB" = 1 ] && [ -x "$DL_DIR/web.sh" ]; then
  "$DL_DIR/web.sh" start
fi

# --- wait + seed -------------------------------------------------------------
for i in $(seq 1 120); do
  podman exec "$C_PG" pg_isready -U demo -d lab -h 127.0.0.1 -q 2>/dev/null && break
  [ "$i" = 120 ] && die "postgres not ready"
  sleep 0.5
done
podman exec "$C_PG" psql -U demo -d lab -q -c "CREATE DATABASE supa_sim" >/dev/null
uv run --no-sync python -I "$DL_DIR/seed_supa_sim.py" \
  | podman exec -i "$C_PG" psql -U demo -d supa_sim -q -v ON_ERROR_STOP=1 >/dev/null
# Redis seed = the lab-smoke seed, unchanged; redis-cli reads REDISCLI_AUTH.
for i in $(seq 1 60); do
  podman exec -e REDISCLI_AUTH="$DATA_BOAR_DEMO_REDIS_PASS" "$C_REDIS" redis-cli ping 2>/dev/null | grep -q PONG && break
  [ "$i" = 60 ] && die "redis not ready"
  sleep 0.5
done
podman exec -i -e REDISCLI_AUTH="$DATA_BOAR_DEMO_REDIS_PASS" -e REDIS_HOST=127.0.0.1 \
  "$C_REDIS" sh -s <"$REPO_ROOT/deploy/lab-smoke-stack/init/redis/01_lab_smoke_seed.sh" >/dev/null
# Mongo: the entrypoint seeds lab_smoke_mongo as root; add a read-only scan user
# in that database (the connector authenticates against the URI database).
for i in $(seq 1 240); do
  podman exec "$C_MONGO" mongosh --quiet \
    -u root -p "$DATA_BOAR_DEMO_MONGO_ROOT_PASS" --authenticationDatabase admin \
    --eval 'db.getSiblingDB("lab_smoke_mongo").lab_people.countDocuments()' 2>/dev/null \
    | grep -q '^2$' && break
  [ "$i" = 240 ] && die "mongo not seeded"
  sleep 0.5
done
podman exec -e BP="$DATA_BOAR_DEMO_MONGO_PASS" "$C_MONGO" mongosh --quiet \
  -u root -p "$DATA_BOAR_DEMO_MONGO_ROOT_PASS" --authenticationDatabase admin --eval \
  'db.getSiblingDB("lab_smoke_mongo").createUser({user:"boar",pwd:process.env.BP,roles:[{role:"read",db:"lab_smoke_mongo"}]})' >/dev/null
wait_port 127.0.0.1 "$PORT_SMB" 30 || die "smb not listening"

# --- Boar --------------------------------------------------------------------
if [ "$MODE" = container ]; then
  "$DL_DIR/build-extras.sh" --ensure
fi
render_config "$MODE" "$STATE/data/config.yaml"
boar_start "$MODE"

OK=1
printf 'up in %.1f s (%s mode)\nDashboard: %s/\n' \
  "$(echo "$(date +%s.%N) - $T0" | bc)" "$MODE" "$BOAR_URL"
