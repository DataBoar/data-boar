#!/usr/bin/env bash
# scripts/demo.sh — thin wrapper for ``data-boar --demo`` (#834, #1113)
#
# Usage:
#   ./scripts/demo.sh              # dashboard (default)
#   ./scripts/demo.sh --no-web    # corpus + config only (headless scan, then exit)
#   ./scripts/demo.sh --headless  # alias for --no-web
#
# Docker variant (no local Python needed):
#   docker run --rm -p 8088:8088 fabioleitao/data_boar:latest demo

set -euo pipefail

PORT="${DATA_BOAR_DEMO_PORT:-8088}"
NO_WEB=false
HEADLESS=false

for arg in "$@"; do
  case "$arg" in
    --no-web)   NO_WEB=true ;;
    --headless) HEADLESS=true; NO_WEB=true ;;
    --help|-h)
      grep '^#' "$0" | head -18 | sed 's/^# \?//'
      exit 0
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if $HEADLESS || $NO_WEB; then
  # Multi-step bash flow: bash trap owns cleanup; disable Python atexit in prepare_demo_workspace.
  DEMO_DIR="${TMPDIR:-/tmp}/data_boar_demo"
  cleanup() {
    echo ""
    echo "[demo] Limpando $DEMO_DIR ..."
    rm -rf "$DEMO_DIR"
    echo "[demo] Pronto."
  }
  trap cleanup EXIT INT TERM

  uv run python -c "
from pathlib import Path
from core.demo.runtime import prepare_demo_workspace
from config.loader import load_config
from core.engine import AuditEngine

demo_dir, config_path, _ = prepare_demo_workspace(
    port=int('${PORT}'),
    register_cleanup=False,
    demo_root=Path('${DEMO_DIR}'),
)
config = load_config(str(config_path))
engine = AuditEngine(config)
try:
    sid = engine.start_audit()
    report = engine.generate_final_reports(sid)
    print(f'[demo] Scan session: {sid}')
    if report:
        print(f'[demo] Report written: {report}')
finally:
    engine.db_manager.dispose()
"
  exit 0
fi

exec uv run python main.py --demo --port "$PORT" "$@"
