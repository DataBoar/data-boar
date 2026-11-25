"""Signing-key passphrase for the issuer scripts: terminal prompt only (#2239).

Shared by ``scripts/issue_dev_license_jwt.py`` and
``scripts/sign-integrity-manifest.py``. The passphrase of an encrypted issuer
key is typed at an interactive terminal. It is never read from the
environment or from a file, and a run without a terminal fails closed.
"""

from __future__ import annotations

import os
import sys
from getpass import getpass

from cryptography.hazmat.primitives.serialization import load_pem_private_key

PASSPHRASE_ENV_IGNORED = "DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD"

_IGNORED_WARNING = (
    f"Warning: {PASSPHRASE_ENV_IGNORED} is set and ignored: "
    "the signing key passphrase is read only from the terminal prompt."
)
_NO_TTY = (
    "Signing key is encrypted: run this command in an interactive terminal to "
    "type the passphrase. The passphrase is never read from the environment or "
    "a file."
)
_EMPTY = "Empty passphrase: signing aborted."
_UNDECRYPTABLE = "Could not decrypt the signing key: wrong passphrase or damaged PEM."

_ignored_env_warned = False


class IssuerPassphraseError(Exception):
    """Fixed message written by us; never carries the passphrase or the PEM."""


def stdin_is_interactive() -> bool:
    """True only when a real console is attached (never block under pytest/CI).

    On Windows, ``subprocess.DEVNULL`` as stdin can still make
    ``sys.stdin.isatty()`` return True; prefer ``os.isatty(fileno)``.
    """
    if os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}:
        return False
    try:
        fd = sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return False
    try:
        return bool(os.isatty(fd))
    except OSError:
        return False


def _warn_when_passphrase_env_is_set() -> None:
    """Report the ignored variable once per process. Only presence is read."""
    global _ignored_env_warned
    if _ignored_env_warned:
        return
    if os.environ.get(PASSPHRASE_ENV_IGNORED, "").strip():
        _ignored_env_warned = True
        print(_IGNORED_WARNING, file=sys.stderr)


def resolve_issuer_key_password(pem: str, *, prompt: str) -> bytes | None:
    """Passphrase for ``load_pem_private_key``: ``None`` for a clean PEM, else the TTY.

    The terminal check comes before ``getpass``: without a TTY, ``getpass``
    falls back to reading stdin, so a piped passphrase would be accepted.
    """
    _warn_when_passphrase_env_is_set()
    if "ENCRYPTED" not in pem:
        return None
    if not stdin_is_interactive():
        raise IssuerPassphraseError(_NO_TTY)
    entered = getpass(prompt)
    if not entered:
        raise IssuerPassphraseError(_EMPTY)
    return entered.encode("utf-8")


def load_issuer_private_key(pem: str, *, prompt: str):
    """Load the issuer private key; decryption failures become a fixed message."""
    password = resolve_issuer_key_password(pem, prompt=prompt)
    try:
        return load_pem_private_key(pem.encode("utf-8"), password=password)
    except (ValueError, TypeError):
        raise IssuerPassphraseError(_UNDECRYPTABLE) from None
