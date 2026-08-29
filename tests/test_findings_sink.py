"""Findings sink (#552): SQL echo of SQLite findings (SQLite via SQLAlchemy in tests)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from config.loader import normalize_config
from core.database import LocalDBManager
from core.engine import AuditEngine
from core.findings_sink import (
    FindingsSinkError,
    SampleExportNotAcknowledged,
    _guard_sql_host,
    _sqlalchemy_url,
    maybe_push_findings_sink,
    push_session_to_sink,
    sink_enabled,
)


def _seed(db_path: str, sid: str = "sink-sess-01") -> str:
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.finish_session(sid)
    finally:
        mgr.dispose()
    return sid


def _sink_cfg(
    tmp_path: Path, *, enabled: bool = True, include_sample: bool = False
) -> dict:
    sink_path = tmp_path / "sink.db"
    return {
        "targets": [],
        "sqlite_path": str(tmp_path / "audit.db"),
        "report": {"output_dir": str(tmp_path / "reports")},
        "findings_sink": {
            "enabled": enabled,
            "type": "sqlite",
            "sqlite_path": str(sink_path),
            "on_conflict": "upsert",
            "include_sample_content": include_sample,
        },
    }


def test_sink_disabled_by_default():
    out = normalize_config({"targets": []})
    assert sink_enabled(out) is False
    assert out["findings_sink"]["enabled"] is False
    assert out["findings_sink"]["include_sample_content"] is False


def test_sink_upserts_on_conflict(tmp_path):
    cfg = _sink_cfg(tmp_path)
    sid = _seed(cfg["sqlite_path"])
    mgr = LocalDBManager(cfg["sqlite_path"])
    try:
        mgr.set_current_session_id(sid)
        push_session_to_sink(cfg, mgr, sid)
        mgr.save_finding(
            "database",
            target_name="prod-postgres",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="LGPD Art. 5(I)",
        )
        push_session_to_sink(cfg, mgr, sid)
    finally:
        mgr.dispose()

    engine = create_engine(f"sqlite:///{cfg['findings_sink']['sqlite_path']}")
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM data_boar_findings")
        ).scalar_one()
        risk = conn.execute(
            text("SELECT risk_level FROM data_boar_findings")
        ).scalar_one()
    engine.dispose()
    assert count == 1
    assert risk == "MEDIUM"


def test_sink_does_not_export_sample_content_by_default(tmp_path):
    cfg = _sink_cfg(tmp_path, include_sample=False)
    sid = _seed(cfg["sqlite_path"])
    mgr = LocalDBManager(cfg["sqlite_path"])
    try:
        mgr.set_current_session_id(sid)
        push_session_to_sink(cfg, mgr, sid)
    finally:
        mgr.dispose()

    engine = create_engine(f"sqlite:///{cfg['findings_sink']['sqlite_path']}")
    with engine.connect() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(data_boar_findings)"))
        }
    engine.dispose()
    assert "sample_content" not in cols


def test_sink_failure_does_not_abort_session(tmp_path, monkeypatch):
    cfg = _sink_cfg(tmp_path, enabled=True)
    sid = _seed(cfg["sqlite_path"])

    def _boom(*_a, **_k):
        raise FindingsSinkError("forced sink failure")

    monkeypatch.setattr("core.findings_sink.push_session_to_sink", _boom)
    engine = AuditEngine(cfg)
    try:
        engine.db_manager.set_current_session_id(sid)
        maybe_push_findings_sink(cfg, engine.db_manager, sid)
        db_rows, _fs, _app, fails = engine.db_manager.get_findings(sid)
        assert any(f.get("reason") == "sink_error" for f in fails)
        assert db_rows  # scan findings still present
    finally:
        engine.db_manager.dispose()


def test_cli_sample_export_requires_allow_flag(tmp_path):
    cfg = _sink_cfg(tmp_path, include_sample=True)
    sid = _seed(cfg["sqlite_path"])
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                f"sqlite_path: {cfg['sqlite_path']}",
                "targets: []",
                "findings_sink:",
                "  enabled: true",
                "  type: sqlite",
                f"  sqlite_path: {cfg['findings_sink']['sqlite_path']}",
                "  include_sample_content: true",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--config",
            str(cfg_path),
            "--export-findings-sink",
            sid,
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "allow-sample-export" in (proc.stderr or "")
    assert "Art. 46" in (proc.stderr or "")


def test_push_raises_without_sample_ack(tmp_path):
    cfg = _sink_cfg(tmp_path, include_sample=True)
    sid = _seed(cfg["sqlite_path"])
    mgr = LocalDBManager(cfg["sqlite_path"])
    try:
        mgr.set_current_session_id(sid)
        try:
            push_session_to_sink(
                cfg,
                mgr,
                sid,
                allow_sample_export=False,
                require_explicit_sample_ack=True,
            )
            raise AssertionError("expected SampleExportNotAcknowledged")
        except SampleExportNotAcknowledged:
            pass
    finally:
        mgr.dispose()


def test_maybe_push_noop_when_disabled(tmp_path):
    cfg = _sink_cfg(tmp_path, enabled=False)
    sid = _seed(cfg["sqlite_path"])
    mgr = LocalDBManager(cfg["sqlite_path"])
    try:
        maybe_push_findings_sink(cfg, mgr, sid)
    finally:
        mgr.dispose()
    assert not Path(cfg["findings_sink"]["sqlite_path"]).exists()


def _pg_sink(**overrides: object) -> dict:
    cfg: dict = {
        "type": "postgresql",
        "host": "db.example.com",
        "port": 5432,
        "database": "audit",
        "user": "u",
        "pass": "p",
    }
    cfg.update(overrides)
    return cfg


def test_sqlalchemy_url_userinfo_special_chars_do_not_shift_host() -> None:
    """Password ``@`` / ``/`` must not become a second authority (#1816)."""
    from sqlalchemy.engine.url import make_url

    url = _sqlalchemy_url(_pg_sink(**{"pass": "p@ss/word#x"}))
    parsed = make_url(url)
    assert parsed.host == "db.example.com"
    assert parsed.port == 5432
    assert parsed.database == "audit"
    assert parsed.password == "p@ss/word#x"
    assert not parsed.query


def test_sqlalchemy_url_encodes_database_so_query_cannot_override_peer() -> None:
    from sqlalchemy.engine.url import make_url

    url = _sqlalchemy_url(_pg_sink(database="audit?hostaddr=10.0.0.9"))
    parsed = make_url(url)
    assert parsed.host == "db.example.com"
    assert not parsed.query
    assert parsed.database == "audit%3Fhostaddr%3D10.0.0.9"


def test_sqlalchemy_url_rejects_host_authority_injection() -> None:
    with pytest.raises(FindingsSinkError, match="illegal '@'"):
        _sqlalchemy_url(_pg_sink(host="evil.example.com@169.254.169.254"))
    with pytest.raises(FindingsSinkError, match=r"illegal '\?'"):
        _sqlalchemy_url(_pg_sink(host="db.example.com?hostaddr=10.0.0.9"))
    with pytest.raises(FindingsSinkError, match="illegal '/'"):
        _sqlalchemy_url(_pg_sink(host="db.example.com/other"))


def test_guard_ssrf_uses_make_url_host_not_raw_yaml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guard candidate is the SQLAlchemy-parsed peer (#1816 / #1556)."""
    seen: list[str] = []

    def fake_resolve(
        url: str,
        *,
        allow_private: bool = False,
        label: str = "url",
    ) -> tuple[None, list]:
        seen.append(url)
        return None, []

    monkeypatch.setattr(
        "connectors.url_guard.resolve_and_validate_outbound_url",
        fake_resolve,
    )
    _guard_sql_host(_pg_sink())
    assert seen == ["db.example.com:5432"]
