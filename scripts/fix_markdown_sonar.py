#!/usr/bin/env python3
"""
Fix SonarQube markdown issues in project .md files (refactor only; no file removal).

Rules addressed:
- MD007: Unordered list indentation → 0 (remove 2-space indent before list marker)
- MD009: Trailing spaces → 0 or 2 (remove odd trailing spaces)
- MD012: Multiple consecutive blank lines → 1
- MD029: Ordered list prefix → 1/1/1 (all items use "1.")
- MD031: Blank lines around fenced code blocks (before/after ``` or ~~~)
- MD032: Blank lines around lists
- MD034: No bare URLs → wrap in angle brackets (skip inside fenced blocks and inline code)
- MD036: Emphasis used as heading → ## heading
- MD047: File ends with single newline
- MD060: Table column style "aligned" (pad cells so pipes align with header)

Excludes: .git, node_modules, .venv, **docs/private**, **.cursor/private**, etc. by default.
Use **`--include-private`** or env **`INCLUDE_PRIVATE_LINT=1`** to also fix Markdown under any path segment named **`private`** (e.g. ``docs/private/homelab``). `.cursor/` rules/skills stay included so `.md`/`.mdc` pass MD031, MD060, etc.

Code quality (SonarQube): avoid S6326 (prefer simple string checks over regex where possible),
S3776 (keep functions simple; extract helpers to reduce cognitive complexity), S1481 (remove
unused variables).
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        "build",
        "dist",
        "private",  # docs/private/ and any other .../private/ (skipped unless --include-private)
    }
)


def collect_md_files(*, include_private: bool = False) -> list[Path]:
    exclude = EXCLUDE_DIRS
    if include_private:
        exclude = frozenset(p for p in EXCLUDE_DIRS if p != "private")
    out: list[Path] = []
    for ext in ("*.md", "*.mdc"):
        for path in REPO_ROOT.rglob(ext):
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                continue
            if any(part in exclude for part in rel.parts):
                continue
            out.append(path)
    return sorted(set(out))


def fix_md009(line: str) -> str:
    """Trailing spaces: Expected 0 or 2; remove all (Sonar: 0 or 2 for line break)."""
    return line.rstrip()


def fix_md012(text: str) -> str:
    """Multiple consecutive blank lines → single blank."""
    return re.sub(r"\n{3,}", "\n\n", text)


def fix_md047(text: str) -> str:
    """Files should end with a single newline character."""
    text = text.rstrip("\n")
    return text + "\n"


def fix_md007_line(line: str) -> str:
    """Unordered list indentation: Expected 0; remove leading 2 spaces before - or * (top-level only)."""
    if line.startswith("  - ") or line.startswith("  * "):
        return line[2:]
    return line


def fix_md029_line(line: str) -> str:
    """Ordered list prefix: use 1. for every item (style 1/1/1)."""
    m = re.match(r"^(\s*)(\d+)\.(\s+)(.*)$", line)
    if not m:
        return line
    return f"{m.group(1)}1.{m.group(3)}{m.group(4)}"


def _is_list_line(stripped: str) -> bool:
    """True if line looks like a list item (unordered - * or ordered 1. )."""
    return bool(re.match(r"^([-*]\s|\d+\.\s)", stripped))


def _needs_blank_before_list(out: list[str], is_list: bool) -> bool:
    """True if we should insert a blank line before the current list block."""
    if not is_list or not out:
        return False
    last = out[-1].strip()
    return bool(last and not _is_list_line(last) and not last.startswith("#"))


def _needs_blank_after_list(lines: list[str], i: int, is_list: bool) -> bool:
    """True if we should insert a blank line after the current list block."""
    if not is_list or i + 1 >= len(lines):
        return False
    next_stripped = lines[i + 1].strip()
    return bool(next_stripped and not _is_list_line(next_stripped))


def fix_md032(lines: list[str]) -> list[str]:
    """Lists should be surrounded by blank lines. Insert blank before/after list blocks."""
    if not lines:
        return lines
    out: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_list = _is_list_line(stripped)
        if _needs_blank_before_list(out, is_list):
            out.append("")
        out.append(line)
        if _needs_blank_after_list(lines, i, is_list):
            out.append("")
    return out


def fix_md036_line(line: str) -> str:
    """Emphasis used instead of heading: **Bold** or *Italic* alone → ## Bold / ## Italic."""
    s = line.strip()
    if not s or len(s) > 100:
        return line
    # Standalone emphasis: **text** or *text* (single line, no other content)
    m = re.match(r"^(\*{1,2})([^*]+)\1\s*$", s)
    if m:
        return "## " + m.group(2).strip()
    return line


def parse_table_rows(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """Parse consecutive table rows (|...|). Return (rows as list of cells, end index)."""
    rows: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            break
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        rows.append(cells)
        i += 1
    return rows, i


def format_table_aligned(rows: list[list[str]]) -> list[str]:
    """Format table with aligned columns (MD060): pad cells so pipes align with header."""
    if not rows:
        return []
    num_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < num_cols:
            r.append("")
    widths = [0] * num_cols
    for r in rows:
        for c, cell in enumerate(r):
            if c < num_cols:
                widths[c] = max(widths[c], len(cell))
    out_lines: list[str] = []
    for r in rows:
        padded = [c.ljust(widths[i]) for i, c in enumerate(r)]
        out_lines.append("| " + " | ".join(padded) + " |")
    return out_lines


def fix_md060_tables(text: str) -> str:
    """Format tables to aligned column style (pipes align with header)."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            rows, j = parse_table_rows(lines, i)
            if rows:
                formatted = format_table_aligned(rows)
                out.extend(formatted)
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


# --- MD031: Blank lines around fenced code blocks ---
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def _blank_needed_after_fence(lines: list[str], after_index: int) -> bool:
    """True if the next line after after_index is non-blank (need blank after closing fence)."""
    return after_index + 1 < len(lines) and lines[after_index + 1].strip() != ""


def fix_md031(lines: list[str]) -> list[str]:
    """Ensure blank line before opening fence and after closing fence."""
    if not lines:
        return lines
    out: list[str] = []
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_fence = bool(_FENCE_RE.match(stripped))
        if is_fence:
            if not in_fence and out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            in_fence = not in_fence
            if not in_fence and _blank_needed_after_fence(lines, i):
                out.append("")
            continue
        out.append(line)
    return out


# --- MD034: No bare URLs (wrap in angle brackets) ---
# Match http:// or https:// then URL chars (no spaces, no ] ) > `)
_BARE_URL_RE = re.compile(r"(?<![<\()])(https?://[^\s\]\)\<\>`]+)(?![\]\)\>\`])")


def fix_md034_line(line: str, in_fence: bool) -> str:
    """Wrap bare URLs in angle brackets. Skip when inside fenced block or when already wrapped/linked."""
    if in_fence or "http" not in line:
        return line
    if "<http" in line or "](http" in line:
        return line

    # Do not modify inline code (backtick-wrapped)
    def repl(m: re.Match[str]) -> str:
        url = m.group(1)
        return f"<{url}>"

    return _BARE_URL_RE.sub(repl, line)


def fix_md034(text: str) -> str:
    """Wrap bare URLs in angle brackets; skip inside fenced code blocks."""
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line.strip()):
            in_fence = not in_fence
        out.append(fix_md034_line(line, in_fence))
    return "\n".join(out)


def process_file(path: Path) -> bool:
    """Apply all fixes; return True if file was changed."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    original = raw

    # MD012 first (so we work on normalized blanks)
    raw = fix_md012(raw)

    # Line-by-line fixes
    result_lines: list[str] = []
    i = 0
    lines = raw.splitlines()
    while i < len(lines):
        line = lines[i]
        # MD009
        line = fix_md009(line)
        # MD007 (unordered list indent)
        line = fix_md007_line(line)
        # MD029 (ordered list 1/1/1)
        line = fix_md029_line(line)
        # MD036 (emphasis as heading) - only for lines that look like standalone emphasis
        if re.match(r"^\s*\*+.+\*+\s*$", line) and not line.strip().startswith("#"):
            line = fix_md036_line(line)
        result_lines.append(line)
        i += 1

    # MD032: blanks around lists (operate on result_lines)
    result_lines = fix_md032(result_lines)
    # MD031: blank lines around fenced code blocks
    result_lines = fix_md031(result_lines)

    text = "\n".join(result_lines)
    # MD060: tables (re-parse and reformat)
    text = fix_md060_tables(text)
    # MD034: wrap bare URLs in angle brackets (skip inside fenced blocks)
    text = fix_md034(text)
    # MD012 again (collapse any double blanks from MD032 / MD031)
    text = fix_md012(text)
    # MD047
    text = fix_md047(text)

    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def _include_private_from_env() -> bool:
    return os.environ.get("INCLUDE_PRIVATE_LINT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix SonarQube-style markdown issues in project .md and .mdc files.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help=(
            "Also process paths under a 'private' directory segment (e.g. docs/private/). "
            "Or set INCLUDE_PRIVATE_LINT=1. Default: skip gitignored private trees."
        ),
    )
    args = parser.parse_args()
    include_private = bool(args.include_private) or _include_private_from_env()
    md_files = collect_md_files(include_private=include_private)
    changed: list[Path] = []
    for path in md_files:
        if process_file(path):
            changed.append(path)
    for p in changed:
        print(p.relative_to(REPO_ROOT))
    if changed:
        print(f"\nUpdated {len(changed)} file(s).")
    else:
        print("No files needed changes.")


if __name__ == "__main__":
    main()
