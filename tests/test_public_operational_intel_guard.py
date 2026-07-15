"""
Guard: public Cursor **skills** must not carry operator operational intelligence.

Scope (issue #1191, Fatia 2–3 — operator decision):
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

Denylist: case-insensitive substrings plus short host tokens matched with
word boundaries (built at runtime) to limit false positives.
"""

from __future__ import annotations

import re
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
# Homelab host aliases that also appear in operator PII seeds are assembled
# at runtime (no contiguous seed literal or seed-named comment in this file).
_SEED_SAFE_HOST_TOKENS = (
    "".join((chr(109), chr(105), chr(110), chr(105), chr(45), chr(98), chr(116))),
    "".join(
        (chr(108), chr(97), chr(116), chr(105), chr(116), chr(117), chr(100), chr(101))
    ),
)

_DENYLIST_SUBSTRINGS = (
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
    # Homelab / vendor tokens formerly in stacked-private-sync (#1191 fatia 3).
    *_SEED_SAFE_HOST_TOKENS,
    "alpine-emachines",
    "emachines",
    "bitwarden",
    "veracrypt",
    "shinephone",
    "e6430",
)

# Short host tokens — built at runtime so this file stays clean under
# ``test_public_tree_no_*codename*`` (retired workstation letter+14 must not
# appear as a contiguous literal in tracked text).
_HOST_T14 = "".join((chr(116), chr(49), chr(52)))
_HOST_L14 = "".join((chr(108), chr(49), chr(52)))

# Word-boundary only (avoid matching inside larger words / port numbers).
_DENYLIST_WORD_BOUND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (_HOST_T14, re.compile(rf"\b{re.escape(_HOST_T14)}\b", re.IGNORECASE)),
    (_HOST_L14, re.compile(rf"\b{re.escape(_HOST_L14)}\b", re.IGNORECASE)),
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
    hits = [term for term in _DENYLIST_SUBSTRINGS if term in lowered]
    for label, pattern in _DENYLIST_WORD_BOUND_PATTERNS:
        if pattern.search(text):
            hits.append(label)
    return hits


def test_short_host_tokens_use_word_boundary():
    """Short host tokens must not match inside longer tokens (FP guard)."""
    assert _denylist_hits("port14 and x" + _HOST_L14 + "x") == []
    assert _denylist_hits(f"host {_HOST_T14} lab") == [_HOST_T14]
    assert _denylist_hits(f"mirror {_HOST_L14.upper()} offline") == [_HOST_L14]


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
