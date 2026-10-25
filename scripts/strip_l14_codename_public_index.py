"""
One-off / maintenance: replace standalone workstation codename token in tracked text.

Run from repo root after review:
  uv run python scripts/strip_workstation_codename_public_index.py --dry-run
  uv run python scripts/strip_workstation_codename_public_index.py

Skips ops/automation/ansible (role prefixes lab_node_01_* are unrelated).
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_C = "".join((chr(76), chr(49), chr(52)))
WORD_FORBIDDEN = re.compile(rf"\b{re.escape(_C)}\b")


def _iter_text_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
    )
    paths: list[Path] = []
    for line in out.splitlines():
        if "ops/automation/ansible" in line.replace("\\", "/"):
            continue
        p = ROOT / line
        if p.suffix.lower() not in (
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
        ):
            continue
        paths.append(p)
    return paths


def _replacement_for(path: Path) -> str:
    s = str(path).replace("\\", "/")
    if ".pt_BR." in s or s.endswith("pt_BR.md"):
        return "PC de desenvolvimento principal"
    return "primary dev PC"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changed = []
    for p in _iter_text_files():
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if not WORD_FORBIDDEN.search(text):
            continue
        repl = _replacement_for(p)
        new = WORD_FORBIDDEN.sub(repl, text)
        if new == text:
            continue
        rel = p.relative_to(ROOT)
        changed.append(str(rel))
        if not args.dry_run:
            p.write_text(new, encoding="utf-8", newline="\n")
    print(f"{'Would change' if args.dry_run else 'Changed'} {len(changed)} files")
    for c in sorted(changed):
        print(c)


if __name__ == "__main__":
    main()
