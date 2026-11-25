"""Signing-key passphrase for the issuer scripts: terminal prompt only (#2239).

Shared by ``scripts/issue_dev_license_jwt.py`` and
``scripts/sign-integrity-manifest.py``. The passphrase of an encrypted issuer
key is typed at an interactive terminal. It is never read from the
environment or from a file, and a run without a terminal fails closed.
"""

from __future__ import annotations

PASSPHRASE_ENV_IGNORED = "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD"


class IssuerPassphraseError(Exception):
    """Fixed message written by us; never carries the passphrase or the PEM."""


def stdin_is_interactive() -> bool:
    raise NotImplementedError


def resolve_issuer_key_password(pem: str, *, prompt: str) -> bytes | None:
    raise NotImplementedError


def load_issuer_private_key(pem: str, *, prompt: str):
    raise NotImplementedError
