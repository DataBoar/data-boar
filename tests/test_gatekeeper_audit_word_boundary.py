"""Word-boundary + allowlist regression tests for the PII seed gate (issue #944).

These lock in the structural fix for the "the gated weakened the gate" incident:
a short seed must match only as a whole word (never a substring of a larger word),
the `-w` flag must stay in both matchers, and a confirmed false positive must be
silenced via the per-location allowlist -- never by loosening the matcher.
"""

from __future__ import annotations

from pathlib import Path

import scripts.gatekeeper_audit as g

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_short_seed_does_not_substring_match_larger_word() -> None:
    # Incident shape (synthetic tokens, NOT the real fragment): a short seed must
    # NOT match as a substring of a larger word (this is what reintroduced the FP).
    assert g._seeds_in_line("the Synthseed is here", ["Synth"]) == set()
    assert g._seeds_in_line('grep -qv "Synthx INPUT"', ["Synth"]) == set()


def test_whole_word_seed_still_matches() -> None:
    # Sensitivity preserved: the seed matches when it is a whole word.
    assert g._seeds_in_line("a Synth token", ["Synth"]) == {"Synth"}


def test_full_string_seed_matches() -> None:
    assert g._seeds_in_line("contact Ada Lovelace now", ["Ada Lovelace"]) == {
        "Ada Lovelace"
    }


def test_python_matcher_uses_word_boundary_flag() -> None:
    src = (REPO_ROOT / "scripts" / "gatekeeper_audit.py").read_text(encoding="utf-8")
    # The -w flag must be passed to git grep; removing it reintroduces substring FPs.
    assert '"-w",' in src


def test_powershell_twin_uses_word_boundary_flag() -> None:
    src = (REPO_ROOT / "scripts" / "gatekeeper-audit.ps1").read_text(encoding="utf-8")
    assert '"grep", "-n", "-w", "-F"' in src


def test_allowlist_suppresses_only_matching_path_and_seed() -> None:
    # Synthetic test token, NOT a real denylist seed.
    hit = "docs/x.md:5:Synthseed_Alpha here\nother.md:9:Synthseed_Alpha here"
    allowlist = [("docs/x.md", "Synthseed_Alpha")]
    out = g.filter_allowlisted(hit, ["Synthseed_Alpha"], allowlist)
    assert "docs/x.md:5" not in out
    assert "other.md:9:Synthseed_Alpha here" in out


def test_allowlist_does_not_suppress_when_another_seed_also_matches() -> None:
    # If a non-allowlisted seed is also on the line, the line still fails.
    # Tokens here are synthetic test fixtures, NOT real denylist seeds.
    hit = "docs/x.md:5:Synthseed_Alpha and Synthseed_Beta"
    allowlist = [("docs/x.md", "Synthseed_Alpha")]
    out = g.filter_allowlisted(hit, ["Synthseed_Alpha", "Synthseed_Beta"], allowlist)
    assert "docs/x.md:5" in out


def test_empty_allowlist_is_noop() -> None:
    hit = "docs/x.md:5:Synthseed_Alpha here"
    assert g.filter_allowlisted(hit, ["Synthseed_Alpha"], []) == hit
