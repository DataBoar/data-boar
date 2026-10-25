"""Case-collision guard (#2044): lowercased ``git ls-files`` paths must be unique."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.check_case_collisions import colliding_groups

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_case_pair_fails_and_names_both_paths() -> None:
    groups = colliding_groups(["A.md", "a.md", "other.txt"])
    assert groups == [("A.md", "a.md")]


def test_no_collision_passes() -> None:
    assert colliding_groups(["README.md", "docs/USAGE.md"]) == []


def test_space_and_accent_path_is_not_a_collision() -> None:
    paths = ["docs/ação final.md", "docs/other file.md"]
    assert colliding_groups(paths) == []


def test_check_all_twins_invoke_case_collision_guard() -> None:
    sh = (REPO_ROOT / "scripts" / "check-all.sh").read_text(encoding="utf-8")
    ps1 = (REPO_ROOT / "scripts" / "check-all.ps1").read_text(encoding="utf-8")
    for text in (sh, ps1):
        assert "scripts/check_case_collisions.py" in text.replace("\\", "/")
        assert "ABORTED by check_case_collisions" in text


def test_repo_tracked_tree_has_no_case_collision() -> None:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_case_collisions.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "check_case_collisions: OK" in proc.stdout
