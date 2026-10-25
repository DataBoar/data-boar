"""
Stable machine fingerprint for optional license binding.

Uses hostname + optional DATA_BOAR_MACHINE_SEED (recommended in Docker/VM pools).
"""

from __future__ import annotations

import hashlib
import os
import socket


def compute_machine_fingerprint() -> str:
    """
    Return SHA-256 hex digest identifying this runtime environment.

    Set DATA_BOAR_MACHINE_SEED in production (especially containers) to a stable
    per-deployment secret so licenses can bind to a deployment, not a random hostname.
    """
    seed = (os.environ.get("DATA_BOAR_MACHINE_SEED") or "").strip()
    host = socket.gethostname().lower()
    # Use a KDF (PBKDF2-HMAC) instead of a direct fast hash to avoid weak-sensitive-hash patterns
    # and keep a stable deterministic fingerprint per host/seed pair.
    data = f"v2|host={host}|seed={seed}".encode("utf-8")
    salt = f"data-boar-mfp|{host}".encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", data, salt, 200_000, dklen=32)
    return derived.hex()
