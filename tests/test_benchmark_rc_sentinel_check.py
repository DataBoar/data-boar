"""benchmark_rc_sentinel_check.py — RC v3 findings + negative SSRF guards."""

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


def _write_rest_optional_db(
    path: Path,
    *,
    session_id: str,
    filesystem_pattern: str,
    scan_failure_target: str | None = None,
) -> None:
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
            CREATE TABLE scan_failures (
                session_id TEXT,
                target_name TEXT,
                reason TEXT
            );
            """
        )
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO scan_sessions VALUES (?, ?, ?)",
            (session_id, ts, "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            (session_id, "Data_Soup_Synthetic", filesystem_pattern),
        )
        if scan_failure_target:
            conn.execute(
                "INSERT INTO scan_failures VALUES (?, ?, ?)",
                (session_id, scan_failure_target, "error"),
            )
        conn.commit()
    finally:
        conn.close()


def test_optional_rest_reachable_zero_application_findings_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bugbot #1983 — httpbin reachability must not require sensitive app findings."""
    monkeypatch.setattr(sentinel_mod, "_probe_reachable", lambda _spec: True)
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
                "optional_connectors": [
                    {
                        "id": "lab_rest_application",
                        "target_name_prefix": "Lab_REST",
                        "probe": "tcp:httpbin.org:443",
                        "require_no_scan_failure": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    _write_rest_optional_db(
        db, session_id="sess-rest-clean", filesystem_pattern="LGPD_CPF"
    )
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert errs == []


def test_optional_rest_reachable_scan_failure_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sentinel_mod, "_probe_reachable", lambda _spec: True)
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
                "optional_connectors": [
                    {
                        "id": "lab_rest_application",
                        "target_name_prefix": "Lab_REST",
                        "probe": "tcp:httpbin.org:443",
                        "require_no_scan_failure": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    _write_rest_optional_db(
        db,
        session_id="sess-rest-fail",
        filesystem_pattern="LGPD_CPF",
        scan_failure_target="Lab_REST_Httpbin_Sample",
    )
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("scan_failures=" in e and "lab_rest_application" in e for e in errs)


def test_required_pattern_max_count_blocks_excess(tmp_path: Path) -> None:
    cfg = tmp_path / "bench.yaml"
    cfg.write_text("sqlite_path: sentinel.db\n", encoding="utf-8")
    spec = tmp_path / "bench.sentinel.yaml"
    spec.write_text(
        yaml.safe_dump(
            {
                "min_total_findings": 2,
                "required_patterns": [
                    {
                        "id": "cap_lgpd",
                        "pattern": "LGPD_CPF",
                        "max_count": 1,
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
            ("sess-cap", ts, "completed"),
        )
        conn.executemany(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            [
                ("sess-cap", "t", "LGPD_CPF"),
                ("sess-cap", "t", "LGPD_CPF"),
            ],
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("max_count" in e for e in errs)


def test_optional_forbidden_substrings_on_rest_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sentinel_mod, "_probe_reachable", lambda _spec: True)
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
                "optional_connectors": [
                    {
                        "id": "lab_rest",
                        "target_name_prefix": "Lab_REST",
                        "probe": "tcp:example.com:443",
                        "forbidden_pattern_substrings": ["CREDIT_CARD"],
                        "max_forbidden_matches": 0,
                        "tables": ["application_findings"],
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
            CREATE TABLE scan_failures (
                session_id TEXT,
                target_name TEXT,
                reason TEXT
            );
            """
        )
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO scan_sessions VALUES (?, ?, ?)",
            ("sess-rest", ts, "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            ("sess-rest", "Data_Soup", "LGPD_CPF"),
        )
        conn.execute(
            "INSERT INTO application_findings VALUES (?, ?, ?)",
            ("sess-rest", "Lab_REST_Httpbin", "CREDIT_CARD"),
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("forbidden_pattern_substrings" in e for e in errs)


def test_optional_rest_forbidden_without_findings_rows_passes_with_no_scan_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#1983 — httpbin may yield zero scoped findings; require_no_scan_failure suffices."""
    monkeypatch.setattr(sentinel_mod, "_probe_reachable", lambda _spec: True)
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
                "optional_connectors": [
                    {
                        "id": "lab_rest_application",
                        "target_name_prefix": "Lab_REST",
                        "probe": "tcp:httpbin.org:443",
                        "require_no_scan_failure": True,
                        "forbidden_pattern_substrings": ["CREDIT_CARD"],
                        "max_forbidden_matches": 0,
                        "tables": ["application_findings"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    db = tmp_path / "sentinel.db"
    _write_rest_optional_db(
        db, session_id="sess-rest-zero-app", filesystem_pattern="LGPD_CPF"
    )
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert errs == []


def test_max_count_rule_scope_empty_not_silent_pass(tmp_path: Path) -> None:
    """Wrong target_name_prefix must not vacuously pass max_count (#1981)."""
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
                "optional_connectors": [
                    {
                        "id": "typo_prefix",
                        "target_name_prefix": "Lab_TYPO",
                        "pattern": "CREDIT_CARD",
                        "max_count": 0,
                        "tables": ["application_findings"],
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
            ("sess-scope", ts, "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            ("sess-scope", "Data_Soup", "LGPD_CPF"),
        )
        conn.execute(
            "INSERT INTO application_findings VALUES (?, ?, ?)",
            ("sess-scope", "Lab_Postgres_RC", "CREDIT_CARD"),
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("scope_empty" in e and "Lab_TYPO" in e for e in errs)


def test_max_count_fails_when_credit_card_in_scoped_target(
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
                "optional_connectors": [
                    {
                        "id": "lab_rest_cap",
                        "target_name_prefix": "Lab_REST",
                        "pattern": "CREDIT_CARD",
                        "max_count": 0,
                        "tables": ["application_findings"],
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
            ("sess-cap-cc", ts, "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            ("sess-cap-cc", "Data_Soup", "LGPD_CPF"),
        )
        conn.execute(
            "INSERT INTO application_findings VALUES (?, ?, ?)",
            ("sess-cap-cc", "Lab_REST_Httpbin", "CREDIT_CARD"),
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("max_count" in e and "lab_rest_cap" in e for e in errs)


def test_target_prefix_like_does_not_match_underscore_wildcard(
    tmp_path: Path,
) -> None:
    """Lab_REST prefix must not match LabXREST (SQLite LIKE _ is one char)."""
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
                "optional_connectors": [
                    {
                        "id": "lab_rest_only",
                        "target_name_prefix": "Lab_REST",
                        "pattern": "CREDIT_CARD",
                        "max_count": 0,
                        "tables": ["application_findings"],
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
            ("sess-like", ts, "completed"),
        )
        conn.execute(
            "INSERT INTO filesystem_findings VALUES (?, ?, ?)",
            ("sess-like", "Data_Soup", "LGPD_CPF"),
        )
        conn.execute(
            "INSERT INTO application_findings VALUES (?, ?, ?)",
            ("sess-like", "LabXREST_Noise", "CREDIT_CARD"),
        )
        conn.commit()
    finally:
        conn.close()
    errs = sentinel_mod._check_findings_sentinel(cfg, spec, db)
    assert any("scope_empty" in e and "Lab_REST" in e for e in errs)


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
