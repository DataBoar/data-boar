"""
QA local license issuer contract (enforcement wave PR2).

The env bypass was removed (#719); ``scripts/issue_dev_license_jwt.py`` is the
only QA path for ``licensing.mode: enforced``. Contract:

- default expiry **60 days** (short-lived);
- default tier **enterprise**;
- default ``dbmfp`` binding to the issuing machine (``--dbmfp auto``);
- bound license validates on the bound machine and dies elsewhere.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUER = REPO_ROOT / "scripts" / "issue_dev_license_jwt.py"


@pytest.fixture
def keypair(tmp_path):
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    priv_path = tmp_path / "priv.pem"
    priv_path.write_bytes(priv_pem)
    return priv_path, pub_pem.decode("ascii"), priv.public_key()


@pytest.fixture(autouse=True)
def _clean_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


def _run_issuer(*argv: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(ISSUER), *argv],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_issuer_defaults_60d_enterprise_machine_bound(keypair):
    priv_path, _pub_pem, pub_key = keypair
    token = _run_issuer("--private-key-pem-file", str(priv_path))
    claims = jwt.decode(token, pub_key, algorithms=["EdDSA"])
    assert claims["dbtier"] == "enterprise"
    # 60-day default expiry (allow scheduling slack of a few minutes).
    lifetime_days = (claims["exp"] - claims["iat"]) / 86400
    assert 59.9 <= lifetime_days <= 60.1
    # Machine-bound by default to the issuing machine.
    assert claims["dbmfp"] == compute_machine_fingerprint()


def test_issuer_show_machine_fingerprint(keypair):
    out = _run_issuer("--show-machine-fingerprint")
    assert out == compute_machine_fingerprint()


def test_issuer_dbmfp_none_unbound(keypair):
    priv_path, _pub_pem, pub_key = keypair
    token = _run_issuer("--private-key-pem-file", str(priv_path), "--dbmfp", "none")
    claims = jwt.decode(token, pub_key, algorithms=["EdDSA"])
    assert "dbmfp" not in claims


def test_bound_license_valid_on_this_machine(keypair, tmp_path):
    priv_path, pub_pem, _pub_key = keypair
    lic = tmp_path / "qa.lic"
    _run_issuer("--private-key-pem-file", str(priv_path), "--out", str(lic))
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pub_pem
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "VALID"
    assert g.context.dbtier == "enterprise"
    assert g.allows_scan() is True


def test_bound_license_rejected_on_other_machine(keypair, tmp_path):
    priv_path, pub_pem, _pub_key = keypair
    lic = tmp_path / "qa.lic"
    _run_issuer(
        "--private-key-pem-file",
        str(priv_path),
        "--dbmfp",
        "f" * 64,  # some other machine's fingerprint
        "--out",
        str(lic),
    )
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pub_pem
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "MACHINE_MISMATCH"
    assert g.allows_scan() is False


def test_maestro_handler_issues_60d_machine_bound():
    """Handle-LicensingMatrix.ps1 passes --days 60 and --dbmfp auto (#719)."""
    src = (REPO_ROOT / "scripts" / "maestro" / "Handle-LicensingMatrix.ps1").read_text(
        encoding="utf-8"
    )
    assert "--days 60" in src
    assert "--dbmfp auto" in src
