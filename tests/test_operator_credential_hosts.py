"""Operator host list for env credentials (#2103)."""

from __future__ import annotations

import logging

import pytest

from config.loader import (
    _operator_host_key,
    enforce_operator_credential_host_gate,
    normalize_config,
)
from core.findings_sink import _sqlalchemy_url

_HOSTS = "DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS"
_OPEN = "DATA_BOAR_CREDENTIAL_HOSTS_UNRESTRICTED"


def _clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_HOSTS, raising=False)
    monkeypatch.delenv(_OPEN, raising=False)


def _db(monkeypatch: pytest.MonkeyPatch, **fields: object) -> dict:
    monkeypatch.setenv("API_DB_PASSWORD", "db-secret")
    target = {
        "name": "db",
        "type": "database",
        "host": "db.trusted.example",
        "user": "scanner",
        "pass_from_env": "API_DB_PASSWORD",
        "allowed_hosts": ["db.trusted.example"],
    }
    target.update(fields)
    return {
        "targets": [target],
        "api": {},
        "report": {"output_dir": "."},
    }


def test_operator_host_key_drops_port_and_brackets() -> None:
    assert _operator_host_key("DB.Example:5432") == "db.example"
    assert _operator_host_key("[2001:db8::1]:5432") == "2001:db8::1"
    assert _operator_host_key("2001:db8::1") == "2001:db8::1"
    assert _operator_host_key("https://DB.Example:443/path") == "db.example"


def test_unset_list_fails_closed_for_env_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    with pytest.raises(ValueError, match=_HOSTS):
        normalize_config(_db(monkeypatch))
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    rest = {
        "targets": [
            {
                "name": "api",
                "type": "api",
                "base_url": "https://api.trusted.example",
                "auth": {
                    "token_from_env": "API_REST_TOKEN",
                    "allowed_hosts": ["api.trusted.example"],
                },
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    with pytest.raises(ValueError, match=_HOSTS):
        normalize_config(rest)
    sink = {
        "type": "postgresql",
        "host": "db.trusted.example",
        "database": "audit",
        "user": "scanner",
        "pass_from_env": "API_DB_PASSWORD",
        "allowed_hosts": ["db.trusted.example"],
    }
    with pytest.raises(ValueError, match=_HOSTS):
        _sqlalchemy_url(sink)


def test_inline_secret_does_not_need_the_operator_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    out = normalize_config(
        {
            "targets": [
                {
                    "name": "db",
                    "type": "database",
                    "host": "db.trusted.example",
                    "user": "scanner",
                    "password": "inline",
                }
            ],
            "api": {},
            "report": {"output_dir": "."},
        }
    )
    assert out["targets"][0]["password"] == "inline"


def test_yaml_host_outside_operator_list_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "db.trusted.example")
    with pytest.raises(ValueError, match="only narrow"):
        normalize_config(
            _db(monkeypatch, allowed_hosts=["db.trusted.example", "other.example"])
        )
    monkeypatch.setenv(_HOSTS, "api.trusted.example")
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    rest = {
        "targets": [
            {
                "name": "api",
                "type": "api",
                "base_url": "https://api.trusted.example",
                "auth": {
                    "token_from_env": "API_REST_TOKEN",
                    "allowed_hosts": ["other.example"],
                },
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    with pytest.raises(ValueError, match="only narrow"):
        normalize_config(rest)
    monkeypatch.setenv(_HOSTS, "db.trusted.example")
    sink = {
        "type": "postgresql",
        "host": "db.trusted.example",
        "database": "audit",
        "user": "scanner",
        "pass_from_env": "API_DB_PASSWORD",
        "allowed_hosts": ["other.example"],
    }
    with pytest.raises(ValueError, match="only narrow"):
        _sqlalchemy_url(sink)


def test_yaml_narrows_and_does_not_widen(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "db.trusted.example,other.example")
    out = normalize_config(_db(monkeypatch))
    assert out["targets"][0]["pass"] == "db-secret"
    monkeypatch.setenv(_HOSTS, "other.example")
    with pytest.raises(ValueError, match="outside"):
        normalize_config(_db(monkeypatch))


def test_opt_out_restores_yaml_gate_and_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_OPEN, "1")
    with caplog.at_level(logging.WARNING):
        out = normalize_config(_db(monkeypatch))
    assert out["targets"][0]["pass"] == "db-secret"
    assert _OPEN in caplog.text
    with pytest.raises(ValueError, match="allowed_hosts"):
        normalize_config(_db(monkeypatch, allowed_hosts=["other.example"]))


def test_yaml_cannot_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    with pytest.raises(ValueError, match=_HOSTS):
        normalize_config(
            _db(
                monkeypatch,
                credential_hosts_unrestricted=True,
            )
        )


def test_reserved_operator_names_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "db.trusted.example")
    for name in (_HOSTS, _HOSTS.swapcase(), _OPEN, _OPEN.casefold()):
        with pytest.raises(ValueError, match="reserved"):
            normalize_config(_db(monkeypatch, pass_from_env=name))
    for secret in (
        "${DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS}",
        "${data_boar_credential_hosts_unrestricted}",
    ):
        data = {
            "targets": [
                {
                    "name": "pbi",
                    "type": "powerbi",
                    "tenant_id": "tenant",
                    "client_id": "client",
                    "client_secret": secret,
                    "allowed_hosts": ["login.microsoftonline.com"],
                }
            ],
            "api": {},
            "report": {"output_dir": "."},
        }
        with pytest.raises(ValueError, match="reserved"):
            normalize_config(data)


def test_mixed_group_and_empty_key_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "listed.example")
    with pytest.raises(ValueError, match="outside"):
        enforce_operator_credential_host_gate(
            [{"listed.example", "other.example"}], "target"
        )
    with pytest.raises(ValueError, match="outside"):
        enforce_operator_credential_host_gate([{""}], "target")
    with pytest.raises(ValueError, match="outside"):
        enforce_operator_credential_host_gate([set()], "target")


def test_rest_without_destination_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "api.trusted.example")
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    data = {
        "targets": [
            {
                "name": "api",
                "type": "api",
                "auth": {"token_from_env": "API_REST_TOKEN"},
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }
    with pytest.raises(ValueError, match="outside"):
        normalize_config(data)


def _rest_with_discover(discover_url: str, hosts: list[str]) -> dict:
    return {
        "targets": [
            {
                "name": "api",
                "type": "api",
                "base_url": "https://api.trusted.example",
                "discover_url": discover_url,
                "auth": {
                    "type": "bearer",
                    "token_from_env": "API_REST_TOKEN",
                    "allowed_hosts": hosts,
                },
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }


def test_discover_url_outside_operator_list_rejected_at_load_and_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from connectors.rest_connector import _assert_rest_credential_hosts_allowlisted

    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "api.trusted.example")
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    data = _rest_with_discover(
        "https://other.example/openapi.json",
        ["api.trusted.example", "other.example"],
    )
    with pytest.raises(ValueError, match="outside"):
        normalize_config(data)
    with pytest.raises(ValueError, match="outside"):
        _assert_rest_credential_hosts_allowlisted(data["targets"][0])


def test_discover_url_on_operator_list_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from connectors.rest_connector import _assert_rest_credential_hosts_allowlisted

    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "api.trusted.example,other.example")
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    data = _rest_with_discover(
        "https://other.example/openapi.json",
        ["api.trusted.example", "other.example"],
    )
    out = normalize_config(data)
    assert out["targets"][0]["auth"]["token"] == "rest-secret"
    _assert_rest_credential_hosts_allowlisted(data["targets"][0])


def test_discover_url_without_host_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from connectors.rest_connector import _assert_rest_credential_hosts_allowlisted

    _clear(monkeypatch)
    monkeypatch.setenv(_HOSTS, "api.trusted.example")
    monkeypatch.setenv("API_REST_TOKEN", "rest-secret")
    data = _rest_with_discover("/openapi.json", ["api.trusted.example"])
    with pytest.raises(ValueError, match="outside"):
        normalize_config(data)
    with pytest.raises(ValueError, match="outside"):
        _assert_rest_credential_hosts_allowlisted(data["targets"][0])
