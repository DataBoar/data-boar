"""
#718 + #846 — runtime fingerprint binding (dbmfp single + deployment pack).

Contract under test:

1. Enforced + license bound to the LOCAL fingerprint (single ``dbmfp`` string
   or pack array containing it) → VALID, scan allowed.
2. Enforced + license bound to ANOTHER fingerprint (or a pack without the
   local one) → MACHINE_MISMATCH, fail-closed (scan denied, tier capped to
   Community) + audit CRITICAL — same posture as #719/#847.
3. Enforced + no ``dbmfp`` claim → no binding (current behavior preserved).
4. Open mode → binding never checked.
5. Malformed ``dbmfp`` claim (wrong type) → INVALID, fail-closed — never
   degrades to "unbound".
6. ``dbmax_deployments`` + ``dbdeployment_pack_id`` claims are plumbed into
   ``LicenseContext`` (issuance-enforced count; runtime validates own fp only).
7. Issuer ``--dbmfp-pack`` emits a pack license usable on a pack member.
8. ``DATA_BOAR_MACHINE_SEED`` changes the computed fingerprint (documented
   deployment-stability knob).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import (
    LicenseGuard,
    _parse_dbmfp_claim,
    reset_license_guard_for_tests,
)
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier

AUDIT_LOGGER = "data_boar.licensing.audit"
REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUER = REPO_ROOT / "scripts" / "issue_dev_license_jwt.py"

OTHER_FP = "f" * 64  # a fingerprint that is never the local machine's


def _pem_public(priv: Ed25519PrivateKey) -> str:
    return (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _pem_private(priv: Ed25519PrivateKey) -> str:
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")


def _make_token(priv: Ed25519PrivateKey, *, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-fp-binding",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-1",
        "dbcname": "Test Customer",
        "dbenv": "qa",
        "dbissuer": "test-issuer",
        "dbkid": "k1",
        "dbtier": "enterprise",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _clean_env():
    reset_license_guard_for_tests()
    keys = (
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_REVOCATION_PATH",
        "DATA_BOAR_LICENSE_MACHINE_STRICT",
        "DATA_BOAR_MACHINE_SEED",
    )
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    reset_license_guard_for_tests()
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _enforced_guard(
    priv: Ed25519PrivateKey, tmp_path, *, extra: dict | None = None
) -> LicenseGuard:
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(priv, extra=extra), encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(priv)
    return LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})


def _audit_records(caplog):
    return [r for r in caplog.records if r.name == AUDIT_LOGGER]


# --- claim parsing -----------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, []),
        ("", []),
        ("  ", []),
        ("ABCD12", ["abcd12"]),
        (["ABCD12", "ef34"], ["abcd12", "ef34"]),
        ([], []),
        (["", "ab"], ["ab"]),
    ],
)
def test_parse_dbmfp_claim_valid_shapes(raw, expected):
    assert _parse_dbmfp_claim(raw) == expected


@pytest.mark.parametrize("raw", [{"a": 1}, 42, [1, 2], ["ok", 3]])
def test_parse_dbmfp_claim_malformed_returns_none(raw):
    assert _parse_dbmfp_claim(raw) is None


# --- 1. bound to local fingerprint → accepted --------------------------------


def test_single_dbmfp_local_accepted(ed25519_priv, tmp_path):
    g = _enforced_guard(
        ed25519_priv, tmp_path, extra={"dbmfp": compute_machine_fingerprint()}
    )
    assert g.context.state == "VALID"
    assert g.allows_scan() is True


def test_pack_containing_local_accepted(ed25519_priv, tmp_path):
    pack = [OTHER_FP, compute_machine_fingerprint()]
    g = _enforced_guard(
        ed25519_priv,
        tmp_path,
        extra={
            "dbmfp": pack,
            "dbdeployment_pack_id": "qa-pack-1",
            "dbmax_deployments": 2,
        },
    )
    assert g.context.state == "VALID"
    assert g.allows_scan() is True
    assert g.context.deployment_pack_id == "qa-pack-1"
    assert g.context.max_deployments == 2


# --- 2. bound to another fingerprint → fail-closed + audit CRITICAL ----------


def test_single_dbmfp_other_host_fails_closed(ed25519_priv, tmp_path, caplog):
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbmfp": OTHER_FP})
        assert g.context.state == "MACHINE_MISMATCH"
        assert g.allows_scan() is False
        cfg = {"licensing": {"mode": "enforced"}}
        assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY
    crit = [r for r in _audit_records(caplog) if r.levelno == logging.CRITICAL]
    assert any("license_evaluated" in r.message for r in crit)
    assert any("scan_gate" in r.message for r in crit)


def test_pack_without_local_fails_closed(ed25519_priv, tmp_path, caplog):
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = _enforced_guard(
            ed25519_priv,
            tmp_path,
            extra={"dbmfp": [OTHER_FP, "e" * 64], "dbmax_deployments": 2},
        )
        assert g.context.state == "MACHINE_MISMATCH"
        assert g.allows_scan() is False
    assert any(r.levelno == logging.CRITICAL for r in _audit_records(caplog))


def test_dev_env_does_not_bypass_machine_mismatch(ed25519_priv, tmp_path, monkeypatch):
    """#719 posture: dev env vars never bypass the fingerprint binding."""
    monkeypatch.setenv("DATA_BOAR_ENV", "development")
    monkeypatch.setenv("DEBUG", "1")
    g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbmfp": OTHER_FP})
    assert g.context.state == "MACHINE_MISMATCH"
    assert g.allows_scan() is False


# --- 3./4. no claim = unbound; open mode never checks -------------------------


def test_enforced_without_dbmfp_runs_normally(ed25519_priv, tmp_path):
    g = _enforced_guard(ed25519_priv, tmp_path)
    assert g.context.state == "VALID"
    assert g.allows_scan() is True


def test_open_mode_never_checks_binding():
    g = LicenseGuard({})
    assert g.context.state == "OPEN"
    assert g.allows_scan() is True


# --- 5. malformed dbmfp fails closed ------------------------------------------


def test_malformed_dbmfp_claim_fails_closed(ed25519_priv, tmp_path, caplog):
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        g = _enforced_guard(ed25519_priv, tmp_path, extra={"dbmfp": [123, 456]})
        assert g.context.state == "INVALID"
        assert g.context.detail == "malformed_dbmfp_claim"
        assert g.allows_scan() is False
    assert any(r.levelno == logging.CRITICAL for r in _audit_records(caplog))


# --- 6. deployment claims plumbing --------------------------------------------


def test_deployment_claims_default_zero_when_absent(ed25519_priv, tmp_path):
    g = _enforced_guard(ed25519_priv, tmp_path)
    assert g.context.deployment_pack_id == ""
    assert g.context.max_deployments == 0


def test_malformed_dbmax_deployments_fail_soft(ed25519_priv, tmp_path):
    g = _enforced_guard(
        ed25519_priv,
        tmp_path,
        extra={"dbmax_deployments": "not-a-number"},
    )
    assert g.context.state == "VALID"
    assert g.context.max_deployments == 0


# --- 7. issuer --dbmfp-pack ----------------------------------------------------


def _run_issuer(args: list[str], env_extra: dict[str, str]) -> str:
    env = dict(os.environ)
    env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(ISSUER), *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
        cwd=str(REPO_ROOT),
    )
    return proc.stdout.strip()


def test_issuer_dbmfp_pack_binds_n_machines(ed25519_priv, tmp_path):
    token = _run_issuer(
        ["--dbmfp-pack", f"auto,{OTHER_FP}", "--sub", "qa-pack-lic"],
        {"DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM": _pem_private(ed25519_priv)},
    )
    claims = jwt.decode(
        token,
        _pem_public(ed25519_priv),
        algorithms=["EdDSA"],
    )
    assert isinstance(claims["dbmfp"], list)
    assert compute_machine_fingerprint() in claims["dbmfp"]
    assert OTHER_FP in claims["dbmfp"]
    assert claims["dbmax_deployments"] == 2
    assert claims["dbdeployment_pack_id"] == "qa-pack-lic-pack"

    # End-to-end: the pack license is VALID on this (pack member) machine.
    lic = tmp_path / "pack.lic"
    lic.write_text(token, encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = _pem_public(ed25519_priv)
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "VALID"
    assert g.context.max_deployments == 2


def test_issuer_explicit_dbmax_deployments_and_pack_id(ed25519_priv):
    token = _run_issuer(
        [
            "--dbmfp-pack",
            f"auto,{OTHER_FP}",
            "--pack-id",
            "plus-5-sites",
            "--dbmax-deployments",
            "5",
        ],
        {"DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PEM": _pem_private(ed25519_priv)},
    )
    claims = jwt.decode(token, _pem_public(ed25519_priv), algorithms=["EdDSA"])
    assert claims["dbdeployment_pack_id"] == "plus-5-sites"
    assert claims["dbmax_deployments"] == 5


# --- 8. DATA_BOAR_MACHINE_SEED stability knob ----------------------------------


def test_machine_seed_changes_fingerprint(monkeypatch):
    base = compute_machine_fingerprint()
    monkeypatch.setenv("DATA_BOAR_MACHINE_SEED", "deployment-secret-1")
    seeded = compute_machine_fingerprint()
    assert seeded != base
    # Deterministic per host/seed pair:
    assert compute_machine_fingerprint() == seeded
