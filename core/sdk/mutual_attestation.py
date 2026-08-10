"""Mutual Ed25519 attestation for the bidirectional Plugin SDK mesh (#1116).

C2PA-inspired challenge/response — not CAI-certified. Fail-closed: any verify
failure or tinted peer trust → Safe-Hold (no data channel).
"""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

SDK_CONTRACT_VERSION = "1.0.0"
NONCE_BYTES = 32
FRESHNESS_WINDOW_S = 300

# Guest refuses hosts at these trust levels (zero-trust: distrust tinted core).
_GUEST_REJECT_HOST_TRUST = frozenset({"untrusted", "adulterated"})


class MeshRole(str, Enum):
    HOST = "host"
    GUEST = "guest"


class SafeHoldReason(str, Enum):
    OK = "ok"
    INVALID_SIGNATURE = "invalid_signature"
    NONCE_MISMATCH = "nonce_mismatch"
    STALE_ATTESTATION = "stale_attestation"
    MISSING_ANCHOR = "missing_anchor"
    HOST_TRUST_REJECTED = "host_trust_rejected"
    GUEST_VIOLATION = "guest_violation"
    SCHEMA_INVALID = "schema_invalid"


@dataclass(frozen=True)
class AttestationPayload:
    """Canonical bytes signed by each party (party + release + anchor + nonce echo)."""

    party: str
    role: str
    release_label: str
    integrity_anchor: str
    issued_at: float
    nonce_echo: str
    trust_level: str

    def to_signed_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )


def new_nonce() -> str:
    return os.urandom(NONCE_BYTES).hex()


def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def trust_is_acceptable_for_guest(host_trust_level: str) -> bool:
    """Guest-side gate: refuse tinted/adulterated host (#1116 / GAP-010)."""
    return host_trust_level not in _GUEST_REJECT_HOST_TRUST


def make_challenge(
    *,
    role: MeshRole,
    party: str,
    trust_level: str,
    integrity_state: str = "ok",
    release_label: str | None = None,
    nonce: str | None = None,
) -> dict[str, Any]:
    return {
        "sdk_contract_version": SDK_CONTRACT_VERSION,
        "schema": "databoar.attestation.challenge",
        "role": role.value,
        "party": party,
        "nonce": nonce or new_nonce(),
        "trust_level": trust_level,
        "integrity_state": integrity_state,
        "issued_at": _iso_now(),
        "release_label": release_label or party,
    }


def make_response(
    *,
    role: MeshRole,
    party: str,
    trust_level: str,
    integrity_anchor: str,
    release_label: str,
    nonce_echo: str,
    signing_key: Ed25519PrivateKey,
    integrity_state: str = "ok",
    counter_nonce: str | None = None,
    issued_at: float | None = None,
) -> tuple[dict[str, Any], AttestationPayload]:
    # Second precision only — must match ISO round-trip in verify_response.
    if issued_at is None:
        issued_dt = datetime.now(UTC).replace(microsecond=0)
    else:
        issued_dt = datetime.fromtimestamp(issued_at, tz=UTC).replace(microsecond=0)
    ts = issued_dt.timestamp()
    iso = issued_dt.isoformat().replace("+00:00", "Z")
    payload = AttestationPayload(
        party=party,
        role=role.value,
        release_label=release_label,
        integrity_anchor=integrity_anchor,
        issued_at=ts,
        nonce_echo=nonce_echo,
        trust_level=trust_level,
    )
    sig = signing_key.sign(payload.to_signed_bytes())
    envelope: dict[str, Any] = {
        "sdk_contract_version": SDK_CONTRACT_VERSION,
        "schema": "databoar.attestation.response",
        "role": role.value,
        "party": party,
        "nonce_echo": nonce_echo,
        "trust_level": trust_level,
        "integrity_state": integrity_state,
        "integrity_anchor": integrity_anchor,
        "release_label": release_label,
        "issued_at": iso,
        "signature_b64": base64.b64encode(sig).decode("ascii"),
    }
    if counter_nonce is not None:
        envelope["counter_nonce"] = counter_nonce
    return envelope, payload


def verify_response(
    response: dict[str, Any],
    *,
    peer_pubkey: Ed25519PublicKey,
    expected_nonce: str,
    now: float | None = None,
) -> tuple[bool, SafeHoldReason]:
    """Fail-closed peer verify (pinned pubkey + nonce echo + freshness + anchor)."""
    try:
        sig = base64.b64decode(response["signature_b64"], validate=True)
        payload = AttestationPayload(
            party=str(response["party"]),
            role=str(response["role"]),
            release_label=str(response["release_label"]),
            integrity_anchor=str(response["integrity_anchor"]),
            issued_at=datetime.fromisoformat(str(response["issued_at"])).timestamp(),
            nonce_echo=str(response["nonce_echo"]),
            trust_level=str(response["trust_level"]),
        )
    except (KeyError, ValueError, TypeError):
        return False, SafeHoldReason.SCHEMA_INVALID

    try:
        peer_pubkey.verify(sig, payload.to_signed_bytes())
    except InvalidSignature:
        return False, SafeHoldReason.INVALID_SIGNATURE

    if payload.nonce_echo != expected_nonce:
        return False, SafeHoldReason.NONCE_MISMATCH

    wall = time.time() if now is None else now
    if (wall - payload.issued_at) > FRESHNESS_WINDOW_S:
        return False, SafeHoldReason.STALE_ATTESTATION

    if not payload.integrity_anchor:
        return False, SafeHoldReason.MISSING_ANCHOR

    return True, SafeHoldReason.OK


def run_mutual_handshake(
    *,
    host_party: str,
    guest_party: str,
    host_trust_level: str,
    guest_trust_level: str,
    host_priv: Ed25519PrivateKey,
    guest_priv: Ed25519PrivateKey,
    host_pubkey_pinned: Ed25519PublicKey,
    guest_pubkey_pinned: Ed25519PublicKey,
    host_anchor: str,
    guest_anchor: str,
    host_release: str,
    guest_release: str,
) -> tuple[bool, SafeHoldReason, dict[str, Any]]:
    """Full host↔guest challenge/response. Opens data channel only when both OK.

    Guest refuses tinted host trust before crypto completes the reverse leg.
    Host contains guest signature/nonce violations as Safe-Hold (no raise).
    """
    detail: dict[str, Any] = {"channel": "closed"}

    if not trust_is_acceptable_for_guest(host_trust_level):
        detail["safe_hold"] = SafeHoldReason.HOST_TRUST_REJECTED.value
        return False, SafeHoldReason.HOST_TRUST_REJECTED, detail

    host_challenge = make_challenge(
        role=MeshRole.HOST,
        party=host_party,
        trust_level=host_trust_level,
    )
    nonce_h = str(host_challenge["nonce"])
    nonce_s = new_nonce()

    guest_resp, _ = make_response(
        role=MeshRole.GUEST,
        party=guest_party,
        trust_level=guest_trust_level,
        integrity_anchor=guest_anchor,
        release_label=guest_release,
        nonce_echo=nonce_h,
        signing_key=guest_priv,
        counter_nonce=nonce_s,
    )
    ok_guest, why_guest = verify_response(
        guest_resp, peer_pubkey=guest_pubkey_pinned, expected_nonce=nonce_h
    )
    if not ok_guest:
        detail["safe_hold"] = why_guest.value
        detail["violator"] = "guest"
        return False, SafeHoldReason.GUEST_VIOLATION, detail

    host_resp, _ = make_response(
        role=MeshRole.HOST,
        party=host_party,
        trust_level=host_trust_level,
        integrity_anchor=host_anchor,
        release_label=host_release,
        nonce_echo=nonce_s,
        signing_key=host_priv,
    )
    ok_host, why_host = verify_response(
        host_resp, peer_pubkey=host_pubkey_pinned, expected_nonce=nonce_s
    )
    if not ok_host:
        detail["safe_hold"] = why_host.value
        detail["violator"] = "host"
        return False, why_host, detail

    detail["channel"] = "open"
    detail["host_challenge"] = host_challenge
    detail["guest_response"] = {
        k: v for k, v in guest_resp.items() if k != "signature_b64"
    }
    detail["host_response"] = {
        k: v for k, v in host_resp.items() if k != "signature_b64"
    }
    return True, SafeHoldReason.OK, detail
