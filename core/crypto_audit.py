"""
Helpers for strong crypto / controls presence detection (Phase 1).

This module provides a small, connector-agnostic helper that inspects
lightweight “connection info” dictionaries and emits best-effort signals
about the likely presence (or absence) of strong transport/database crypto.

Later phases can wire these signals into a full Crypto & Controls report
sheet and stronger heuristics per connector type.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Set


class StrongCryptoSignal(str, Enum):
    """Coarse-grained signals about crypto / transport strength.

    These are deliberately high-level and conservative; they should be used
    as hints for a future "Crypto & controls" report sheet, not as a formal
    compliance certification.
    """

    TRANSPORT_TLS = "transport_tls"  # e.g. https://
    TRANSPORT_PLAINTEXT = "transport_plaintext"  # e.g. http://
    DB_TLS_REQUIRED = "db_tls_required"  # e.g. sslmode=require / verify-*
    DB_TLS_DISABLED = "db_tls_disabled"  # e.g. sslmode=disable / plaintext


def _lower_or_empty(value: Any) -> str:
    return str(value or "").strip().lower()


def validate_crypto_enabled(config: dict[str, Any] | None) -> bool:
    """
    Return True when optional strong-crypto / controls validation is enabled.

    Config key: ``scan.validate_crypto`` (bool). Off by default. CLI
    ``--validate-crypto`` and API/dashboard ``validate_crypto: true`` set this
    for the current run (see PLAN_OPTIONAL_STRONG_CRYPTO_AND_CONTROLS_VALIDATION).
    """
    if not isinstance(config, dict):
        return False
    scan = config.get("scan")
    if not isinstance(scan, dict):
        return False
    return bool(scan.get("validate_crypto"))


def summarize_crypto_from_connection_info(
    info: dict[str, Any],
) -> Set[StrongCryptoSignal]:
    """
    Inspect a minimal connector-agnostic "connection info" dict and emit
    coarse StrongCryptoSignal values.

    Supported hints (Phase 1):
    - REST/API: base_url / url / scheme (http vs https).
    - SQL (PostgreSQL-like): driver / dsn / sslmode heuristics.
    """

    signals: set[StrongCryptoSignal] = set()

    # --- Transport / REST-style targets (HTTP/HTTPS) ---
    base_url = _lower_or_empty(info.get("base_url") or info.get("url"))
    scheme = _lower_or_empty(info.get("scheme"))

    url_scheme = ""
    if base_url.startswith("http://") or base_url.startswith("https://"):
        url_scheme = base_url.split(":", 1)[0]
    elif scheme in ("http", "https"):
        url_scheme = scheme

    if url_scheme == "https":
        signals.add(StrongCryptoSignal.TRANSPORT_TLS)
    elif url_scheme == "http":
        signals.add(StrongCryptoSignal.TRANSPORT_PLAINTEXT)

    # --- Database-style hints (PostgreSQL-like for now) ---
    driver = _lower_or_empty(info.get("driver"))
    dsn = _lower_or_empty(info.get("dsn"))
    sslmode = _lower_or_empty(info.get("sslmode"))

    # Roughly identify Postgres-style connections so sslmode hints make sense.
    is_postgres_like = any(
        token in driver or token in dsn
        for token in ("postgresql", "postgres+psycopg2", "postgres")
    )

    if is_postgres_like:
        # sslmode from explicit field or embedded in DSN/query string
        if not sslmode and "sslmode=" in dsn:
            # naive parse: take text after first "sslmode="
            part = dsn.split("sslmode=", 1)[1]
            sslmode = part.split("&", 1)[0]

        strong_modes: Iterable[str] = ("require", "verify-ca", "verify-full")
        weak_modes: Iterable[str] = ("disable", "allow")

        if sslmode in strong_modes:
            signals.add(StrongCryptoSignal.DB_TLS_REQUIRED)
        elif sslmode in weak_modes:
            signals.add(StrongCryptoSignal.DB_TLS_DISABLED)

    return signals
