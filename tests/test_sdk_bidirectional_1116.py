"""Bidirectional Plugin SDK mesh conformance (#1116 / ADR-0087)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from core.sdk.boar_fast_filter_dogfood import (
    GUEST_PARTY,
    filter_batch_with_mutual_attestation,
    guest_refuses_tinted_host,
)
from core.sdk.mutual_attestation import (
    MeshRole,
    SafeHoldReason,
    generate_keypair,
    make_challenge,
    make_response,
    new_nonce,
    run_mutual_handshake,
    trust_is_acceptable_for_guest,
    verify_response,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "sdk" / "PLUGIN_CONTRACT.schema.json"
EXAMPLE_CHALLENGE = REPO_ROOT / "docs" / "sdk" / "example-attestation-challenge.json"
EXAMPLE_RESPONSE = REPO_ROOT / "docs" / "sdk" / "example-attestation-response.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", [EXAMPLE_CHALLENGE, EXAMPLE_RESPONSE])
def test_attestation_examples_validate(path: Path) -> None:
    jsonschema.validate(
        instance=json.loads(path.read_text(encoding="utf-8")),
        schema=_schema(),
    )


def test_guest_refuses_tinted_host_trust() -> None:
    assert trust_is_acceptable_for_guest("trusted")
    assert not trust_is_acceptable_for_guest("adulterated")
    assert not trust_is_acceptable_for_guest("untrusted")
    assert guest_refuses_tinted_host("adulterated")


def test_host_tinted_guest_refuses_no_channel() -> None:
    result = filter_batch_with_mutual_attestation(
        ["a@b.co"],
        host_trust_level="adulterated",
        filter_impl=None,
    )
    assert not result.channel_open
    assert result.reason is SafeHoldReason.HOST_TRUST_REJECTED
    assert result.suspect_indexes == ()


def test_guest_violation_contained_by_host() -> None:
    host_priv, host_pub = generate_keypair()
    guest_priv, _guest_pub_real = generate_keypair()
    _wrong_priv, wrong_pub = generate_keypair()  # pin does not match signer

    ok, reason, detail = run_mutual_handshake(
        host_party="data-boar-core",
        guest_party=GUEST_PARTY,
        host_trust_level="trusted",
        guest_trust_level="trusted",
        host_priv=host_priv,
        guest_priv=guest_priv,
        host_pubkey_pinned=host_pub,
        guest_pubkey_pinned=wrong_pub,  # host pin wrong → guest looks violating
        host_anchor="h",
        guest_anchor="g",
        host_release="core",
        guest_release="bff",
    )
    assert not ok
    assert reason is SafeHoldReason.GUEST_VIOLATION
    assert detail.get("violator") == "guest"


def test_mutual_handshake_opens_channel() -> None:
    host_priv, host_pub = generate_keypair()
    guest_priv, guest_pub = generate_keypair()
    ok, reason, detail = run_mutual_handshake(
        host_party="data-boar-core",
        guest_party=GUEST_PARTY,
        host_trust_level="trusted",
        guest_trust_level="trusted",
        host_priv=host_priv,
        guest_priv=guest_priv,
        host_pubkey_pinned=host_pub,
        guest_pubkey_pinned=guest_pub,
        host_anchor="host-anchor",
        guest_anchor="guest-anchor",
        host_release="data-boar",
        guest_release="boar_fast_filter-0.1.0",
    )
    assert ok
    assert reason is SafeHoldReason.OK
    assert detail["channel"] == "open"


def test_challenge_and_response_envelopes_schema_valid() -> None:
    schema = _schema()
    ch = make_challenge(
        role=MeshRole.HOST,
        party="data-boar-core",
        trust_level="trusted",
    )
    jsonschema.validate(instance=ch, schema=schema)
    priv, _pub = generate_keypair()
    resp, _ = make_response(
        role=MeshRole.GUEST,
        party=GUEST_PARTY,
        trust_level="trusted",
        integrity_anchor="anchor",
        release_label="boar_fast_filter-0.1.0",
        nonce_echo=str(ch["nonce"]),
        signing_key=priv,
        counter_nonce=new_nonce(),
    )
    jsonschema.validate(instance=resp, schema=schema)


def test_replay_nonce_fails() -> None:
    priv, pub = generate_keypair()
    nonce = new_nonce()
    resp, _ = make_response(
        role=MeshRole.GUEST,
        party=GUEST_PARTY,
        trust_level="trusted",
        integrity_anchor="a",
        release_label="bff",
        nonce_echo=nonce,
        signing_key=priv,
    )
    ok, why = verify_response(resp, peer_pubkey=pub, expected_nonce=new_nonce())
    assert not ok
    assert why is SafeHoldReason.NONCE_MISMATCH


def test_dogfood_with_mock_filter() -> None:
    class _MockFF:
        def filter_batch(self, batch: list[str]) -> list[int]:
            return [i for i, s in enumerate(batch) if "@" in s]

    result = filter_batch_with_mutual_attestation(
        ["plain", "a@b.co"],
        host_trust_level="trusted",
        filter_impl=_MockFF(),
    )
    assert result.channel_open
    assert result.suspect_indexes == (1,)


def test_dogfood_contains_crashing_guest_filter() -> None:
    class _Boom:
        def filter_batch(self, batch: list[str]) -> list[int]:
            raise RuntimeError("guest boom")

    result = filter_batch_with_mutual_attestation(
        ["x"],
        host_trust_level="trusted",
        filter_impl=_Boom(),
    )
    assert not result.channel_open
    assert result.reason is SafeHoldReason.GUEST_VIOLATION
