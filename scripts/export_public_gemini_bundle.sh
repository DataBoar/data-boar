#!/usr/bin/env bash
# Safe public bundle for Gemini (or any offline reviewer): tracked files only, FILE markers.
# Usage: from repo root —  ./scripts/export_public_gemini_bundle.sh [extra args passed to Python]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec uv run python scripts/export_public_gemini_bundle.py "$@"
