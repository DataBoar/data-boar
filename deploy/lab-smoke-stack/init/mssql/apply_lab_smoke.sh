#!/bin/bash
# One-shot MSSQL seed for lab-smoke-stack (#1369).
# The official SQL Server image does not auto-run /docker-entrypoint-initdb.d scripts.
set -euo pipefail

MSSQL_HOST="${MSSQL_HOST:-lab-mssql}"
MSSQL_PORT="${MSSQL_PORT:-1433}"
SA_PASSWORD="${MSSQL_SA_PASSWORD:?MSSQL_SA_PASSWORD required}"
SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
SEED_DIR="${SEED_DIR:-/seed}"

wait_for_mssql() {
  attempt=0
  while [ "$attempt" -lt 90 ]; do
    if "$SQLCMD" -S "${MSSQL_HOST},${MSSQL_PORT}" -U sa -P "$SA_PASSWORD" -C -Q "SELECT 1" -b -o /dev/null 2>/dev/null; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  echo "lab-mssql-init: SQL Server not ready at ${MSSQL_HOST}:${MSSQL_PORT}" >&2
  exit 1
}

wait_for_mssql

for sql_file in \
  "$SEED_DIR"/01_lab_smoke.sql \
  "$SEED_DIR"/02_lab_smoke_linkage.sql \
  "$SEED_DIR"/03_lab_fp_numeric_ids.sql; do
  if [ ! -f "$sql_file" ]; then
    echo "lab-mssql-init: missing $sql_file" >&2
    exit 1
  fi
  echo "lab-mssql-init: applying $(basename "$sql_file")"
  "$SQLCMD" -S "${MSSQL_HOST},${MSSQL_PORT}" -U sa -P "$SA_PASSWORD" -C -i "$sql_file"
done

echo "lab-mssql-init: seed applied"
