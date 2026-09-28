"""REST pass_from_env egress (#2006): loader → connector path (not hand-built targets)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from config.loader import load_config
from connectors.rest_connector import _build_auth


def _write_and_load_rest_target(tmp_path: Path, *extra_target_lines: str) -> dict:
    extra = ""
    if extra_target_lines:
        extra = "\n".join(f"    {line}" for line in extra_target_lines) + "\n"
    body = f"""targets:
  - name: rest-env-exfil
    type: api
    base_url: https://attacker.example
    paths: ["/json"]
    user: labuser
{extra}report:
  output_dir: .
sqlite_path: audit_loader_test.db
"""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(body, encoding="utf-8")
    return load_config(cfg_path)["targets"][0]


def test_pass_from_env_via_loader_requires_explicit_allowed_hosts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: env password must not use attacker base_url as implicit allowlist (#2006)."""
    monkeypatch.setenv("API_REST_EXFIL_PASS", "stolen-value")
    target = _write_and_load_rest_target(tmp_path, "pass_from_env: API_REST_EXFIL_PASS")
    assert target["pass"] == "stolen-value"
    assert target.get("pass_from_env") == "API_REST_EXFIL_PASS"
    client = SimpleNamespace(headers={}, auth=None)
    with pytest.raises(ValueError, match="allowed_hosts.*#1977"):
        _build_auth(client, target)
    assert client.auth is None


def test_pass_from_env_via_loader_rejects_non_allowlisted_base_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_REST_EXFIL_PASS", "stolen-value")
    target = _write_and_load_rest_target(
        tmp_path,
        "pass_from_env: API_REST_EXFIL_PASS",
        'allowed_hosts: ["api.trusted.example"]',
    )
    client = SimpleNamespace(headers={}, auth=None)
    with pytest.raises(ValueError, match="base_url host.*#1977"):
        _build_auth(client, target)


def test_pass_from_env_via_loader_rejects_disallowed_env_name_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LAB_PG_PASSWORD", "db-secret")
    target = _write_and_load_rest_target(
        tmp_path,
        "pass_from_env: LAB_PG_PASSWORD",
        'allowed_hosts: ["attacker.example"]',
    )
    client = SimpleNamespace(headers={}, auth=None)
    with pytest.raises(ValueError, match="pass_from_env.*#1977"):
        _build_auth(client, target)


def test_pass_from_env_via_loader_allows_explicit_allowlisted_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_REST_OK_PASS", "inline-secret")
    target = _write_and_load_rest_target(
        tmp_path,
        "pass_from_env: API_REST_OK_PASS",
        'allowed_hosts: ["attacker.example"]',
    )
    client = SimpleNamespace(headers={}, auth=None)
    _build_auth(client, target)
    expected = httpx.BasicAuth("labuser", "inline-secret")
    assert client.auth._auth_header == expected._auth_header
