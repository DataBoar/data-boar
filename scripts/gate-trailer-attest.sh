#!/usr/bin/env bash
# Gate trailer SSH ed25519 attestation wrapper (ADR-0056 file ns + ADR-0071).
# See scripts/gate_trailer_attest.py for behaviour.
#
# Usage (from repo root):
#   ./scripts/gate-trailer-attest.sh verify --commit <sha>
#   ./scripts/gate-trailer-attest.sh sign --text 'Gate-Change-Approved-By: @FabioLeitao | ...' --key ~/.ssh/id_ed25519_attest
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v ssh-keygen >/dev/null 2>&1; then
  echo "gate-trailer-attest.sh: ABORTED: ssh-keygen not on PATH." >&2
  exit 2
fi

exec uv run python scripts/gate_trailer_attest.py "$@"
