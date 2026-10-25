"""In-memory WebAuthn challenge/state store (single-process; see docs)."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Literal

TTL_SECONDS = 300.0

_kind = Literal["reg", "auth"]


@dataclass
class PendingWebAuthn:
    kind: _kind
    challenge: bytes
    expires_at: float
    # For authentication, we may need the current sign_count for the credential being used.
    credential_id: bytes | None


_lock = threading.Lock()
_store: dict[str, PendingWebAuthn] = {}


def new_state_token() -> str:
    return secrets.token_urlsafe(32)


def put_pending(
    *,
    token: str,
    kind: _kind,
    challenge: bytes,
    credential_id: bytes | None = None,
) -> None:
    now = time.monotonic()
    with _lock:
        _prune_unlocked(now)
        _store[token] = PendingWebAuthn(
            kind=kind,
            challenge=challenge,
            expires_at=now + TTL_SECONDS,
            credential_id=credential_id,
        )


def pop_pending(token: str) -> PendingWebAuthn | None:
    now = time.monotonic()
    with _lock:
        _prune_unlocked(now)
        return _store.pop(token, None)


def _prune_unlocked(now: float) -> None:
    dead = [k for k, v in _store.items() if v.expires_at < now]
    for k in dead:
        del _store[k]
