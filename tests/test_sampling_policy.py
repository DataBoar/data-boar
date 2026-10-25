"""Unit tests for hierarchical SQL sample limits (core.sampling_policy)."""

from connectors.sql_sampling import SamplingManager
from core.sampling_policy import SamplingPolicy


def _cfg(overrides: dict) -> dict:
    return {"sql_sampling": {"overrides": overrides}}


def test_policy_global_only():
    p = SamplingPolicy.from_config({})
    assert (
        p.get_effective_sample_limit(
            target_name="any",
            schema="public",
            table="users",
            global_limit=10,
        )
        == 10
    )


def test_policy_target_sample_limit():
    p = SamplingPolicy.from_config(
        _cfg(
            {
                "targets": {"slow_db": {"sample_limit": 3}},
                "patterns": {},
            }
        )
    )
    assert (
        p.get_effective_sample_limit(
            target_name="slow_db",
            schema="public",
            table="any_table",
            global_limit=50,
        )
        == 3
    )
    assert (
        p.get_effective_sample_limit(
            target_name="other",
            schema="public",
            table="any_table",
            global_limit=50,
        )
        == 50
    )


def test_policy_table_overrides_target():
    p = SamplingPolicy.from_config(
        _cfg(
            {
                "targets": {
                    "prod": {
                        "sample_limit": 5,
                        "tables": {"public.huge": 500, "tiny": 2},
                    }
                },
                "patterns": {},
            }
        )
    )
    assert (
        p.get_effective_sample_limit(
            target_name="prod",
            schema="public",
            table="huge",
            global_limit=10,
        )
        == 500
    )
    assert (
        p.get_effective_sample_limit(
            target_name="prod",
            schema="",
            table="tiny",
            global_limit=10,
        )
        == 2
    )
    assert (
        p.get_effective_sample_limit(
            target_name="prod",
            schema="public",
            table="other",
            global_limit=10,
        )
        == 5
    )


def test_policy_pattern_fallback():
    p = SamplingPolicy.from_config(
        _cfg(
            {
                "targets": {},
                "patterns": {"*_audit": 80, "*_logs": 40},
            }
        )
    )
    assert (
        p.get_effective_sample_limit(
            target_name="db",
            schema="s",
            table="payments_audit",
            global_limit=10,
        )
        == 80
    )


def test_policy_pattern_after_target_cap():
    """Target-wide limit wins over pattern when both apply."""
    p = SamplingPolicy.from_config(
        _cfg(
            {
                "targets": {"db": {"sample_limit": 7}},
                "patterns": {"*_audit": 99},
            }
        )
    )
    assert (
        p.get_effective_sample_limit(
            target_name="db",
            schema="s",
            table="row_audit",
            global_limit=50,
        )
        == 7
    )


def test_slice_audit_log_pattern_log_overrides_global_five():
    """
    PoC slice scenario: target ``db_prod``, table ``audit_log``, global cap 5,
    pattern ``*_log`` -> 50; SQL must use non-null filter and LIMIT 50 (PostgreSQL).
    """
    p = SamplingPolicy.from_config(_cfg({"targets": {}, "patterns": {"*_log": 50}}))
    lim = p.get_effective_sample_limit(
        target_name="db_prod",
        schema="public",
        table="audit_log",
        global_limit=5,
    )
    assert lim == 50
    plan = SamplingManager.build_column_sample(
        "postgresql",
        safe_col="body",
        safe_table="audit_log",
        safe_schema="public",
        schema="public",
        limit=lim,
        table_metadata=None,
    )
    sql = str(plan.query)
    assert "IS NOT NULL" in sql
    assert "LIMIT 50" in sql


def test_policy_table_beats_pattern():
    p = SamplingPolicy.from_config(
        _cfg(
            {
                "targets": {
                    "db": {
                        "tables": {"public.row_audit": 12},
                    }
                },
                "patterns": {"*_audit": 99},
            }
        )
    )
    assert (
        p.get_effective_sample_limit(
            target_name="db",
            schema="public",
            table="row_audit",
            global_limit=50,
        )
        == 12
    )
