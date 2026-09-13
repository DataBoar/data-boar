#!/usr/bin/env python3
"""Fail GitHub Actions ``run:`` steps that mix YAML folded scalars with ``\\``.

Folded style (``>`` / ``>-`` / ``>+``) collapses newlines to spaces. A shell
line-continuation backslash then becomes ``\\ -r`` / ``\\ -e`` and pip treats
``-r`` as a requirement (#1904 ``ci.yml``, #1906 ``wheelhouse-recipe.yml``).

This scans **source** (PyYAML drops scalar style). Literal ``|`` with ``\\``
is allowed. Folded ``run:`` without a backslash is allowed (GitHub folds
argv across lines). ``defaults.run`` mappings are ignored.

Exit: 0 ok, 1 findings, 2 tool error.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# ``run:`` then optional folded/literal indicator (GitHub Actions YAML 1.1).
_RUN_KEY = r"run:"
_FOLDED = frozenset({">", ">-", ">+"})
_LITERAL = frozenset({"|", "|-", "|+"})


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _strip_comment(raw: str) -> str:
    in_single = False
    in_double = False
    out: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
        elif ch == "#" and not in_single and not in_double:
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _style_and_remainder(after_run: str) -> tuple[str | None, str]:
    """Return (style, remainder) for a ``run:`` value; style None = mapping or plain."""
    s = after_run.strip()
    if not s:
        return None, ""
    for token in sorted(_FOLDED | _LITERAL, key=len, reverse=True):
        if s == token:
            return token, ""
        if s.startswith(token) and (len(s) == len(token) or s[len(token)].isspace()):
            return token, s[len(token) :].lstrip()
    return None, s


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _is_mapping_child(line: str, run_indent: int) -> bool:
    stripped = line.lstrip(" \t")
    if not stripped or stripped.startswith("#"):
        return False
    if _line_indent(line) <= run_indent:
        return False
    if stripped.startswith(("|", ">")):
        return False
    # Nested mapping under ``defaults: run:`` — ``working-directory:``, ``shell:``.
    if ":" in stripped and not stripped.startswith(("'", '"')):
        key = stripped.split(":", 1)[0]
        return key.replace("_", "").replace("-", "").isalnum()
    return False


def iter_folded_run_findings(text: str, path: Path) -> list[Finding]:
    lines = text.splitlines()
    findings: list[Finding] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        code = _strip_comment(raw)
        stripped = code.lstrip(" \t")
        if not stripped.startswith(_RUN_KEY):
            i += 1
            continue
        after = stripped[len(_RUN_KEY) :]
        style, remainder = _style_and_remainder(after_run=after)
        run_indent = _line_indent(code)
        start_line = i + 1
        if style is None:
            # ``defaults.run`` mapping: next non-empty line is a nested key.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _is_mapping_child(lines[j], run_indent):
                i = j
                continue
            i += 1
            continue
        if style in _LITERAL:
            i += 1
            continue
        if style not in _FOLDED:
            i += 1
            continue
        body_parts: list[str] = []
        if remainder:
            body_parts.append(remainder)
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if not nxt.strip():
                body_parts.append("")
                j += 1
                continue
            if nxt.lstrip(" \t").startswith("#") and _line_indent(nxt) <= run_indent:
                break
            if _line_indent(nxt) <= run_indent:
                break
            body_parts.append(nxt)
            j += 1
        body = "\n".join(body_parts)
        if "\\" in body:
            findings.append(
                Finding(
                    path=path,
                    line=start_line,
                    message=(
                        "folded YAML `run:` (`>` / `>-` / `>+`) must not contain "
                        r"`\`; use a literal block (`|`) so shell line continuations "
                        "keep their newlines (#1918)"
                    ),
                )
            )
        i = j
    return findings


def scan_workflows_dir(workflows_dir: Path) -> list[Finding]:
    if not workflows_dir.is_dir():
        return []
    findings: list[Finding] = []
    for path in sorted(workflows_dir.glob("*.yml")) + sorted(
        workflows_dir.glob("*.yaml")
    ):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        findings.extend(iter_folded_run_findings(text, path))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject folded YAML run: scalars that contain backslash continuations."
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=DEFAULT_WORKFLOWS_DIR,
        help="Directory of GitHub Actions workflows (default: .github/workflows)",
    )
    args = parser.parse_args(argv)
    workflows_dir = args.workflows_dir
    if not workflows_dir.is_dir():
        print(
            f"workflow_run_scalar_guard: missing directory {workflows_dir}",
            file=sys.stderr,
        )
        return 2
    findings = scan_workflows_dir(workflows_dir)
    if findings:
        print("workflow_run_scalar_guard: FAILED", file=sys.stderr)
        for item in findings:
            print(item.format(), file=sys.stderr)
        return 1
    n = len(list(workflows_dir.glob("*.yml"))) + len(list(workflows_dir.glob("*.yaml")))
    print(f"workflow_run_scalar_guard: OK ({n} workflow files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
