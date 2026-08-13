#!/usr/bin/env bash
# scripts/labop-sudoers-load-order-lib.sh
# Pure helpers for Maestro sudoers.d load-order doctrine (maestro#6 / data-boar#1021).
#
# Doctrine:
#   - Files in /etc/sudoers.d/ are read in lexical order; the LAST matching rule wins.
#   - A generic %wheel/%sudo ALL=ALL (password) that loads AFTER a narrow labop grant
#     silently overrides NOPASSWD - sudo -l still lists NOPASSWD (masks the failure).
#   - Maestro narrow drop-ins MUST sort AFTER generic wheel (convention: z-labop-*).
#   - Test the RUN (sudo -n ...), not only sudo -l.
#
# Sourced by labop-gate-readiness.sh; also unit-tested via fixture directories.

# shellcheck shell=bash

labop_sudoers_is_skippable_dropin_name() {
  local base="$1"
  case "$base" in
    ''|README|README.*|*.md|*~|*.bak|*.dpkg-*|*.rpmnew|*.rpmsave|*.orig)
      return 0
      ;;
  esac
  # visudo editor leftovers
  case "$base" in
    .*|*.tmp)
      return 0
      ;;
  esac
  return 1
}

# stdout: generic_wheel | maestro_narrow | other
labop_sudoers_classify_dropin() {
  local path="$1"
  local base content
  base="$(basename -- "$path")"
  if labop_sudoers_is_skippable_dropin_name "$base"; then
    printf '%s\n' other
    return 0
  fi
  if [[ ! -f "$path" ]] || [[ ! -r "$path" ]]; then
    printf '%s\n' other
    return 0
  fi
  content="$(tr -d '\r' <"$path" 2>/dev/null || true)"

  # Generic password (or blanket) group grant - last-match overrides prior NOPASSWD.
  if grep -Eq '^[[:space:]]*%(wheel|sudo)[[:space:]]+ALL[[:space:]]*=\(?ALL' <<<"$content"; then
    printf '%s\n' generic_wheel
    return 0
  fi

  local looks_maestro=0
  case "$base" in
    *labop*|*LABOP*) looks_maestro=1 ;;
  esac
  if grep -Eq 'LABOP_[A-Z0-9_]+|labop-[a-z0-9_-]+-ensure\.sh|labop-dep-doctor\.sh|labop-gate-readiness\.sh' <<<"$content"; then
    looks_maestro=1
  fi
  if [[ $looks_maestro -eq 1 ]] && grep -Eq 'NOPASSWD' <<<"$content"; then
    printf '%s\n' maestro_narrow
    return 0
  fi

  printf '%s\n' other
}

# List readable drop-ins in lexical order (one basename per line).
labop_sudoers_list_dropin_basenames() {
  local dir="${1:-/etc/sudoers.d}"
  local f base
  [[ -d "$dir" ]] || return 0
  # LC_ALL=C for stable byte-wise lexical order matching sudoers.
  LC_ALL=C find "$dir" -maxdepth 1 -type f -print 2>/dev/null | LC_ALL=C sort | while IFS= read -r f; do
    base="$(basename -- "$f")"
    if labop_sudoers_is_skippable_dropin_name "$base"; then
      continue
    fi
    if [[ -r "$f" ]]; then
      printf '%s\n' "$base"
    fi
  done
}

# Print violations: one line each
#   before=<maestro_file> after=<generic_file> tip=rename_to_z-<maestro_file>
# Exit 0 if any violation, 1 if clean / unreadable / empty.
labop_sudoers_find_load_order_violations() {
  local dir="${1:-/etc/sudoers.d}"
  local -a names=()
  local -a kinds=()
  local base path kind i j
  local found=0

  if [[ ! -d "$dir" ]]; then
    return 1
  fi

  while IFS= read -r base; do
    [[ -n "$base" ]] || continue
    path="$dir/$base"
    kind="$(labop_sudoers_classify_dropin "$path")"
    names+=("$base")
    kinds+=("$kind")
  done < <(labop_sudoers_list_dropin_basenames "$dir")

  local n=${#names[@]}
  [[ $n -gt 0 ]] || return 1

  for ((i = 0; i < n; i++)); do
    [[ "${kinds[$i]}" == maestro_narrow ]] || continue
    for ((j = i + 1; j < n; j++)); do
      if [[ "${kinds[$j]}" == generic_wheel ]]; then
        found=1
        tip="rename_to_z-${names[$i]}"
        # Prefer tip that matches worked-example when base lacks z- already.
        case "${names[$i]}" in
          z-*|zz-*) tip="ensure_${names[$i]}_sorts_after_${names[$j]}" ;;
        esac
        printf 'before=%s after=%s tip=%s\n' "${names[$i]}" "${names[$j]}" "$tip"
      fi
    done
  done

  [[ $found -eq 1 ]]
}

# Emit gate-readiness style lines on stdout; never fails hard (WARN only).
# Usage: labop_sudoers_emit_gate_lines <host> [dir]
labop_sudoers_emit_gate_lines() {
  local host="$1"
  local dir="${2:-/etc/sudoers.d}"
  local line

  if [[ ! -d "$dir" ]]; then
    printf 'GR host=%s check=sudoers_load_order status=OK detail=no_sudoers_d\n' "$host"
    return 0
  fi
  if [[ ! -r "$dir" ]]; then
    printf 'GR host=%s check=sudoers_load_order status=OK detail=sudoers_d_unreadable\n' "$host"
    return 0
  fi

  local violations
  violations="$(labop_sudoers_find_load_order_violations "$dir" || true)"
  if [[ -z "$violations" ]]; then
    printf 'GR host=%s check=sudoers_load_order status=OK detail=maestro_after_wheel_or_no_conflict\n' "$host"
    return 0
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    printf 'GR host=%s check=sudoers_load_order status=WARN detail=%s lesson=test_RUN_not_sudo_l\n' "$host" "$line"
  done <<<"$violations"
}
