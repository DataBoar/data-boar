"""
Helpers for strong crypto / controls validation (Order 5).

Phase 1: coarse connection-info signals + ``validate_crypto_enabled``.
Phase 2a: result criteria, SQLAlchemy post-connect probe facts, evaluation
to ok/warning/fail/not_available/not_applicable (no secrets in details).
Phase 2c: MongoDB / Redis TLS connect intent + post-connect probe facts
(allowlisted tokens only — never raw URI/DSN fragments in details).
Phase 2d: SMB signing/encryption from smbprotocol Session after connect
(allowlisted dialect/signing/encryption tokens only).
Phase 2.4: REST / Power BI / Dataverse HTTPS + TLS via httpx (allowlisted
scheme/tls/cipher/verify posture only — never URLs, tokens, or query strings).
Phase 3: heuristic anonymisation/control inference from identifier *name
patterns only* (counts by category — never sample values or raw column lists).
"""

from __future__ import annotations

import re
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
    # Phase 2d SMB — allowlisted tokens only (never UNC paths or credentials).
    smb_dialect: str | None = None
    smb_signing: str | None = None
    smb_encryption: str | None = None


def _lower_or_empty(value: Any) -> str:
    return str(value or "").strip().lower()


# libpq / psycopg sslmode values only — never persist arbitrary DSN fragments.
_KNOWN_SSLMODES = frozenset(
    {
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    }
)


def _canonical_sslmode(raw: Any) -> str | None:
    """
    Return a known sslmode token, or None.

    Rejects anything that is not exactly one of the libpq sslmode values so
    DSN leftovers (e.g. ``password=...`` after a space-separated parse) never
    enter ``strong_crypto_details`` or other persisted/report fields.
    """
    token = _lower_or_empty(raw)
    if not token:
        return None
    # Defensive: take first whitespace/&/;-delimited piece before allowlist check.
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    if token in _KNOWN_SSLMODES:
        return token
    return None


def _sslmode_from_connection_string(raw: Any) -> str | None:
    """Extract sslmode from a DSN/URL only when the value is a known token."""
    text = _lower_or_empty(raw)
    if "sslmode=" not in text:
        return None
    part = text.split("sslmode=", 1)[1]
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in part:
            part = part.split(sep, 1)[0]
    return _canonical_sslmode(part)


# redis-py / ssl module cert requirement tokens only.
_KNOWN_SSL_CERT_REQS = frozenset({"none", "optional", "required"})

# URI / config bool tokens accepted for tls=/ssl= query-style values.
_KNOWN_BOOL_TOKENS = {
    "true": True,
    "1": True,
    "yes": True,
    "on": True,
    "false": False,
    "0": False,
    "no": False,
    "off": False,
}


def _canonical_ssl_cert_reqs(raw: Any) -> str | None:
    """Return a known ssl_cert_reqs token, or None (never raw URI tails)."""
    token = _lower_or_empty(raw)
    if not token:
        return None
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    if token in _KNOWN_SSL_CERT_REQS:
        return token
    return None


def _canonical_bool_token(raw: Any) -> bool | None:
    """Map allowlisted bool spellings to bool; reject anything else."""
    token = _lower_or_empty(raw)
    if not token:
        return None
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    return _KNOWN_BOOL_TOKENS.get(token)


def _query_param_bool(text: str, key: str) -> bool | None:
    """
    Extract ``key=<allowlisted-bool>`` from a URI/query string.

    Stops at ``&`` / space / ``;`` and allowlists the value — never returns
    arbitrary DSN/URI remainder (password tails, etc.).
    """
    lowered = _lower_or_empty(text)
    needle = f"{key}="
    if needle not in lowered:
        return None
    part = lowered.split(needle, 1)[1]
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in part:
            part = part.split(sep, 1)[0]
    return _canonical_bool_token(part)


def _config_truthy_flag(config: dict[str, Any], *keys: str) -> bool | None:
    """Return True/False when a config key is an explicit bool-like value."""
    for key in keys:
        if key not in config:
            continue
        val = config.get(key)
        if isinstance(val, bool):
            return val
        parsed = _canonical_bool_token(val)
        if parsed is not None:
            return parsed
    return None


def _uri_implies_tls(uri: Any) -> bool | None:
    """Detect TLS intent from URI scheme / allowlisted tls|ssl query params."""
    text = _lower_or_empty(uri)
    if not text:
        return None
    if text.startswith("mongodb+srv://") or text.startswith("rediss://"):
        return True
    for key in ("tls", "ssl"):
        parsed = _query_param_bool(text, key)
        if parsed is not None:
            return parsed
    return None


def resolve_nosql_tls_connect_options(
    target_config: dict[str, Any],
) -> tuple[bool, str | None, str | None]:
    """
    Resolve whether to enable TLS on Mongo/Redis connect.

    Returns ``(tls_enabled, sslmode_posture, ssl_cert_reqs)`` where:
    - ``sslmode_posture`` is an allowlisted libpq-style token for evaluation
      (``verify-full`` when certs are verified, ``require`` when TLS without
      verification, ``disable`` when TLS is off).
    - ``ssl_cert_reqs`` is an allowlisted redis-py token or None.
    """
    uri = (
        target_config.get("uri")
        or target_config.get("url")
        or target_config.get("connection_string")
        or target_config.get("dsn")
        or ""
    )
    tls_flag = _config_truthy_flag(target_config, "tls", "ssl")
    if tls_flag is None:
        tls_flag = _uri_implies_tls(uri)

    insecure = _config_truthy_flag(
        target_config,
        "tls_insecure",
        "tlsInsecure",
        "tls_allow_invalid_certificates",
        "tlsAllowInvalidCertificates",
    )
    if insecure is None:
        insecure = _query_param_bool(str(uri), "tlsinsecure")

    cert_reqs = _canonical_ssl_cert_reqs(target_config.get("ssl_cert_reqs"))
    if cert_reqs is None:
        # Allowlisted extraction only — never persist raw query tails.
        text = _lower_or_empty(uri)
        if "ssl_cert_reqs=" in text:
            part = text.split("ssl_cert_reqs=", 1)[1]
            for sep in (" ", "\t", "&", ";", "\n", "\r"):
                if sep in part:
                    part = part.split(sep, 1)[0]
            cert_reqs = _canonical_ssl_cert_reqs(part)

    if tls_flag is False:
        return False, "disable", cert_reqs

    if tls_flag is not True and cert_reqs is None and insecure is not True:
        # No TLS intent — connect plaintext; probe will report fail/not_available.
        return False, None, None

    # TLS on (explicit flag, rediss/mongodb+srv, or ssl_cert_reqs present).
    tls_enabled = True
    if insecure is True or cert_reqs == "none":
        return tls_enabled, "require", cert_reqs or "none"
    if cert_reqs == "optional":
        return tls_enabled, "prefer", cert_reqs
    # Default when TLS is requested: expect certificate verification.
    return tls_enabled, "verify-full", cert_reqs or "required"


def _ssl_socket_probe(sock: Any) -> tuple[str | None, str | None]:
    """Best-effort TLS version + cipher name from an SSLSocket-like object."""
    tls_version = None
    cipher = None
    try:
        if hasattr(sock, "version"):
            tls_version = _normalize_tls_version(sock.version())
    except Exception:
        tls_version = None
    try:
        if hasattr(sock, "cipher"):
            info = sock.cipher()
            if isinstance(info, tuple) and info:
                cipher = str(info[0]).strip()[:80] or None
            elif isinstance(info, str):
                cipher = info.strip()[:80] or None
    except Exception:
        cipher = None
    return tls_version, cipher


# smbprotocol Dialects revision values → canonical labels (allowlist only).
_SMB_DIALECT_BY_REV: dict[int, str] = {
    0x0202: "SMB_2_0_2",
    0x0210: "SMB_2_1_0",
    0x0300: "SMB_3_0_0",
    0x0302: "SMB_3_0_2",
    0x0311: "SMB_3_1_1",
}
_KNOWN_SMB_DIALECTS = frozenset(_SMB_DIALECT_BY_REV.values())
_KNOWN_SMB_SIGNING = frozenset({"required", "disabled"})
_KNOWN_SMB_ENCRYPTION = frozenset({"on", "off", "unsupported"})
_SMB3_DIALECTS = frozenset({"SMB_3_0_0", "SMB_3_0_2", "SMB_3_1_1"})
_SMB2_DIALECTS = frozenset({"SMB_2_0_2", "SMB_2_1_0"})


def _canonical_smb_dialect(raw: Any) -> str | None:
    """Map dialect revision int or name to an allowlisted SMB dialect label."""
    if raw is None:
        return None
    if isinstance(raw, int):
        return _SMB_DIALECT_BY_REV.get(raw)
    token = str(raw).strip().upper().replace("-", "_").replace(".", "_")
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    if token in _KNOWN_SMB_DIALECTS:
        return token
    # Accept bare "SMB_311" style typos? No — allowlist only.
    return None


def _canonical_smb_signing(raw: Any) -> str | None:
    token = _lower_or_empty(raw)
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    if token in _KNOWN_SMB_SIGNING:
        return token
    return None


def _canonical_smb_encryption(raw: Any) -> str | None:
    token = _lower_or_empty(raw)
    for sep in (" ", "\t", "&", ";", "\n", "\r"):
        if sep in token:
            token = token.split(sep, 1)[0].strip()
    if token in _KNOWN_SMB_ENCRYPTION:
        return token
    return None


def resolve_smb_connect_options(
    target_config: dict[str, Any],
) -> tuple[bool | None, bool | None]:
    """
    Resolve optional SMB connect kwargs for smbclient.register_session.

    Returns ``(encrypt, require_signing)`` where ``None`` means “leave library
    default” (encrypt unset; require_signing defaults to True in smbclient).
    """
    encrypt = _config_truthy_flag(
        target_config, "encrypt", "smb_encrypt", "require_encryption"
    )
    require_signing = _config_truthy_flag(
        target_config, "require_signing", "smb_signing"
    )
    return encrypt, require_signing


_KNOWN_HTTP_SCHEMES = frozenset({"http", "https"})


def _canonical_http_scheme(raw: Any) -> str | None:
    """
    Return ``http`` or ``https`` only.

    Accepts a bare scheme or a URL prefix. Never returns host, path, query,
    userinfo, or any other URI fragment.
    """
    text = _lower_or_empty(raw)
    if not text:
        return None
    if text.startswith("https://") or text == "https":
        return "https"
    if text.startswith("http://") or text == "http":
        return "http"
    # Bare token with junk after it (e.g. "https password=...") — allowlist first piece.
    for sep in (" ", "\t", "&", ";", "\n", "\r", "?", "#", "/"):
        if sep in text:
            text = text.split(sep, 1)[0].strip()
            break
    if text in _KNOWN_HTTP_SCHEMES:
        return text
    return None


def resolve_httpx_tls_connect_options(
    target_config: dict[str, Any],
) -> bool | None:
    """
    Resolve httpx ``verify`` for Client construction.

    ``None`` means leave the library default (True). Explicit False disables
    certificate verification (maps to sslmode=require at evaluate time).
    """
    return _config_truthy_flag(target_config, "verify", "verify_ssl")


def _safe_httpx_probe_path(raw: Any) -> str:
    """
    Return a path-only probe target (leading ``/``).

    Rejects absolute URLs, query strings, and fragments so credentials or
    tokens in query never become part of persisted crypto details.
    """
    text = str(raw or "").strip()
    if not text:
        return "/"
    lower = text.lower()
    if "://" in lower or "?" in text or "#" in text or "\n" in text or "\r" in text:
        return "/"
    if not text.startswith("/"):
        text = "/" + text.lstrip("/")
    # Defensive: drop anything after whitespace.
    for sep in (" ", "\t"):
        if sep in text:
            text = text.split(sep, 1)[0]
    return text or "/"


def validate_crypto_enabled(config: dict[str, Any] | None) -> bool:
    """
    Return True when optional strong-crypto / controls validation is enabled.

    Config key: ``scan.validate_crypto`` (bool). Off by default. CLI
    ``--validate-crypto`` and API/dashboard ``validate_crypto: true`` set this
    for the current run (see completed/PLAN_OPTIONAL_STRONG_CRYPTO_AND_CONTROLS_VALIDATION).
    """
    if not isinstance(config, dict):
        return False
    scan = config.get("scan")
    if not isinstance(scan, dict):
        return False
    return bool(scan.get("validate_crypto"))


# Phase 3 — identifier name heuristics (category label → match callables).
# One category per name (first match wins). Never persist the raw identifier.
_INFER_CATEGORY_ORDER = (
    "hashing",
    "masking",
    "tokenization",
    "anonymization",
)
_INFER_PREFIXES: dict[str, tuple[str, ...]] = {
    "hashing": ("hash_",),
    "masking": ("mask_", "masked_"),
    "tokenization": ("token_", "tok_"),
    "anonymization": ("anon_", "anonymous_", "pseudonym_", "pseudo_"),
}
_INFER_SUFFIXES: dict[str, tuple[str, ...]] = {
    "hashing": ("_hash", "_hashed"),
    "masking": ("_masked", "_mask"),
    "tokenization": ("_token", "_tok"),
    "anonymization": ("_anon", "_anonymous", "_pseudonym", "_pseudo"),
}
_INFER_SUMMARY_MAX = 480
_INFER_DISCLAIMER = "heuristic; not verified — human review required"
# Allowlisted metadata hint tokens only (never persist free-text comments).
_INFER_METADATA_HINTS = frozenset(
    {"masking", "mask", "hashing", "hashed", "tokenization", "tokenised", "tokenized"}
)
_IDENTIFIER_NORMALIZE_RE = re.compile(r"[^a-z0-9_]+")


def _normalize_identifier_name(raw: Any) -> str | None:
    """Normalize an identifier for pattern matching; reject empty/oversized."""
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = bytes(raw).decode("utf-8", errors="ignore")
        except Exception:
            return None
    text = str(raw or "").strip().lower()
    if not text or len(text) > 256:
        return None
    # Flatten Redis-style separators so token_user and token:user both match.
    text = text.replace("-", "_").replace(".", "_").replace(":", "_").replace("/", "_")
    text = _IDENTIFIER_NORMALIZE_RE.sub("_", text).strip("_")
    return text or None


def _category_for_identifier(name: str) -> str | None:
    for category in _INFER_CATEGORY_ORDER:
        for prefix in _INFER_PREFIXES.get(category, ()):
            if name.startswith(prefix):
                return category
        for suffix in _INFER_SUFFIXES.get(category, ()):
            if name.endswith(suffix):
                return category
    return None


def infer_controls_from_identifiers(
    names: Iterable[Any],
    *,
    metadata_hints: Iterable[Any] | None = None,
) -> str | None:
    """
    Best-effort inference of anonymisation/control *hints* from identifier names.

    Returns a short count-by-category summary, or None when nothing matched.
    Never includes sample values or the raw identifier list — only allowlisted
    category labels and counts. Not a compliance certification.
    """
    counts: dict[str, int] = {c: 0 for c in _INFER_CATEGORY_ORDER}
    seen: set[str] = set()
    for raw in names:
        normalized = _normalize_identifier_name(raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        category = _category_for_identifier(normalized)
        if category:
            counts[category] += 1

    meta_hits = 0
    if metadata_hints:
        for hint in metadata_hints:
            token = _lower_or_empty(hint)
            if token in _INFER_METADATA_HINTS:
                meta_hits += 1

    parts: list[str] = []
    for category in _INFER_CATEGORY_ORDER:
        n = counts[category]
        if n <= 0:
            continue
        noun = "name" if n == 1 else "names"
        parts.append(f"{n} {noun} suggest {category}")
    if meta_hits:
        parts.append(
            f"{meta_hits} metadata hint"
            + ("s" if meta_hits != 1 else "")
            + " (allowlisted)"
        )
    if not parts:
        return None
    summary = "; ".join(parts) + f" ({_INFER_DISCLAIMER})"
    if len(summary) > _INFER_SUMMARY_MAX:
        summary = summary[: _INFER_SUMMARY_MAX - 1].rstrip() + "…"
    return summary


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
    sslmode = _canonical_sslmode(info.get("sslmode"))
    if not sslmode:
        sslmode = _sslmode_from_connection_string(dsn)

    # Roughly identify Postgres-style connections so sslmode hints make sense.
    is_postgres_like = any(
        token in driver or token in dsn
        for token in ("postgresql", "postgres+psycopg2", "postgres")
    )

    if is_postgres_like and sslmode:
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


def _evaluate_smb_strong_crypto(
    facts: CryptoProbeFacts,
) -> tuple[StrongCryptoResult, str]:
    """SMB signing/encryption criteria (Phase 2d); allowlisted tokens only."""
    dialect = _canonical_smb_dialect(facts.smb_dialect)
    signing = _canonical_smb_signing(facts.smb_signing)
    encryption = _canonical_smb_encryption(facts.smb_encryption)
    detail_parts: list[str] = []
    if facts.source:
        # Keep source short and allowlisted-looking (smb_* prefixes only).
        src = (facts.source or "").strip()
        if src.lower().startswith("smb"):
            detail_parts.append(f"source={src[:40]}")
    if dialect:
        detail_parts.append(f"dialect={dialect}")
    if signing:
        detail_parts.append(f"signing={signing}")
    if encryption:
        detail_parts.append(f"encryption={encryption}")

    def _details(extra: str = "") -> str:
        base = "; ".join(detail_parts) if detail_parts else "no probe details"
        return f"{base}; {extra}" if extra else base

    if not dialect and not signing and encryption is None:
        return (
            StrongCryptoResult.NOT_AVAILABLE,
            _details("SMB session did not expose signing/encryption attributes"),
        )

    if signing == "disabled":
        return (
            StrongCryptoResult.FAIL,
            _details("SMB signing disabled"),
        )

    if encryption == "on" and signing == "required" and dialect in _SMB3_DIALECTS:
        return (StrongCryptoResult.OK, _details("SMB 3.x signing+encryption"))

    if encryption == "on" and signing == "required":
        return (StrongCryptoResult.OK, _details("SMB signing+encryption"))

    if signing == "required" and encryption in ("off", "unsupported"):
        if dialect in _SMB3_DIALECTS:
            return (
                StrongCryptoResult.WARNING,
                _details("SMB 3.x signed without encryption"),
            )
        if dialect in _SMB2_DIALECTS:
            return (
                StrongCryptoResult.WARNING,
                _details("SMB 2.x signed; encryption not available"),
            )
        return (
            StrongCryptoResult.WARNING,
            _details("SMB signed without encryption"),
        )

    if signing == "required":
        return (
            StrongCryptoResult.WARNING,
            _details("SMB signing required; encryption state unknown"),
        )

    return (
        StrongCryptoResult.NOT_AVAILABLE,
        _details("SMB crypto posture incomplete"),
    )


def evaluate_strong_crypto(facts: CryptoProbeFacts) -> tuple[StrongCryptoResult, str]:
    """
    Apply Phase 2 strong-crypto criteria to probe facts.

    Criteria (best-effort, not a compliance certification):
    - Local / N/A dialects (source=sqlite): not_applicable
    - SMB (source smb_* or smb_* fields): signing/encryption dialect rules
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

    if (
        source.startswith("smb")
        or facts.smb_dialect
        or facts.smb_signing
        or facts.smb_encryption
    ):
        return _evaluate_smb_strong_crypto(facts)

    # Allowlist again at evaluate time so details never echo arbitrary DSN text.
    sslmode = _canonical_sslmode(facts.sslmode)
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
    # Never accept raw DSN fragments as sslmode (allowlist only).
    sslmode = _canonical_sslmode(target_config.get("sslmode"))
    if not sslmode:
        sslmode = _sslmode_from_connection_string(
            target_config.get("dsn")
            or target_config.get("url")
            or target_config.get("connection_string")
        )

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
            # Fail-soft: live SQL TLS probe must never fail the scan.
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
            # Fail-soft: live SQL TLS probe must never fail the scan.
            pass

    return CryptoProbeFacts(
        sslmode=sslmode or None,
        source="config_sslmode" if sslmode else "unavailable",
    )


def collect_mongodb_crypto_facts(
    client: Any, target_config: dict[str, Any]
) -> CryptoProbeFacts:
    """
    Best-effort TLS facts from a live PyMongo client + allowlisted config.

    Prefers live SSL socket attributes when reachable; otherwise records
    connect-time TLS intent (``tls`` / URI scheme) mapped to sslmode posture.
    Never returns URI fragments, credentials, or PEMs.
    """
    tls_enabled, sslmode, _cert = resolve_nosql_tls_connect_options(target_config)

    tls_version = None
    cipher = None
    live_tls: bool | None = None
    source = "config_tls" if tls_enabled or sslmode else "unavailable"

    # Prefer client options when PyMongo exposes them.
    try:
        opts = getattr(client, "options", None)
        if opts is not None:
            opt_tls = getattr(opts, "tls", None)
            if opt_tls is None and hasattr(opts, "_options"):
                opt_tls = getattr(opts._options, "tls", None)
            if isinstance(opt_tls, bool):
                live_tls = opt_tls
                source = "mongodb_client_options"
    except Exception:
        # Fail-soft: client-option introspection must never fail the scan.
        pass

    # Best-effort: inspect one pooled socket after a cheap server ping.
    try:
        if client is not None:
            client.admin.command("ping")
            sock_info = None
            topo = getattr(client, "_topology", None)
            if topo is not None:
                servers = getattr(topo, "_servers", None) or {}
                for server in list(servers.values()):
                    pool = getattr(server, "_pool", None)
                    if pool is None:
                        continue
                    sock_info = getattr(pool, "socket_info", None) or getattr(
                        pool, "_socket_info", None
                    )
                    if sock_info is not None:
                        break
                    # PyMongo 4.x Pool may expose sockets via gen contexts — skip if opaque.
            sock = None
            if sock_info is not None:
                sock = getattr(sock_info, "sock", None) or getattr(
                    sock_info, "socket", None
                )
            if sock is not None and hasattr(sock, "version"):
                tls_version, cipher = _ssl_socket_probe(sock)
                live_tls = True
                source = "mongodb_ssl_socket"
    except Exception:
        # Fail-soft: Mongo live TLS probe must never fail the scan.
        pass

    if live_tls is None:
        live_tls = True if tls_enabled else False

    if not live_tls and not tls_enabled:
        return CryptoProbeFacts(
            tls_in_use=False,
            sslmode=sslmode or "disable",
            source=source if source != "unavailable" else "mongodb_plaintext",
        )

    return CryptoProbeFacts(
        tls_in_use=True if live_tls else tls_enabled,
        tls_version=tls_version,
        cipher=cipher,
        sslmode=sslmode or None,
        source=source,
    )


def collect_redis_crypto_facts(
    client: Any, target_config: dict[str, Any]
) -> CryptoProbeFacts:
    """
    Best-effort TLS facts from a live redis-py client + allowlisted config.

    Borrows one pool connection to read ``SSLSocket.version()`` / ``cipher()``
    when available. Never returns URL fragments, passwords, or PEMs.
    """
    tls_enabled, sslmode, _cert = resolve_nosql_tls_connect_options(target_config)

    tls_version = None
    cipher = None
    live_tls: bool | None = None
    source = "config_tls" if tls_enabled or sslmode else "unavailable"

    conn = None
    pool = None
    try:
        pool = getattr(client, "connection_pool", None)
        if pool is not None:
            conn = pool.get_connection("_")
            try:
                if getattr(conn, "_sock", None) is None and hasattr(conn, "connect"):
                    conn.connect()
                sock = getattr(conn, "_sock", None) or getattr(conn, "sock", None)
                if sock is not None and hasattr(sock, "version"):
                    tls_version, cipher = _ssl_socket_probe(sock)
                    live_tls = True
                    source = "redis_ssl_socket"
                elif sock is not None:
                    # Connected socket without SSL API → plaintext TCP.
                    live_tls = False
                    source = "redis_tcp_socket"
                elif bool(getattr(conn, "ssl", False) or getattr(conn, "_ssl", False)):
                    live_tls = True
                    source = "redis_connection_ssl_flag"
            finally:
                if conn is not None and pool is not None:
                    pool.release(conn)
                    conn = None
    except Exception:
        # Fail-soft: Redis live TLS probe must never fail the scan.
        if conn is not None and pool is not None:
            try:
                pool.release(conn)
            except Exception:
                # Fail-soft: pool release during probe cleanup is best-effort.
                pass

    if live_tls is None:
        live_tls = True if tls_enabled else False

    if not live_tls and not tls_enabled:
        return CryptoProbeFacts(
            tls_in_use=False,
            sslmode=sslmode or "disable",
            source=source if source != "unavailable" else "redis_plaintext",
        )

    return CryptoProbeFacts(
        tls_in_use=True if live_tls else tls_enabled,
        tls_version=tls_version,
        cipher=cipher,
        sslmode=sslmode or None,
        source=source,
    )


def collect_smb_crypto_facts(
    session: Any, target_config: dict[str, Any] | None = None
) -> CryptoProbeFacts:
    """
    Best-effort SMB signing/encryption facts from an smbprotocol Session.

    Prefer live Session / Connection attributes after ``register_session``.
    Never returns passwords, UNC paths, hostnames, or algorithm key material.
    """
    _ = target_config  # reserved for future allowlisted config fallbacks
    if session is None:
        return CryptoProbeFacts(source="unavailable")

    dialect = None
    signing = None
    encryption = None
    source = "smb_session"

    try:
        connection = getattr(session, "connection", None)
        if connection is not None:
            dialect = _canonical_smb_dialect(getattr(connection, "dialect", None))
        signing_required = getattr(session, "signing_required", None)
        if signing_required is None and connection is not None:
            signing_required = getattr(connection, "require_signing", None)
        if isinstance(signing_required, bool):
            signing = "required" if signing_required else "disabled"

        enc = getattr(session, "encrypt_data", None)
        if isinstance(enc, bool):
            encryption = "on" if enc else "off"
        elif connection is not None:
            supports = getattr(connection, "supports_encryption", None)
            if supports is False:
                encryption = "unsupported"
    except Exception:
        # Fail-soft: SMB attribute probe must never fail the scan.
        return CryptoProbeFacts(source="unavailable")

    if dialect is None and signing is None and encryption is None:
        return CryptoProbeFacts(source="unavailable")

    return CryptoProbeFacts(
        source=source,
        smb_dialect=dialect,
        smb_signing=signing,
        smb_encryption=encryption,
    )


def collect_httpx_crypto_facts(
    client: Any,
    target_config: dict[str, Any] | None = None,
    *,
    probe_url: str = "/",
    probe_params: dict[str, Any] | None = None,
) -> CryptoProbeFacts:
    """
    Best-effort HTTPS/TLS facts from a live httpx.Client.

    Probes TLS version/cipher via an open stream's network_stream socket when
    available. Never stores URLs, Authorization headers, tokens, query strings,
    or response bodies — only allowlisted scheme/tls/cipher/sslmode tokens.
    """
    cfg = target_config if isinstance(target_config, dict) else {}
    scheme = None
    try:
        base = getattr(client, "base_url", None)
        if base is not None:
            scheme = _canonical_http_scheme(str(base))
    except Exception:
        scheme = None
    if scheme is None:
        scheme = _canonical_http_scheme(
            cfg.get("base_url")
            or cfg.get("url")
            or cfg.get("org_url")
            or cfg.get("environment_url")
            or ""
        )

    verify_opt = resolve_httpx_tls_connect_options(cfg)
    if verify_opt is False:
        sslmode = "require"
    elif scheme == "https":
        # Default httpx verify=True when unset.
        sslmode = "verify-full"
    else:
        sslmode = "disable" if scheme == "http" else None

    if scheme == "http":
        return CryptoProbeFacts(
            tls_in_use=False,
            sslmode=sslmode or "disable",
            source="httpx_plaintext",
        )

    if scheme != "https":
        return CryptoProbeFacts(
            sslmode=sslmode,
            source="unavailable",
        )

    tls_version = None
    cipher = None
    source = "httpx_https_scheme"
    path = _safe_httpx_probe_path(probe_url)
    try:
        if client is not None:
            with client.stream("GET", path, params=probe_params) as resp:
                extensions = getattr(resp, "extensions", None) or {}
                net = extensions.get("network_stream")
                sock = None
                if net is not None and hasattr(net, "get_extra_info"):
                    sock = net.get_extra_info("socket")
                    if sock is None:
                        sock = net.get_extra_info("ssl_object")
                if sock is not None:
                    tls_version, cipher = _ssl_socket_probe(sock)
                    if tls_version or cipher:
                        source = "httpx_ssl_socket"
                # Do not resp.read(): probe only needs TLS socket metadata;
                # draining the body could use unbounded memory on a hostile host.
                # Closing the stream context is enough.
    except Exception:
        # Fail-soft: httpx TLS probe must never fail the scan.
        pass

    return CryptoProbeFacts(
        tls_in_use=True,
        tls_version=tls_version,
        cipher=cipher,
        sslmode=sslmode,
        source=source,
    )
