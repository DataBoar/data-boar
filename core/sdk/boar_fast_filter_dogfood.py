"""Dogfood: ``boar_fast_filter`` as first bidirectional SDK guest (#1116).

Proves zero-trust mesh in-house: core (host) and prefilter (guest) mutual
Ed25519 attestation before any batch crosses the boundary. Tinted host → guest
Safe-Hold (no filter). Guest crypto violation → host Safe-Hold (scan continues).

Rust ``guest_accepts_host_trust`` is consulted when the extension is installed;
absence of the wheel falls back to the pure-Python trust gate (still fail-closed).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from core.sdk.mutual_attestation import (
    SafeHoldReason,
    generate_keypair,
    run_mutual_handshake,
    trust_is_acceptable_for_guest,
)

GUEST_PARTY = "boar_fast_filter"
HOST_PARTY = "data-boar-core"


@dataclass(frozen=True)
class DogfoodResult:
    channel_open: bool
    reason: SafeHoldReason
    suspect_indexes: tuple[int, ...]
    detail: dict[str, Any]


def _rust_guest_accepts(host_trust_level: str) -> bool | None:
    """Return Rust gate result, or None if extension unavailable."""
    try:
        import boar_fast_filter  # type: ignore[import-not-found]
    except ImportError:
        return None
    fn = getattr(boar_fast_filter, "guest_accepts_host_trust", None)
    if fn is None:
        return None
    return bool(fn(host_trust_level))


def guest_refuses_tinted_host(host_trust_level: str) -> bool:
    """True when guest must Safe-Hold (refuse to process)."""
    rust = _rust_guest_accepts(host_trust_level)
    if rust is not None:
        return not rust
    return not trust_is_acceptable_for_guest(host_trust_level)


def filter_batch_with_mutual_attestation(
    batch: Sequence[str],
    *,
    host_trust_level: str = "trusted",
    guest_trust_level: str = "trusted",
    host_priv: Ed25519PrivateKey | None = None,
    guest_priv: Ed25519PrivateKey | None = None,
    host_pubkey_pinned: Ed25519PublicKey | None = None,
    guest_pubkey_pinned: Ed25519PublicKey | None = None,
    host_anchor: str = "host-anchor-dogfood",
    guest_anchor: str = "guest-anchor-dogfood",
    host_release: str = "data-boar",
    guest_release: str = "boar_fast_filter-0.1.0",
    filter_impl: Any | None = None,
) -> DogfoodResult:
    """Run mutual attestation then optional FastFilter; never raises into the scan."""
    if guest_refuses_tinted_host(host_trust_level):
        return DogfoodResult(
            channel_open=False,
            reason=SafeHoldReason.HOST_TRUST_REJECTED,
            suspect_indexes=(),
            detail={"safe_hold": "host_trust_rejected", "party": GUEST_PARTY},
        )

    if host_priv is None:
        h_priv, h_pub = generate_keypair()
    else:
        h_priv = host_priv
        h_pub = host_pubkey_pinned or host_priv.public_key()
    if guest_priv is None:
        g_priv, g_pub = generate_keypair()
    else:
        g_priv = guest_priv
        g_pub = guest_pubkey_pinned or guest_priv.public_key()

    ok, reason, detail = run_mutual_handshake(
        host_party=HOST_PARTY,
        guest_party=GUEST_PARTY,
        host_trust_level=host_trust_level,
        guest_trust_level=guest_trust_level,
        host_priv=h_priv,
        guest_priv=g_priv,
        host_pubkey_pinned=h_pub,
        guest_pubkey_pinned=g_pub,
        host_anchor=host_anchor,
        guest_anchor=guest_anchor,
        host_release=host_release,
        guest_release=guest_release,
    )
    if not ok:
        return DogfoodResult(
            channel_open=False,
            reason=reason,
            suspect_indexes=(),
            detail=detail,
        )

    indexes: list[int] = []
    if filter_impl is not None:
        try:
            indexes = list(filter_impl.filter_batch(list(batch)))
        except Exception as exc:  # noqa: BLE001 — Safe-Hold: contain guest runtime faults
            return DogfoodResult(
                channel_open=False,
                reason=SafeHoldReason.GUEST_VIOLATION,
                suspect_indexes=(),
                detail={"safe_hold": "guest_runtime_error", "error": str(exc)},
            )
    else:
        try:
            from boar_fast_filter import FastFilter  # type: ignore[import-not-found]

            indexes = list(FastFilter().filter_batch(list(batch)))
        except ImportError:
            detail["filter"] = "skipped_extension_missing"
        except Exception as exc:  # noqa: BLE001
            return DogfoodResult(
                channel_open=False,
                reason=SafeHoldReason.GUEST_VIOLATION,
                suspect_indexes=(),
                detail={"safe_hold": "guest_runtime_error", "error": str(exc)},
            )

    return DogfoodResult(
        channel_open=True,
        reason=SafeHoldReason.OK,
        suspect_indexes=tuple(indexes),
        detail=detail,
    )
