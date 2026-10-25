"""
Guardrail: tracked docs must not suggest the PowerShell anti-pattern of running
`.venv\\Scripts\\activate` or `.venv/Scripts/activate` without `Activate.ps1`.

In pwsh, `…\\Scripts\\activate` is not a recognized command (unlike `Activate.ps1`
or `activate` on POSIX). This test catches copy-paste errors in CONTRIBUTING,
runbooks, and rules.

See: CONTRIBUTING.md (Windows / PowerShell venv activation).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# `.venv\Scripts\activate` or `.venv/Scripts/activate` as a path segment, but
# not `.venv\Scripts\Activate.ps1` (negative lookahead after "activate").
_BAD_PWSH_ACTIVATE_PATH = re.compile(
    r"(?i)(?<!\w)\.venv[\\/]Scripts[\\/]activate(?!\.ps1)"
)

# Tracked text we scan for the bad pattern
_SCAN_SUFFIXES: frozenset[str] = frozenset({".md", ".mdc"})


def _git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    )
    return [p for p in result.stdout.decode("utf-8", errors="replace").split("\0") if p]


def _should_scan_path(rel: str) -> bool:
    low = rel.lower()
    if not any(low.endswith(s) for s in _SCAN_SUFFIXES):
        return False
    if low.startswith(
        (
            "docs/feedbacks",
            "docs/private/",
        )
    ):
        return False
    return True


def test_tracked_docs_avoid_pwsh_bare_scripts_activate_path():
    """Fail if docs teach the non-invokable `…Scripts\\activate` path for pwsh."""
    violations: list[str] = []
    for rel in _git_ls_files():
        if not _should_scan_path(rel):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _BAD_PWSH_ACTIVATE_PATH.search(text):
            violations.append(
                f"  {rel}: use .venv\\\\Scripts\\\\Activate.ps1 (or prefer uv run); "
                f"do not document .venv + Scripts + extensionless activate as one path"
            )
    assert not violations, (
        "PowerShell venv activation anti-pattern in tracked docs:\n"
        + "\n".join(sorted(violations))
    )
