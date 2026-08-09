"""
Helpers for strong crypto / controls validation (Order 5).

Phase 1: coarse connection-info signals + ``validate_crypto_enabled``.
Phase 2a: result criteria, SQLAlchemy post-connect probe facts, evaluation
to ok/warning/fail/not_available/not_applicable (no secrets in details).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Set


class StrongCryptoSignal(str, Enum):
    """Coarse-grained signals about crypto / transport strength (Phase 1)."""

    TRANSPORT_TLS = "transport_tls"  # e.g. https://
    TRANSPORT_PLAINTEXT = "transport_plaintext"  # e.g. http://
    DB_TLS_REQUIRED = "db_tls_required"  # e.g. sslmode=require / verify-*
    DB_TLS_DISABLED = "db_tls_disabled"  # e.g. sslmode=disable / plaintext


class StrongCryptoResult(str, Enum):
    """Per-target strong-crypto validation outcome (Phase 2)."""

    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"
    NOT_AVAILABLE = "not_available"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class CryptoProbeFacts:
    """Best-effort TLS/crypto facts from a live connection or config fallback.

    Never store certificate PEMs, private keys, or connection strings here.
    """

    tls_in_use: bool | None = None
    tls_version: str | None = None
    cipher: str | None = None
    sslmode: str | None = None
    source: str = ""


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


def _normalize_tls_version(raw: str | None) -> str | None:
    """Map driver/status strings to a short label (e.g. TLSv1.2)."""
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    lower = s.lower().replace(" ", "")
    for label, needles in (
        ("TLSv1.3", ("tlsv1.3", "tls1.3")),
        ("TLSv1.2", ("tlsv1.2", "tls1.2")),
        ("TLSv1.1", ("tlsv1.1", "tls1.1")),
        ("TLSv1.0", ("tlsv1.0", "tls1.0")),
    ):
        if any(n in lower for n in needles):
            return label
    # Bare major minor without "tls" prefix (e.g. status value "1.2")
    if lower in ("1.3", "v1.3"):
        return "TLSv1.3"
    if lower in ("1.2", "v1.2"):
        return "TLSv1.2"
    if lower in ("1.1", "v1.1"):
        return "TLSv1.1"
    if lower in ("1.0", "v1.0"):
        return "TLSv1.0"
    return s[:40]


def evaluate_strong_crypto(facts: CryptoProbeFacts) -> tuple[StrongCryptoResult, str]:
    """
    Apply Phase 2 strong-crypto criteria to probe facts.

    Criteria (best-effort, not a compliance certification):
    - Local / N/A dialects (source=sqlite): not_applicable
    - TLS disabled or sslmode=disable: fail
    - TLS 1.0 / 1.1: fail
    - TLS 1.2 / 1.3: ok (note warning if sslmode is require without verify-*)
    - TLS in use but version unknown: warning
    - Only config sslmode available: map require→warning, verify-*→ok, else not_available
    """
    source = (facts.source or "").strip().lower()
    if source == "sqlite":
        return (
            StrongCryptoResult.NOT_APPLICABLE,
            "SQLite is local; TLS validation does not apply",
        )

    sslmode = _lower_or_empty(facts.sslmode)
    tls_version = _normalize_tls_version(facts.tls_version)
    detail_parts: list[str] = []
    if facts.source:
        detail_parts.append(f"source={facts.source}")
    if tls_version:
        detail_parts.append(f"tls={tls_version}")
    if facts.cipher:
        # Cipher suite *name* only (not secrets).
        detail_parts.append(f"cipher={str(facts.cipher).strip()[:80]}")
    if sslmode:
        detail_parts.append(f"sslmode={sslmode}")

    def _details(extra: str = "") -> str:
        base = "; ".join(detail_parts) if detail_parts else "no probe details"
        return f"{base}; {extra}" if extra else base

    if facts.tls_in_use is False or sslmode == "disable":
        return (
            StrongCryptoResult.FAIL,
            _details("TLS not in use or sslmode=disable"),
        )

    if tls_version in ("TLSv1.0", "TLSv1.1"):
        return (
            StrongCryptoResult.FAIL,
            _details("TLS below 1.2"),
        )

    if tls_version in ("TLSv1.2", "TLSv1.3"):
        if sslmode == "require":
            return (
                StrongCryptoResult.WARNING,
                _details("TLS OK; sslmode=require (cert not verify-full/verify-ca)"),
            )
        return (StrongCryptoResult.OK, _details("TLS >= 1.2"))

    if facts.tls_in_use is True:
        return (
            StrongCryptoResult.WARNING,
            _details("TLS in use; version not reported"),
        )

    # Config-only fallback (no live TLS attributes)
    if sslmode in ("verify-ca", "verify-full"):
        return (
            StrongCryptoResult.OK,
            _details(
                "config sslmode requires verified TLS (live version not available)"
            ),
        )
    if sslmode == "require":
        return (
            StrongCryptoResult.WARNING,
            _details("config sslmode=require (live TLS version not available)"),
        )
    if sslmode in ("prefer", "allow"):
        return (
            StrongCryptoResult.WARNING,
            _details(f"config sslmode={sslmode} allows plaintext fallback"),
        )
    if sslmode:
        return (
            StrongCryptoResult.NOT_AVAILABLE,
            _details("unrecognized sslmode; live TLS not available"),
        )

    return (
        StrongCryptoResult.NOT_AVAILABLE,
        _details("driver did not expose TLS attributes"),
    )


def collect_sql_crypto_facts(
    sa_engine: Any, target_config: dict[str, Any]
) -> CryptoProbeFacts:
    """
    Best-effort live TLS facts from a SQLAlchemy engine after connect.

    Postgres: ``pg_stat_ssl`` for the backend pid.
    MySQL/MariaDB: ``SHOW STATUS LIKE 'Ssl_version'`` / ``Ssl_cipher``.
    SQLite: source=sqlite (evaluator → not_applicable).
    Else: sslmode from target config only.
    """
    sslmode = _lower_or_empty(target_config.get("sslmode"))
    if not sslmode:
        dsn = _lower_or_empty(
            target_config.get("dsn")
            or target_config.get("url")
            or target_config.get("connection_string")
        )
        if "sslmode=" in dsn:
            part = dsn.split("sslmode=", 1)[1]
            sslmode = part.split("&", 1)[0].strip()

    dialect = ""
    try:
        dialect = (sa_engine.dialect.name or "").strip().lower()
    except Exception:
        dialect = ""

    if dialect == "sqlite":
        return CryptoProbeFacts(source="sqlite", sslmode=sslmode or None)

    if dialect in ("postgresql", "postgres"):
        try:
            from sqlalchemy import text

            with sa_engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT ssl, version, cipher FROM pg_stat_ssl "
                        "WHERE pid = pg_backend_pid()"
                    )
                ).fetchone()
            if row is not None:
                return CryptoProbeFacts(
                    tls_in_use=bool(row[0]),
                    tls_version=str(row[1]) if row[1] else None,
                    cipher=str(row[2]) if row[2] else None,
                    sslmode=sslmode or None,
                    source="pg_stat_ssl",
                )
        except Exception:
            pass

    if dialect in ("mysql", "mariadb"):
        try:
            from sqlalchemy import text

            ver = None
            cipher = None
            with sa_engine.connect() as conn:
                r_ver = conn.execute(text("SHOW STATUS LIKE 'Ssl_version'")).fetchone()
                r_cipher = conn.execute(
                    text("SHOW STATUS LIKE 'Ssl_cipher'")
                ).fetchone()
            if r_ver is not None and len(r_ver) >= 2:
                ver = str(r_ver[1] or "").strip() or None
            if r_cipher is not None and len(r_cipher) >= 2:
                cipher = str(r_cipher[1] or "").strip() or None
            if ver or cipher:
                return CryptoProbeFacts(
                    tls_in_use=bool(ver),
                    tls_version=ver,
                    cipher=cipher,
                    sslmode=sslmode or None,
                    source="mysql_ssl_status",
                )
        except Exception:
            pass

    return CryptoProbeFacts(
        sslmode=sslmode or None,
        source="config_sslmode" if sslmode else "unavailable",
    )
