"""Canonical org-wide license path fallback (#1940)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests
from core.licensing.paths import (
    canonical_org_license_jwt_path,
    resolve_license_path,
    user_config_dir,
)
from tests.license_verify_pin import pin_embedded_ed25519_pem as _pin_verify_pem


def _pem_public(priv: Ed25519PrivateKey) -> str:
    pub = priv.public_key()
    return (
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _make_token(priv: Ed25519PrivateKey) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-canonical-1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-1",
        "dbcname": "Canonical Customer",
        "dbenv": "qa",
        "dbissuer": "test-issuer",
        "dbkid": "k1",
    }
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _reset_guard_and_env():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    for k in (
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
    ):
        os.environ.pop(k, None)


def _linux_style_config_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    lic = home / ".config" / "databoar" / "license.jwt"
    lic.parent.mkdir(parents=True)
    return lic


def test_resolve_license_path_unit_precedence(tmp_path, monkeypatch):
    _linux_style_config_home(tmp_path, monkeypatch)
    assert resolve_license_path(None) == ""
    assert resolve_license_path("") == ""
    assert resolve_license_path("   ") == ""


def test_canonical_fallback_valid_license(
    ed25519_priv: Ed25519PrivateKey, tmp_path, monkeypatch
):
    lic = _linux_style_config_home(tmp_path, monkeypatch)
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    _pin_verify_pem(_pem_public(ed25519_priv))
    g = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert g.context.state == "VALID"
    assert g.allows_scan() is True
    assert resolve_license_path(None) == str(lic)


def test_env_explicit_wins_over_canonical_even_when_missing(
    ed25519_priv: Ed25519PrivateKey, tmp_path, monkeypatch
):
    lic = _linux_style_config_home(tmp_path, monkeypatch)
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    missing = tmp_path / "nope.lic"
    monkeypatch.setenv("DATA_BOAR_LICENSE_PATH", str(missing))
    _pin_verify_pem(_pem_public(ed25519_priv))
    g = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert g.context.state == "UNLICENSED"
    assert g.context.detail == "missing_license_file"
    assert resolve_license_path(None) == str(missing)


def test_config_explicit_wins_over_canonical_even_when_missing(
    ed25519_priv: Ed25519PrivateKey, tmp_path, monkeypatch
):
    lic = _linux_style_config_home(tmp_path, monkeypatch)
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    missing = tmp_path / "cfg-missing.lic"
    _pin_verify_pem(_pem_public(ed25519_priv))
    g = LicenseGuard(
        {
            "licensing": {
                "mode": "enforced",
                "license_path": str(missing),
            }
        }
    )
    assert g.context.state == "UNLICENSED"
    assert g.context.detail == "missing_license_file"


def test_whitespace_env_and_config_treated_as_unset(
    ed25519_priv: Ed25519PrivateKey, tmp_path, monkeypatch
):
    lic = _linux_style_config_home(tmp_path, monkeypatch)
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    monkeypatch.setenv("DATA_BOAR_LICENSE_PATH", "  \t  ")
    _pin_verify_pem(_pem_public(ed25519_priv))
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": "  "}})
    assert g.context.state == "VALID"
    assert resolve_license_path("  ") == str(lic)


def test_no_canonical_file_unchanged_unlicensed(tmp_path, monkeypatch, ed25519_priv):
    _linux_style_config_home(tmp_path, monkeypatch)
    _pin_verify_pem(_pem_public(ed25519_priv))
    g = LicenseGuard({"licensing": {"mode": "enforced"}})
    assert g.context.state == "UNLICENSED"
    assert g.context.detail == "missing_license_file"
    assert not canonical_org_license_jwt_path().is_file()


def test_user_config_dir_honors_xdg_config_home(tmp_path, monkeypatch):
    xdg = tmp_path / "xdg"
    xdg.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert user_config_dir() == xdg
    assert canonical_org_license_jwt_path() == xdg / "databoar" / "license.jwt"
