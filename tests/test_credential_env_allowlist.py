"""Non-REST pass_from_env must reuse the #1977 prefix and host allowlist (#2086)."""

from __future__ import annotations

import ast
from pathlib import Path

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


@pytest.mark.parametrize("kind", ["dataverse", "powerapps"])
def test_org_and_token_url_must_both_be_allowlisted(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_DV_SECRET", "dv-secret")
    target = {
        "name": kind,
        "type": kind,
        "org_url": "https://org.crm.dynamics.com",
        "client_secret_from_env": "API_DV_SECRET",
        "auth": {"token_url": "https://evil.example/oauth/token"},
        "allowed_hosts": ["org.crm.dynamics.com"],
    }
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        normalize_config(
            {"targets": [target], "api": {}, "report": {"output_dir": "."}}
        )


@pytest.mark.parametrize("kind", ["dataverse", "powerapps"])
def test_org_and_token_url_copy_when_both_allowlisted(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_DV_SECRET", "dv-secret")
    target = {
        "name": kind,
        "type": kind,
        "org_url": "https://org.crm.dynamics.com",
        "client_secret_from_env": "API_DV_SECRET",
        "auth": {
            "token_url": "https://login.microsoftonline.com/tenant/oauth2/v2.0/token"
        },
        "allowed_hosts": ["org.crm.dynamics.com", "login.microsoftonline.com"],
    }
    out = normalize_config(
        {"targets": [target], "api": {}, "report": {"output_dir": "."}}
    )
    assert out["targets"][0]["client_secret"] == "dv-secret"


def test_reserved_process_env_name_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A name this process reserves is not a target credential."""
    from config.loader import BOAR_INTERNAL_ENV_NAMES

    reserved = sorted(BOAR_INTERNAL_ENV_NAMES)[0]
    monkeypatch.setenv(reserved, "unit-test-value")
    data = _database_target(
        pass_from_env=reserved,
        allowed_hosts=["attacker.example"],
    )
    with pytest.raises(ValueError, match="reserved for this process"):
        normalize_config(data)


def test_operator_prefixed_name_still_copies(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public prefix list still accepts an operator credential name."""
    monkeypatch.setenv("DATA_BOAR_DEMO_DB_PASSWORD", "db-secret")
    data = _database_target(
        pass_from_env="DATA_BOAR_DEMO_DB_PASSWORD",
        allowed_hosts=["attacker.example"],
    )
    out = normalize_config(data)
    assert out["targets"][0]["pass"] == "db-secret"


def test_config_resolved_internal_env_name_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A name the config uses for an internal secret cannot also be a target credential."""
    monkeypatch.setenv("DATA_BOAR_LAB_DB_PASSWORD", "db-secret")
    data = _database_target(
        pass_from_env="DATA_BOAR_LAB_DB_PASSWORD",
        allowed_hosts=["attacker.example"],
    )
    data["api"] = {"api_key_from_env": "DATA_BOAR_LAB_DB_PASSWORD"}
    with pytest.raises(ValueError, match="reserved for this process"):
        normalize_config(data)


def test_reserved_name_match_ignores_case(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reserved name is refused even when its letters change case."""
    from config.loader import BOAR_INTERNAL_ENV_NAMES

    reserved = sorted(BOAR_INTERNAL_ENV_NAMES)[0].swapcase()
    monkeypatch.setenv(reserved, "unit-test-value")
    data = _database_target(pass_from_env=reserved, allowed_hosts=["attacker.example"])
    with pytest.raises(ValueError, match="reserved for this process"):
        normalize_config(data)


def test_vendor_client_secret_interpolation_stays_valid() -> None:
    """Unprefixed vendor names in client_secret stay accepted."""
    data = {
        "targets": [
            {
                "name": "pbi",
                "type": "powerbi",
                "auth": {"client_secret": "${POWERBI_CLIENT_SECRET}"},
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    out = normalize_config(data)
    assert out["targets"][0]["auth"]["client_secret"] == "${POWERBI_CLIENT_SECRET}"


def test_reserved_name_inside_client_secret_interpolation_is_refused() -> None:
    """A reserved name inside a client_secret placeholder is refused."""
    from config.loader import BOAR_INTERNAL_ENV_NAMES

    reserved = sorted(BOAR_INTERNAL_ENV_NAMES)[0]
    data = {
        "targets": [
            {
                "name": "pbi",
                "type": "powerbi",
                "auth": {"client_secret": "${" + reserved + "}"},
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    with pytest.raises(ValueError, match="reserved for this process"):
        normalize_config(data)


def _env_name_literals(node: ast.AST) -> set[str]:
    found: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Constant) or not isinstance(child.value, str):
            continue
        if child.value.startswith("DATA_BOAR_") and child.value.isupper():
            found.add(child.value)
    return found


def _assigned_env_names(tree: ast.AST) -> dict[str, set[str]]:
    assigned: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        target = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if isinstance(target, ast.Name) and value is not None:
            names = _env_name_literals(value)
            if names:
                assigned.setdefault(target.id, set()).update(names)
    return assigned


def _is_env_read(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr in {"get", "getenv", "pop"}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id == "getenv"
    return isinstance(node, ast.Subscript)


def data_boar_env_names_read_by_source(root: Path) -> set[str]:
    """DATA_BOAR_* names passed to an environment read in product code."""
    found: set[str] = set()
    for folder in ("core", "api", "config", "scripts"):
        for path in (root / folder).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            assigned = _assigned_env_names(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"get", "getenv", "pop"} and node.args:
                        found.update(_env_name_literals(node.args[0]))
                        if isinstance(node.args[0], ast.Name):
                            found.update(assigned.get(node.args[0].id, set()))
                if isinstance(node, ast.Subscript):
                    found.update(_env_name_literals(node.slice))
                    slice_name = node.slice
                    if isinstance(slice_name, ast.Name):
                        found.update(assigned.get(slice_name.id, set()))
                if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                    if any(_is_env_read(child) for child in ast.walk(node)):
                        found.update(_env_name_literals(node.iter))
    return found


def test_source_scan_classifies_every_data_boar_env_read() -> None:
    """Every DATA_BOAR_* environment read is internal-refused or operator-allowed."""
    from config.loader import BOAR_INTERNAL_ENV_NAMES, OPERATIONAL_ENV_NAMES

    root = Path(__file__).resolve().parents[1]
    read = data_boar_env_names_read_by_source(root)
    classified = BOAR_INTERNAL_ENV_NAMES | OPERATIONAL_ENV_NAMES
    assert not (BOAR_INTERNAL_ENV_NAMES & OPERATIONAL_ENV_NAMES)
    assert not (read - classified), sorted(read - classified)
    assert read
