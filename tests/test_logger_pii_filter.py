"""#1722: logging Filter on get_logger + anti-str(e) log-call gate."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import logging
import time

import pytest

from tests.str_e_callsite_gate import (
    SCAN_DIRS,
    classify_str_e_in_source,
    scan_tree,
)
from utils.logger import (
    SANITIZE_LOG_FILTER_NAME,
    configure_audit_log_directory,
    get_logger,
)

REPO = Path(__file__).resolve().parents[1]

# Justified remaining log-call sites: Filter redacts; ADR-0036 decision 4.
LOG_STR_E_ALLOWLIST: dict[tuple[str, str], str] = {
    ("connectors/sql_connector.py", "sample"): (
        "warning after save_failure; SanitizeLogFilter redacts err=%s"
    ),
    ("core/detector.py", "_predict_ml_confidence"): (
        "ML fallback warning; SanitizeLogFilter redacts exception text"
    ),
}

# Snapshot of the #1722 survey (connectors/core/app/api). Counts, not line numbers.
# persist = save_failure (sanitized in LocalDBManager); logger = log call;
# inert = raise/print/UI/dict/control-flow — not a log or SQLite details sink.
EXPECTED_STR_E_COUNTS: Counter[tuple[str, str, str]] = Counter(
    {
        ("api/routes.py", "scan_database", "inert"): 1,
        ("app/dashboard.py", "main", "inert"): 1,
        ("connectors/dataverse_connector.py", "run", "persist"): 2,
        ("connectors/hubspot_connector.py", "run", "persist"): 1,
        ("connectors/mongodb_connector.py", "run", "persist"): 2,
        ("connectors/mongodb_connector.py", "_save_inventory_snapshot", "inert"): 1,
        ("connectors/powerbi_connector.py", "run", "persist"): 2,
        ("connectors/redis_connector.py", "run", "persist"): 2,
        ("connectors/redis_connector.py", "_save_inventory_snapshot", "inert"): 1,
        ("connectors/rest_connector.py", "run", "persist"): 1,
        ("connectors/sharepoint_connector.py", "run", "persist"): 1,
        ("connectors/smb_connector.py", "_run_registered_session", "persist"): 2,
        ("connectors/snowflake_connector.py", "run", "persist"): 2,
        ("connectors/sql_connector.py", "sample", "logger"): 1,
        ("connectors/sql_connector.py", "run", "persist"): 2,
        ("connectors/webdav_connector.py", "run", "persist"): 2,
        ("core/archives.py", "normalize_compressed_extensions", "inert"): 1,
        ("core/archives.py", "_norm_content_extensions", "inert"): 1,
        ("core/archives.py", "classify_zip_member_read_failure", "inert"): 1,
        ("core/archives.py", "classify_7z_member_read_failure", "inert"): 1,
        ("core/detector.py", "_predict_ml_confidence", "logger"): 1,
        ("core/engine.py", "_compute_config_scope_hash", "inert"): 1,
        ("core/engine.py", "start_audit", "inert"): 1,
        ("core/findings_sink.py", "push_session_to_sink", "inert"): 1,
        ("core/findings_sink.py", "maybe_push_findings_sink", "persist"): 1,
        ("core/integrity_anchor.py", "ensure_integrity_anchor", "inert"): 1,
        (
            "core/sdk/boar_fast_filter_dogfood.py",
            "filter_batch_with_mutual_attestation",
            "inert",
        ): 2,
    }
)

DSN_WITH_PASSWORD = "postgresql://user:hunter2secret@db.example.com:5432/app"


@pytest.fixture
def audit_log_dir(tmp_path: Path):
    configure_audit_log_directory(tmp_path)
    yield tmp_path
    configure_audit_log_directory(None)


def test_get_logger_warning_redacts_dsn_password(audit_log_dir: Path, caplog) -> None:
    logger = get_logger()
    assert any(
        getattr(f, "name", None) == SANITIZE_LOG_FILTER_NAME for f in logger.filters
    )
    with caplog.at_level(logging.WARNING, logger="LGPDAudit"):
        logger.warning("%s", DSN_WITH_PASSWORD)
    assert "hunter2secret" not in caplog.text
    assert "***REDACTED***" in caplog.text
    log_files = list(audit_log_dir.glob("audit_*.log"))
    assert log_files
    body = log_files[0].read_text(encoding="utf-8")
    assert "hunter2secret" not in body
    assert "***REDACTED***" in body


def test_sanitize_filter_overhead_measured(audit_log_dir: Path) -> None:
    """Measured cost (not a guess). Generous CI bound; ADR records the lab number."""
    logger = get_logger()
    n = 400
    t0 = time.perf_counter()
    for _ in range(n):
        logger.warning("dsn=%s", DSN_WITH_PASSWORD)
    elapsed_s = time.perf_counter() - t0
    per_call_us = (elapsed_s / n) * 1_000_000
    # Lab (Linux primary, 2026-09-12): ~80–200 µs/call including FileHandler I/O.
    # Fail only if the Filter+I/O path becomes pathologically slow (seconds).
    assert per_call_us < 50_000, (
        f"sanitize filter path too slow: {per_call_us:.1f} µs/call"
    )
    assert elapsed_s > 0


def test_str_e_survey_matches_snapshot() -> None:
    sites = scan_tree(REPO, SCAN_DIRS)
    got = Counter((s.path, s.func, s.kind) for s in sites)
    assert got == EXPECTED_STR_E_COUNTS, (
        "str(e) survey drifted — update EXPECTED_STR_E_COUNTS with justification. "
        f"only_in_got={got - EXPECTED_STR_E_COUNTS} "
        f"only_in_expected={EXPECTED_STR_E_COUNTS - got}"
    )
    kind_totals = Counter(s.kind for s in sites)
    assert kind_totals["logger"] == 2
    assert kind_totals["persist"] == 20
    assert kind_totals["inert"] == 14


def test_logger_str_e_sites_are_allowlisted() -> None:
    sites = scan_tree(REPO, SCAN_DIRS)
    logger_keys = {(s.path, s.func) for s in sites if s.kind == "logger"}
    extra = logger_keys - set(LOG_STR_E_ALLOWLIST)
    missing = set(LOG_STR_E_ALLOWLIST) - logger_keys
    assert not extra, f"new logger str(e) without allowlist justification: {extra}"
    assert not missing, f"allowlist stale (site gone): {missing}"


def test_gate_detects_logger_str_e_and_ignores_save_failure() -> None:
    """Self-test of the gate (precedent: tests/test_commit_no_tool_coauthorship.py)."""
    log_src = "def boom(e):\n    get_logger().warning('%s', str(e))\n"
    persist_src = "def boom(e):\n    db.save_failure('t', 'error', str(e))\n"
    log_sites = classify_str_e_in_source(log_src, rel_path="fake/mod.py")
    persist_sites = classify_str_e_in_source(persist_src, rel_path="fake/mod.py")
    assert [s.kind for s in log_sites] == ["logger"]
    assert [s.kind for s in persist_sites] == ["persist"]
    assert ("fake/mod.py", "boom") not in LOG_STR_E_ALLOWLIST
