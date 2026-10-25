"""Release/version policy guards (#978, ADR-0072/0073).

- While release gate #406 is OPEN: pyproject version must be pre-release.
- Denylist phantom version strings (e.g. 1.7.5) in tracked files.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import tomllib
import yaml
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "security" / "version_policy.yaml"


def _tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [REPO_ROOT / part for part in out.stdout.decode("utf-8").split("\0") if part]


def _load_policy() -> dict:
    with POLICY_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _project_version() -> str:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


def test_release_gate_open_requires_prerelease_on_main() -> None:
    """Stable-looking pyproject version blocked while release gate is open."""
    policy = _load_policy()
    gate = policy.get("release_gate") or {}
    if not gate.get("open"):
        pytest.skip("release_gate.open is false — operator closed #406")

    version = Version(_project_version())
    assert version.is_prerelease, (
        f"release gate #{gate.get('issue_number', 406)} is OPEN but "
        f"pyproject.toml version {version} is not pre-release (-beta/-rc). "
        "See ADR-0072 and docs/VERSIONING.md."
    )


def test_forbidden_version_literals_absent_from_tracked_files() -> None:
    """Denylist strings (phantom roadmap) must not appear outside allowlisted paths."""
    policy = _load_policy()
    forbidden: list[str] = list(policy.get("forbidden_version_literals") or [])
    allow_substrings: list[str] = list(
        policy.get("scan_allowlist_path_substrings") or []
    )

    hits: list[str] = []
    for path in _tracked_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if any(sub in rel for sub in allow_substrings):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for literal in forbidden:
            if literal in text:
                hits.append(f"{rel}: contains forbidden {literal!r}")

    assert not hits, "Forbidden version literals found:\n" + "\n".join(hits)
