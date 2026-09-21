#!/usr/bin/env bash
# Emit/verify local unsigned provenance record (#1950). Not SLSA.
# Twin of emit-provenance.ps1. Default: emit then verify with SBOM digests required.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ $# -eq 0 ]]; then
  uv run python scripts/emit_provenance.py emit --require-sboms
  exec uv run python scripts/emit_provenance.py verify --require-sboms
fi
exec uv run python scripts/emit_provenance.py "$@"
