"""RoPA evidence export (#837): payload, 'A COMPLETAR', Excel, config, CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import load_workbook

from config.loader import normalize_config
from core.database import LocalDBManager
from core.findings_common import UnknownSessionError
from core.ropa_export import (
    PENDING,
    build_ropa_payload,
    write_ropa_outputs,
    write_ropa_xlsx,
)
from tests.governance_fixtures import SESSION_NEW, seed_two_sessions

REPO = Path(__file__).resolve().parents[1]

ROPA_CFG = {
    "controller": {
        "name": "Example Controller Ltda",
        "contact": "privacy@example.test",
        "dpo_name": "Example DPO",
        "dpo_contact": "dpo@example.test",
    },
    "defaults": {
        "retention": "5 years after contract end",
        "security_measures": ["Encryption at rest", "RBAC"],
    },
    "activities": [
        {
            "target": "crm-db",
            "name": "Customer relationship management",
            "purposes": ["Contract performance"],
            "legal_basis": "Art. 6(1)(b) GDPR",
            "data_subject_categories": ["customers"],
            "recipients": ["Payment processor"],
            "transfers": ["None"],
        }
    ],
}


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "audit.db")
    seed_two_sessions(path)
    mgr = LocalDBManager(path)
    yield mgr
    mgr.dispose()


def _norm(ropa):
    return normalize_config({"targets": [], "ropa": ropa})["ropa"]


def test_payload_without_ropa_block_marks_everything_a_completar(db):
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=_norm(None))
    assert payload["controller"]["name"]["value"] == PENDING
    assert payload["controller"]["dpo_name"]["status"] == "pending"
    assert {r["target"] for r in payload["records"]} == {"crm-db", "file-share"}
    for rec in payload["records"]:
        for name, fld in rec["art30_fields"].items():
            assert fld["value"] == PENDING, name
    assert payload["summary"]["fields_pending_completion"] > 0
    assert "not a legal conclusion" in payload["evidence_notice"]


def test_payload_scan_evidence_is_derived_from_findings(db):
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=_norm(None))
    crm = next(r for r in payload["records"] if r["target"] == "crm-db")
    ev = crm["scan_evidence"]
    labels = {c["label"] for c in ev["personal_data_categories"]}
    assert labels == {"EMAIL", "LGPD_CPF"}
    assert ev["max_sensitivity"] == "HIGH"
    assert ev["findings_total"] == 2
    assert "LGPD Art. 5(II)" in ev["norm_tags"]
    assert {loc["location"] for loc in ev["locations"]} == {
        "public.users.email",
        "public.users.cpf",
    }
    assert crm["source_type"] == "database"
    fs = next(r for r in payload["records"] if r["target"] == "file-share")
    assert fs["scan_evidence"]["locations"][0]["location"] == (
        "/srv/exports/report_may.csv"
    )


def test_payload_with_ropa_block_declares_fields_and_defaults(db):
    payload = build_ropa_payload(
        db, session_id=SESSION_NEW, ropa_config=_norm(ROPA_CFG)
    )
    assert payload["controller"]["name"] == {
        "value": "Example Controller Ltda",
        "status": "declared_in_config",
    }
    assert payload["controller"]["representative"]["value"] == PENDING
    crm = next(r for r in payload["records"] if r["target"] == "crm-db")
    assert crm["processing_activity"]["value"] == "Customer relationship management"
    f = crm["art30_fields"]
    assert f["purposes"]["value"] == ["Contract performance"]
    assert f["legal_basis"]["value"] == ["Art. 6(1)(b) GDPR"]
    assert f["retention"]["value"] == "5 years after contract end"  # from defaults
    assert f["security_measures"]["value"] == ["Encryption at rest", "RBAC"]
    fs = next(r for r in payload["records"] if r["target"] == "file-share")
    assert fs["art30_fields"]["purposes"]["value"] == PENDING
    assert fs["art30_fields"]["retention"]["value"] == "5 years after contract end"


def test_declared_activity_without_scan_evidence_is_listed(db):
    cfg = _norm({"activities": [{"target": "hr-system", "purposes": "payroll"}]})
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=cfg)
    assert payload["summary"]["declared_activities_without_scan_evidence"] == [
        "hr-system"
    ]


def test_payload_is_metadata_only(db):
    text = json.dumps(build_ropa_payload(db, session_id=SESSION_NEW))
    for needle in ("sample_content", "sample_value", "raw_sample"):
        assert needle not in text


def test_unknown_session_is_an_error_not_an_empty_register(db):
    with pytest.raises(UnknownSessionError):
        build_ropa_payload(db, session_id="no-such-session")


def test_xlsx_has_expected_sheets_and_placeholders(db, tmp_path):
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=_norm(None))
    dest = write_ropa_xlsx(payload, tmp_path / "ropa.xlsx")
    wb = load_workbook(dest)
    assert wb.sheetnames == ["RoPA", "Controller", "Locations", "Notes"]
    rows = list(wb["RoPA"].iter_rows(values_only=True))
    assert rows[0][0].startswith("Source")
    assert any(PENDING in (c or "") for row in rows[1:] for c in row if c)
    ctrl = list(wb["Controller"].iter_rows(values_only=True))
    assert ctrl[1][2] == PENDING


def test_xlsx_neutralizes_formula_injection(db, tmp_path):
    cfg = _norm({"controller": {"name": '=HYPERLINK("http://x.test","a")'}})
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=cfg)
    wb = load_workbook(write_ropa_xlsx(payload, tmp_path / "r.xlsx"))
    value = wb["Controller"].cell(row=2, column=3).value
    assert value.startswith("'=")


def test_write_outputs_names_are_session_prefixed(db, tmp_path):
    payload = build_ropa_payload(db, session_id=SESSION_NEW, ropa_config=_norm(None))
    out = write_ropa_outputs(payload, tmp_path / "out")
    assert out["json"].suffix == ".json" and out["xlsx"].suffix == ".xlsx"
    assert out["json"].name.startswith("ropa_")
    assert json.loads(out["json"].read_text(encoding="utf-8"))["schema_version"] == 1


# --- config block validation -------------------------------------------------


def test_ropa_defaults_to_empty_normalized_block():
    cfg = normalize_config({"targets": []})
    assert cfg["ropa"]["activities"] == []
    assert cfg["ropa"]["controller"]["name"] == ""


@pytest.mark.parametrize(
    ("ropa", "match"),
    [
        ({"controler": {}}, "unknown key"),
        ({"controller": {"nome": "x"}}, "unknown key"),
        ({"defaults": {"purpose": "x"}}, "unknown key"),
        ({"controller": []}, "must be a mapping"),
        ({"activities": {"a": 1}}, "must be a list"),
        ({"activities": [{"name": "no target"}]}, "target is required"),
        ({"activities": [{"target": "t", "bogus": 1}]}, "unknown key"),
        ({"defaults": {"purposes": [{"x": 1}]}}, "string"),
        ({"controller": {"name": "x" * 5000}}, "longer than"),
    ],
)
def test_ropa_block_validation_errors(ropa, match):
    with pytest.raises(ValueError, match=match):
        normalize_config({"targets": [], "ropa": ropa})


# --- CLI --------------------------------------------------------------------


def _cli(tmp_path, *extra, tier="pro_plus", ropa_yaml=""):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"targets: []\nsqlite_path: {tmp_path / 'audit.db'}\n"
        f"report:\n  output_dir: {tmp_path / 'default_out'}\n"
        f"licensing:\n  mode: open\n  effective_tier: {tier}\n{ropa_yaml}",
        encoding="utf-8",
    )
    return subprocess.run(
        [sys.executable, str(REPO / "main.py"), "--config", str(cfg), *extra],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=False,
    )


def test_cli_export_ropa_writes_xlsx_and_json_without_ropa_block(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    out = tmp_path / "ropa_out"
    proc = _cli(tmp_path, "--export-ropa", SESSION_NEW, "--ropa-output", str(out))
    assert proc.returncode == 0, proc.stderr
    files = sorted(p.name for p in out.iterdir())
    assert len(files) == 2 and files[0].endswith(".json") and files[1].endswith(".xlsx")
    assert "A COMPLETAR" in proc.stderr
    data = json.loads((out / files[0]).read_text(encoding="utf-8"))
    assert data["controller"]["name"]["value"] == PENDING


def test_cli_export_ropa_with_config_block(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    ropa_yaml = (
        "ropa:\n  controller:\n    name: Example Controller Ltda\n"
        "  activities:\n    - target: crm-db\n      purposes: [Contract performance]\n"
    )
    out = tmp_path / "o"
    proc = _cli(
        tmp_path,
        "--export-ropa",
        SESSION_NEW,
        "--ropa-output",
        str(out),
        ropa_yaml=ropa_yaml,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    assert data["controller"]["name"]["value"] == "Example Controller Ltda"


def test_cli_export_ropa_default_dir_is_report_output_dir(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    proc = _cli(tmp_path, "--export-ropa", SESSION_NEW)
    assert proc.returncode == 0, proc.stderr
    assert list((tmp_path / "default_out").glob("ropa_*.xlsx"))


def test_cli_export_ropa_unknown_session_exit_2(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    proc = _cli(tmp_path, "--export-ropa", "no-such")
    assert proc.returncode == 2
    assert "Unknown session" in proc.stderr
    assert not (tmp_path / "default_out").exists() or not list(
        (tmp_path / "default_out").glob("ropa_*")
    )


def test_cli_export_ropa_blocked_below_pro_plus(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    proc = _cli(tmp_path, "--export-ropa", SESSION_NEW, tier="pro")
    assert proc.returncode == 2
    assert "Licensing" in proc.stderr


def test_cli_invalid_ropa_block_is_a_config_error(tmp_path):
    proc = _cli(tmp_path, "--validate-config", ropa_yaml="ropa:\n  controler: {}\n")
    assert proc.returncode == 1
    assert "unknown key" in proc.stdout


def test_cli_ropa_output_requires_export_ropa(tmp_path):
    proc = _cli(tmp_path, "--ropa-output", "x")
    assert proc.returncode == 2
    assert "requires --export-ropa" in proc.stderr
