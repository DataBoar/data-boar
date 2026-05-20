#!/usr/bin/env bash
# check-all.sh — Linux/macOS (bash) mirror of scripts/check-all.ps1.
# Same gates: gatekeeper (pwsh) + Rust (cargo fmt/check/test, PYO3 ABI3 hint) +
# plans-stats --write + pre-commit-and-tests.sh (venv + pre-commit + pytest).
# From repo root:
#   ./scripts/check-all.sh
#   ./scripts/check-all.sh --skip-pre-commit
#   ./scripts/check-all.sh --include-version-smoke
# On Windows, prefer .\scripts\check-all.ps1 (identical flow).
# Full parity with Windows requires pwsh for gatekeeper-audit.ps1; install
# PowerShell Core where possible. Rust requires cargo on PATH.
# Memory safety: pre-commit-and-tests.sh runs tests/security/test_mem_integrity.py first (Hypothesis),
# then full pytest with --deselect on that file (parity with check-all.ps1).
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

SKIP_PRECOMMIT=0
INCLUDE_VERSION_SMOKE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -SkipPreCommit | --skip-pre-commit) SKIP_PRECOMMIT=1 ;;
    -IncludeVersionSmoke | --include-version-smoke) INCLUDE_VERSION_SMOKE=1 ;;
    -h | --help)
      echo "Usage: $0 [options]"
      echo "  --skip-pre-commit          Only run pytest (same as check-all.ps1 -SkipPreCommit)"
      echo "  --include-version-smoke    After success, run version-readiness-smoke.ps1 (requires pwsh)"
      echo "  -h, --help                 This help"
      exit 0
      ;;
    *)
      echo "check-all.sh: unknown option: $1" >&2
      exit 2
      ;;
  esac
  shift
done

# PII gate (parity with check-all.ps1) — reuses PowerShell script.
if command -v pwsh >/dev/null 2>&1; then
  if ! pwsh "$REPO_ROOT/scripts/gatekeeper-audit.ps1"; then
    echo "check-all.sh: ABORTED by gatekeeper-audit (PII seed hit in staged files)." >&2
    exit "$?"
  fi
else
  echo "check-all.sh: WARN: pwsh not on PATH; skipping gatekeeper-audit.ps1 (install PowerShell for parity with check-all.ps1)." >&2
fi

# Rust guard (same commands as check-all.ps1: fmt --check, check, test --quiet)
if ! command -v cargo >/dev/null 2>&1; then
  printf '\033[31m%s\033[0m\n' "Rust Guard... Failed (cargo not on PATH)" >&2
  exit 1
fi
echo "Running Rust guard (cargo fmt, check, test)..." >&2
if ! (
  export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
  cd "$REPO_ROOT/rust/boar_fast_filter" || exit 1
  cargo fmt -- --check && cargo check && cargo test --quiet
); then
  printf '\033[31m%s\033[0m\n' "Rust Guard... Failed" >&2
  exit 1
fi
printf '\033[32m%s\033[0m\n' "Rust Guard... Passed" >&2

echo "=== check-all.sh: lint + tests (repo: $REPO_ROOT) ===" >&2

# Keep plan dashboard stats in sync before lint/tests (same as check-all.ps1).
PY=python3
if ! command -v python3 >/dev/null 2>&1; then
  PY=python
fi
echo "Refreshing plans status dashboard..." >&2
"$PY" "$REPO_ROOT/scripts/plans-stats.py" --write

echo "Checking hub index links..." >&2
"$PY" "$REPO_ROOT/scripts/check_hubs.py" || {
  echo "check-all.sh: FAILED hub link check (check_hubs.py)." >&2
  exit 1
}

# Delegate: same behaviour as pre-commit-and-tests.ps1 (venv recovery, pre-commit, pytest).
pct_args=()
if [[ "$SKIP_PRECOMMIT" -eq 1 ]]; then
  pct_args+=(--skip-pre-commit)
fi
set +e
bash "$REPO_ROOT/scripts/pre-commit-and-tests.sh" "${pct_args[@]}"
exit_code=$?
set -e
if [[ "$exit_code" -ne 0 ]]; then
  echo "check-all.sh: FAILED (see output above)." >&2
  exit "$exit_code"
fi

if [[ "$INCLUDE_VERSION_SMOKE" -eq 1 ]]; then
  vsmoke="$REPO_ROOT/scripts/version-readiness-smoke.ps1"
  if [[ -f "$vsmoke" ]]; then
    if command -v pwsh >/dev/null 2>&1; then
      echo "Running version readiness smoke..." >&2
      pwsh "$vsmoke" || exit "$?"
    else
      echo "check-all.sh: --include-version-smoke needs pwsh; skipping (script present)." >&2
    fi
  else
    echo "Version readiness smoke script not found; skipping." >&2
  fi
fi

echo "check-all.sh: OK (pre-commit and pytest passed)." >&2
exit 0
