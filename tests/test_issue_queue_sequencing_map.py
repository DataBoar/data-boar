"""Guardrail: ISSUE_QUEUE_SEQUENCING_MAP.md matches scripts/issue_queue_sequencing_map.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / "docs" / "ops" / "ISSUE_QUEUE_SEQUENCING_MAP.md"


def _load_mod():
    path = REPO_ROOT / "scripts" / "issue_queue_sequencing_map.py"
    spec = importlib.util.spec_from_file_location("issue_queue_sequencing_map", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_issue_queue_map_has_required_sections() -> None:
    text = MAP_PATH.read_text(encoding="utf-8")
    for needle in (
        "**Total open issues:**",
        "Issue Type Bug / Feature / Task",
        "## Hard-blockers (active)",
        "### Stale `NÃO INICIAR` text",
        "```mermaid",
    ):
        assert needle in text, f"missing section marker: {needle!r}"


def test_scan_blockers_detects_active_and_stale() -> None:
    mod = _load_mod()
    issues = [
        {
            "number": 10,
            "title": "blocked",
            "body": "NÃO INICIAR ANTES DE #9",
        },
        {
            "number": 20,
            "title": "stale cite",
            "body": "NÃO INICIAR ANTES DE #99",
        },
        {"number": 9, "title": "blocker", "body": ""},
    ]

    def fake_state(number: int, cache: dict[int, str]) -> str:
        if number == 99:
            return "CLOSED"
        return cache.get(number, "OPEN")

    mod._issue_state = fake_state  # type: ignore[method-assign]
    active, stale = mod._scan_blockers(issues)
    assert active == {9: [10]}
    assert stale == [(20, 99)]


def test_issue_queue_sequencing_map_check_mode_offline(
    tmp_path: Path, monkeypatch
) -> None:
    """--check must not call live gh (CI has no GH_TOKEN on the test job)."""
    mod = _load_mod()
    fake_issues = [
        {
            "number": 42,
            "title": "sample",
            "body": "",
            "issueType": {"name": "Task"},
            "milestone": {"title": "v1.8.0"},
            "labels": {"nodes": [{"name": "[P2]"}]},
        },
    ]
    monkeypatch.setattr(mod, "fetch_open_issues", lambda: fake_issues)
    map_path = tmp_path / "ISSUE_QUEUE_SEQUENCING_MAP.md"
    map_path.write_text(mod.build_map(fake_issues).rstrip() + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "MAP_PATH", map_path)

    monkeypatch.setattr(sys, "argv", ["issue_queue_sequencing_map.py", "--check"])
    assert mod.main() == 0

    map_path.write_text("stale\n", encoding="utf-8")
    assert mod.main() == 1
