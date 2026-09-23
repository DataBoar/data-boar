"""benchmark_rc_sentinel_check.py — RC v2 findings + negative SSRF guards."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from scripts import benchmark_rc_sentinel_check as sentinel_mod


def _write_min_db(path: Path, session_id: str, pattern: str) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE scan_sessions (
                session_id TEXT PRIMARY KEY,
                started_at TEXT,
                status TEXT
            );
            CREATE TABLE filesystem_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            CREATE TABLE database_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            CREATE TABLE application_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO scan_sessions VALUES (?, ?, ?)",
            (session_id, datetime.now(timezone.utc).isoformat(), "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            (session_id, "Data_Soup_Synthetic", pattern),
        )
        conn.commit()
    finally:
        conn.close()


def test_findings_sentinel_passes_with_required_pattern(tmp_path: Path) -> None:
    cfg = tmp_path / "bench.yaml"
    cfg.write_text("sqlite_path: sentinel.db\n", encoding="utf-8")
    spec = tmp_path / "bench.sentinel.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "min_total_findings": 1,
                "required_patterns": [
                    {
                        "id": "filesystem_lgpd_cpf",
                        "pattern": "LGPD_CPF",
                        "min_count": 1,
                        "tables": ["filesystem_findings"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    _write_min_db(db, "sess-1", "LGPD_CPF")
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert errs == []


def test_findings_sentinel_rejects_latest_session_when_not_completed(
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "bench.yaml"
    cfg.write_text("sqlite_path: sentinel.db\n", encoding="utf-8")
    spec = tmp_path / "bench.sentinel.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "min_total_findings": 1,
                "required_patterns": [
                    {
                        "pattern": "LGPD_CPF",
                        "min_count": 1,
                        "tables": ["filesystem_findings"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(
            """
            CREATE TABLE scan_sessions (
                session_id TEXT PRIMARY KEY,
                started_at TEXT,
                status TEXT
            );
            CREATE TABLE filesystem_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            CREATE TABLE database_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            CREATE TABLE application_findings (
                session_id TEXT,
                target_name TEXT,
                pattern_detected TEXT
            );
            """
        )
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO scan_sessions VALUES (?, ?, ?)",
            ("sess-partial", ts, "running"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            ("sess-partial", "Data_Soup_Synthetic", "LGPD_CPF"),
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert errs
    assert any("completed" in e and "running" in e for e in errs)


def test_findings_sentinel_fails_when_pattern_missing(tmp_path: Path) -> None:
    cfg = tmp_path / "bench.yaml"
    cfg.write_text("sqlite_path: sentinel.db\n", encoding="utf-8")
    spec = tmp_path / "bench.sentinel.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "min_total_findings": 1,
                "required_patterns": [
                    {
                        "pattern": "LGPD_CPF",
                        "min_count": 1,
                        "tables": ["filesystem_findings"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    _write_min_db(db, "sess-1", "OTHER_PATTERN")
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("LGPD_CPF" in e or "count=" in e for e in errs)


def test_negative_ssrf_rest_auth_host_blocked() -> None:
    negative = (
        Path(sentinel_mod._REPO_ROOT) / "tests/config/benchmark-rc-ssrf-negative.yaml"
    )
    cases = sentinel_mod._load_yaml(negative)["cases"]
    exfil = next(c for c in cases if c["id"] == "rest_auth_host_not_allowlisted")
    target = exfil["target"]
    client = MagicMock()
    client.headers = {}
    with pytest.raises(ValueError, match="#1977"):
        from connectors.rest_connector import _build_auth

        _build_auth(client, target)


def test_negative_ssrf_metadata_url_blocked() -> None:
    negative = (
        Path(sentinel_mod._REPO_ROOT) / "tests/config/benchmark-rc-ssrf-negative.yaml"
    )
    errs = sentinel_mod._check_negative_ssrf(negative)
    assert errs == []


def _credit_card_in_pattern(pattern_detected: str | None) -> bool:
    return "CREDIT_CARD" in (pattern_detected or "")


def test_rc_sentinel_golden_int_year_join_must_not_credit_card() -> None:
    """Grok fixture — joined INTEGER/year columns must stay CREDIT_CARD=0 (#1332)."""
    from connectors.sample_value_dedup import join_distinct_sample
    from core.scanner import DataScanner

    scanner = DataScanner()
    fixtures = {
        "Ano": [2020, 2021, 2022, 2023, 2024],
        "id": [1001, 1002, 1003, 1004, 1005],
        "last_four_digits": [1234, 5678, 9012, 3456, 7890],
    }
    for column, values in fixtures.items():
        sample = join_distinct_sample(values, distinct_cap=5)
        result = scanner.scan_column(column, sample)
        assert not _credit_card_in_pattern(result.get("pattern_detected")), (
            f"RC profile must not treat joined {column!r} as CREDIT_CARD (#1332)"
        )


def test_rc_sentinel_golden_luhn_pan_tab_and_nbsp_still_credit_card() -> None:
    """Grok fixture — tab/NBSP PAN must remain CREDIT_CARD after #1978 Luhn span gate."""
    from core.scanner import DataScanner

    scanner = DataScanner()
    for label, pan in (
        ("tab", "4111\t1111\t1111\t1111"),
        ("nbsp", "4111\xa01111\xa01111\xa01111"),
    ):
        result = scanner.scan_column("card_number", pan)
        assert _credit_card_in_pattern(result.get("pattern_detected")), (
            f"RC profile must detect Luhn-valid PAN with {label} separator (#1978)"
        )
