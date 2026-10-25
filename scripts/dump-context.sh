#!/usr/bin/env bash
# dump-context.sh
# Build a single governance/context TXT bundle for external audits.
# Privacy guardrails:
# - Exclude any path containing a directory segment named "private".
# - Exclude any file whose basename starts with ".env".
set -euo pipefail

OUTPUT="${1:-data-boar-blackbox-audit.txt}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TARGET_DIRS=(
  ".cursor"
  ".vscode"
  ".github"
  "docs/ops/inspirations"
  "scripts"
)

TARGET_FILES=(
  "AGENTS.md"
  ".gitignore"
  "pyproject.toml"
  "uv.lock"
  ".pre-commit-config.yaml"
  "docs/plans/PLANS_TODO.md"
  ".cursor/rules/session-mode-keywords.mdc"
  ".cursor/rules/check-all-gate.mdc"
  "scripts/check-all.ps1"
  "scripts/check-all.sh"
  "scripts/pre-commit-and-tests.ps1"
  "scripts/pre-commit-and-tests.sh"
)

is_excluded_path() {
  local path="${1//\\//}"
  local base
  base="${path##*/}"
  if [[ "$base" == .env* ]]; then
    return 0
  fi

  local segment
  IFS='/' read -r -a _segments <<< "$path"
  for segment in "${_segments[@]}"; do
    if [[ "$segment" == "private" ]]; then
      return 0
    fi
  done
  return 1
}

declare -A SEEN=()
FILES=()

add_file_if_allowed() {
  local path="$1"
  if [[ -z "$path" ]]; then
    return
  fi
  if ! [[ -f "$path" ]]; then
    return
  fi
  if is_excluded_path "$path"; then
    return
  fi
  if [[ -n "${SEEN[$path]:-}" ]]; then
    return
  fi
  SEEN["$path"]=1
  FILES+=("$path")
}

for f in "${TARGET_FILES[@]}"; do
  add_file_if_allowed "$f"
done

for dir in "${TARGET_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    while IFS= read -r tracked_file; do
      add_file_if_allowed "$tracked_file"
    done < <(git ls-files -- "$dir")
  fi
done

mapfile -t SORTED_FILES < <(printf "%s\n" "${FILES[@]}" | LC_ALL=C sort)

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
head_sha="$(git rev-parse HEAD 2>/dev/null || echo "unknown")"
remote_sha="unknown"
sync_status="WARNING: Unable to validate sync with origin (missing remote ref or fetch failure)."

if git fetch --quiet origin >/dev/null 2>&1; then
  if git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
    remote_sha="$(git rev-parse "origin/$branch" 2>/dev/null || echo "unknown")"
    if [[ "$head_sha" == "$remote_sha" ]]; then
      sync_status="SYNC_OK: HEAD matches origin/$branch"
    else
      sync_status="WARNING: Local HEAD differs from origin/$branch"
    fi
  elif git rev-parse --verify "@{u}" >/dev/null 2>&1; then
    remote_sha="$(git rev-parse "@{u}" 2>/dev/null || echo "unknown")"
    if [[ "$head_sha" == "$remote_sha" ]]; then
      sync_status="SYNC_OK: HEAD matches upstream @{u}"
    else
      sync_status="WARNING: Local HEAD differs from upstream @{u}"
    fi
  fi
fi

{
  echo "==========================================================="
  echo "DATA BOAR - AGENT AUDIT DUMP (LINUX) - $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Scope: Rules, Skills, Rituals, Taxonomy and Gates"
  echo "BRANCH: $branch"
  echo "HEAD: $head_sha"
  echo "REMOTE_HEAD: $remote_sha"
  echo "$sync_status"
  echo "PRIVACY_GUARD: skip */private/* and .env*"
  echo "==========================================================="
} > "$OUTPUT"

for file in "${SORTED_FILES[@]}"; do
  perm="$(stat -c '%a' "$file" 2>/dev/null || stat -f '%Lp' "$file" 2>/dev/null || echo 'n/a')"
  size="$(wc -c < "$file" | tr -d '[:space:]')"
  {
    echo
    echo "#### START_FILE: $file ####"
    echo "TIMESTAMP: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "PERMISSIONS: $perm"
    echo "SIZE_BYTES: $size"
    echo "-----------------------------------------------------------"
    cat "$file"
    echo "#### END_FILE: $file ####"
  } >> "$OUTPUT"
done

if [[ -f "check-all.log" ]] && ! is_excluded_path "check-all.log"; then
  {
    echo
    echo "#### TELEMETRY: check-all.log (Tail 100) ####"
    tail -n 100 "check-all.log"
  } >> "$OUTPUT"
fi

echo "Dump concluido: $REPO_ROOT/$OUTPUT"
