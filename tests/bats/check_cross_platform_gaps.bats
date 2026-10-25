#!/usr/bin/env bats
# Hermetic checks for scripts/check-cross-platform-gaps.sh (#1926).

load helpers

@test "check-cross-platform-gaps.sh --missing-only exits 0" {
  run bash "$REPO_ROOT/scripts/check-cross-platform-gaps.sh" --missing-only
  [ "$status" -eq 0 ]
}

@test "check-cross-platform-gaps.sh -MissingOnly alias exits 0" {
  run bash "$REPO_ROOT/scripts/check-cross-platform-gaps.sh" -MissingOnly
  [ "$status" -eq 0 ]
}

@test "check-cross-platform-gaps.sh default (no args) exits 0" {
  run bash "$REPO_ROOT/scripts/check-cross-platform-gaps.sh"
  [ "$status" -eq 0 ]
}
