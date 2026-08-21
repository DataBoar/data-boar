#!/usr/bin/env python3
"""Fail if a pytest JUnit report skipped more tests than the extras-job ceiling (#1638).

The default Linux CI matrix installs only ``--extra shares``. Optional connectors
then ``pytest.skip`` / ``importorskip`` in silence. The dedicated extras job
installs SQL extras except ``mariadb`` (CPython 3.13 SyntaxError in upstream
1.1.14), plus ``nosql`` + ``compressed`` + ``dataformats``, deselects
``MAESTRO_ROOT``-gated tests (public CI / maestro#8), and must keep the
remaining skip count under a declared ceiling so a new extra cannot hide again
without a workflow change.

Exit codes: 0 within ceiling, 1 over ceiling or missing report, 2 usage/parse error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import defusedxml.ElementTree as ET

# Keep in sync with ``.github/workflows/ci.yml`` extras job ``--max-skipped``.
# Calibrated from extras job 989a4a3f (skipped=106 minus 56 MAESTRO_ROOT guards
# = 50 remainder, JUnit counts 1 xfail as skip) plus +10 slack.
DEFAULT_MAX_SKIPPED = 60


def skipped_count(junit_path: Path) -> int:
    """Return the skip total from a pytest ``--junitxml`` report.

    Prefers the ``skipped`` attribute on ``testsuite`` / ``testsuites`` nodes.
    Falls back to counting ``<skipped/>`` children when attributes are absent.
    """
    tree = ET.parse(junit_path)
    root = tree.getroot()
    saw_attr = False
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag not in {"testsuite", "testsuites"}:
            continue
        if "skipped" in node.attrib:
            saw_attr = True
            break
    if saw_attr:
        # Nested ``testsuites`` + child ``testsuite`` would double-count; prefer
        # the outermost node that declared ``skipped``.
        outer = root.attrib.get("skipped")
        if outer is not None:
            return int(outer)
        suites = [
            n
            for n in root.iter()
            if n.tag.rsplit("}", 1)[-1] == "testsuite" and "skipped" in n.attrib
        ]
        if len(suites) == 1:
            return int(suites[0].attrib["skipped"])
        return sum(int(n.attrib["skipped"]) for n in suites)

    skipped_nodes = 0
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "skipped":
            skipped_nodes += 1
    return skipped_nodes


def evaluate(skipped: int, max_skipped: int) -> int:
    """Return 0 if ``skipped`` is within the ceiling, else 1."""
    if skipped > max_skipped:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "junitxml",
        type=Path,
        help="Path to pytest --junitxml output",
    )
    parser.add_argument(
        "--max-skipped",
        type=int,
        default=DEFAULT_MAX_SKIPPED,
        help=f"Fail when skipped tests exceed this (default {DEFAULT_MAX_SKIPPED})",
    )
    args = parser.parse_args(argv)
    path = args.junitxml
    if not path.is_file():
        print(f"ci_pytest_skip_ceiling: missing JUnit report: {path}", file=sys.stderr)
        return 1
    try:
        skipped = skipped_count(path)
    except (ET.ParseError, ValueError) as exc:
        print(f"ci_pytest_skip_ceiling: cannot parse {path}: {exc}", file=sys.stderr)
        return 2
    rc = evaluate(skipped, args.max_skipped)
    print(f"ci_pytest_skip_ceiling: skipped={skipped} max={args.max_skipped}")
    if rc != 0:
        print(
            "ci_pytest_skip_ceiling: skip count exceeded ceiling "
            "(new optional extra hiding tests, or raise --max-skipped with evidence).",
            file=sys.stderr,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
