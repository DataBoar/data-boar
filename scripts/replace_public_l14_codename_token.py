"""
Maintenance: remove the retired workstation codename token from tracked public text.

The codename is built at runtime (no contiguous token in this source file).

Run from repo root:
  uv run python scripts/replace_public_workstation_codename_token.py --dry-run
  uv run python scripts/replace_public_workstation_codename_token.py
  uv run python scripts/replace_public_workstation_codename_token.py --scan-worktree

Skips docs/private/ and ops/automation/ansible/ (role prefixes).
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Retired two-letter Windows workstation codename (avoid literal in repo source).
_C = "".join((chr(76), chr(49), chr(52)))

SUFFIXES = (
    ".md",
    ".mdc",
    ".py",
    ".ps1",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".txt",
    ".sh",
)


def _git_ls_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
    )
    lines = []
    for line in out.splitlines():
        norm = line.replace("\\", "/")
        if norm.startswith("docs/private/"):
            continue
        if "ops/automation/ansible/" in norm:
            continue
        if not any(norm.endswith(s) for s in SUFFIXES):
            continue
        lines.append(line)
    return lines


def _worktree_text_files() -> list[Path]:
    """Tracked + untracked public docs (no docs/private)."""
    found: list[Path] = []
    for base in (ROOT / ".cursor", ROOT / "docs", ROOT / "scripts", ROOT / "tests"):
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel.startswith("docs/private/"):
                continue
            if rel.startswith("docs/feedbacks"):
                continue
            if "ops/automation/ansible/" in rel:
                continue
            if p.suffix.lower() not in SUFFIXES:
                continue
            found.append(p)
    for name in ("AGENTS.md", "CONTRIBUTING.md", "README.md"):
        p = ROOT / name
        if p.is_file():
            found.append(p)
    return sorted(set(found), key=lambda x: str(x))


def _is_pt_br(path: str) -> bool:
    return ".pt_BR." in path or path.endswith("pt_BR.md")


def apply(text: str, pt_br: bool) -> str:
    generic = (
        "PC Windows principal de desenvolvimento" if pt_br else "primary Windows dev PC"
    )
    c = re.escape(_C)
    text = re.sub(
        rf"ThinkPad \*{c}\*",
        "ThinkPad *L-series (14-inch class)*",
        text,
    )
    text = re.sub(
        rf"ThinkPad {c}",
        "ThinkPad L-series (14-inch class)",
        text,
    )
    text = re.sub(rf"\*{c}\*", "*L-series*", text)
    text = re.sub(
        rf"LAB-NODE-01/{c}",
        "T-series and L-series ThinkPads",
        text,
    )
    text = re.sub(
        rf"RAM {c}\b",
        "RAM (primary dev PC)" if not pt_br else "RAM (PC principal de dev)",
        text,
    )
    text = re.sub(
        rf"WSL2 on {c}\b",
        "WSL2 on the primary Windows dev PC"
        if not pt_br
        else "WSL2 no PC Windows principal de desenvolvimento",
        text,
    )
    text = re.sub(rf"\bnon-{c}\b", "non-primary-workstation", text)
    text = re.sub(
        rf"{c}-safe",
        "primary-dev-workstation-safe"
        if not pt_br
        else "seguro no PC principal de desenvolvimento",
        text,
    )
    text = re.sub(
        rf"Windows {c}\b",
        "Windows primary dev PC"
        if not pt_br
        else "Windows (PC principal de desenvolvimento)",
        text,
    )
    text = re.sub(rf"\b{c}\b", generic, text)
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--scan-worktree",
        action="store_true",
        help="Also process untracked public paths under .cursor/, docs/, scripts/, tests/",
    )
    args = ap.parse_args()
    paths: list[Path] = []
    seen: set[str] = set()
    for rel in _git_ls_files():
        if rel not in seen:
            seen.add(rel)
            paths.append(ROOT / rel)
    if args.scan_worktree:
        for p in _worktree_text_files():
            key = p.relative_to(ROOT).as_posix()
            if key not in seen:
                seen.add(key)
                paths.append(p)
    changed: list[str] = []
    for p in sorted(paths, key=lambda x: str(x)):
        if not p.is_file():
            continue
        try:
            raw = p.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = p.relative_to(ROOT).as_posix()
        pt = _is_pt_br(rel)
        new = apply(raw, pt)
        if new != raw:
            changed.append(rel)
            if not args.dry_run:
                p.write_text(new, encoding="utf-8", newline="\n")
    print(f"{'Would change' if args.dry_run else 'Changed'} {len(changed)} files")
    for c in sorted(changed):
        print(c)


if __name__ == "__main__":
    main()
