#!/usr/bin/env bash
# Fail if the application CycloneDX is missing Cargo.lock crates (#1950).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP="${1:-sbom-python.cdx.json}"
RUNTIME="${2:-}"

args=(--application "$APP")
if [[ -n "$RUNTIME" ]]; then
  args+=(--runtime "$RUNTIME")
elif [[ -f sbom-docker-image.cdx.json ]]; then
  args+=(--runtime sbom-docker-image.cdx.json)
fi

exec uv run python scripts/application_sbom.py check "${args[@]}"
