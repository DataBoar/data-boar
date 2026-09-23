"""Trust-anchor cross-sign for key rotation (#1992 / #1462)."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard
from core.licensing.trust_anchor import (
    ROTATION_DOMAIN,
    canonical_rotation_message,
    verify_rotation_attestation,
)

pytestmark = pytest.mark.skipif(
    not __import__(
        "cryptography.hazmat.backends.openssl.backend", fromlist=["backend"]
    ).backend.mldsa_supported(),
    reason="OpenSSL backend has no ML-DSA support",
)


def _ed_pem(priv: Ed25519PrivateKey) -> str:
    return (
        priv.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _ml_pem(priv: MLDSA65PrivateKey) -> str:
    raw = priv.public_key().public_bytes_raw()
    body = base64.b64encode(raw).decode("ascii")
    lines = [body[i : i + 64] for i in range(0, len(body), 64)]
    return (
        "-----BEGIN ML-DSA-65 PUBLIC KEY-----\n"
        + "\n".join(lines)
        + "\n-----END ML-DSA-65 PUBLIC KEY-----\n"
    )


def _attest(
    ed_anchor: Ed25519PrivateKey,
    ml_anchor: MLDSA65PrivateKey,
    *,
    epoch: int,
    new_ed: str,
    new_ml: str,
    message: bytes | None = None,
) -> str:
    signed = message or canonical_rotation_message(epoch, new_ed, new_ml)
    doc = {
        "epoch": epoch,
        "ed25519_pub_pem": new_ed,
        "mldsa_pub_pem": new_ml,
        "sig_ed25519": base64.b64encode(ed_anchor.sign(signed)).decode("ascii"),
        "sig_mldsa": base64.b64encode(ml_anchor.sign(signed)).decode("ascii"),
    }
    return json.dumps(doc)


def _license(priv: Ed25519PrivateKey) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "lic-rotation-1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=2)).timestamp()),
            "dbcid": "lab-dev",
            "dbcname": "Lab",
            "dbenv": "qa",
            "dbissuer": "test",
            "dbkid": "rot",
            "dbtier": "enterprise",
            "dbmfp": compute_machine_fingerprint(),
        },
        priv,
        algorithm="EdDSA",
    )


def test_rotation_message_has_domain_and_epoch_inside() -> None:
    msg = canonical_rotation_message(7, "ed", "ml")
    assert msg.startswith(ROTATION_DOMAIN)
    epoch = int.from_bytes(msg[len(ROTATION_DOMAIN) : len(ROTATION_DOMAIN) + 8], "big")
    assert epoch == 7
    assert b'"epoch"' not in msg.split(ROTATION_DOMAIN, 1)[1][8:]


def test_epoch_outside_the_signature_does_not_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rewriting epoch after signing is a replay, not a new epoch (sdk#12)."""
    ed_anchor = Ed25519PrivateKey.generate()
    ml_anchor = MLDSA65PrivateKey.generate()
    new_ed = Ed25519PrivateKey.generate()
    new_ml = MLDSA65PrivateKey.generate()
    raw = _attest(
        ed_anchor,
        ml_anchor,
        epoch=1,
        new_ed=_ed_pem(new_ed),
        new_ml=_ml_pem(new_ml),
    )
    bumped = json.loads(raw)
    bumped["epoch"] = 9
    with pytest.raises(Exception) as exc:
        verify_rotation_attestation(
            json.dumps(bumped),
            ed25519_anchor_pem=_ed_pem(ed_anchor),
            mldsa_anchor_pem=_ml_pem(ml_anchor),
            min_epoch=1,
        )
    assert getattr(exc.value, "detail", "") == "signature"


def test_raw_env_key_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    priv = Ed25519PrivateKey.generate()
    lic = tmp_path / "self.lic"
    lic.write_text(_license(priv), encoding="utf-8")
    monkeypatch.setenv("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", _ed_pem(priv))
    guard = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert guard.context.state == "INVALID"
    assert guard.context.detail == "untrusted_key_override"


def test_unsigned_rotation_fails_and_cross_signed_rotation_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ed_anchor = Ed25519PrivateKey.generate()
    ml_anchor = MLDSA65PrivateKey.generate()
    attacker_ed = Ed25519PrivateKey.generate()
    attacker_ml = MLDSA65PrivateKey.generate()
    new_ed = Ed25519PrivateKey.generate()
    new_ml = MLDSA65PrivateKey.generate()
    monkeypatch.setattr(
        "core.licensing.guard.load_embedded_official_public_key_pem",
        lambda: _ed_pem(ed_anchor),
    )
    monkeypatch.setattr(
        "core.licensing.trust_anchor.load_embedded_mldsa_anchor_pem",
        lambda: _ml_pem(ml_anchor),
    )
    new_ed_pem = _ed_pem(new_ed)
    new_ml_pem = _ml_pem(new_ml)
    fake = tmp_path / "fake.json"
    fake.write_text(
        _attest(
            attacker_ed,
            attacker_ml,
            epoch=1,
            new_ed=new_ed_pem,
            new_ml=new_ml_pem,
        ),
        encoding="utf-8",
    )
    lic = tmp_path / "rot.lic"
    lic.write_text(_license(new_ed), encoding="utf-8")
    denied = LicenseGuard(
        {
            "licensing": {
                "mode": "enforced",
                "license_path": str(lic),
                "rotation_attestation_path": str(fake),
            }
        }
    )
    assert denied.context.state == "INVALID"
    assert denied.context.detail == "rotation_rejected:signature"

    stale = tmp_path / "stale.json"
    stale.write_text(
        _attest(
            ed_anchor,
            ml_anchor,
            epoch=0,
            new_ed=new_ed_pem,
            new_ml=new_ml_pem,
        ),
        encoding="utf-8",
    )
    old = LicenseGuard(
        {
            "licensing": {
                "mode": "enforced",
                "license_path": str(lic),
                "rotation_attestation_path": str(stale),
            }
        }
    )
    assert old.context.detail == "rotation_rejected:epoch_too_old:0<1"

    good = tmp_path / "good.json"
    good.write_text(
        _attest(
            ed_anchor,
            ml_anchor,
            epoch=1,
            new_ed=new_ed_pem,
            new_ml=new_ml_pem,
        ),
        encoding="utf-8",
    )
    accepted = LicenseGuard(
        {
            "licensing": {
                "mode": "enforced",
                "license_path": str(lic),
                "rotation_attestation_path": str(good),
            }
        }
    )
    assert accepted.context.state == "VALID"
    assert accepted.context.detail == "rotation_epoch_1"

    bare = canonical_rotation_message(1, new_ed_pem, new_ml_pem)[len(ROTATION_DOMAIN) :]
    no_domain = _attest(
        ed_anchor,
        ml_anchor,
        epoch=1,
        new_ed=new_ed_pem,
        new_ml=new_ml_pem,
        message=bare,
    )
    with pytest.raises(Exception) as naked:
        verify_rotation_attestation(
            no_domain,
            ed25519_anchor_pem=_ed_pem(ed_anchor),
            mldsa_anchor_pem=_ml_pem(ml_anchor),
        )
    assert getattr(naked.value, "detail", "") == "signature"
