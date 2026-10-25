#!/usr/bin/env bash
# PyPI publish dispatch wrapper (#1046) - OIDC via CI, zero local API token.
# Build+upload: .github/workflows/publish-pypi.yml (not local uv publish).
# ADR-0031 (Hatchling packaging) + ADR-0005 (workflow Action SHA pins).
# Linux/macOS twin: scripts/pypi-publish.ps1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TARGET="testpypi"
REF="main"

usage() {
  cat <<'EOF'
Usage: ./scripts/pypi-publish.sh [-t testpypi|pypi] [-r REF]

Dispatches publish-pypi.yml (PyPI Trusted Publishing / OIDC). No UV_PUBLISH_TOKEN.

After dispatch:
  gh run list --workflow=publish-pypi.yml --limit 3
  gh run watch

Verify:
  testpypi -> https://test.pypi.org/project/data-boar/
  pypi     -> https://pypi.org/project/data-boar/
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help) usage ;;
    -t | --target)
      TARGET="${2:-}"
      shift 2
      ;;
    -r | --ref)
      REF="${2:-}"
      shift 2
      ;;
    *)
      echo "pypi-publish.sh: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  testpypi | pypi) ;;
  *)
    echo "pypi-publish.sh: target must be testpypi or pypi (got: $TARGET)" >&2
    exit 2
    ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  echo "pypi-publish.sh: gh not on PATH (install GitHub CLI; gh auth login)" >&2
  exit 1
fi

echo "=== PyPI publish dispatch (OIDC via CI) ==="
echo "Target: $TARGET  Ref: $REF"
echo "Local uv build/publish: disabled (CI builds dist; OIDC uploads)."

if [[ "$TARGET" == "pypi" ]]; then
  echo "Production PyPI: confirm GitHub Release exists and TestPyPI was verified." >&2
fi

gh workflow run publish-pypi.yml --ref "$REF" -f "target=$TARGET"

echo ""
echo "[OK] Workflow dispatched. Monitor:"
echo "  gh run list --workflow=publish-pypi.yml --limit 3"
echo "  gh run watch"
echo ""
if [[ "$TARGET" == "testpypi" ]]; then
  echo "Verify package: https://test.pypi.org/project/data-boar/"
else
  echo "Verify package: https://pypi.org/project/data-boar/"
fi
