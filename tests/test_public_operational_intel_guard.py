"""
Guard: public Cursor **skills** must not carry operator operational intelligence.

Scope (issue #1191, Fatia 2 — operator decision):
  - Scan **only** tracked files under ``.cursor/skills/`` (``git ls-files``).
  - Do **not** scan ``.cursor/rules/``. Keyword shorthands in
    ``session-mode-keywords.mdc`` and ``lab-op-systems-context.mdc`` are
    **intentionally public** so the agent can discover session keywords; the
    real runbooks live under gitignored ``.cursor/private/skills/`` and
    ``docs/private/``.

Allowlist:
  - File paths under ``docs/private/`` or ``docs/private.example/`` (policy
    reserved; not under the skills tree today).
  - Product skill ``.cursor/skills/sensitive-data-detection/`` — cites PII terms
    as **detection examples**, not operator personal data.

Denylist terms are case-insensitive substrings. A hit outside the allowlist fails CI.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_SKILLS_PREFIX = ".cursor/skills/"

# Path prefixes that skip the denylist (posix, trailing slash).
_ALLOWLIST_PATH_PREFIXES = (
    "docs/private/",
    "docs/private.example/",
    ".cursor/skills/sensitive-data-detection/",
)

# Case-insensitive operational-intel substrings forbidden in public skills.
_DENYLIST_TERMS = (
    "gmail",
    "@gmail",
    "enel",
    "growatt",
    "lab-router",
    "warm session",
    "linkedin",
    "candidate",
    # Real GPG key-id fragments formerly tracked in gpg-key-lifecycle skill.
    "871542e6",
    "ad93917a",
)


def _git_ls_files(*pathspecs: str) -> list[str]:
    cmd = ["git", "ls-files", "-z", "--", *pathspecs]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not (REPO_ROOT / ".git").exists():
        pytest.skip(
            "Not a git checkout or git ls-files failed — cannot enforce skills guard."
        )
    out: list[str] = []
    for chunk in proc.stdout.split(b"\0"):
        if not chunk:
            continue
        out.append(chunk.decode("utf-8", errors="replace").replace("\\", "/"))
    return out


def _is_allowlisted(posix_path: str) -> bool:
    return any(posix_path.startswith(prefix) for prefix in _ALLOWLIST_PATH_PREFIXES)


def _denylist_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in _DENYLIST_TERMS if term in lowered]


def test_public_cursor_skills_have_no_operational_intel():
    """Tracked `.cursor/skills/**` must not contain denylist operational terms."""
    tracked = _git_ls_files(_SKILLS_PREFIX)
    assert tracked, "Expected tracked files under .cursor/skills/"

    violations: list[str] = []
    for posix_path in tracked:
        if not posix_path.startswith(_SKILLS_PREFIX):
            continue
        if _is_allowlisted(posix_path):
            continue
        path = REPO_ROOT / posix_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            violations.append(f"{posix_path}: unreadable ({exc})")
            continue
        hits = _denylist_hits(text)
        if hits:
            violations.append(f"{posix_path}: denylist hit(s) {hits!r}")

    assert not violations, (
        "Public `.cursor/skills/` must not embed operator operational intelligence "
        "(#1191). Move runbooks to `.cursor/private/skills/` or strip terms. "
        "Product skill `sensitive-data-detection` is allowlisted. "
        "Rules with keyword shorthands stay out of this guard by design.\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
