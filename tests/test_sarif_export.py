"""SARIF 2.1.0 export (#838): structure, mapping, metadata-only, CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.database import LocalDBManager
from core.findings_common import UnknownSessionError
from core.licensing.guard import reset_license_guard_for_tests
from core.sarif_export import (
    artifact_uri,
    build_rule_ids,
    build_sarif_payload,
    sarif_level,
)
from tests.governance_fixtures import (
    SESSION_NEW,
    SESSION_OLD,
    assert_valid_sarif,
    seed_two_sessions,
)

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "audit.db")
    seed_two_sessions(path)
    mgr = LocalDBManager(path)
    yield mgr
    mgr.dispose()


def test_sarif_structure_and_required_fields(db):
    doc = build_sarif_payload(db, session_id=SESSION_NEW)
    assert_valid_sarif(doc)
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "Data Boar"
    assert run["automationDetails"]["id"] == f"data-boar/{SESSION_NEW}"
    assert run["properties"]["metadata_only"] is True


def test_sarif_rule_per_detector_and_results_per_hit(db):
    doc = build_sarif_payload(db, session_id=SESSION_NEW)
    rules = {r["id"] for r in doc["runs"][0]["tool"]["driver"]["rules"]}
    # "LGPD_CPF, EMAIL" is two detector hits -> two rules, shared with other rows.
    assert rules == {"DATABOAR.EMAIL", "DATABOAR.LGPD_CPF"}
    results = doc["runs"][0]["results"]
    # email(db)=1, cpf(db)=1, report_may.csv has two hits -> 4 results
    assert len(results) == 4


def test_sarif_level_from_sensitivity():
    assert sarif_level("HIGH") == "error"
    assert sarif_level("medium") == "warning"
    assert sarif_level("LOW") == "note"
    assert sarif_level("") == "note"


def test_sarif_locations_database_and_filesystem(db):
    doc = build_sarif_payload(db, session_id=SESSION_NEW)
    results = doc["runs"][0]["results"]
    db_res = next(
        r
        for r in results
        if r["properties"]["source_type"] == "database"
        and r["ruleId"] == "DATABOAR.LGPD_CPF"
    )
    logical = db_res["locations"][0]["logicalLocations"][0]
    assert logical["fullyQualifiedName"] == "crm-db.public.users.cpf"
    assert "physicalLocation" not in db_res["locations"][0]
    fs_res = next(r for r in results if r["properties"]["source_type"] == "filesystem")
    uri = fs_res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri == "file:///srv/exports/report_may.csv"


def test_sarif_baseline_state_and_delta_properties(db):
    doc = build_sarif_payload(db, session_id=SESSION_NEW)
    run = doc["runs"][0]
    assert run["properties"]["previous_session_id"] == SESSION_OLD
    assert run["properties"]["new_findings_count"] == 1
    assert run["properties"]["resolved_count"] == 1
    states = {
        r["ruleId"]: r["baselineState"]
        for r in run["results"]
        if r["properties"]["source_type"] == "database"
    }
    assert states == {"DATABOAR.EMAIL": "unchanged", "DATABOAR.LGPD_CPF": "new"}


def test_sarif_first_session_has_no_baseline(db):
    doc = build_sarif_payload(db, session_id=SESSION_OLD)
    run = doc["runs"][0]
    assert run["properties"]["previous_session_id"] is None
    assert run["properties"]["new_findings_count"] is None
    assert run["properties"]["delta_available"] is False
    assert all("baselineState" not in r for r in run["results"])


def test_sarif_fingerprint_stable_across_runs(db):
    a = build_sarif_payload(db, session_id=SESSION_NEW)["runs"][0]["results"]
    b = build_sarif_payload(db, session_id=SESSION_NEW)["runs"][0]["results"]
    fa = [r["partialFingerprints"] for r in a]
    assert fa == [r["partialFingerprints"] for r in b]
    assert len({json.dumps(f, sort_keys=True) for f in fa}) == len(fa)


def test_sarif_metadata_only_no_sample_fields(db):
    text = json.dumps(build_sarif_payload(db, session_id=SESSION_NEW))
    for needle in ("sample_content", "sample_value", "raw_sample"):
        assert needle not in text


def test_sarif_unknown_session_raises(db):
    with pytest.raises(UnknownSessionError):
        build_sarif_payload(db, session_id="nope")


def test_rule_ids_are_stable_and_never_merge_distinct_detectors():
    ids = build_rule_ids({"A B", "A_B", "CPF"})
    assert ids["CPF"] == "DATABOAR.CPF"
    assert ids["A B"] != ids["A_B"]  # same slug -> hash suffix on both
    assert build_rule_ids({"A B", "A_B", "CPF"}) == ids


@pytest.mark.parametrize(
    ("path", "name", "expected"),
    [
        ("/srv/a b", "x#1.csv", "file:///srv/a%20b/x%231.csv"),
        ("C:\\data\\hr", "cv.docx", "file:///C:/data/hr/cv.docx"),
        ("rel/dir", "f.txt", "rel/dir/f.txt"),
        (None, None, None),
    ],
)
def test_artifact_uri_percent_encoded(path, name, expected):
    assert artifact_uri(path, name) == expected


def _run_cli(tmp_path, *extra):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"targets: []\nsqlite_path: {tmp_path / 'audit.db'}\n"
        f"report:\n  output_dir: {tmp_path}\n"
        "licensing:\n  mode: open\n  effective_tier: pro_plus\n",
        encoding="utf-8",
    )
    return subprocess.run(
        [sys.executable, str(REPO / "main.py"), "--config", str(cfg), *extra],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=False,
    )


def test_cli_export_sarif_stdout(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    proc = _run_cli(tmp_path, "--export-sarif", SESSION_NEW)
    assert proc.returncode == 0, proc.stderr
    assert_valid_sarif(json.loads(proc.stdout))


def test_cli_export_sarif_output_file(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    dest = tmp_path / "out.sarif"
    proc = _run_cli(
        tmp_path, "--export-sarif", SESSION_NEW, "--sarif-output", str(dest)
    )
    assert proc.returncode == 0, proc.stderr
    assert_valid_sarif(json.loads(dest.read_text(encoding="utf-8")))


def test_cli_export_sarif_unknown_session_exit_2(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    proc = _run_cli(tmp_path, "--export-sarif", "no-such-session")
    assert proc.returncode == 2
    assert "Unknown session" in proc.stderr


def test_cli_export_sarif_blocked_below_pro_plus(tmp_path):
    seed_two_sessions(str(tmp_path / "audit.db"))
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"targets: []\nsqlite_path: {tmp_path / 'audit.db'}\n"
        "licensing:\n  mode: open\n  effective_tier: pro\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "main.py"),
            "--config",
            str(cfg),
            "--export-sarif",
            SESSION_NEW,
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=False,
    )
    assert proc.returncode == 2
    assert "Licensing" in proc.stderr
    assert proc.stdout.strip() == ""


@pytest.mark.parametrize(
    "other",
    [
        ["--export-ropa", "x"],
        ["--export-dsar", "x"],
        ["--web"],
        ["--reset-data"],
        ["--validate-config"],
    ],
)
def test_cli_export_sarif_mutually_exclusive(tmp_path, other):
    proc = _run_cli(tmp_path, "--export-sarif", "x", *other)
    assert proc.returncode == 2
    assert "Cannot combine" in proc.stderr


def test_cli_sarif_output_requires_export_sarif(tmp_path):
    proc = _run_cli(tmp_path, "--sarif-output", "x.sarif")
    assert proc.returncode == 2
    assert "requires --export-sarif" in proc.stderr
