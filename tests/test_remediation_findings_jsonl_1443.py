"""Regression: host writes findings JSONL before remediation plugin (#1443).

Without the fix, the hook invents findings_{session_id}.jsonl but nothing
writes it — plugins see a ghost path. These tests require a real SQLite-backed
export (same taxonomy as #649 remediation_targets).
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from core.database import LocalDBManager
from core.plugins.hook import maybe_run_remediation_hook
from core.remediation_manifest import write_findings_jsonl


class _CountingRemediationPlugin:
    """Requires an existing non-empty findings JSONL (regression guard)."""

    last_line_count: int = -1
    last_path: Path | None = None

    @property
    def name(self) -> str:
        return "counting-remediator"

    @property
    def version(self) -> str:
        return "0.0.1"

    def remediate(self, findings_path: Path, config: dict) -> Path:
        assert findings_path.is_file(), f"ghost findings_path: {findings_path}"
        lines = [
            ln
            for ln in findings_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert lines, f"empty findings JSONL (ghost/mask): {findings_path}"
        for ln in lines:
            obj = json.loads(ln)
            assert "finding_id" in obj
            assert "pii_type" in obj
        _CountingRemediationPlugin.last_line_count = len(lines)
        _CountingRemediationPlugin.last_path = findings_path
        out = findings_path.parent / "remediation_report.json"
        out.write_text(
            json.dumps({"findings_seen": len(lines)}) + "\n", encoding="utf-8"
        )
        return out


def _seed_session(db_path: str, sid: str = "jsonl-sess-01") -> str:
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="primary_db",
            schema_name="public",
            table_name="customers",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5(II)",
            ml_confidence=97,
        )
        mgr.save_finding(
            "filesystem",
            target_name="files-export",
            path="/data/exports",
            file_name="report.csv",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def test_write_findings_jsonl_uses_649_taxonomy(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path)
    out = tmp_path / "out" / f"findings_{sid}.jsonl"
    mgr = LocalDBManager(db_path)
    try:
        written = write_findings_jsonl(mgr, session_id=sid, path=out, config={})
    finally:
        mgr.dispose()
    assert written == out
    assert out.is_file()
    rows = [json.loads(ln) for ln in out.read_text(encoding="utf-8").splitlines() if ln]
    assert len(rows) == 2
    assert {r["pii_type"] for r in rows} == {"cpf_br", "email"}
    assert all(r["finding_id"].startswith("find_") for r in rows)


def test_write_findings_jsonl_unknown_session_safe_hold(tmp_path: Path) -> None:
    db_path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(db_path)
    try:
        assert (
            write_findings_jsonl(
                mgr, session_id="no-such-session", path=tmp_path / "x.jsonl"
            )
            is None
        )
    finally:
        mgr.dispose()
    assert not (tmp_path / "x.jsonl").exists()


def test_hook_writes_real_jsonl_before_plugin_no_preseed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fails before #1443 fix (ghost path); passes when host writes from SQLite."""
    db_path = str(tmp_path / "audit.db")
    sid = _seed_session(db_path, sid="hook-jsonl-01")
    findings_path = tmp_path / f"findings_{sid}.jsonl"
    assert not findings_path.exists()

    mod = types.ModuleType("tests._fake_counting_remediation_plugin")
    mod.CountingPlugin = _CountingRemediationPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)
    _CountingRemediationPlugin.last_line_count = -1

    cfg = {
        "licensing": {"mode": "open", "effective_tier": "enterprise"},
        "report": {"output_dir": str(tmp_path)},
        "targets": [{"name": "primary_db", "type": "postgresql"}],
        "remediation": {
            "enabled": True,
            "plugin": f"{mod.__name__}:CountingPlugin",
            "verify_after": False,
            "config": {},
        },
    }
    mgr = LocalDBManager(db_path)
    try:
        maybe_run_remediation_hook(cfg, sid, db_manager=mgr)
    finally:
        mgr.dispose()

    out = capsys.readouterr().out
    assert "Remediation complete:" in out
    assert findings_path.is_file()
    assert _CountingRemediationPlugin.last_line_count == 2
    assert (tmp_path / "remediation_report.json").is_file()


def test_hook_without_db_manager_skips_ghost_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = {
        "licensing": {"mode": "open", "effective_tier": "enterprise"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": "tests._never_loaded:X",
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "ghost-sess")
    err = capsys.readouterr().err
    assert "no db_manager" in err
    assert not (tmp_path / "findings_ghost-sess.jsonl").exists()
