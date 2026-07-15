"""
Markdown lint tests aligned with SonarQube / markdownlint rules.

Checks project .md and .mdc files for:
- MD009: No trailing spaces at end of line
- MD012: No multiple consecutive blank lines (max 1)
- MD024: No duplicate heading text in the same file (sibling headings)
- MD036: No emphasis-only line used as a heading (use ## instead of **Bold**)
- MD051: Link fragments (anchors) use valid format: no spaces, safe characters
- MD060: Fenced code blocks use consistent marker (all ``` or all ~~~)
- MD031: Blanks around fences (blank line before/after fenced code blocks)
- MD034: No bare URLs (wrap in angle brackets or use [text](url); skip inside code blocks)
- Table (compact): No space to the left of pipe (e.g. |col not | col)

Excludes: paths in MARKDOWN_LINT_EXCLUDE only (.git, node_modules, .venv, **private**, etc.) by default.
Collection uses **git-tracked** ``*.md`` / ``*.mdc`` (``git ls-files``) so local equals CI (#1240);
filesystem ``rglob`` is a fallback only when git is unavailable.
Pass **``pytest --include-private``** or set **``INCLUDE_PRIVATE_LINT=1``** to lint **``docs/private/``** too (see ``tests/conftest.py``). .cursor/ is included so rules and skills (.mdc, SKILL.md) comply with MD031, MD060, etc.
"""

import re
import subprocess
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _collect_md_files_via_rglob(root: Path, exclude_dirs: frozenset[str]) -> list[Path]:
    """Filesystem walk fallback when git is unavailable (e.g. tarball tree)."""
    out: list[Path] = []
    for ext in ("*.md", "*.mdc"):
        for path in root.rglob(ext):
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            if any(part in exclude_dirs for part in rel.parts):
                continue
            out.append(path)
    return out


def _collect_md_files(root: Path, exclude_dirs: frozenset[str]) -> list[Path]:
    """Return .md/.mdc paths under root that are git-tracked (local == CI).

    Falls back to ``rglob`` when ``git ls-files`` is unavailable (#1240), so
    tarball / non-git trees still lint. Always honor ``exclude_dirs`` (e.g.
    conditional ``private``).
    """
    out: list[Path] = []
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z", "*.md", "*.mdc"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        raw = proc.stdout.split(b"\0")
        for entry in raw:
            if not entry:
                continue
            rel = Path(entry.decode("utf-8", errors="replace"))
            if any(part in exclude_dirs for part in rel.parts):
                continue
            out.append(root / rel)
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        out = _collect_md_files_via_rglob(root, exclude_dirs)
    return sorted(set(out))


def _markdown_lint_skip_ephemeral_root_markdown(root: Path, path: Path) -> bool:
    """Root-level executive desk Markdown from local runs (gitignored; not maintained to docs bar)."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) != 1:
        return False
    return rel.name.startswith("POC_SUMMARY_") and rel.suffix.lower() == ".md"


# Exclude tooling/dependency dirs and docs/private (git-ignored user content; not part of repo lint).
# .cursor is included so rules/skills pass MD031, MD060, etc.
MARKDOWN_LINT_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        "build",
        "dist",
        "private",
        # External review copies (e.g. Corporate-Entity-C); not maintained to markdownlint bar.
        "feedbacks, reviews, comments and criticism",
        # Shallow clones of external GitHub repos (local polish; not part of Data Boar CI docs bar).
        "_upstream_rust_sgad",
        "_upstream_python_sgad",
        "_upstream_go_sgat",
        "_upstream_wf_t1r",
        "_upstream_batch_reload_ap",
        "_upstream_bash_localiza_danfe_por_id_de_upload",
    }
)

# Paths (relative to repo root) skipped by MD009–MD060: nested ``` inside ````markdown` breaks the
# naive fence toggle in _check_md031; content is a Docker Hub paste template, not normal docs flow.
MARKDOWN_LINT_EXCLUDE_FILES = frozenset(
    {
        "docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md",
    }
)


def _markdown_lint_exclude_dirs(*, include_private: bool) -> frozenset[str]:
    """Effective exclude set; omit ``private`` when operator opts in."""
    if include_private:
        return frozenset(p for p in MARKDOWN_LINT_EXCLUDE_DIRS if p != "private")
    return MARKDOWN_LINT_EXCLUDE_DIRS


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --- MD009: Trailing spaces ---


def _check_md009(text: str) -> list[tuple[int, str]]:
    """Return (line_number, "MD009: trailing spaces") for each violation."""
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if line.endswith(" ") or line.endswith("\t"):
            violations.append((i, "MD009: trailing spaces"))
    return violations


# --- MD012: Multiple consecutive blank lines ---


def _check_md012(text: str) -> list[tuple[int, str]]:
    """Return (line_number, "MD012: multiple consecutive blank lines") for each violation."""
    violations: list[tuple[int, str]] = []
    lines = text.splitlines()
    blank_count = 0
    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            blank_count += 1
            if blank_count >= 2:
                violations.append((i, "MD012: multiple consecutive blank lines"))
        else:
            blank_count = 0
    return violations


# --- MD024: Duplicate heading content ---


def _check_md024(text: str) -> list[tuple[int, str]]:
    """Return (line_number, "MD024: duplicate heading") for duplicate heading text (case-insensitive). Skip inside fenced code blocks."""
    violations: list[tuple[int, str]] = []
    heading_re = re.compile(r"^#{1,6}\s+(.+)$")
    seen: dict[str, int] = {}
    in_fence = False
    fence_char = ""
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_fence:
                in_fence = True
                fence_char = stripped[:3]
            elif stripped.startswith(fence_char):
                in_fence = False
            continue
        if in_fence:
            continue
        m = heading_re.match(stripped)
        if not m:
            continue
        content = m.group(1).strip()
        normalized = content.lower()
        if normalized in seen:
            violations.append(
                (
                    i,
                    f"MD024: duplicate heading (same as line {seen[normalized]}): {content!r}",
                )
            )
        else:
            seen[normalized] = i
    return violations


# --- MD036: Emphasis used instead of heading ---


def _is_standalone_emphasis_heading(
    lines: list[str], idx: int, emphasis_only_re: re.Pattern[str]
) -> bool:
    """True if line at idx is a short emphasis-only line with blank before/after (or file boundary)."""
    s = lines[idx].strip()
    if not s or len(s) > 80 or not emphasis_only_re.match(s):
        return False
    before = lines[idx - 1].strip() if idx >= 1 else ""
    after = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
    return (idx == 0 or not before) and (idx >= len(lines) - 1 or not after)


def _check_md036(text: str) -> list[tuple[int, str]]:
    """Flag lines that are only emphasis (e.g. **Bold.**) as if a heading. Exclude labels (colon), list, blockquote, table."""
    violations: list[tuple[int, str]] = []
    emphasis_only_re = re.compile(
        r"^\s*(\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_)\s*\.?\s*$"
    )
    lines = text.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or ":" in s or "|" in line:
            continue
        if (
            s.startswith(">")
            or re.match(r"^[\s]*[-*+]\s", line)
            or re.match(r"^[\s]*\d+\.\s", line)
        ):
            continue
        if _is_standalone_emphasis_heading(lines, i, emphasis_only_re):
            violations.append(
                (i + 1, "MD036: emphasis used instead of heading (use ## instead)")
            )
    return violations


# --- MD051: Link fragment (anchor) format ---


def _check_md051(text: str) -> list[tuple[int, str]]:
    """Flag link targets that are fragments but contain spaces (invalid anchor)."""
    violations: list[tuple[int, str]] = []
    link_re = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    for i, line in enumerate(text.splitlines(), start=1):
        for _label, target in link_re.findall(line):
            target = target.strip()
            if "#" not in target:
                continue
            _path, _, fragment = target.partition("#")
            if not fragment:
                continue
            if " " in fragment or "\t" in fragment:
                violations.append(
                    (i, f"MD051: link fragment contains spaces: {fragment!r}")
                )
                break
    return violations


# --- MD060: Consistent fenced code block markers ---


def _check_md060(text: str) -> list[tuple[int, str]]:
    """Flag mixed code fence styles (e.g. ``` and ~~~ in same file)."""
    violations: list[tuple[int, str]] = []
    fence_re = re.compile(r"^(\s*)(`{3,}|~{3,})\s*(\S*)\s*$")
    fences: set[str] = set()
    for i, line in enumerate(text.splitlines(), start=1):
        m = fence_re.match(line)
        if not m:
            continue
        fence = m.group(2)
        fences.add(fence[0])  # '`' or '~'
    if len(fences) > 1:
        violations.append(
            (1, "MD060: use consistent fenced code block markers (all ``` or all ~~~)")
        )
    return violations


# --- MD031: Blanks around fences ---


def _md031_violation_at(
    lines: list[str], idx: int, in_fence: bool
) -> tuple[int, str] | None:
    """Return (line_no, message) if this fence line violates MD031, else None."""
    if not in_fence:
        if idx > 0 and lines[idx - 1].strip() != "":
            return (idx + 1, "MD031: blank line required before fenced code block")
    else:
        if idx + 1 < len(lines) and lines[idx + 1].strip() != "":
            return (idx + 1, "MD031: blank line required after fenced code block")
    return None


def _check_md031(text: str) -> list[tuple[int, str]]:
    """Fenced code blocks should be surrounded by blank lines."""
    violations: list[tuple[int, str]] = []
    lines = text.splitlines()
    fence_re = re.compile(r"^\s*(`{3,}|~{3,})")
    in_fence = False
    for i, line in enumerate(lines):
        if not fence_re.match(line.strip()):
            continue
        v = _md031_violation_at(lines, i, in_fence)
        if v:
            violations.append(v)
        in_fence = not in_fence
    return violations


# --- MD034: No bare URLs ---


def _check_md034(text: str) -> list[tuple[int, str]]:
    """Bare http(s):// URLs should be wrapped in angle brackets or links. Skip inside fenced code blocks."""
    violations: list[tuple[int, str]] = []
    lines = text.splitlines()
    in_fence = False
    fence_re = re.compile(r"^\s*(`{3,}|~{3,})")
    for i, line in enumerate(lines):
        if fence_re.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence or ("http://" not in line and "https://" not in line):
            continue
        if "<http" in line or "](http" in line:
            continue
        if re.search(r"`[^`]*https?://[^`]*`", line):
            continue
        violations.append(
            (i + 1, "MD034: bare URL used (wrap in <...> or [text](url))")
        )
    return violations


# --- Table: MD060 aligned style accepted (no check; Sonar + scripts/fix_markdown_sonar.py enforce) ---
# SonarQube MD060 expects "aligned" table column style (pipes align with header).
# We no longer require "compact" (no space left of pipe) so aligned tables from fix_markdown_sonar.py pass.


def _check_table_pipe_space(_text: str) -> list[tuple[int, str]]:
    """No violation: table style is enforced by Sonar and scripts/fix_markdown_sonar.py (MD060 aligned)."""
    return []


def _lint_one(path: Path) -> list[tuple[int, str]]:
    """Run all checks on one file. Returns list of (line, message)."""
    text = _read_md(path)
    out: list[tuple[int, str]] = []
    out.extend(_check_md009(text))
    out.extend(_check_md012(text))
    out.extend(_check_md024(text))
    out.extend(_check_md036(text))
    out.extend(_check_md051(text))
    out.extend(_check_md060(text))
    out.extend(_check_md031(text))
    out.extend(_check_md034(text))
    out.extend(_check_table_pipe_space(text))
    return out


def test_markdown_lint_no_violations(include_private_lint: bool):
    """
    All project .md files (except excluded dirs) pass MD009, MD012, MD024, MD036, MD051, MD060, MD031, MD034.
    Table style: SonarQube MD060 (aligned) is enforced via scripts/fix_markdown_sonar.py; test does not check table pipes.

    SonarQube / markdownlint-style quality so CI catches regressions.

    Opt-in: ``pytest --include-private`` or ``INCLUDE_PRIVATE_LINT=1`` to include ``docs/private/``.
    """
    root = _project_root()
    exclude = _markdown_lint_exclude_dirs(include_private=include_private_lint)
    md_files = _collect_md_files(root, exclude)
    md_files = [
        p
        for p in md_files
        if p.relative_to(root).as_posix() not in MARKDOWN_LINT_EXCLUDE_FILES
        and not _markdown_lint_skip_ephemeral_root_markdown(root, p)
    ]
    all_violations: list[tuple[Path, int, str]] = []
    for path in md_files:
        for line_no, msg in _lint_one(path):
            all_violations.append((path, line_no, msg))
    lines = []
    for path, line_no, msg in sorted(all_violations, key=lambda x: (str(x[0]), x[1])):
        rel = path.relative_to(root)
        lines.append(f"  {rel}:{line_no} {msg}")
    assert not all_violations, "Markdown lint violations:\n" + "\n".join(lines)
