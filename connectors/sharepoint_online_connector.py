"""
Microsoft Graph reader, type ``sharepoint_online``, delegated mode (device code).

Contract: ``docs/desenho/2206.1.md`` (task 2206.1, #2261; real proof in #2260).

* Nothing environment-specific lives here: tenant, client id, scopes, login host,
  Graph base URL, the host allowlists, the download host suffixes, the folder and
  every limit come from the target YAML. A missing key is a ``config_error`` citing
  it; there is no default (operator rule on #2261).
* Read-only. A human signs in with the OAuth device code flow (public client, no
  secret) and only from an interactive one-shot CLI scan
  (``enable_interactive_sign_in()`` plus a terminal on the prompt stream). Tokens
  live in memory for the duration of ``run()`` only.
* The delegated file permission lets the token read the whole drive; the folder
  restriction is enforced here: the configured root folder is resolved once to
  ``(driveId, itemId)`` and the walk only follows item ids below it.
* Downloads use the pre-authenticated ``Location`` of ``/content`` through a second
  client without ``Authorization``, after the YAML host-suffix allowlist and the
  outbound URL guard (no private-network opt-in).
* Tokens, the device code, the client id and download URLs never reach a log, a
  failure, a finding, an exception that leaves ``run()`` or ``repr()``. Every failure
  detail is a fixed message from the design.

What this module has been tested against is a simulated Graph (tests/m365_fake_graph.py).
Real behaviour against a personal OneDrive is only what the Phase 0 evidence records.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
import time
from collections import deque
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, NamedTuple
from urllib.parse import quote

import httpx

from connectors import url_guard
from connectors.filesystem_connector import (
    SUPPORTED_EXTENSIONS,
    _read_text_sample,
    _scan_sqlite_file_as_db,
    scan_archive_at_path,
)
from core.about import get_http_user_agent
from core.archives import (
    default_compressed_extensions,
    is_supported_archive,
    normalize_compressed_extensions,
)
from core.connector_registry import register
from core.content_type import (
    choose_effective_pdf_extension,
    choose_effective_rich_media_extension,
)

# Protocol constants (OAuth 2.0 device authorization grant, RFC 8628 / Entra v2.0).
DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
OAUTH_PATH = "oauth2/v2.0"
OFFLINE_ACCESS_SCOPE = "offline_access"  # OAuth scope that asks for a refresh token

# Keys the reader requires; there is no default for any of them (#2261).
REQUIRED_KEYS = [
    "name",
    "auth.mode",
    "auth.tenant",
    "auth.client_id",
    "auth.login_host",
    "auth.scopes",
    "graph.base_url",
    "download_host_suffixes",
    "drive",
    "include_names",
    "max_depth",
    "max_file_bytes",
    "page_size",
    "max_pages_per_folder",
    "http_timeout_seconds",
    "throttle_max_wait_seconds",
]

REFRESH_MARGIN_SECONDS = 300
THROTTLE_BACKOFF_SECONDS = (1, 2, 4, 8, 16)  # one wait per throttled attempt (5)
SERVER_ERROR_BACKOFF_SECONDS = (1, 2, 4)  # one wait per failed attempt (3)
SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}

AUTH_REQUIRED_MESSAGE = (
    "delegated sign-in needs an interactive CLI session (run the scan from a "
    "terminal); unattended scans use app-only mode (#2262)"
)
SIGN_IN_EXPIRED_MESSAGE = "Microsoft sign-in code expired"
TOKEN_REJECTED_MESSAGE = "Microsoft Graph rejected the access token"
RENEWAL_FAILED_MESSAGE = (
    "Microsoft sign-in session could not be renewed without a terminal"
)

IGNORED_REASONS = ("remote", "package", "other_drive", "malware", "deleted", "no_facet")
_TARGET_ENDING_REASONS = frozenset({"auth_failed", "auth_required", "config_error"})

_GUID = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")
_TENANT = re.compile(r"[A-Za-z0-9-]{1,64}")
_HOST = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?)+"
)
# Read-only rule on the scope structure: <Resource>.Read, .Read.All or .Read.Selected.
_READ_PERMISSION = re.compile(
    r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)*?\.Read(?:\.All|\.Selected)?"
)
_WRITE_WORDS = re.compile(r"write|manage|fullcontrol", re.I)
_HOST_SUFFIX = re.compile(r"(?:\.[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?){2,}")
_ITEM_ID = re.compile(r"[A-Za-z0-9!._-]{1,256}")
_FORBIDDEN_SEGMENT_CHARS = frozenset("\\*<>?:|")
_OAUTH_ERROR = re.compile(r"[a-z_]{1,64}")
_LOGGED_URL = re.compile(r"https?://([A-Za-z0-9.-]+)(?::\d+)?(?:[/?#][^\s\"'<>]*)?")

_interactive_enabled = False
_DEVICE_CODE_LOCK = threading.Lock()
_LOG_FILTER_LOCK = threading.Lock()
_REDACTED_SUFFIXES: set[str] = set()


class SharePointOnlineError(Exception):
    """A failure that ends the target (or one item); ``detail`` is a fixed message."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class ScopeEntry(NamedTuple):
    display_path: str
    size: int
    kind: Literal["file", "folder"]
    skipped_reason: str | None


def enable_interactive_sign_in() -> None:
    """Allow the device code sign-in in this process (one-shot CLI scan only)."""
    global _interactive_enabled
    _interactive_enabled = True


# ----------------------------------------------------------------------------
# Log hygiene
# ----------------------------------------------------------------------------


def _is_download_host(host: str, suffixes: Any) -> bool:
    host = host.lower()
    return any(host.endswith(suffix) and len(host) > len(suffix) for suffix in suffixes)


def _redact_logged_url(match: re.Match[str]) -> str:
    host = match.group(1).lower()
    with _LOG_FILTER_LOCK:
        suffixes = tuple(_REDACTED_SUFFIXES)
    if _is_download_host(host, suffixes):
        return f"https://{host}/<redacted>"
    return match.group(0)


class _DownloadUrlRedactor(logging.Filter):
    """Rewrites download-host URLs in ``httpx`` records to ``https://<host>/<redacted>``."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken record is left to logging itself
            return True
        redacted = _LOGGED_URL.sub(_redact_logged_url, message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return True


def install_download_log_filter(suffixes: Any) -> None:
    """Install the download-URL redactor on the ``httpx`` logger (idempotent).

    ``suffixes`` are the download host suffixes of a target YAML; they are added to
    the set the redactor covers for the rest of the process.
    """
    with _LOG_FILTER_LOCK:
        _REDACTED_SUFFIXES.update(str(x).lower() for x in suffixes)
        httpx_logger = logging.getLogger("httpx")
        if not any(isinstance(f, _DownloadUrlRedactor) for f in httpx_logger.filters):
            httpx_logger.addFilter(_DownloadUrlRedactor())


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------


class _Settings(NamedTuple):
    tenant: str
    client_id: str
    login_host: str
    scopes: str
    graph_root: str
    graph_host: str
    graph_prefix: bytes
    download_suffixes: tuple[str, ...]
    root_folder: str | None
    root_segments: tuple[str, ...]
    root_folder_id: str | None
    max_depth: int
    max_file_bytes: int
    page_size: int
    max_pages: int
    http_timeout: int
    throttle_max_wait: int
    include_names: frozenset[str]
    token_cache_path: Path | None


def _config_error(message: str) -> SharePointOnlineError:
    return SharePointOnlineError("config_error", message)


def _lookup(cfg: dict[str, Any], dotted: str) -> Any:
    node: Any = cfg
    for part in dotted.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _int_key(cfg: dict[str, Any], key: str, low: int, high: int) -> int:
    raw = _lookup(cfg, key)
    if isinstance(raw, bool) or not isinstance(raw, int) or not low <= raw <= high:
        raise _config_error(f"{key} must be an integer between {low} and {high}")
    return raw


def _root_segments(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw.startswith("/"):
        raise _config_error("root_folder must be an absolute folder path")
    body = raw[1:].rstrip("/")
    if not body:
        raise _config_error("root_folder must be a folder, never the drive root")
    segments = tuple(body.split("/"))
    for seg in segments:
        if (
            not seg
            or seg in (".", "..")
            or any(ch in _FORBIDDEN_SEGMENT_CHARS for ch in seg)
            or not seg.isprintable()
        ):
            raise _config_error("root_folder has an empty, relative or invalid segment")
    return segments


def _graph_base(cfg: dict[str, Any]) -> tuple[str, str, bytes]:
    raw = _lookup(cfg, "graph.base_url")
    try:
        url = httpx.URL(raw) if isinstance(raw, str) else None
    except (httpx.InvalidURL, TypeError, ValueError):
        url = None
    host = ((url.host if url is not None else "") or "").lower()
    path = url.raw_path if url is not None else b""
    if (
        url is None
        or url.scheme != "https"
        or url.userinfo
        or url.port not in (None, 443)
        or url.query
        or url.fragment
        or not path.startswith(b"/")
        or b".." in path.split(b"/")
        or not _HOST.fullmatch(host)
    ):
        raise _config_error(
            "graph.base_url must be an https URL with a path and no port, "
            "userinfo, query or fragment"
        )
    prefix = path.rstrip(b"/")
    return f"https://{host}{prefix.decode('ascii')}", host, prefix + b"/"


def _read_only_scopes(raw: Any, graph_host: str) -> str:
    """Accept only read permissions, bare or on the configured Graph host."""
    message = (
        "auth.scopes must hold only read permissions (<Resource>.Read, .Read.All "
        "or .Read.Selected, bare or on the graph.base_url host) and optionally "
        f"{OFFLINE_ACCESS_SCOPE}"
    )
    tokens = raw.split() if isinstance(raw, str) and raw.isprintable() else []
    permissions = 0
    for token in tokens:
        if token == OFFLINE_ACCESS_SCOPE:
            continue
        permission = token
        if "://" in token:
            try:
                url = httpx.URL(token)
            except (httpx.InvalidURL, TypeError, ValueError):
                raise _config_error(message) from None
            if (
                url.scheme != "https"
                or (url.host or "").lower() != graph_host
                or url.port is not None
                or url.userinfo
                or url.query
            ):
                raise _config_error(message)
            permission = url.path.lstrip("/")
        if not _READ_PERMISSION.fullmatch(permission) or _WRITE_WORDS.search(
            permission
        ):
            raise _config_error(message)
        permissions += 1
    if not permissions:
        raise _config_error(message)
    return " ".join(tokens)


def _operator_approves_hosts(cfg: dict[str, Any]) -> None:
    """The operator list (DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS) approves login and Graph.

    Reuses the #2086/#2103 gate of config/loader.py with its current semantics: it
    checks only when the operator opted into strict mode.
    """
    from config.loader import assert_explicit_destination_allowlisted

    try:
        assert_explicit_destination_allowlisted(cfg, "sharepoint_online target")
    except ValueError:
        raise _config_error(
            "auth.login_host or graph.base_url is not approved by the operator "
            "credential host list (#2103)"
        ) from None


def _include_names(raw: Any) -> frozenset[str]:
    """Exact, case-sensitive file names; an empty list means "no name filter"."""
    if not isinstance(raw, list) or not all(
        isinstance(n, str)
        and n
        and n.strip() == n
        and n not in (".", "..")
        and "/" not in n
        and "\\" not in n
        and n.isprintable()
        for n in raw
    ):
        raise _config_error(
            "include_names must be a list of exact file names ([] means no filter)"
        )
    return frozenset(raw)


def _cache_refused(reason: str) -> SharePointOnlineError:
    return _config_error(f"auth.token_cache_path is refused: {reason}")


def _private_dir_problem(path: Path) -> str | None:
    st = os.lstat(path)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        return "its directory is a symlink or not a directory"
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        return "its directory must be mode 0700"
    if hasattr(os, "getuid") and st.st_uid != os.getuid():
        return "its directory is not owned by the current user"
    return None


def _windows_acl_platform() -> bool:
    """True on Windows, where privacy comes from the DACL, not from mode bits."""
    return os.name == "nt"


def _restrict_temp_dir(path: str) -> None:
    """Windows: restrict the download temp dir to the current user and prove it.

    POSIX already gets 0700 from ``tempfile.mkdtemp``. On Windows the directory
    inherits the profile ACL, so the reader reuses the repo's owner-only helpers
    (icacls /grant:r and /inheritance:r, then a SID check of the DACL) and fails
    closed when containment cannot be proven.
    """
    if not _windows_acl_platform():
        return
    from core.l3_transformed_rows import (
        L3ContainmentError,
        _restrict_to_owner,
        _windows_acl_sid_snapshot,
        classify_windows_acl_sids,
    )

    try:
        _restrict_to_owner(Path(path))
        current, aces = _windows_acl_sid_snapshot(Path(path))
        classify_windows_acl_sids(aces, current)
    except L3ContainmentError:
        raise _config_error(
            "the download temporary directory could not be restricted to the "
            "current user"
        ) from None


def _posix_file_permissions() -> bool:
    """True where 0600/0700 mode bits exist and can be enforced (not Windows)."""
    return os.name == "posix"


def _token_cache_path(auth: dict[str, Any]) -> Path | None:
    """Optional refresh-token cache (the only optional key; absent = memory only)."""
    if "token_cache_path" not in auth:
        return None
    if not _posix_file_permissions():
        # 0600/0700 cannot be guaranteed without POSIX permissions: fail closed.
        raise _cache_refused("token cache needs POSIX file permissions")
    raw = auth.get("token_cache_path")
    if not isinstance(raw, str) or not raw or not os.path.isabs(raw):
        raise _cache_refused("it must be an absolute file path")
    path = Path(raw)
    parent = path.parent
    if path.name in ("", ".", ".."):
        raise _cache_refused("it must name a file")
    for ancestor in (parent, *parent.parents):
        if os.path.lexists(ancestor / ".git"):
            raise _cache_refused("it is inside a git repository")
    if os.path.lexists(parent):
        problem = _private_dir_problem(parent)
        if problem:
            raise _cache_refused(problem)
    elif not os.path.isdir(parent.parent) or os.path.islink(parent.parent):
        raise _cache_refused("only its own directory may be created")
    if os.path.lexists(path):
        from core.l3_transformed_rows import (
            L3ContainmentError,
            verify_owner_containment,
        )

        try:
            verify_owner_containment(path)
        except L3ContainmentError:
            raise _cache_refused(
                "the file must be a regular 0600 file owned by the current user"
            ) from None
    return path


def _validate(cfg: dict[str, Any]) -> _Settings:
    """Validate the target YAML; every key is required and nothing is assumed."""
    from core.connector_registry import missing_required_keys

    missing = missing_required_keys(cfg, REQUIRED_KEYS)
    if missing:
        raise _config_error(
            f"required key {missing[0]} is missing (sharepoint_online has no defaults)"
        )
    auth = cfg.get("auth")
    if not isinstance(auth, dict):
        raise _config_error("auth must be a mapping")
    mode = auth.get("mode")
    if mode == "app_only":
        raise _config_error("auth.mode app_only is not available yet (#2262)")
    if mode != "delegated":
        raise _config_error("auth.mode must be 'delegated'")
    tenant = auth.get("tenant")
    if not isinstance(tenant, str) or not _TENANT.fullmatch(tenant):
        raise _config_error(
            "auth.tenant must be a tenant id or alias (letters, digits and hyphens)"
        )
    client_id = auth.get("client_id")
    if not isinstance(client_id, str) or not _GUID.fullmatch(client_id):
        raise _config_error("auth.client_id must be a GUID")
    login_host = auth.get("login_host")
    if not isinstance(login_host, str) or not _HOST.fullmatch(login_host.lower()):
        raise _config_error("auth.login_host must be a host name")
    graph_root, graph_host, graph_prefix = _graph_base(cfg)
    scopes = _read_only_scopes(auth.get("scopes"), graph_host)
    _operator_approves_hosts(cfg)
    suffixes = cfg.get("download_host_suffixes")
    if (
        not isinstance(suffixes, list)
        or not suffixes
        or not all(
            isinstance(x, str) and _HOST_SUFFIX.fullmatch(x.lower()) for x in suffixes
        )
    ):
        raise _config_error(
            "download_host_suffixes must be a non-empty list of suffixes that start "
            "with a dot and have at least two labels"
        )
    include_names = _include_names(cfg.get("include_names"))
    token_cache_path = _token_cache_path(auth)
    if cfg.get("drive") != "me":
        raise _config_error("drive selection is not available yet (#2262)")

    has_path = cfg.get("root_folder") is not None
    has_id = cfg.get("root_folder_id") is not None
    if has_path == has_id:
        raise _config_error("exactly one of root_folder or root_folder_id is required")
    root_folder: str | None = None
    segments: tuple[str, ...] = ()
    root_folder_id: str | None = None
    if has_path:
        segments = _root_segments(cfg.get("root_folder"))
        root_folder = "/" + "/".join(segments)
    else:
        raw_id = cfg.get("root_folder_id")
        if (
            not isinstance(raw_id, str)
            or not _ITEM_ID.fullmatch(raw_id)
            or raw_id in (".", "..")
        ):
            raise _config_error("root_folder_id has an invalid format")
        root_folder_id = raw_id

    return _Settings(
        tenant=tenant,
        client_id=client_id,
        login_host=login_host.lower(),
        scopes=scopes,
        graph_root=graph_root,
        graph_host=graph_host,
        graph_prefix=graph_prefix,
        download_suffixes=tuple(x.lower() for x in suffixes),
        root_folder=root_folder,
        root_segments=segments,
        root_folder_id=root_folder_id,
        include_names=include_names,
        token_cache_path=token_cache_path,
        max_depth=_int_key(cfg, "max_depth", 1, 256),
        max_file_bytes=_int_key(cfg, "max_file_bytes", 1, 2 * 1024**3),
        page_size=_int_key(cfg, "page_size", 1, 1000),
        max_pages=_int_key(cfg, "max_pages_per_folder", 1, 1_000_000),
        http_timeout=_int_key(cfg, "http_timeout_seconds", 1, 600),
        throttle_max_wait=_int_key(cfg, "throttle_max_wait_seconds", 1, 600),
    )


def _normalize_extensions(extensions: Any) -> set[str]:
    if not extensions:
        return set(SUPPORTED_EXTENSIONS)
    exts = list(extensions) if isinstance(extensions, (list, set)) else [extensions]
    use_all = any(str(x).strip().lower() in ("*", "all", ".*") for x in exts)
    if use_all:
        return set(SUPPORTED_EXTENSIONS)
    return {e if e.startswith(".") else f".{e.lstrip('*')}" for e in exts}


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------


def _printable(value: Any, limit: int = 256) -> str:
    return "".join(ch for ch in str(value) if ch.isprintable())[:limit]


def _bounded_int(value: Any, low: int, high: int, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return max(low, min(high, value))


def _retry_after_seconds(resp: httpx.Response) -> int | None:
    raw = (resp.headers.get("retry-after") or "").strip()
    if raw.isdigit():
        return int(raw)
    return None


def _oauth_failure(body: dict[str, Any], status: int) -> SharePointOnlineError:
    """auth_failed with the OAuth error code and AADSTS numbers only."""
    error = body.get("error")
    if not isinstance(error, str) or not _OAUTH_ERROR.fullmatch(error):
        return SharePointOnlineError(
            "auth_failed", f"token endpoint error (HTTP {status})"
        )
    raw_codes = body.get("error_codes")
    codes = [
        c
        for c in (raw_codes if isinstance(raw_codes, list) else [])
        if isinstance(c, int) and not isinstance(c, bool)
    ][:5]
    suffix = " (" + ", ".join(f"AADSTS{c}" for c in codes) + ")" if codes else ""
    return SharePointOnlineError("auth_failed", f"token endpoint error {error}{suffix}")


def _status_failure(status: int, where: str) -> SharePointOnlineError:
    if status == 403:
        return SharePointOnlineError(
            "permission_denied", f"{where}: access denied by Microsoft Graph (HTTP 403)"
        )
    if status in (404, 410):
        return SharePointOnlineError(
            "not_found", f"{where}: not found in Microsoft Graph (HTTP {status})"
        )
    return SharePointOnlineError(
        "unreachable",
        f"{where}: unexpected answer from Microsoft Graph (HTTP {status})",
    )


def _download_failure(status: int, where: str) -> SharePointOnlineError:
    if status in (401, 403):
        return SharePointOnlineError(
            "permission_denied", f"{where}: download link refused (HTTP {status})"
        )
    if status in (404, 410):
        return SharePointOnlineError(
            "not_found", f"{where}: download link expired (HTTP {status})"
        )
    return SharePointOnlineError(
        "unreachable",
        f"{where}: unexpected answer from the download host (HTTP {status})",
    )


def _safe_next_link(link: Any, host: str, prefix: bytes) -> httpx.URL | None:
    """The nextLink as a URL only if it stays under the configured Graph base URL."""
    if not isinstance(link, str):
        return None
    try:
        url = httpx.URL(link)
    except (httpx.InvalidURL, TypeError, ValueError):
        return None
    path = url.raw_path.split(b"?", 1)[0]
    if (
        url.scheme != "https"
        or (url.host or "").lower() != host
        or url.port not in (None, 443)
        or url.userinfo
        or not path.startswith(prefix)
        or b".." in path.split(b"/")
        or b"%2e" in path.lower()
    ):
        return None
    return url


class _Tokens:
    """In-memory OAuth tokens; never printed."""

    __slots__ = ("access", "refresh", "expires_at")

    def __init__(self, access: str, refresh: str | None, expires_at: float) -> None:
        self.access = access
        self.refresh = refresh
        self.expires_at = expires_at

    def __repr__(self) -> str:
        return "<_Tokens redacted>"

    __str__ = __repr__


class _Item(NamedTuple):
    """One node seen by the walk (or one per-item failure)."""

    kind: Literal["file", "folder"]
    display_path: str
    name: str
    item_id: str
    size: int
    skipped_reason: str | None
    failure: tuple[str, str] | None


class _ListingViolation(NamedTuple):
    detail: str


# ----------------------------------------------------------------------------
# Connector
# ----------------------------------------------------------------------------


class SharePointOnlineConnector:
    """Graph reader for one folder of the signed-in user's OneDrive (delegated)."""

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        extensions: set[str] | list[str] | None = None,
        scan_sqlite_as_db: bool = True,
        sample_limit: int = 5,
        file_sample_max_chars: int = 12_000,
        file_passwords: dict[str, str] | None = None,
        *,
        _transport: httpx.BaseTransport | None = None,
        _sleep: Any = time.sleep,
        _monotonic: Any = time.monotonic,
        _prompt_stream: Any = None,
        _interactive: bool | None = None,
    ) -> None:
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.scan_sqlite_as_db = scan_sqlite_as_db
        self.sample_limit = sample_limit
        self.file_sample_max_chars = int(file_sample_max_chars)
        self.extensions = _normalize_extensions(extensions)
        self.file_passwords = file_passwords or {}
        self._name = str(target_config.get("name") or "sharepoint_online")
        self._transport = _transport
        self._sleep = _sleep
        self._monotonic = _monotonic
        self._prompt_stream = _prompt_stream
        self._interactive = _interactive
        self._settings: _Settings | None = None
        self._tokens: _Tokens | None = None
        self._drive_id: str = ""
        self._tmpdir: str | None = None
        self._user_agent = get_http_user_agent()

        fs_opts = target_config.get("file_scan") or {}
        self.scan_compressed = bool(fs_opts.get("scan_compressed"))
        self.max_inner_size = fs_opts.get("max_inner_size")
        self.max_members = fs_opts.get("max_members")
        self.max_total_uncompressed = fs_opts.get("max_total_uncompressed")
        self.max_expansion_ratio = fs_opts.get("max_expansion_ratio")
        self.compressed_extensions = normalize_compressed_extensions(
            fs_opts.get("compressed_extensions") or default_compressed_extensions()
        )
        self.use_content_type = bool(fs_opts.get("use_content_type", False))
        from core.licensing.augmented_scan import effective_rich_media_flags

        self.scan_rich_media_metadata, self.scan_image_ocr = effective_rich_media_flags(
            bool(fs_opts.get("scan_rich_media_metadata", False)),
            bool(fs_opts.get("scan_image_ocr", False)),
        )
        try:
            self.ocr_max_dimension = int(fs_opts.get("ocr_max_dimension", 2000))
        except (TypeError, ValueError):
            self.ocr_max_dimension = 2000
        self.ocr_max_dimension = max(256, min(8000, self.ocr_max_dimension))
        self.ocr_lang = str(fs_opts.get("ocr_lang") or "eng").strip() or "eng"
        self.scan_for_stego = bool(fs_opts.get("scan_for_stego", False))
        from core.rich_media_magic import IMAGE_EXTENSIONS, RICH_MEDIA_SCAN_EXTENSIONS

        if self.scan_rich_media_metadata:
            self.extensions = set(self.extensions) | set(RICH_MEDIA_SCAN_EXTENSIONS)
        elif self.scan_image_ocr:
            self.extensions = set(self.extensions) | set(IMAGE_EXTENSIONS)

    def __repr__(self) -> str:
        return f"SharePointOnlineConnector(name={_printable(self._name)!r})"

    __str__ = __repr__

    # -- public entry points ---------------------------------------------------

    def run(self) -> None:
        """Scan the configured folder; every failure becomes ``save_failure``."""
        counts = dict.fromkeys(IGNORED_REASONS, 0)
        stats = {"listed": 0, "downloaded": 0, "depth_limited": 0}
        try:
            client = self._session()
            try:
                self._tmpdir = tempfile.mkdtemp(prefix="databoar-m365-")
                _restrict_temp_dir(self._tmpdir)
                for item in self._walk(client, stats):
                    self._handle_item(client, item, counts, stats)
            finally:
                client.close()
            ignored = sum(counts.values())
            self._log_summary(stats, counts)
            if ignored:
                self._save_failure(
                    "skipped",
                    f"{ignored} items skipped: "
                    + ", ".join(f"{r}={counts[r]}" for r in IGNORED_REASONS),
                )
        except SharePointOnlineError as failure:
            if failure.reason == "auth_failed":
                self._drop_cache()
            self._save_failure(failure.reason, failure.detail)
        except KeyboardInterrupt:
            raise
        except Exception as unexpected:  # noqa: BLE001 - nothing may leave run()
            self._save_failure(
                "unreachable",
                "unexpected error in the sharepoint_online reader "
                f"({type(unexpected).__name__})",
            )
        finally:
            self._tokens = None
            if self._tmpdir:
                shutil.rmtree(self._tmpdir, ignore_errors=True)
                self._tmpdir = None

    def list_scope(self) -> list[ScopeEntry]:
        """Sign in, resolve and walk without downloading; target-ending errors raise."""
        stats = {"listed": 0, "downloaded": 0, "depth_limited": 0}
        try:
            client = self._session()
            try:
                return [
                    ScopeEntry(i.display_path, i.size, i.kind, i.skipped_reason)
                    for i in self._walk(client, stats)
                ]
            finally:
                client.close()
        except SharePointOnlineError as failure:
            if failure.reason == "auth_failed":
                self._drop_cache()
            raise
        except KeyboardInterrupt:
            raise
        except Exception as unexpected:  # noqa: BLE001 - keep URLs out of the message
            raise SharePointOnlineError(
                "unreachable",
                "unexpected error in the sharepoint_online reader "
                f"({type(unexpected).__name__})",
            ) from None
        finally:
            self._tokens = None

    # -- session -----------------------------------------------------------------

    def _session(self) -> httpx.Client:
        self._settings = _validate(self.config)
        install_download_log_filter(self._settings.download_suffixes)
        cached = self._load_cache()
        if cached is None and not self._interactive_allowed():
            raise SharePointOnlineError("auth_required", AUTH_REQUIRED_MESSAGE)
        client = self._open_api_client()
        try:
            if cached is not None:
                # Renew from the cache: no device code, no new MFA.
                self._tokens = _Tokens("", cached, self._monotonic())
                cached = None
                self._renew(client)
            else:
                self._device_code_sign_in(client)
        except BaseException:
            client.close()
            raise
        return client

    # -- optional refresh-token cache (auth.token_cache_path) ----------------------

    def _cache_binding(self) -> dict[str, str]:
        settings = self._settings
        assert settings is not None
        return {
            "client_id": settings.client_id,
            "tenant": settings.tenant,
            "login_host": settings.login_host,
            "scopes_sha256": hashlib.sha256(settings.scopes.encode()).hexdigest(),
        }

    def _load_cache(self) -> str | None:
        """Refresh token from the cache, or None (absent, unreadable or other config)."""
        path = self._settings.token_cache_path if self._settings else None
        if path is None or not os.path.lexists(path):
            return None
        from core.l3_transformed_rows import (
            L3ContainmentError,
            verify_owner_containment_fd,
        )

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        data: Any = None
        try:
            fd = os.open(path, flags)
            try:
                verify_owner_containment_fd(fd)
                raw = os.read(fd, 65_536)
            finally:
                os.close(fd)
            data = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError, L3ContainmentError):
            data = None
        refresh = data.get("refresh_token") if isinstance(data, dict) else None
        bound = isinstance(data, dict) and all(
            data.get(k) == v for k, v in self._cache_binding().items()
        )
        if not bound or not isinstance(refresh, str) or not refresh:
            self._drop_cache()
            return None
        return refresh

    def _save_cache(self, refresh: str | None) -> None:
        """Rotate the cache atomically (temp 0600 in the same dir, fsync, replace)."""
        path = self._settings.token_cache_path if self._settings else None
        if path is None:
            return
        if refresh is None:
            self._drop_cache()
            return
        from core.l3_transformed_rows import L3ContainmentError, persist_l3_body

        parent = path.parent
        try:
            if not os.path.lexists(parent):
                os.mkdir(parent, 0o700)
                os.chmod(parent, 0o700)
            problem = _private_dir_problem(parent)
            if problem:
                raise _cache_refused(problem)
            body = json.dumps({**self._cache_binding(), "refresh_token": refresh})
            persist_l3_body(path, body)
            dir_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, L3ContainmentError):
            raise _cache_refused("the cache could not be written safely") from None

    def _drop_cache(self) -> None:
        path = self._settings.token_cache_path if self._settings else None
        if path is None:
            return
        try:
            if os.path.lexists(path) and not os.path.islink(path):
                os.unlink(path)
        except OSError:
            pass

    def _interactive_allowed(self) -> bool:
        enabled = (
            _interactive_enabled
            if self._interactive is None
            else bool(self._interactive)
        )
        if not enabled:
            return False
        stream = self._stream()
        isatty = getattr(stream, "isatty", None)
        if not callable(isatty):
            return False
        try:
            return bool(isatty())
        except (OSError, ValueError):
            return False

    def _stream(self) -> Any:
        return self._prompt_stream if self._prompt_stream is not None else sys.stderr

    def _open_api_client(self) -> httpx.Client:
        assert self._settings is not None
        timeout = float(self._settings.http_timeout)
        pins: dict[str, list[str]] = {}
        for host in (self._settings.login_host, self._settings.graph_host):
            err, ips = url_guard.resolve_and_validate_outbound_url(
                f"https://{host}/", allow_private=False, label=host
            )
            if err or not ips:
                raise SharePointOnlineError(
                    "unreachable", f"outbound URL guard refused {host}"
                )
            pins[host] = [str(ip) for ip in ips]
        if self._transport is not None:
            return httpx.Client(
                transport=self._transport,
                follow_redirects=False,
                timeout=timeout,
            )
        return url_guard.build_pinned_httpx_client(
            host_to_ips=pins, follow_redirects=False, timeout=timeout
        )

    # -- HTTP with retry policies --------------------------------------------------

    def _send(
        self,
        client: httpx.Client,
        request: httpx.Request,
        *,
        service: str,
        where: str | None = None,
        deadline: float | None = None,
        stream: bool = False,
    ) -> httpx.Response:
        """Send with the 429/503 and 5xx policies (section 6 of the design)."""
        prefix = f"{where}: " if where else ""
        cap = self._settings.throttle_max_wait if self._settings else 120
        throttled = 0
        failed = 0
        while True:
            try:
                resp = client.send(request, stream=stream)
            except (httpx.HTTPError, httpx.InvalidURL, ValueError) as network:
                raise SharePointOnlineError(
                    "unreachable",
                    f"{prefix}network error contacting {service} "
                    f"({type(network).__name__})",
                ) from None
            status = resp.status_code
            if status in (429, 503):
                throttled += 1
                wait = _retry_after_seconds(resp)
                if wait is None:
                    wait = THROTTLE_BACKOFF_SECONDS[throttled - 1]
                resp.close()
                self._wait(min(wait, cap), deadline)
                if throttled >= len(THROTTLE_BACKOFF_SECONDS):
                    raise SharePointOnlineError(
                        "throttled",
                        f"{prefix}{service} kept throttling the requests (HTTP {status})",
                    )
                continue
            if status >= 500:
                failed += 1
                resp.close()
                self._wait(min(SERVER_ERROR_BACKOFF_SECONDS[failed - 1], cap), deadline)
                if failed >= len(SERVER_ERROR_BACKOFF_SECONDS):
                    raise SharePointOnlineError(
                        "unreachable",
                        f"{prefix}{service} kept failing (HTTP {status})",
                    )
                continue
            return resp

    def _wait(self, seconds: float, deadline: float | None) -> None:
        if deadline is not None and self._monotonic() + seconds >= deadline:
            raise SharePointOnlineError("auth_failed", SIGN_IN_EXPIRED_MESSAGE)
        self._sleep(seconds)

    def _login_post(
        self,
        client: httpx.Client,
        endpoint: str,
        form: dict[str, str],
        *,
        deadline: float | None = None,
    ) -> tuple[int, dict[str, Any]]:
        assert self._settings is not None
        request = client.build_request(
            "POST",
            f"https://{self._settings.login_host}/{self._settings.tenant}/"
            f"{OAUTH_PATH}/{endpoint}",
            data=form,
            headers={"User-Agent": self._user_agent, "Accept": "application/json"},
        )
        resp = self._send(client, request, service="Microsoft login", deadline=deadline)
        try:
            body = resp.json()
        except ValueError:
            body = None
        finally:
            resp.close()
        if not isinstance(body, dict):
            raise SharePointOnlineError(
                "unreachable", "malformed response from Microsoft login"
            )
        return resp.status_code, body

    # -- device code and tokens ------------------------------------------------------

    def _device_code_sign_in(self, client: httpx.Client) -> None:
        if not self._interactive_allowed():
            raise SharePointOnlineError("auth_required", AUTH_REQUIRED_MESSAGE)
        assert self._settings is not None
        with _DEVICE_CODE_LOCK:
            started = self._monotonic()
            status, body = self._login_post(
                client,
                "devicecode",
                {"client_id": self._settings.client_id, "scope": self._settings.scopes},
            )
            if status != 200:
                raise _oauth_failure(body, status)
            device_code = body.get("device_code")
            user_code = body.get("user_code")
            verification_uri = body.get("verification_uri")
            if not all(
                isinstance(v, str) and v
                for v in (device_code, user_code, verification_uri)
            ):
                raise SharePointOnlineError(
                    "unreachable", "malformed response from Microsoft login"
                )
            lifetime = _bounded_int(body.get("expires_in"), 60, 1800, 900)
            interval = _bounded_int(body.get("interval"), 1, 60, 5)
            deadline = started + lifetime
            self._prompt(verification_uri, user_code, lifetime)
            form = {
                "grant_type": DEVICE_CODE_GRANT,
                "client_id": self._settings.client_id,
                "device_code": device_code,
            }
            while True:
                if self._monotonic() >= deadline:
                    raise SharePointOnlineError("auth_failed", SIGN_IN_EXPIRED_MESSAGE)
                status, body = self._login_post(
                    client, "token", form, deadline=deadline
                )
                if status == 200:
                    self._store_tokens(body)
                    return
                error = body.get("error")
                if error == "authorization_pending":
                    pass
                elif error == "slow_down":
                    interval += 5
                elif error == "authorization_declined":
                    raise SharePointOnlineError(
                        "auth_failed", "Microsoft sign-in was declined"
                    )
                elif error == "expired_token":
                    raise SharePointOnlineError("auth_failed", SIGN_IN_EXPIRED_MESSAGE)
                elif error == "bad_verification_code":
                    raise SharePointOnlineError(
                        "auth_failed", "device code was not recognised"
                    )
                else:
                    raise _oauth_failure(body, status)
                if self._monotonic() + interval >= deadline:
                    raise SharePointOnlineError("auth_failed", SIGN_IN_EXPIRED_MESSAGE)
                self._sleep(interval)

    def _prompt(self, verification_uri: str, user_code: str, lifetime: int) -> None:
        minutes = max(1, math.ceil(lifetime / 60))
        stream = self._stream()
        stream.write(
            f"To sign in to Microsoft for target '{_printable(self._name)}', open "
            f"{_printable(verification_uri)} and enter the code {_printable(user_code)}. "
            f"The code expires in {minutes} minutes.\n"
        )
        flush = getattr(stream, "flush", None)
        if callable(flush):
            try:
                flush()
            except (OSError, ValueError):
                pass

    def _store_tokens(self, body: dict[str, Any]) -> None:
        access = body.get("access_token")
        if not isinstance(access, str) or not access:
            raise SharePointOnlineError(
                "auth_failed", "token endpoint returned no access token"
            )
        refresh = body.get("refresh_token")
        lifetime = _bounded_int(body.get("expires_in"), 1, 86_400, 3600)
        self._tokens = _Tokens(
            access,
            refresh if isinstance(refresh, str) and refresh else None,
            self._monotonic() + lifetime,
        )
        self._save_cache(self._tokens.refresh)

    def _access_token(self, client: httpx.Client) -> str:
        tokens = self._tokens
        if tokens is None:
            raise SharePointOnlineError("auth_failed", TOKEN_REJECTED_MESSAGE)
        now = self._monotonic()
        if tokens.refresh is not None:
            if now >= tokens.expires_at - REFRESH_MARGIN_SECONDS:
                self._renew(client)
        elif now >= tokens.expires_at:
            self._sign_in_again(client)
        assert self._tokens is not None
        return self._tokens.access

    def _renew(self, client: httpx.Client) -> None:
        """Refresh grant; the new refresh token replaces (and drops) the old one."""
        assert self._settings is not None and self._tokens is not None
        refresh = self._tokens.refresh
        if refresh is None:
            self._sign_in_again(client)
            return
        status, body = self._login_post(
            client,
            "token",
            {
                "grant_type": "refresh_token",
                "client_id": self._settings.client_id,
                "scope": self._settings.scopes,
                "refresh_token": refresh,
            },
        )
        if status == 200:
            self._store_tokens(body)
            return
        if body.get("error") in ("invalid_grant", "interaction_required"):
            self._drop_cache()
            self._sign_in_again(client)
            return
        raise _oauth_failure(body, status)

    def _sign_in_again(self, client: httpx.Client) -> None:
        self._tokens = None
        if not self._interactive_allowed():
            raise SharePointOnlineError("auth_failed", RENEWAL_FAILED_MESSAGE)
        self._device_code_sign_in(client)

    # -- Graph -------------------------------------------------------------------------

    def _graph_get(
        self,
        client: httpx.Client,
        url: httpx.URL,
        *,
        where: str,
        stream: bool = False,
    ) -> httpx.Response:
        """GET with a per-request bearer; one refresh and one retry on 401."""
        for attempt in (1, 2):
            token = self._access_token(client)
            request = client.build_request(
                "GET",
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": self._user_agent,
                    "Accept": "application/json",
                },
            )
            resp = self._send(
                client, request, service="Microsoft Graph", where=where, stream=stream
            )
            if resp.status_code != 401:
                return resp
            resp.close()
            if attempt == 1:
                self._renew(client)
        raise SharePointOnlineError("auth_failed", TOKEN_REJECTED_MESSAGE)

    def _graph_json(
        self, client: httpx.Client, url: httpx.URL, where: str
    ) -> dict[str, Any]:
        resp = self._graph_get(client, url, where=where)
        try:
            if resp.status_code != 200:
                raise _status_failure(resp.status_code, where)
            try:
                body = resp.json()
            except ValueError:
                body = None
        finally:
            resp.close()
        if not isinstance(body, dict):
            raise SharePointOnlineError(
                "unreachable", f"{where}: malformed response from Microsoft Graph"
            )
        return body

    def _resolve_root(self, client: httpx.Client) -> tuple[str, str]:
        """Resolve the root folder once; return ``(item id, display path)``."""
        settings = self._settings
        assert settings is not None
        if settings.root_folder is not None:
            encoded = "".join(
                "/" + quote(seg, safe="") for seg in settings.root_segments
            )
            url = httpx.URL(f"{settings.graph_root}/me/drive/root:{encoded}")
            where = "root_folder"
        else:
            assert settings.root_folder_id is not None
            url = httpx.URL(
                f"{settings.graph_root}/me/drive/items/{quote(settings.root_folder_id, safe='')}"
            )
            where = "root_folder_id"
        body = self._graph_json(client, url, where)
        parent = body.get("parentReference")
        drive_id = parent.get("driveId") if isinstance(parent, dict) else None
        item_id = body.get("id")
        if (
            not isinstance(body.get("folder"), dict)
            or any(k in body for k in ("root", "remoteItem", "package"))
            or not isinstance(drive_id, str)
            or not drive_id
            or not isinstance(item_id, str)
            or not item_id
        ):
            raise _config_error(
                "root_folder must be a folder inside the signed-in user's drive"
            )
        self._drive_id = drive_id
        if settings.root_folder is not None:
            display = f"onedrive:{settings.root_folder}"
        else:
            display = f"onedrive:/{_printable(body.get('name') or item_id)}"
        return item_id, display

    def _children(
        self, client: httpx.Client, folder_id: str, where: str
    ) -> Iterator[dict[str, Any] | _ListingViolation]:
        settings = self._settings
        assert settings is not None
        url = httpx.URL(
            f"{settings.graph_root}/me/drive/items/{quote(folder_id, safe='')}/children"
            f"?$top={settings.page_size}"
        )
        seen_links = {str(url)}
        pages = 0
        while True:
            body = self._graph_json(client, url, where)
            pages += 1
            values = body.get("value")
            for value in values if isinstance(values, list) else []:
                yield value
            link = body.get("@odata.nextLink")
            if link is None:
                return
            next_url = _safe_next_link(link, settings.graph_host, settings.graph_prefix)
            if next_url is None or str(next_url) in seen_links:
                yield _ListingViolation(f"{where}: unexpected @odata.nextLink rejected")
                return
            if pages >= settings.max_pages:
                yield _ListingViolation(
                    f"{where}: too many pages in one folder listing"
                )
                return
            seen_links.add(str(next_url))
            url = next_url

    def _classify(self, value: Any) -> str | None:
        if not isinstance(value, dict):
            return "no_facet"
        for facet, reason in (
            ("remoteItem", "remote"),
            ("package", "package"),
            ("malware", "malware"),
            ("deleted", "deleted"),
        ):
            if facet in value:
                return reason
        parent = value.get("parentReference")
        drive_id = parent.get("driveId") if isinstance(parent, dict) else None
        if not isinstance(drive_id, str) or drive_id.casefold() != (
            self._drive_id.casefold()
        ):
            return "other_drive"
        item_id = value.get("id")
        if not isinstance(item_id, str) or not item_id:
            return "no_facet"
        if isinstance(value.get("folder"), dict) or isinstance(value.get("file"), dict):
            return None
        return "no_facet"

    def _walk(self, client: httpx.Client, stats: dict[str, int]) -> Iterator[_Item]:
        """Breadth-first walk by item id from the resolved root folder."""
        assert self._settings is not None
        root_id, root_display = self._resolve_root(client)
        queue: deque[tuple[str, str, int]] = deque([(root_id, root_display, 0)])
        seen = {root_id}
        while queue:
            folder_id, display, depth = queue.popleft()
            try:
                for value in self._children(client, folder_id, display):
                    if isinstance(value, _ListingViolation):
                        yield _Item(
                            "folder",
                            display,
                            "",
                            folder_id,
                            0,
                            "scope_violation",
                            ("scope_violation", value.detail),
                        )
                        break
                    stats["listed"] += 1
                    item = self._to_item(value, display)
                    names = self._settings.include_names
                    if (
                        names
                        and item.kind == "file"
                        and item.skipped_reason is None
                        and item.name not in names
                    ):
                        continue  # outside include_names: never downloaded nor listed
                    if item.kind == "folder" and item.skipped_reason is None:
                        if item.item_id in seen:
                            continue
                        seen.add(item.item_id)
                        if depth + 1 < self._settings.max_depth:
                            queue.append((item.item_id, item.display_path, depth + 1))
                        else:
                            stats["depth_limited"] += 1
                    yield item
            except SharePointOnlineError as failure:
                if depth == 0 or failure.reason in _TARGET_ENDING_REASONS:
                    raise
                yield _Item(
                    "folder",
                    display,
                    "",
                    folder_id,
                    0,
                    failure.reason,
                    (failure.reason, failure.detail),
                )

    def _to_item(self, value: Any, parent_display: str) -> _Item:
        reason = self._classify(value)
        data = value if isinstance(value, dict) else {}
        name = _printable(data.get("name") or "")
        size = data.get("size")
        size = size if isinstance(size, int) and not isinstance(size, bool) else 0
        kind: Literal["file", "folder"] = (
            "folder" if isinstance(data.get("folder"), dict) else "file"
        )
        item_id = data.get("id") if isinstance(data.get("id"), str) else ""
        return _Item(
            kind, f"{parent_display}/{name}", name, item_id, size, reason, None
        )

    # -- per item -------------------------------------------------------------------------

    def _handle_item(
        self,
        client: httpx.Client,
        item: _Item,
        counts: dict[str, int],
        stats: dict[str, int],
    ) -> None:
        if item.failure is not None:
            self._save_failure(*item.failure)
            return
        if item.skipped_reason is not None:
            counts[item.skipped_reason] = counts.get(item.skipped_reason, 0) + 1
            return
        if item.kind != "file":
            return
        ext = Path(item.name).suffix.lower()
        if ext not in self.extensions and not (
            self.scan_compressed and ext in self.compressed_extensions
        ):
            return
        assert self._settings is not None
        if item.size > self._settings.max_file_bytes:
            self._save_failure(
                "skipped", f"{item.display_path}: file larger than max_file_bytes"
            )
            return
        temp_path: str | None = None
        try:
            temp_path = self._download(client, item, ext)
            stats["downloaded"] += 1
            self._extract(temp_path, item, ext)
        except SharePointOnlineError as failure:
            if failure.reason in _TARGET_ENDING_REASONS:
                raise
            self._save_failure(failure.reason, failure.detail)
        except KeyboardInterrupt:
            raise
        except Exception as extraction:  # noqa: BLE001 - one bad file never stops the scan
            self._save_failure(
                "skipped",
                f"{item.display_path}: content could not be extracted "
                f"({type(extraction).__name__})",
            )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def _download(self, client: httpx.Client, item: _Item, ext: str) -> str:
        """Download one file to the private temp dir; return the temp path."""
        settings = self._settings
        assert settings is not None
        content_url = httpx.URL(
            f"{settings.graph_root}/me/drive/items/{quote(item.item_id, safe='')}/content"
        )
        where = item.display_path
        for attempt in (1, 2):
            resp = self._graph_get(client, content_url, where=where, stream=True)
            try:
                if resp.status_code == 200:
                    return self._write_body(resp, where, ext)
                if resp.status_code != 302:
                    raise _status_failure(resp.status_code, where)
                location = resp.headers.get("location")
            finally:
                resp.close()
            url, host, ips = self._approve_location(location, where)
            status, path = self._fetch_download(url, host, ips, where, ext)
            if path is not None:
                return path
            if status in (401, 403, 404, 410) and attempt == 1:
                continue
            raise _download_failure(status, where)
        raise _download_failure(403, where)  # pragma: no cover - the loop always exits

    def _approve_location(
        self, location: str | None, where: str
    ) -> tuple[httpx.URL, str, list[Any]]:
        try:
            url = httpx.URL(location or "")
        except (httpx.InvalidURL, TypeError, ValueError):
            raise SharePointOnlineError(
                "scope_violation", f"{where}: download host not allowlisted: <invalid>"
            ) from None
        host = (url.host or "").lower()
        shown = _printable(host) or "<none>"
        assert self._settings is not None
        if not host or not _is_download_host(host, self._settings.download_suffixes):
            raise SharePointOnlineError(
                "scope_violation", f"{where}: download host not allowlisted: {shown}"
            )
        if url.scheme != "https" or url.userinfo or url.port not in (None, 443):
            raise SharePointOnlineError(
                "scope_violation", f"{where}: download link rejected: {shown}"
            )
        err, ips = url_guard.resolve_and_validate_outbound_url(
            f"https://{host}/", allow_private=False, label="download host"
        )
        if err or not ips:
            raise SharePointOnlineError(
                "scope_violation",
                f"{where}: download host refused by the outbound URL guard: {shown}",
            )
        return url, host, ips

    def _fetch_download(
        self, url: httpx.URL, host: str, ips: list[Any], where: str, ext: str
    ) -> tuple[int, str | None]:
        """GET the pre-authenticated URL with a separate client (no Authorization)."""
        assert self._settings is not None
        timeout = float(self._settings.http_timeout)
        if self._transport is not None:
            downloader = httpx.Client(
                transport=self._transport,
                follow_redirects=False,
                timeout=timeout,
            )
        else:
            downloader = url_guard.build_pinned_httpx_client(
                host_to_ips={host: [str(ip) for ip in ips]},
                follow_redirects=False,
                timeout=timeout,
            )
        with downloader:
            request = downloader.build_request(
                "GET", url, headers={"User-Agent": self._user_agent}
            )
            resp = self._send(
                downloader,
                request,
                service="the download host",
                where=where,
                stream=True,
            )
            try:
                if resp.status_code == 200:
                    return 200, self._write_body(resp, where, ext)
                return resp.status_code, None
            finally:
                resp.close()

    def _write_body(self, resp: httpx.Response, where: str, ext: str) -> str:
        """Stream the body into the temp dir, aborting above ``max_file_bytes``."""
        assert self._settings is not None and self._tmpdir is not None
        cap = self._settings.max_file_bytes
        total = 0
        with tempfile.NamedTemporaryFile(
            dir=self._tmpdir, prefix="item-", suffix=ext, delete=False
        ) as handle:
            path = handle.name
            try:
                for chunk in resp.iter_bytes():
                    total += len(chunk)
                    if total > cap:
                        raise SharePointOnlineError(
                            "skipped", f"{where}: file larger than max_file_bytes"
                        )
                    handle.write(chunk)
            except BaseException:
                handle.close()
                try:
                    os.unlink(path)
                except OSError:
                    pass
                raise
        return path

    def _extract(self, temp_path: str, item: _Item, ext: str) -> None:
        """Same extraction and detection as the SharePoint on-prem connector."""
        from utils.audit_log_display import audit_log_target_label

        display = item.display_path
        if (
            self.scan_compressed
            and ext in self.compressed_extensions
            and is_supported_archive(Path(temp_path), exts=self.compressed_extensions)
        ):
            scan_archive_at_path(
                archive_path=Path(temp_path),
                archive_display_name=item.name,
                target_name=self._name,
                path_display=display,
                scanner=self.scanner,
                db_manager=self.db_manager,
                extensions=self.extensions,
                max_inner_size=self.max_inner_size,
                max_members=self.max_members,
                max_total_uncompressed=self.max_total_uncompressed,
                max_expansion_ratio=self.max_expansion_ratio,
                file_passwords=self.file_passwords,
                file_sample_max_chars=self.file_sample_max_chars,
                rich_media_metadata=self.scan_rich_media_metadata,
                scan_image_ocr=self.scan_image_ocr,
                ocr_max_dimension=self.ocr_max_dimension,
                ocr_lang=self.ocr_lang,
                scan_for_stego=self.scan_for_stego,
                use_content_type=self.use_content_type,
                audit_log_name=audit_log_target_label(
                    self.config, default="SharePoint Online"
                ),
            )
            return
        if self.scan_sqlite_as_db and ext in SQLITE_EXTENSIONS:
            for finding in _scan_sqlite_file_as_db(
                Path(temp_path), self.scanner, self.sample_limit
            ):
                self.db_manager.save_finding(
                    "filesystem",
                    target_name=self._name,
                    path=display,
                    file_name=finding["file_name"],
                    data_type=finding["data_type"],
                    sensitivity_level=finding["sensitivity_level"],
                    pattern_detected=finding["pattern_detected"],
                    norm_tag=finding["norm_tag"],
                    ml_confidence=finding["ml_confidence"],
                )
            return
        effective_ext = choose_effective_pdf_extension(
            ext, self.use_content_type, Path(temp_path)
        )
        effective_ext = choose_effective_rich_media_extension(
            effective_ext, self.use_content_type, Path(temp_path)
        )
        text = _read_text_sample(
            Path(temp_path),
            effective_ext,
            self.file_sample_max_chars,
            self.file_passwords,
            rich_media_metadata=self.scan_rich_media_metadata,
            scan_image_ocr=self.scan_image_ocr,
            ocr_max_dimension=self.ocr_max_dimension,
            ocr_lang=self.ocr_lang,
            scan_for_stego=self.scan_for_stego,
        )
        res = self.scanner.scan_file_content(text, Path(item.name))
        if res is not None:
            self.db_manager.save_finding(
                "filesystem",
                target_name=self._name,
                path=display,
                file_name=item.name,
                data_type=ext.replace(".", "").upper(),
                sensitivity_level=res["sensitivity_level"],
                pattern_detected=res["pattern_detected"],
                norm_tag=res.get("norm_tag", ""),
                ml_confidence=res.get("ml_confidence", 0),
            )

    # -- outputs -----------------------------------------------------------------------------

    def _save_failure(self, reason: str, detail: str) -> None:
        if self.db_manager is not None:
            self.db_manager.save_failure(self._name, reason, detail)

    def _log_summary(self, stats: dict[str, int], counts: dict[str, int]) -> None:
        from utils.audit_log_display import audit_log_target_label
        from utils.logger import get_logger

        get_logger().info(
            "sharepoint_online %s: listed=%d downloaded=%d depth_limited=%d skipped %s",
            audit_log_target_label(self.config, default="SharePoint Online"),
            stats["listed"],
            stats["downloaded"],
            stats["depth_limited"],
            " ".join(f"{r}={counts[r]}" for r in IGNORED_REASONS),
        )


register("sharepoint_online", SharePointOnlineConnector, REQUIRED_KEYS)
