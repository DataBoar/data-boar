#!/usr/bin/env bash
# Security scan tier for check-all (issue #1044) — commands mirror CI workflows.
# Invoked from check-all.sh / check-all.ps1; fail-collect (run all, report at end).
# Usage (from repo root):
#   ./scripts/check-all-security-scans.sh
#   ./scripts/check-all-security-scans.sh --enforced   # + Semgrep (semgrep.yml parity)
set -uo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

ENFORCED=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --enforced | -Enforced) ENFORCED=1 ;;
    -h | --help)
      echo "Usage: $0 [--enforced]"
      echo "  Default: Bandit + Zizmor (offline-capable after uv sync)."
      echo "  --enforced: also run Semgrep (network; engine version from semgrep.yml image tag)."
      exit 0
      ;;
    *)
      echo "check-all-security-scans.sh: unknown option: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v uv >/dev/null 2>&1; then
  echo "check-all-security-scans.sh: ABORTED: uv not on PATH." >&2
  exit 2
fi

FAILURES=()

_run_scan() {
  local name="$1"
  shift
  echo "=== Security scan: $name ===" >&2
  set +e
  "$@"
  local code=$?
  set -e
  if [[ "$code" -eq 0 ]]; then
    printf '\033[32m%s\033[0m\n' "$name... Passed" >&2
  else
    printf '\033[31m%s\033[0m\n' "$name... Failed (exit $code)" >&2
    FAILURES+=("$name (exit $code)")
  fi
}

# Mirrors ci.yml job Bandit (strict paths; QUALITY_WORKFLOW_RECOMMENDATIONS.md).
_run_scan "Bandit" uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q

# Local uvx zizmor is the PyPI CLI. CI (.github/workflows/zizmor.yml) runs
# zizmorcore/zizmor-action@<SHA> (SARIF upload, offline-audits). Those are
# different artifacts — do not invent CLI==action version parity (#1793).
_run_scan "Zizmor" uvx zizmor .github/workflows/

_semgrep_ver_from_workflow() {
  local wf=".github/workflows/semgrep.yml"
  local ver=""
  # GNU grep -P matches the issue recipe; POSIX sed covers macOS / no -P.
  if grep -oP 'semgrep/semgrep:\K[0-9]+\.[0-9]+\.[0-9]+' "$wf" >/dev/null 2>&1; then
    ver="$(grep -oP 'semgrep/semgrep:\K[0-9]+\.[0-9]+\.[0-9]+' "$wf" | head -n 1)"
  else
    ver="$(sed -n 's/.*semgrep\/semgrep:\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' "$wf" | head -n 1)"
  fi
  printf '%s' "$ver"
}

if [[ "$ENFORCED" -eq 1 ]]; then
  SEMGREP_VER="$(_semgrep_ver_from_workflow)"
  if [[ -z "$SEMGREP_VER" ]]; then
    echo "check-all-security-scans.sh: ABORTED: could not read Semgrep version from .github/workflows/semgrep.yml" >&2
    exit 1
  fi
  echo "Semgrep pin: ${SEMGREP_VER} (from .github/workflows/semgrep.yml image tag)." >&2
  _run_scan "Semgrep" uvx "semgrep@${SEMGREP_VER}" scan --config p/python --metrics=off \
    --exclude-rule python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text \
    --error .
fi

if [[ "${#FAILURES[@]}" -gt 0 ]]; then
  echo "check-all-security-scans.sh: FAILED (${#FAILURES[@]} scan(s)):" >&2
  for item in "${FAILURES[@]}"; do
    echo "  - $item" >&2
  done
  exit 1
fi

echo "check-all-security-scans.sh: OK (all security scans passed)." >&2
exit 0
