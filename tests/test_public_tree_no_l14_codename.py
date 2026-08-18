"""
Public tree must not use the retired two-letter Windows workstation codename as a word token.

Ansible paths under ops/automation/ansible are excluded (unrelated lab_node_01_* role prefixes).
The forbidden token is built at runtime so this file stays self-clean under the same guard.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_C = "".join((chr(76), chr(49), chr(52)))
WORD_FORBIDDEN = re.compile(rf"\b{re.escape(_C)}\b")


def _git_ls_text_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=REPO_ROOT, text=True, encoding="utf-8"
    )
    paths: list[Path] = []
    for line in out.splitlines():
        norm = line.replace("\\", "/")
        if "ops/automation/ansible/" in norm:
            continue
        if norm.startswith("docs/private/"):
            continue
        p = REPO_ROOT / line
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


@pytest.mark.skipif(
    not (REPO_ROOT / ".git").exists(),
    reason="not a git checkout",
)
def test_tracked_text_files_exclude_workstation_codename_word():
    hits: list[str] = []
    for p in _git_ls_text_files():
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if WORD_FORBIDDEN.search(text):
            hits.append(str(p.relative_to(REPO_ROOT)))
    assert not hits, (
        "Remove retired workstation codename token from public tree: "
        + ", ".join(sorted(hits)[:40])
    )


@pytest.mark.skipif(
    not (REPO_ROOT / ".git").exists(),
    reason="not a git checkout",
)
def test_tracked_paths_exclude_workstation_codename_in_filename():
    """No path segment in the index may contain the retired codename (case-sensitive)."""
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=REPO_ROOT, text=True, encoding="utf-8"
    )
    bad = [line for line in out.splitlines() if _C in line.replace("\\", "/")]
    assert not bad, "Rename paths that embed the retired codename: " + ", ".join(
        sorted(bad)[:40]
    )
