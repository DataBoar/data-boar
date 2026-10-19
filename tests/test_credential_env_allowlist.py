"""Non-REST pass_from_env must reuse the #1977 prefix and host allowlist (#2086)."""

from __future__ import annotations

import pytest

from config.loader import normalize_config
from core.findings_sink import _sqlalchemy_url


def _database_target(**extra: object) -> dict:
    target: dict = {
        "name": "db1",
        "type": "database",
        "host": "attacker.example",
        "pass_from_env": "LAB_PG_PASSWORD",
    }
    target.update(extra)
    return {
        "targets": [target],
        "api": {},
        "report": {"output_dir": "."},
    }


@pytest.mark.parametrize("kind", ["database", "mongodb", "redis", "smb"])
def test_non_rest_pass_from_env_rejects_non_prefixed_name(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LAB_PG_PASSWORD", "db-secret")
    data = _database_target(type=kind, allowed_hosts=["attacker.example"])
    with pytest.raises(ValueError, match="pass_from_env.*#1977"):
        normalize_config(data)


def test_sql_pass_from_env_rejects_host_outside_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_DB_PASSWORD", "db-secret")
    data = _database_target(
        pass_from_env="API_DB_PASSWORD",
        allowed_hosts=["db.trusted.example"],
    )
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        normalize_config(data)


def test_sql_pass_from_env_copies_only_allowlisted_prefixed_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_DB_PASSWORD", "db-secret")
    data = _database_target(
        pass_from_env="API_DB_PASSWORD",
        allowed_hosts=["attacker.example"],
    )
    out = normalize_config(data)
    assert out["targets"][0]["pass"] == "db-secret"


def test_findings_sink_pass_from_env_rejects_non_prefixed_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LAB_PG_PASSWORD", "sink-secret")
    cfg = {
        "type": "postgresql",
        "host": "attacker.example",
        "database": "audit",
        "user": "scanner",
        "pass_from_env": "LAB_PG_PASSWORD",
        "allowed_hosts": ["attacker.example"],
    }
    with pytest.raises(ValueError, match="pass_from_env.*#1977"):
        _sqlalchemy_url(cfg)
