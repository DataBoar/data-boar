#!/bin/sh
# AUDIT RITUAL - DATA BOAR
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +'%Y%m%d_%H%M')
LOG_FILE="$LOG_DIR/audit-$TIMESTAMP.log"
LATEST_LOG="$LOG_DIR/latest.log"

{
	echo "--- AUDIT START: $(date +'%Y-%m-%d %H:%M:%S') ---"
	echo "OPERATOR: $USER | COMMIT: $(git rev-parse --short HEAD 2>/dev/null)"
	echo "---------------------------------------------------"

	# Executa o motor em Bash
	/bin/bash ./scripts/check-all.sh

	echo "---------------------------------------------------"
	echo "--- AUDIT END: $(date +'%Y-%m-%d %H:%M:%S') ---"
} 2>&1 | tee "$LOG_FILE"

cp "$LOG_FILE" "$LATEST_LOG"
