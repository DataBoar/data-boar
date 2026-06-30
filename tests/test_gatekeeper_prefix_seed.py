"""Gatekeeper prefix IP seed matching (#944 / RFC1918 FP class)."""

from __future__ import annotations

from scripts.gatekeeper_audit import _seeds_in_line, refine_strict_seed_hits


def test_prefix_ip_seed_does_not_match_longer_cidr_literal() -> None:
    seeds = ["192.168"]
    line = '    echo "192.168.40.0/24"'
    assert "192.168" not in _seeds_in_line(line, seeds)


def test_prefix_ip_seed_still_matches_standalone_prefix_token() -> None:
    seeds = ["192.168"]
    line = "subnet=192.168 "
    assert "192.168" in _seeds_in_line(line, seeds)


def test_refine_strict_seed_hits_drops_prefix_false_positive_grep_line() -> None:
    seeds = ["192.168"]
    grep_out = 'scripts/labop-firewall-lib.sh:33:    echo "192.168.0.0/16"'
    refined = refine_strict_seed_hits(grep_out, seeds)
    assert refined.strip() == ""
