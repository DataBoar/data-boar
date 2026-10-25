#!/usr/bin/env bats
# Argument parsing surface for scripts/demo.sh (#1926) — help only; no scan execution.

load helpers

@test "demo.sh --help prints usage and exits 0" {
  run bash "$REPO_ROOT/scripts/demo.sh" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"--no-web"* ]]
  [[ "$output" == *"--headless"* ]]
}

@test "demo.sh -h prints usage and exits 0" {
  run bash "$REPO_ROOT/scripts/demo.sh" -h
  [ "$status" -eq 0 ]
  [[ "$output" == *"demo.sh"* ]]
}
