"""
Guardrail: sensitive commercial / client-specific material must not be Git-tracked.

**Policy (summary):** Drafts and studies with **pricing**, **client-specific** terms, **strategic**
market notes that could help competitors, or similar **confidential** content belong only under
**`docs/private/`** (gitignored). The **only** tracked `commercial` path is
**`docs/private.example/commercial/`** — layout pointers **without** real numbers or client facts.

**Regression:** If someone force-adds `docs/private/...` or creates `docs/.../commercial/...`
outside the example tree, or uses forbidden **study filenames** under tracked `docs/`, CI fails.

See **`docs/PRIVATE_OPERATOR_NOTES.md`**, **`.cursor/rules/confidential-commercial-never-tracked.mdc`**,
and **`docs/private.example/commercial/README.md`**.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Tracked template only — any other `.../commercial/...` under docs/ is forbidden.
_COMMERCIAL_EXAMPLE_PREFIX = "docs/private.example/commercial/"

# Basename fragments (case-insensitive) that must not appear in tracked files under docs/
# (except under docs/private.example/, which only holds the layout README).
_FORBIDDEN_NAME_MARKERS = (
    "MATURITY_CONSULTING_PRICING",
    "PRICING_STUDY",
    "RATE_CARD",
    "COMMERCIAL_CONFIDENTIAL",
)


def _git_ls_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not (REPO_ROOT / ".git").exists():
        pytest.skip(
            "Not a git checkout or git ls-files failed — cannot enforce index guard."
        )
    raw = proc.stdout.split(b"\0")
    out: list[str] = []
    for chunk in raw:
        if not chunk:
            continue
        out.append(chunk.decode("utf-8", errors="replace").replace("\\", "/"))
    return out


def _forbidden_commercial_path_segments(posix_path: str) -> bool:
    """True if `commercial` appears as a path segment outside the allowed example prefix."""
    if posix_path.startswith(_COMMERCIAL_EXAMPLE_PREFIX):
        return False
    parts = posix_path.split("/")
    return "commercial" in parts


def _docs_forbidden_basename(posix_path: str) -> bool:
    if not posix_path.startswith("docs/"):
        return False
    if posix_path.startswith("docs/private.example/"):
        return False
    name = posix_path.rsplit("/", 1)[-1]
    upper = name.upper()
    return any(marker in upper for marker in _FORBIDDEN_NAME_MARKERS)


def test_git_index_excludes_private_trees_and_stray_commercial_docs():
    violations: list[str] = []
    tracked = _git_ls_files()

    for p in tracked:
        if p.startswith("docs/private/"):
            violations.append(f"tracked path must not be under docs/private/: {p}")
        if p.startswith(".cursor/private/"):
            violations.append(f"tracked path must not be under .cursor/private/: {p}")
        if p.startswith("docs/") and _forbidden_commercial_path_segments(p):
            violations.append(
                f"tracked docs path contains segment 'commercial' outside {_COMMERCIAL_EXAMPLE_PREFIX}: {p}"
            )
        if _docs_forbidden_basename(p):
            violations.append(
                f"tracked docs file basename matches confidential commercial filename guard: {p}"
            )

    if violations:
        joined = "\n".join(violations)
        raise AssertionError(
            "Confidential commercial guard failed — move content to gitignored docs/private/ "
            "and keep only templates under docs/private.example/.\n" + joined
        )


def test_gitignore_documents_private_trees():
    """Sanity: .gitignore must keep docs/private/ and .cursor/private/ ignored."""
    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    lines = {
        ln.strip()
        for ln in gi.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    }
    assert "docs/private/" in lines, ".gitignore must list docs/private/"
    assert ".cursor/private/" in lines, ".gitignore must list .cursor/private/"
