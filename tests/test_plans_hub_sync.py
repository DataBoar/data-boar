"""Guardrail: PLANS_HUB.md auto-table lists every PLAN_*.md file."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HUB_PATH = REPO_ROOT / "docs" / "plans" / "PLANS_HUB.md"
START = "<!-- PLANS_HUB_TABLE:START -->"
END = "<!-- PLANS_HUB_TABLE:END -->"


def _load_plans_hub_sync():
    path = REPO_ROOT / "scripts" / "plans_hub_sync.py"
    spec = importlib.util.spec_from_file_location("plans_hub_sync", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_plans_hub_table_lists_every_plan_file() -> None:
    mod = _load_plans_hub_sync()
    text = HUB_PATH.read_text(encoding="utf-8")
    assert START in text and END in text
    inner = text.split(START, 1)[1].split(END, 1)[0]
    for path, prefix in mod.discover_plan_files():
        needle = f"]({prefix}{path.name})"
        assert needle in inner, f"missing hub row for {prefix}{path.name}"


def test_plans_hub_table_matches_script_output() -> None:
    mod = _load_plans_hub_sync()
    text = HUB_PATH.read_text(encoding="utf-8")
    inner = text.split(START, 1)[1].split(END, 1)[0].strip("\n") + "\n"
    assert inner == mod.compute_table_block()


def test_plans_hub_sync_check_cli() -> None:
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "plans_hub_sync.py"), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
