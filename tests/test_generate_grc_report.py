"""Tests for ``scripts/generate_grc_report.py`` CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    script = repo_root / "scripts" / "generate_grc_report.py"
    cmd = [sys.executable, str(script), *args]
    return subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def test_generate_grc_report_lab_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    lab = {
        "run_stamp": "20990101_000000",
        "overall_status": "completed",
        "connectivity_status": {"summary": "all_hosts_ok_no_degraded_connectivity"},
    }
    lab_path = tmp_path / "lab_result.json"
    lab_path.write_text(json.dumps(lab), encoding="utf-8")
    out_path = tmp_path / "GRC.json"
    proc = _run_cli(
        repo_root,
        "--lab-result",
        str(lab_path),
        "--output",
        str(out_path),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "data_boar_grc_executive_report_v1"
    assert "20990101" in data["report_metadata"]["scope"]
    assert len(data["detailed_findings"]) == 0
    assert any(r["id"] == "REC-LAB-ORCH-01" for r in data["recommendations"])


def test_generate_grc_report_with_raw_assets(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw = {
        "scope": "Synthetic",
        "assets": [
            {
                "asset_id": "db:t:dbo.x",
                "asset_class": "database_table",
                "use_lgpd_density_risk": True,
                "pii_types": [{"type": "EMAIL", "count": 2}],
            }
        ],
    }
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    out_path = tmp_path / "out.json"
    proc = _run_cli(
        repo_root,
        "--input",
        str(raw_path),
        "--output",
        str(out_path),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(data["detailed_findings"]) == 1
    row = data["detailed_findings"][0]
    assert row["asset_id"] == "db:t:dbo.x"
    assert "risk_density_raw" in row


def test_generate_grc_report_findings_and_id_shape(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw = {
        "scope": "Slice workshop",
        "assets": [
            {
                "id": "host:postgres.public.users",
                "asset_class": "database_table",
                "use_lgpd_density_risk": True,
                "findings": [
                    {"type": "EMAIL", "count": 2},
                    {"type": "BRAZIL_CPF", "count": 1},
                ],
            }
        ],
    }
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    out_path = tmp_path / "out.json"
    proc = _run_cli(
        repo_root,
        "--input",
        str(raw_path),
        "--output",
        str(out_path),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out_path.read_text(encoding="utf-8"))
    row = data["detailed_findings"][0]
    assert row["asset_id"] == "host:postgres.public.users"
    reg = str(row.get("regulatory_impact", "") or "")
    assert "LGPD Art. 5, I" in reg
    assert "LGPD Art. 7" in reg


def test_generate_grc_report_critical_adds_p0_recommendation(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw = {
        "assets": [
            {
                "asset_id": "db:critical",
                "use_lgpd_density_risk": False,
                "risk_score": 85.0,
                "pii_types": [{"type": "EMAIL", "count": 1}],
            }
        ],
    }
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    out_path = tmp_path / "out.json"
    proc = _run_cli(
        repo_root,
        "--input",
        str(raw_path),
        "--output",
        str(out_path),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["executive_summary"]["critical_assets_at_risk"] >= 1
    assert any(
        isinstance(r, dict) and r.get("id") == "REC-GRC-CRITICAL-CRYPTO"
        for r in data.get("recommendations", [])
    )
