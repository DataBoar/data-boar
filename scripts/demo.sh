#!/usr/bin/env bash
# scripts/demo.sh — zero-config demo entrypoint for Data Boar (#834)
#
# Usage:
#   ./scripts/demo.sh              # generates corpus, starts dashboard
#   ./scripts/demo.sh --no-web    # generates corpus only (no dashboard)
#   ./scripts/demo.sh --headless  # generates corpus + runs CLI scan (non-interactive)
#
# No real data required. All synthetic files are written to /tmp/data_boar_demo/
# and cleaned up on exit (Ctrl+C).
#
# Docker variant (no local Python needed):
#   docker run --rm -p 8088:8088 fabioleitao/data_boar:latest demo
#   (passes "demo" arg → container runs this script via entrypoint)

set -euo pipefail

DEMO_DIR="${TMPDIR:-/tmp}/data_boar_demo"
CONFIG_FILE="$DEMO_DIR/demo.config.yaml"
PORT="${DATA_BOAR_DEMO_PORT:-8088}"
NO_WEB=false
HEADLESS=false

for arg in "$@"; do
  case "$arg" in
    --no-web)   NO_WEB=true ;;
    --headless) HEADLESS=true; NO_WEB=true ;;
    --help|-h)
      grep '^#' "$0" | head -15 | sed 's/^# \?//'
      exit 0
      ;;
  esac
done

cleanup() {
  echo ""
  echo "[demo] Limpando $DEMO_DIR ..."
  rm -rf "$DEMO_DIR"
  echo "[demo] Pronto. Até logo!"
}
trap cleanup EXIT INT TERM

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Data Boar — Demo (corpus sintético, zero dados reais)  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Gera corpus sintético
echo "[demo] Gerando corpus sintético em $DEMO_DIR/corpus ..."
mkdir -p "$DEMO_DIR/corpus"
uv run python scripts/generate_synthetic_poc_corpus.py \
  --output "$DEMO_DIR/corpus" \
  --scenario "happy,unhappy,false_positive"
echo "[demo] Corpus gerado com sucesso."
echo ""

# 2. Gera config mínimo apontando para o corpus
cat > "$CONFIG_FILE" <<YAML
targets:
  - name: demo-corpus
    type: filesystem
    path: $DEMO_DIR/corpus
    recursive: true

report:
  output_dir: $DEMO_DIR/reports

api:
  port: $PORT
YAML

echo "[demo] Config: $CONFIG_FILE"
echo ""

# 3. Modo headless: roda CLI scan e sai
if $HEADLESS; then
  echo "[demo] Modo headless — executando varredura CLI ..."
  uv run python main.py \
    --config "$CONFIG_FILE" \
    --output "$DEMO_DIR/reports" \
    --quiet
  echo ""
  echo "[demo] Varredura concluída. Relatórios em: $DEMO_DIR/reports"
  echo "[demo] (A pasta será removida quando o script sair.)"
  exit 0
fi

# 4. Modo dashboard
if ! $NO_WEB; then
  echo "[demo] Iniciando dashBOARd em http://127.0.0.1:${PORT}/pt-br/"
  echo "[demo] Pressione Ctrl+C para encerrar e limpar arquivos temporários."
  echo ""
  uv run python main.py \
    --web \
    --config "$CONFIG_FILE" \
    --allow-insecure-http
fi
