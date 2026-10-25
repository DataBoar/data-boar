#!/bin/bash
# One-shot Oracle XE PDB seed for lab-smoke-stack (#1369).
# gvenzl init hooks run as SYS on the CDB root; lab tables must live in XEPDB1.
set -euo pipefail

ORACLE_HOST="${ORACLE_HOST:-lab-oracle}"
ORACLE_PORT="${ORACLE_PORT:-1521}"
ORACLE_SERVICE="${ORACLE_SERVICE:-XEPDB1}"
APP_USER="${APP_USER:-lab_smoke}"
APP_USER_PASSWORD="${APP_USER_PASSWORD:?APP_USER_PASSWORD required}"
SEED_DIR="${SEED_DIR:-/seed}"

CONN="${APP_USER}/${APP_USER_PASSWORD}@//${ORACLE_HOST}:${ORACLE_PORT}/${ORACLE_SERVICE}"

wait_for_oracle() {
  attempt=0
  while [ "$attempt" -lt 120 ]; do
    if echo "SELECT 1 FROM dual;" | sqlplus -s "$CONN" >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  echo "lab-oracle-init: Oracle PDB not ready at ${ORACLE_HOST}:${ORACLE_PORT}/${ORACLE_SERVICE}" >&2
  exit 1
}

run_sql_file() {
  sql_file="$1"
  echo "lab-oracle-init: applying $(basename "$sql_file")"
  sqlplus -s "$CONN" @"$sql_file" || {
    rc=$?
    echo "lab-oracle-init: sqlplus failed for $(basename "$sql_file") (exit $rc)" >&2
    exit "$rc"
  }
}

wait_for_oracle

for sql_file in \
  "$SEED_DIR"/01_lab_smoke.sql \
  "$SEED_DIR"/02_lab_smoke_linkage.sql \
  "$SEED_DIR"/03_lab_fp_numeric_ids.sql; do
  if [ ! -f "$sql_file" ]; then
    echo "lab-oracle-init: missing $sql_file" >&2
    exit 1
  fi
  run_sql_file "$sql_file"
done

echo "lab-oracle-init: seed applied"
