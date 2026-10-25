"""Benchmark RC configs must not leave untracked SQLite files at repo root (#2064)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_GLOB = "tests/config/benchmark-*.yaml"
SQLITE_KEY = "sqlite_path"


def _relative_sqlite_paths() -> list[str]:
    paths: list[str] = []
    for cfg in sorted(REPO_ROOT.glob(CONFIG_GLOB)):
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        raw = data.get(SQLITE_KEY)
        if raw is None:
            continue
        path = str(raw).strip()
        if not path or path.startswith("/") or path.startswith("~"):
            continue
        if ".." in Path(path).parts:
            continue
        paths.append(path)
    return paths


def _gitignore_covers(path: str) -> bool:
    """True when git would ignore path at repo root (check-ignore semantics)."""
    proc = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        check=False,
    )
    return proc.returncode == 0


@pytest.mark.parametrize("sqlite_path", _relative_sqlite_paths())
def test_benchmark_sqlite_path_is_gitignored(sqlite_path: str) -> None:
    assert _gitignore_covers(sqlite_path), (
        f"{sqlite_path} from {CONFIG_GLOB} is not ignored — add a matching rule to .gitignore"
    )


def test_benchmark_configs_declare_expected_rc_databases() -> None:
    """Guard against an empty glob missing new benchmark sqlite_path keys."""
    paths = _relative_sqlite_paths()
    assert paths, f"no relative {SQLITE_KEY} entries under {CONFIG_GLOB}"
    assert any(re.fullmatch(r"audit_results_rc_v\d+\.db", p) for p in paths)
