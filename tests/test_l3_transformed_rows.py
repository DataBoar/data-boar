"""L3 transformed_rows producer — grant scope, ephemerality, no-value audit (#1334)."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from core.database import LocalDBManager
from core.l3_transformed_rows import (
    L3_FEATURE,
    CONTAINMENT_NOT_ENFORCED,
    CONTAINMENT_OWNER_ONLY,
    CONTAINMENT_OWNER_PLUS_PRIVILEGED,
    L3ContainmentError,
    L3GrantMissingError,
    L3ScopeError,
    assert_l3_contract,
    assert_windows_dacl_owner_contained,
    build_l3_transformed_rows,
    dumps_l3_audit,
    dumps_l3_rows,
    load_grant_file,
    parse_grant_document,
    parse_icacls_aces,
    persist_l3_body,
    resolve_projection_columns,
    verify_owner_containment,
)
from core.licensing.feature_gate import require_feature
from core.licensing.errors import FeatureTierBlockedError
from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier

CELL_A = "l3-synth-cell-alpha"
CELL_B = "l3-synth-cell-beta"
OUT_OF_SCOPE = "criminal_records"


def _seed_target_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE users (email TEXT, cpf TEXT, criminal_records TEXT)")
    conn.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (CELL_A, CELL_B, "must-never-be-projected"),
    )
    conn.commit()
    conn.close()


def _seed_session(audit_db: str, *, target_name: str = "lab-sql") -> str:
    sid = "l3-sess-01"
    mgr = LocalDBManager(audit_db)
    try:
        mgr.create_session_record(sid)
        mgr.set_current_session_id(sid)
        mgr.save_finding(
            "database",
            target_name=target_name,
            schema_name="main",
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


def _grant_doc(**overrides: object) -> dict:
    base: dict = {
        "grant_id": "grn-lab-001",
        "target": "lab-sql",
        "table": "users",
        "columns": ["email", "cpf"],
    }
    base.update(overrides)
    return base


def _write_grant(tmp_path: Path, doc: dict) -> Path:
    path = tmp_path / "grant.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _config_yaml(
    tmp_path: Path,
    *,
    target_db: Path,
    audit_db: Path,
    tier: str | None = None,
) -> Path:
    lines = [
        f"sqlite_path: {str(audit_db).replace(chr(92), '/')}",
        "report:",
        f"  output_dir: {str(tmp_path / 'reports').replace(chr(92), '/')}",
        "targets:",
        "  - name: lab-sql",
        "    type: database",
        "    driver: sqlite",
        f"    database: {str(target_db).replace(chr(92), '/')}",
    ]
    if tier is not None:
        lines.extend(
            [
                "licensing:",
                "  mode: open",
                f"  effective_tier: {tier}",
            ]
        )
    cfg = tmp_path / "config.yaml"
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cfg


def test_feature_is_paid_not_community() -> None:
    assert FEATURE_TIER_MAP[L3_FEATURE] == Tier.STD
    reset_license_guard_for_tests()
    with pytest.raises(FeatureTierBlockedError):
        require_feature(
            {"licensing": {"mode": "open", "effective_tier": "community"}},
            L3_FEATURE,
        )
    reset_license_guard_for_tests()
    require_feature(
        {"licensing": {"mode": "open", "effective_tier": "std"}},
        L3_FEATURE,
    )
    reset_license_guard_for_tests()


def test_star_and_empty_columns_are_scope_errors() -> None:
    with pytest.raises(L3ScopeError):
        parse_grant_document(_grant_doc(columns=["*"]))
    with pytest.raises(L3ScopeError):
        parse_grant_document(_grant_doc(columns=[]))
    with pytest.raises(L3ScopeError):
        parse_grant_document(_grant_doc(table="*"))


def test_request_column_outside_grant_is_exit_4_shape() -> None:
    grant = parse_grant_document(_grant_doc())
    with pytest.raises(L3ScopeError, match="outside the grant"):
        resolve_projection_columns(grant, [OUT_OF_SCOPE])
    with pytest.raises(L3ScopeError):
        parse_grant_document(_grant_doc(request_columns=["email", OUT_OF_SCOPE]))


def test_missing_grant_file(tmp_path: Path) -> None:
    with pytest.raises(L3GrantMissingError):
        load_grant_file(tmp_path / "nope.json")


def test_projection_skips_out_of_grant_column(tmp_path: Path) -> None:
    target_db = tmp_path / "target.db"
    audit_db = tmp_path / "audit.db"
    _seed_target_db(target_db)
    sid = _seed_session(str(audit_db))
    grant = parse_grant_document(_grant_doc())
    mgr = LocalDBManager(str(audit_db))
    try:
        rows, audit = build_l3_transformed_rows(
            mgr,
            session_id=sid,
            grant=grant,
            config={
                "targets": [
                    {
                        "name": "lab-sql",
                        "type": "database",
                        "driver": "sqlite",
                        "database": str(target_db),
                    }
                ]
            },
            projection_columns=("email", "cpf"),
            max_rows=10,
        )
    finally:
        mgr.dispose()
    values = [r["value"] for r in rows]
    assert CELL_A in values
    assert CELL_B in values
    assert "must-never-be-projected" not in values
    assert audit["grant_id"] == "grn-lab-001"
    assert audit["columns"] == ["email", "cpf"]
    assert audit["row_count"] == 2
    assert "value" not in audit
    audit_line = dumps_l3_audit(audit)
    assert CELL_A not in audit_line
    assert CELL_B not in audit_line
    assert_l3_contract(rows)


def test_persist_sets_owner_containment(tmp_path: Path) -> None:
    dest = tmp_path / "out" / "l3.json"
    label = persist_l3_body(dest, "[]\n")
    verified = verify_owner_containment(dest)
    if os.name == "nt":
        assert label == CONTAINMENT_OWNER_PLUS_PRIVILEGED
        assert verified == CONTAINMENT_OWNER_PLUS_PRIVILEGED
    else:
        assert label == CONTAINMENT_OWNER_ONLY
        mode = dest.stat().st_mode
        assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0
        assert verified == CONTAINMENT_OWNER_ONLY


def test_windows_dacl_parser_rejects_users_ace() -> None:
    listing = (
        r"C:\tmp\l3.json BUILTIN\Users:(I)(RX)" + "\n"
        r"               WIN-CI\runneradmin:(F)" + "\n\n"
        "Successfully processed 1 files; Failed processing 0 files\n"
    )
    aces = parse_icacls_aces(listing, Path(r"C:\tmp\l3.json"))
    with pytest.raises(L3ContainmentError, match="inherited ACE"):
        assert_windows_dacl_owner_contained(aces, "runneradmin")


def test_windows_dacl_parser_allows_system_and_administrators() -> None:
    listing = (
        r"C:\tmp\l3.json NT AUTHORITY\SYSTEM:(F)" + "\n"
        r"               BUILTIN\Administrators:(F)" + "\n"
        r"               WIN-CI\runneradmin:(F)" + "\n\n"
        "Successfully processed 1 files; Failed processing 0 files\n"
    )
    aces = parse_icacls_aces(listing, Path(r"C:\tmp\l3.json"))
    assert_windows_dacl_owner_contained(aces, "runneradmin")


def test_windows_dacl_parser_rejects_other_user() -> None:
    listing = (
        r"C:\tmp\l3.json NT AUTHORITY\SYSTEM:(F)" + "\n"
        r"               WIN-CI\other:(F)" + "\n"
        r"               WIN-CI\runneradmin:(F)" + "\n"
    )
    aces = parse_icacls_aces(listing, Path(r"C:\tmp\l3.json"))
    with pytest.raises(L3ContainmentError, match="unprivileged ACE"):
        assert_windows_dacl_owner_contained(aces, "runneradmin")


def test_persist_fail_closed_unlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "l3.json"

    def boom(_path: Path) -> None:
        raise L3ContainmentError("simulated containment failure")

    monkeypatch.setattr("core.l3_transformed_rows._restrict_to_owner", boom)
    with pytest.raises(L3ContainmentError, match="simulated"):
        persist_l3_body(dest, "[]\n")
    assert not dest.exists()


def test_persist_allow_unprotected_keeps_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "l3.json"

    def boom(_path: Path) -> None:
        raise L3ContainmentError("simulated containment failure")

    monkeypatch.setattr("core.l3_transformed_rows._restrict_to_owner", boom)
    label = persist_l3_body(dest, "[]\n", allow_unprotected=True)
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "[]\n"
    assert label == CONTAINMENT_NOT_ENFORCED


def test_cli_stdout_ephemeral_and_audit_has_no_cells(tmp_path: Path) -> None:
    target_db = tmp_path / "target.db"
    audit_db = tmp_path / "audit.db"
    _seed_target_db(target_db)
    sid = _seed_session(str(audit_db))
    grant_path = _write_grant(tmp_path, _grant_doc())
    cfg = _config_yaml(tmp_path, target_db=target_db, audit_db=audit_db)
    repo = Path(__file__).resolve().parents[1]
    surprise = tmp_path / "should-not-exist.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-l3",
            sid,
            "--l3-grant",
            str(grant_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert isinstance(payload, list)
    assert {row["value"] for row in payload} == {CELL_A, CELL_B}
    assert not surprise.exists()
    assert CELL_A not in proc.stderr
    assert CELL_B not in proc.stderr
    audit = json.loads(proc.stderr.strip().splitlines()[-1])
    assert audit["event"] == "l3_export_audit"
    assert audit["row_count"] == 2
    assert audit["persisted"] is False
    assert "value" not in audit


def test_cli_persist_requires_flag(tmp_path: Path) -> None:
    target_db = tmp_path / "target.db"
    audit_db = tmp_path / "audit.db"
    _seed_target_db(target_db)
    sid = _seed_session(str(audit_db))
    grant_path = _write_grant(tmp_path, _grant_doc())
    cfg = _config_yaml(tmp_path, target_db=target_db, audit_db=audit_db)
    dest = tmp_path / "explicit-l3.json"
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-l3",
            sid,
            "--l3-grant",
            str(grant_path),
            "--l3-persist",
            str(dest),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert dest.is_file()
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert {row["value"] for row in payload} == {CELL_A, CELL_B}
    audit = json.loads(proc.stderr.strip().splitlines()[-1])
    assert audit["persisted"] is True
    assert audit["containment"] in {
        CONTAINMENT_OWNER_ONLY,
        CONTAINMENT_OWNER_PLUS_PRIVILEGED,
    }
    assert CELL_A not in proc.stderr


def test_cli_column_outside_grant_exit_4(tmp_path: Path) -> None:
    target_db = tmp_path / "target.db"
    audit_db = tmp_path / "audit.db"
    _seed_target_db(target_db)
    sid = _seed_session(str(audit_db))
    grant_path = _write_grant(tmp_path, _grant_doc())
    cfg = _config_yaml(tmp_path, target_db=target_db, audit_db=audit_db)
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-l3",
            sid,
            "--l3-grant",
            str(grant_path),
            "--l3-column",
            OUT_OF_SCOPE,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 4, proc.stderr
    assert CELL_A not in proc.stdout
    assert "must-never-be-projected" not in proc.stdout


def test_cli_missing_grant_exit_3(tmp_path: Path) -> None:
    audit_db = tmp_path / "audit.db"
    sid = _seed_session(str(audit_db))
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"sqlite_path: {str(audit_db).replace(chr(92), '/')}\n"
        "targets: []\n"
        "report:\n  output_dir: reports\n",
        encoding="utf-8",
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-l3",
            sid,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3, proc.stderr


def test_cli_community_tier_exit_3(tmp_path: Path) -> None:
    target_db = tmp_path / "target.db"
    audit_db = tmp_path / "audit.db"
    _seed_target_db(target_db)
    sid = _seed_session(str(audit_db))
    grant_path = _write_grant(tmp_path, _grant_doc())
    cfg = _config_yaml(
        tmp_path, target_db=target_db, audit_db=audit_db, tier="community"
    )
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--export-l3",
            sid,
            "--l3-grant",
            str(grant_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3, proc.stderr
    assert CELL_A not in proc.stdout


def test_dumps_l3_audit_refuses_value_key() -> None:
    with pytest.raises(Exception, match="value"):
        dumps_l3_audit({"event": "x", "value": CELL_A})
    dumps_l3_rows([])
