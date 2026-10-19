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


def test_sharepoint_pass_from_env_accepts_site_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_SP_PASSWORD", "sp-secret")
    data = {
        "targets": [
            {
                "name": "sp",
                "type": "sharepoint",
                "site_url": "https://sharepoint.example/sites/hr",
                "pass_from_env": "API_SP_PASSWORD",
                "allowed_hosts": ["sharepoint.example"],
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    out = normalize_config(data)
    assert out["targets"][0]["pass"] == "sp-secret"


def test_snowflake_pass_from_env_accepts_account_or_derived_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_SF_PASSWORD", "sf-secret")
    base = {
        "name": "sf",
        "type": "snowflake",
        "account": "xy12345.us-east-1",
        "user": "loader",
        "pass_from_env": "API_SF_PASSWORD",
    }
    for allowed in (
        ["xy12345.us-east-1"],
        ["xy12345.us-east-1.snowflakecomputing.com"],
    ):
        data = {
            "targets": [{**base, "allowed_hosts": allowed}],
            "api": {},
            "report": {"output_dir": "."},
        }
        out = normalize_config(data)
        assert out["targets"][0]["pass"] == "sf-secret"


@pytest.mark.parametrize(
    ("kind", "fields", "allowed"),
    [
        ("database", {"host": "db.example"}, ["db.example"]),
        ("mongodb", {"host": "mongo.example"}, ["mongo.example"]),
        ("redis", {"host": "redis.example"}, ["redis.example"]),
        ("smb", {"host": "files.example"}, ["files.example"]),
        ("cifs", {"host": "files.example"}, ["files.example"]),
        ("nfs", {"server": "nas.example"}, ["nas.example"]),
        (
            "sharepoint",
            {"site_url": "https://sharepoint.example/sites/hr"},
            ["sharepoint.example"],
        ),
        (
            "webdav",
            {"base_url": "https://dav.example/remote.php"},
            ["dav.example"],
        ),
        (
            "snowflake",
            {"account": "xy12345.us-east-1"},
            ["xy12345.us-east-1.snowflakecomputing.com"],
        ),
        (
            "dataverse",
            {"org_url": "https://org.crm.dynamics.com"},
            ["org.crm.dynamics.com"],
        ),
        (
            "powerapps",
            {"environment_url": "https://org.crm.dynamics.com"},
            ["org.crm.dynamics.com"],
        ),
    ],
)
def test_non_rest_env_credential_copies_when_destination_allowlisted(
    kind: str, fields: dict, allowed: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_TARGET_SECRET", "copied-secret")
    target = {
        "name": kind,
        "type": kind,
        "pass_from_env": "API_TARGET_SECRET",
        "allowed_hosts": allowed,
        **fields,
    }
    out = normalize_config(
        {"targets": [target], "api": {}, "report": {"output_dir": "."}}
    )
    assert out["targets"][0]["pass"] == "copied-secret"


@pytest.mark.parametrize(
    ("kind", "fields"),
    [
        ("database", {"host": "db.example"}),
        ("mongodb", {"host": "mongo.example"}),
        ("redis", {"host": "redis.example"}),
        ("smb", {"host": "files.example"}),
        ("cifs", {"host": "files.example"}),
        ("nfs", {"server": "nas.example"}),
        ("webdav", {"base_url": "https://dav.example/remote.php"}),
        ("sharepoint", {"site_url": "https://sharepoint.example/sites/hr"}),
        ("snowflake", {"account": "xy12345.us-east-1"}),
        ("dataverse", {"org_url": "https://org.crm.dynamics.com"}),
    ],
)
def test_non_rest_env_credential_rejects_other_host(
    kind: str, fields: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_TARGET_SECRET", "copied-secret")
    target = {
        "name": kind,
        "type": kind,
        "pass_from_env": "API_TARGET_SECRET",
        "allowed_hosts": ["other.example"],
        **fields,
    }
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        normalize_config(
            {"targets": [target], "api": {}, "report": {"output_dir": "."}}
        )


def test_hubspot_token_from_env_keeps_vendor_host_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_HUBSPOT_TOKEN", "pat-secret")
    out = normalize_config(
        {
            "targets": [
                {
                    "name": "crm",
                    "type": "hubspot",
                    "auth": {"token_from_env": "API_HUBSPOT_TOKEN"},
                }
            ],
            "api": {},
            "report": {"output_dir": "."},
        }
    )
    assert out["targets"][0]["auth"]["token"] == "pat-secret"


def test_findings_sink_pass_from_env_rejects_other_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_SINK_PASSWORD", "sink-secret")
    cfg = {
        "type": "postgresql",
        "host": "attacker.example",
        "database": "audit",
        "user": "scanner",
        "pass_from_env": "API_SINK_PASSWORD",
        "allowed_hosts": ["db.trusted.example"],
    }
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        _sqlalchemy_url(cfg)


def test_findings_sink_pass_from_env_accepts_allowlisted_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_SINK_PASSWORD", "sink-secret")
    cfg = {
        "type": "postgresql",
        "host": "db.trusted.example",
        "database": "audit",
        "user": "scanner",
        "pass_from_env": "API_SINK_PASSWORD",
        "allowed_hosts": ["db.trusted.example"],
    }
    url = _sqlalchemy_url(cfg)
    assert "sink-secret" in url
    assert "db.trusted.example" in url


def test_powerbi_client_secret_from_env_uses_vendor_token_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_PBI_SECRET", "pbi-secret")
    data = {
        "targets": [
            {
                "name": "pbi",
                "type": "powerbi",
                "tenant_id": "tenant",
                "client_id": "client",
                "client_secret_from_env": "API_PBI_SECRET",
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    out = normalize_config(data)
    assert out["targets"][0]["client_secret"] == "pbi-secret"
