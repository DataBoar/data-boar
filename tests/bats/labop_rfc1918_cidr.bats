#!/usr/bin/env bats
# Unit tests for labop_is_rfc1918_cidr (#1926, #1020).

load helpers

setup() {
  # shellcheck source=/dev/null
  source "$REPO_ROOT/scripts/labop-rfc1918-cidr-lib.sh"
}

@test "accepts 10.0.0.0/8" {
  run labop_is_rfc1918_cidr 10.0.0.0/8
  [ "$status" -eq 0 ]
}

@test "accepts 172.16.0.0/12" {
  run labop_is_rfc1918_cidr 172.16.0.0/12
  [ "$status" -eq 0 ]
}

@test "accepts class-C private /24" {
  run labop_is_rfc1918_cidr 192.168.1.0/24
  [ "$status" -eq 0 ]
}

@test "rejects empty input" {
  run labop_is_rfc1918_cidr ""
  [ "$status" -eq 1 ]
}

@test "rejects public CIDR" {
  run labop_is_rfc1918_cidr 8.8.8.0/24
  [ "$status" -eq 1 ]
}

@test "rejects 192.x non-168 second octet" {
  run labop_is_rfc1918_cidr 192.10.1.0/24
  [ "$status" -eq 1 ]
}
