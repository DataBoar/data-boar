"""pre-commit ruff hook rev must meet pyproject.toml ruff floor (#491)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from packaging.version import Version

_REPO = Path(__file__).resolve().parents[1]


def test_ruff_pre_commit_rev_meets_pyproject_floor() -> None:
    pyproject = (_REPO / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'"ruff>=([^"]+)"', pyproject)
    assert m, "expected ruff>= floor in pyproject.toml"
    floor = Version(m.group(1))

    cfg = yaml.safe_load(
        (_REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    ruff_rev: str | None = None
    for repo in cfg.get("repos") or []:
        if repo.get("repo") == "https://github.com/astral-sh/ruff-pre-commit":
            ruff_rev = str(repo.get("rev") or "")
            break
    assert ruff_rev, "ruff-pre-commit repo missing from .pre-commit-config.yaml"
    assert ruff_rev.startswith("v"), ruff_rev
    hooked = Version(ruff_rev[1:])
    assert hooked >= floor, (
        f"pre-commit {ruff_rev} is below pyproject floor ruff>={floor}"
    )

    # 0.16 default rule set is wider than 0.15; keep classic select (#491).
    assert 'select = ["E4", "E7", "E9", "F"]' in pyproject
