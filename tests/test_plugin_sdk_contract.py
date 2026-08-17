"""Conformance for Plugin SDK language-neutral contract (#865 / ADR-0086)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from core.database import LocalDBManager
from core.plugins.hook import maybe_run_remediation_hook

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "sdk" / "PLUGIN_CONTRACT.schema.json"
EXAMPLE_REQUEST = REPO_ROOT / "docs" / "sdk" / "example-request.json"
EXAMPLE_DECISION = REPO_ROOT / "docs" / "sdk" / "example-decision.json"
L2_STUB = REPO_ROOT / "docs" / "sdk" / "stubs" / "l2_jsonrpc_echo.py"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _seed_db(tmp_path: Path, sid: str) -> LocalDBManager:
    db_path = str(tmp_path / f"{sid}.db")
    mgr = LocalDBManager(db_path)
    mgr.create_session_record(sid)
    mgr.set_current_session_id(sid)
    mgr.save_finding(
        "database",
        target_name="primary_db",
        schema_name="public",
        table_name="customers",
        column_name="email",
        sensitivity_level="HIGH",
        pattern_detected="EMAIL",
        norm_tag="LGPD Art. 5(I)",
    )
    mgr.finish_session(sid)
    return mgr


def test_schema_file_exists() -> None:
    assert SCHEMA_PATH.is_file()
    schema = _load_schema()
    assert "$defs" in schema
    assert "request" in schema["$defs"]
    assert "decision" in schema["$defs"]
    assert "receipt" in schema["$defs"]


@pytest.mark.parametrize(
    "example_path",
    [EXAMPLE_REQUEST, EXAMPLE_DECISION],
    ids=["request", "decision"],
)
def test_examples_validate_against_contract_schema(example_path: Path) -> None:
    schema = _load_schema()
    instance = json.loads(example_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)


def test_invalid_decision_fails_schema() -> None:
    schema = _load_schema()
    bad = {
        "sdk_contract_version": "1.0.0",
        "schema": "databoar.plugin.decision",
        "session_id": "s",
        "plugin": {"name": "x", "version": "0"},
        "status": "not_a_real_status",
        "decided_at": "2026-08-09T18:00:00Z",
        "results": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_crashing_l1_plugin_safe_hold_does_not_abort_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid / crashing L1 remediator → stderr Safe-Hold; hook must not raise."""
    import types

    class _CrashPlugin:
        @property
        def name(self) -> str:
            return "crash"

        @property
        def version(self) -> str:
            return "0.0.1"

        def remediate(self, findings_path: Path, config: dict) -> Path:
            raise RuntimeError("intentional plugin crash for #865 Safe-Hold")

    mod = types.ModuleType("tests._fake_crash_remediation_plugin")
    mod.CrashPlugin = _CrashPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, mod.__name__, mod)

    sid = "sess-crash-865"
    cfg = {
        "licensing": {"mode": "open", "effective_tier": "enterprise"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": f"{mod.__name__}:CrashPlugin",
            "verify_after": False,
            "config": {},
        },
    }
    mgr = _seed_db(tmp_path, sid)
    try:
        maybe_run_remediation_hook(cfg, sid, db_manager=mgr)  # must not raise
    finally:
        mgr.dispose()
    err = capsys.readouterr().err
    assert "[remediation] plugin error:" in err
    assert "intentional plugin crash" in err


def test_l2_stdio_stub_returns_schema_valid_safe_hold() -> None:
    assert L2_STUB.is_file()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "databoar.remediation.decide",
        "params": {
            "session_id": "sess_stub_test",
            "request_id": "req_stub_test",
            "trust_level": "trusted",
        },
    }
    proc = subprocess.run(
        [sys.executable, str(L2_STUB)],
        input=json.dumps(req) + "\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    line = proc.stdout.strip().splitlines()[-1]
    envelope = json.loads(line)
    assert "result" in envelope
    decision = envelope["result"]
    assert decision["status"] == "safe_hold"
    jsonschema.validate(instance=decision, schema=_load_schema())


def test_l2_stub_handle_line_unit() -> None:
    """Import stub helpers without executing main()."""
    spec = importlib.util.spec_from_file_location("l2_jsonrpc_echo", L2_STUB)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    resp = mod.handle_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "databoar.remediation.decide",
                "params": {"session_id": "s7"},
            }
        )
    )
    assert resp is not None
    jsonschema.validate(instance=resp["result"], schema=_load_schema())
