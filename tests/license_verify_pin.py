"""Pin the embedded Ed25519 loader for tests.

Production never reads a verify key from the environment (#1992). Tests that
need a throwaway issuer key replace the loader; ``restore_embedded_ed25519_loader``
runs after every test via ``tests/conftest.py``.
"""

from __future__ import annotations


def pin_embedded_ed25519_pem(pem: str) -> None:
    import core.licensing.guard as guard_mod

    guard_mod.load_embedded_official_public_key_pem = lambda: pem


def restore_embedded_ed25519_loader() -> None:
    import core.licensing.guard as guard_mod
    from core.licensing.verify import load_embedded_official_public_key_pem

    guard_mod.load_embedded_official_public_key_pem = (
        load_embedded_official_public_key_pem
    )
