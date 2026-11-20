"""Common layer of the ``object_storage`` reader (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md`` (revisions 1 to 6b; revision 6 wins on conflict), sections
0, 1, 3, 4, 6 to 12 and 14, and the rules R6-1 to R6-10.

The common layer decides scope, limits, network safety, temporary files, findings, failures,
inventory and coverage. It talks to a provider only through the driver contract of
``connectors/object_storage_driver.py`` and never imports a concrete driver (D2306-65).

Security notes (section 6 and section 12):

- one destination host per target, validated once by ``url_guard`` and pinned by IP; every
  request the driver prepares must stay on that host, over ``https``; redirects are never
  followed;
- credentials are read from the environment only (``auth.*_from_env`` with a #1977 prefix),
  kept in ``self._creds`` (a masked ``ResolvedCredentials``) and cleared in ``finally``;
- no failure, log line or inventory field is built from an exception text, a URL or a
  response body: every message is a fixed phrase of this module or of the driver contract.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from connectors import url_guard
from connectors.filesystem_connector import (
    SUPPORTED_EXTENSIONS,
    _read_text_sample,
    _scan_sqlite_file_as_db,
    scan_archive_at_path,
)
from connectors.object_storage_driver import (
    COMMON_FORBIDDEN_INLINE_KEYS,
    DriverConfigError,
    DriverProtocolError,
    DriverSettings,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
    StorageDriver,
    get_driver,
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

# Generic keys (revision 6, R6-8); each driver declares its own ``required_keys``.
REQUIRED_KEYS = ["name", "driver"]

SOURCE_TYPE = "object_storage"
SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}

# Section 1: (default, maximum) of each limit; the minimum is 1.
_LIMITS: dict[str, tuple[int, int]] = {
    "max_objects": (10_000, 1_000_000),
    "max_download_bytes": (1024**3, 100 * 1024**3),
    "max_object_bytes": (100 * 1024**2, 2 * 1024**3),
}
_UNLIMITED = "unlimited"
_TIMEOUT_DEFAULTS = (25, 90)
_TIMEOUT_RANGE = (1, 300)

_LISTING_MAX_BYTES = 16 * 1024 * 1024
_ERROR_BODY_MAX_BYTES = 64 * 1024
_BACKOFF = (1, 2, 4)
_RETRY_AFTER_MAX = 60
_MAX_CONSECUTIVE_EXHAUSTED = 3
_MAX_FAILURES_PER_REASON = 100
_DISPLAY_MAX = 512
_SERVER_HEADER_MAX = 48
_PREFIX_MAX_BYTES = 1024

# Reasons of objects that were listed and not scanned (R6-6).
_NOT_SCANNED_REASONS = (
    "out_of_prefix",
    "invalid_key",
    "unsafe_key",
    "too_large",
    "over_budget",
    "size_mismatch",
    "download_failed",
)
# Reasons whose listed size counts in bytes_not_scanned (section 8, step 8).
_SIZED_REASONS = frozenset(
    {"too_large", "over_budget", "unsafe_key", "size_mismatch", "download_failed"}
)
# Order of the "skipped" summary (section 8, step 6).
_SKIPPED_SUMMARY = (
    "too_large",
    "unsafe_key",
    "out_of_prefix",
    "invalid_key",
    "size_mismatch",
    "download_failed",
)
# Fixed per-object messages (only written with report_object_names: true).
_OBJECT_MESSAGES = {
    "too_large": "object larger than max_object_bytes; not downloaded",
    "unsafe_key": "key has a '.' or '..' segment; not read (unsafe_key)",
    "size_mismatch": "object size differs from the listed size; discarded",
}


class _Stop(Exception):
    """Ends the target with one failure (reason and a fixed message)."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.message = message


class _ObjectFailed(Exception):
    """One object not scanned (reason and a fixed message)."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.message = message


@dataclass
class _Limits:
    max_objects: int | None
    max_download_bytes: int | None
    max_object_bytes: int | None
    disabled: list[str]


@dataclass
class _Stats:
    listed: int = 0
    scanned: int = 0
    bytes_downloaded: int = 0
    folder_marker: int = 0
    extension: int = 0
    not_scanned: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(_NOT_SCANNED_REASONS, 0)
    )
    bytes_not_scanned: int = 0
    unknown_size: int = 0
    listing_complete: bool = False
    per_object: dict[str, int] = field(default_factory=dict)


def _printable(value: str, limit: int | None = None) -> str:
    """Non-printable characters become ``\\xNN`` (``\\uNNNN`` above 0xFF); an escape is never
    split by the cut (R6-7)."""
    out: list[str] = []
    size = 0
    for ch in value:
        if ch.isprintable():
            token = ch
        elif ord(ch) <= 0xFF:
            token = f"\\x{ord(ch):02x}"
        else:
            token = f"\\u{ord(ch):04x}"
        if limit is not None and size + len(token) > limit:
            break
        out.append(token)
        size += len(token)
    return "".join(out)


def _normalize_extensions(extensions: Any) -> set[str]:
    if not extensions:
        return set(SUPPORTED_EXTENSIONS)
    exts = (
        list(extensions) if isinstance(extensions, (list, set, tuple)) else [extensions]
    )
    if any(str(x).strip().lower() in ("*", "all", ".*") for x in exts):
        return set(SUPPORTED_EXTENSIONS)
    out: set[str] = set()
    for raw in exts:
        e = str(raw).strip().lower()
        out.add(e if e.startswith(".") else f".{e.lstrip('*')}")
    return out


def _restrict_temp_dir(path: str) -> None:
    """Windows: restrict the temp dir to the current user and prove it (section 8, step 5).

    Same hardening as ``sharepoint_online`` (copied, as the design allows). POSIX already
    gets 0700 from ``tempfile.mkdtemp``.
    """
    if os.name != "nt":
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
        raise _Stop(
            "error",
            "the download temporary directory could not be restricted to the "
            "current user",
        ) from None


def _readable_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _retry_after(headers: httpx.Headers) -> int | None:
    raw = headers.get("retry-after")
    if raw is None or not raw.strip().isdigit():
        return None
    return min(int(raw.strip()), _RETRY_AFTER_MAX)


def _key_ext(key: str) -> str:
    last = key.rsplit("/", 1)[-1]
    return Path(last).suffix.lower() if "." in last else ""


class ObjectStorageConnector:
    """Read-only object storage connector (one target, one driver, one pinned host)."""

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        extensions: Any = None,
        scan_sqlite_as_db: bool = True,
        sample_limit: int = 5,
        file_sample_max_chars: int = 12_000,
        file_passwords: dict[str, Any] | None = None,
        *,
        _transport: Any = None,
        _sleep: Callable[[float], None] = time.sleep,
        _now: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.scan_sqlite_as_db = scan_sqlite_as_db
        self.sample_limit = sample_limit
        self.file_sample_max_chars = int(file_sample_max_chars)
        self.extensions = _normalize_extensions(extensions)
        self.file_passwords = file_passwords or {}
        self._name = str(target_config.get("name") or "object_storage")
        self._transport = _transport
        self._sleep = _sleep
        self._now = _now or (lambda: datetime.now(timezone.utc))
        self._creds: ResolvedCredentials | None = None
        self._tmpdir: str | None = None

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

        # Run state (reset by run()).
        self._driver: StorageDriver | None = None
        self._driver_name: str = "unknown"
        self._settings: DriverSettings | None = None
        self._limits: _Limits | None = None
        self._timeouts: tuple[float, float] = (
            float(_TIMEOUT_DEFAULTS[0]),
            float(_TIMEOUT_DEFAULTS[1]),
        )
        self._prefix = ""
        self._report_names = False
        self._validated = False
        self._stats = _Stats()
        self._responses = 0
        self._server_header: str | None = None
        self._budget_left: int | None = None
        self._host = ""
        self._obj_counter = 0
        self._limit_failures: list[str] = []
        self._ended: str | None = None

    def __repr__(self) -> str:
        return f"ObjectStorageConnector(name={_printable(self._name, 100)!r})"

    __str__ = __repr__

    # ------------------------------------------------------------------ run

    def run(self) -> None:
        """Scan the target; every failure becomes ``save_failure`` (nothing escapes but
        ``KeyboardInterrupt``)."""
        self._stats = _Stats()
        self._ended = None
        self._limit_failures = []
        client: httpx.Client | None = None
        try:
            try:
                self._validate()
                self._validated = True
                client = self._open_client()
                self._tmpdir = tempfile.mkdtemp(prefix="databoar-objstore-")
                _restrict_temp_dir(self._tmpdir)
                self._scan(client)
            except _Stop as stop:
                self._ended = stop.reason
                self._failure(stop.reason, stop.message)
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # unexpected: fixed message, class name only
                self._ended = "error"
                self._failure(
                    "error",
                    "unexpected error in object_storage connector "
                    f"({type(exc).__name__})",
                )
            self._write_summaries()
        finally:
            if client is not None:
                client.close()
            if self._tmpdir is not None:
                shutil.rmtree(self._tmpdir, ignore_errors=True)
                self._tmpdir = None
            if self._creds is not None:
                self._creds.clear()
            self._creds = None
            self._write_inventory()
            self._log_summary()

    # ------------------------------------------------------------ validation

    def _validate(self) -> None:
        cfg = self.config
        raw_driver = cfg.get("driver")
        try:
            driver = get_driver(raw_driver if isinstance(raw_driver, str) else "")
        except KeyError as missing:
            # The registry raises a fixed message (section 0): never the configured value.
            raise _Stop("config_error", missing.args[0]) from None
        self._driver = driver
        self._driver_name = str(raw_driver)

        if "headers" in cfg:
            raise _Stop(
                "config_error", "custom headers are not accepted for object_storage"
            )
        for key in ("verify_ssl", "verify"):
            if key in cfg and not cfg[key]:
                raise _Stop(
                    "config_error",
                    "TLS verification cannot be disabled for object_storage",
                )
        for key, hint in driver.misnamed_keys.items():
            if key in cfg:
                raise _Stop(
                    "config_error",
                    f"{key} is not accepted by driver {driver.name}; {hint}",
                )
        self._check_inline_credentials(cfg, driver)
        for key in getattr(driver, "required_keys", ()):
            if cfg.get(key) is None or cfg.get(key) == "":
                raise _Stop("config_error", f"missing required key: {key}")
        self._prefix = self._validate_prefix(cfg.get("prefix", ""))
        self._limits = self._parse_limits(cfg)
        self._timeouts = self._parse_timeouts(cfg)
        names = cfg.get("report_object_names", False)
        if not isinstance(names, bool):
            raise _Stop("config_error", "report_object_names must be true or false")
        self._report_names = names
        try:
            settings = driver.settings(cfg)
        except DriverConfigError as bad:
            # Driver contract: a DriverConfigError carries a fixed message of the driver.
            raise _Stop("config_error", self._fixed_driver_text(bad)) from None
        if not isinstance(settings, DriverSettings):
            raise _Stop("config_error", "driver returned invalid settings")
        self._settings = settings
        self._creds = self._read_credentials(cfg, driver)

    @staticmethod
    def _fixed_driver_text(exc: DriverConfigError) -> str:
        first = exc.args[0] if exc.args else ""
        if not isinstance(first, str) or not first:
            return "invalid configuration for the driver"
        return _printable(first, 200)

    @staticmethod
    def _check_inline_credentials(cfg: dict[str, Any], driver: StorageDriver) -> None:
        """Defence in depth for a connector built without the loader (section 3)."""
        declared = {name for name, _req in driver.credential_keys}
        forbidden = set(COMMON_FORBIDDEN_INLINE_KEYS) | set(
            driver.forbidden_inline_keys
        )
        for key in sorted(forbidden):
            if key in cfg:
                raise _Stop(
                    "config_error",
                    f"{key} is not accepted; use auth.<name>_from_env (#2306)",
                )
        auth = cfg.get("auth")
        if isinstance(auth, dict):
            for key in sorted(forbidden - declared):
                if key in auth:
                    raise _Stop(
                        "config_error",
                        f"auth.{key} is not accepted; use auth.<name>_from_env (#2306)",
                    )

    @staticmethod
    def _validate_prefix(raw: Any) -> str:
        if raw is None:
            return ""
        if not isinstance(raw, str):
            raise _Stop("config_error", "prefix must be a string")
        if len(raw.encode("utf-8", errors="surrogatepass")) > _PREFIX_MAX_BYTES:
            raise _Stop("config_error", "prefix is longer than 1024 bytes")
        if raw.startswith("/"):
            raise _Stop("config_error", "prefix must not start with '/'")
        if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in raw):
            raise _Stop("config_error", "prefix has control characters")
        if any(seg in (".", "..") for seg in raw.split("/")):
            raise _Stop("config_error", "prefix has a '.' or '..' segment")
        return raw

    @staticmethod
    def _parse_limits(cfg: dict[str, Any]) -> _Limits:
        values: dict[str, int | None] = {}
        disabled: list[str] = []
        for key, (default, maximum) in _LIMITS.items():
            if key not in cfg:
                values[key] = default
                continue
            value = cfg[key]
            if value == _UNLIMITED and isinstance(value, str):
                values[key] = None
                disabled.append(key)
            elif _readable_int(value) and 1 <= value <= maximum:
                values[key] = value
            else:
                raise _Stop(
                    "config_error",
                    f'{key} must be an integer from 1 to {maximum} or "{_UNLIMITED}"',
                )
        return _Limits(
            values["max_objects"],
            values["max_download_bytes"],
            values["max_object_bytes"],
            sorted(disabled),
        )

    @staticmethod
    def _parse_timeouts(cfg: dict[str, Any]) -> tuple[float, float]:
        out: list[float] = []
        for key, default in zip(
            ("connect_timeout_seconds", "read_timeout_seconds"), _TIMEOUT_DEFAULTS
        ):
            value = cfg.get(key, cfg.get("timeout", default))
            ok = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and _TIMEOUT_RANGE[0] <= value <= _TIMEOUT_RANGE[1]
            )
            if not ok:
                raise _Stop("config_error", "timeout must be between 1 and 300 seconds")
            out.append(value)
        return out[0], out[1]

    def _read_credentials(
        self, cfg: dict[str, Any], driver: StorageDriver
    ) -> ResolvedCredentials:
        """Read the values of the names the driver declares (section 3, #1977)."""
        from config.loader import assert_credential_env_name

        raw_auth = cfg.get("auth")
        auth: dict[str, Any] = raw_auth if isinstance(raw_auth, dict) else {}
        values: dict[str, str] = {}
        try:
            for key, required in driver.credential_keys:
                label = f"auth.{key}"
                env_name = auth.get(key)
                if env_name is None:
                    if required:
                        raise _Stop("config_error", f"{label} is required")
                    continue
                if not isinstance(env_name, str) or not env_name.strip():
                    raise _Stop("config_error", f"{label} must name a variable")
                try:
                    assert_credential_env_name(env_name, label)
                except ValueError:
                    raise _Stop(
                        "config_error",
                        f"{label} must name a variable with an allowed prefix (#1977)",
                    ) from None
                value = (os.environ.get(env_name.strip()) or "").strip()
                if not value:
                    raise _Stop("config_error", f"credential from {label} is empty")
                if any(
                    ch.isspace() or ord(ch) < 0x21 or ord(ch) > 0x7E for ch in value
                ):
                    raise _Stop(
                        "config_error",
                        f"credential from {label} has invalid characters",
                    )
                values[key] = value
            return ResolvedCredentials(values)
        finally:
            values.clear()

    # --------------------------------------------------------------- network

    def _open_client(self) -> httpx.Client:
        driver, settings = self._require()
        url = driver.destination(settings)
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or not parts.hostname:
            raise _Stop("config_error", "the driver destination must be an https URL")
        self._host = parts.hostname.lower()
        honors = bool(getattr(driver, "honors_allow_private_networks", False))
        allow_private = honors and url_guard.target_allows_private(self.config)
        err, ips = url_guard.resolve_and_validate_outbound_url(
            url, allow_private=allow_private, label="object_storage endpoint"
        )
        if err is not None or not ips:
            # The guard text names the host and the IP: never recorded (section 6).
            text = err or ""
            if "DNS resolution failed" in text or "resolved to no addresses" in text:
                raise _Stop("unreachable", "the destination host could not be resolved")
            raise _Stop(
                "scope_violation",
                "the destination host was refused by the outbound guard",
            )
        connect, read = self._timeouts
        timeout = httpx.Timeout(connect=connect, read=read, write=read, pool=connect)
        headers = {"User-Agent": get_http_user_agent()}
        if self._transport is not None:
            return httpx.Client(
                transport=self._transport,
                follow_redirects=False,
                timeout=timeout,
                headers=headers,
            )
        return url_guard.build_pinned_httpx_client(
            host_to_ips=url_guard.host_pins_from_url(url, ips),
            follow_redirects=False,
            timeout=timeout,
            headers=headers,
        )

    def _require(self) -> tuple[StorageDriver, DriverSettings]:
        if self._driver is None or self._settings is None:
            raise _Stop("error", "object_storage connector used before validation")
        return self._driver, self._settings

    def _creds_now(self) -> ResolvedCredentials:
        if self._creds is None:
            raise _Stop("error", "object_storage credentials are not loaded")
        return self._creds

    def _check_prepared(self, prepared: PreparedGet) -> None:
        parts = urllib.parse.urlsplit(prepared.url)
        if parts.scheme != "https" or (parts.hostname or "").lower() != self._host:
            raise _Stop("scope_violation", "a driver request left the destination host")

    def _observe(self, response: httpx.Response) -> None:
        self._responses += 1
        if self._server_header is None:
            server = response.headers.get("server")
            if server is not None:
                self._server_header = _printable(server, _SERVER_HEADER_MAX)

    def _send(
        self,
        client: httpx.Client,
        prepare: Callable[[datetime], PreparedGet],
        during: str,
    ) -> tuple[httpx.Response | None, ErrorClass | None, str | None]:
        """GET with the section 6 retry policy.

        Returns ``(response, None, None)`` on 200 (a streaming response the caller closes),
        ``(None, error_class, None)`` for an HTTP error (``retryable`` true when the
        retries ran out), or ``(None, None, exception_class_name)`` when the network
        retries ran out.
        """
        driver, _settings = self._require()
        attempt = 0
        while True:
            prepared = prepare(self._now())
            self._check_prepared(prepared)
            request = client.build_request(
                "GET", prepared.url, headers=prepared.headers
            )
            try:
                response = client.send(request, stream=True)
            except httpx.TransportError as net:
                if attempt >= len(_BACKOFF):
                    return None, None, type(net).__name__
                self._sleep(_BACKOFF[attempt])
                attempt += 1
                continue
            self._observe(response)
            if response.status_code == 200:
                return response, None, None
            try:
                body = self._read_capped(response, _ERROR_BODY_MAX_BYTES, strict=False)
            finally:
                response.close()
            ec = driver.classify_error(
                response.status_code,
                response.headers,
                body,
                during="list" if during == "list" else "get",
            )
            if ec.retryable and attempt < len(_BACKOFF):
                wait = _retry_after(response.headers)
                self._sleep(_BACKOFF[attempt] if wait is None else wait)
                attempt += 1
                continue
            return None, ec, None

    @staticmethod
    def _read_capped(response: httpx.Response, cap: int, *, strict: bool) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_bytes():
            size += len(chunk)
            if size > cap:
                if strict:
                    raise _Stop("protocol_error", "listing response too large")
                chunks.append(chunk[: cap - (size - len(chunk))])
                break
            chunks.append(chunk)
        return b"".join(chunks)

    # --------------------------------------------------------------- listing

    def _scan(self, client: httpx.Client) -> None:
        driver, settings = self._require()
        limits = self._limits
        assert limits is not None
        self._budget_left = limits.max_download_bytes
        left = limits.max_objects
        token: str | None = None
        seen_tokens: set[str] = set()
        consecutive = [0]
        while True:
            page_size = (
                driver.max_page_size
                if left is None
                else min(driver.max_page_size, left)
            )
            page = self._list_page(client, token, page_size)
            if page is None:  # the listing ended with a recorded failure
                return
            entries = list(page.entries)
            dropped = left is not None and len(entries) > left
            if left is not None:
                entries = entries[:left]
                left -= len(entries)
            self._stats.listed += len(entries)
            self._process(client, entries, consecutive)
            if dropped or (page.truncated and left == 0):
                self._limit_failures.append(
                    f"max_objects reached ({limits.max_objects}); listing stopped "
                    "before the end of the prefix"
                )
                return
            if not page.truncated:
                self._stats.listing_complete = True
                return
            nxt = page.next_token
            if not nxt or nxt in seen_tokens or nxt == token:
                self._failure("protocol_error", "listing pagination loop")
                return
            seen_tokens.add(nxt)
            token = nxt

    def _list_page(
        self, client: httpx.Client, token: str | None, page_size: int
    ) -> ListPage | None:
        driver, settings = self._require()
        creds = self._creds_now()
        response, ec, net = self._send(
            client,
            lambda now: driver.list_request(
                settings, creds, self._prefix, token, page_size, now
            ),
            "list",
        )
        if net is not None:
            raise _Stop("unreachable", f"listing failed after retries ({net})")
        if ec is not None:
            if ec.ends_target:
                raise _Stop(ec.reason, ec.message)
            self._failure(ec.reason, ec.message)
            return None
        assert response is not None
        try:
            try:
                body = self._read_capped(response, _LISTING_MAX_BYTES, strict=True)
            except _Stop as big:
                self._failure(big.reason, big.message)
                return None
        finally:
            response.close()
        try:
            return driver.parse_list(body)
        except DriverProtocolError:
            self._failure("protocol_error", "malformed listing response")
            return None

    def _classify(self, entry: ObjectEntry) -> str | None:
        """Section 7 table; ``None`` means accepted for download."""
        key = entry.key
        if key is None:
            return "invalid_key"
        if not key.startswith(self._prefix):
            return "out_of_prefix"
        driver, _settings = self._require()
        try:
            key_bytes = len(key.encode("utf-8"))
        except UnicodeEncodeError:
            return "invalid_key"
        if key_bytes > driver.max_key_bytes:
            return "invalid_key"
        if key.endswith("/"):
            return "folder_marker"
        if any(seg in (".", "..") for seg in key.split("/")):
            return "unsafe_key"
        ext = _key_ext(key)
        if ext not in self.extensions and not (
            self.scan_compressed and ext in self.compressed_extensions
        ):
            return "extension"
        limits = self._limits
        assert limits is not None
        if (
            entry.size is not None
            and limits.max_object_bytes is not None
            and entry.size > limits.max_object_bytes
        ):
            return "too_large"
        return None

    def _process(
        self, client: httpx.Client, entries: list[ObjectEntry], consecutive: list[int]
    ) -> None:
        for index, entry in enumerate(entries):
            reason = self._classify(entry)
            if reason == "folder_marker":
                self._stats.folder_marker += 1
                continue
            if reason == "extension":
                self._stats.extension += 1
                continue
            if reason is not None:
                self._not_scanned(entry, reason, _OBJECT_MESSAGES.get(reason))
                continue
            assert entry.key is not None
            if (
                entry.size is not None
                and self._budget_left is not None
                and entry.size > self._budget_left
            ):
                self._not_scanned(entry, "over_budget", None)
                continue
            try:
                exhausted = self._download_and_scan(client, entry)
            except _Stop:
                self._count_untried(entries[index + 1 :])
                raise
            if exhausted:
                consecutive[0] += 1
                if consecutive[0] >= _MAX_CONSECUTIVE_EXHAUSTED:
                    self._count_untried(entries[index + 1 :])
                    raise _Stop("unreachable", "endpoint stopped responding")
            else:
                consecutive[0] = 0

    def _count_untried(self, rest: list[ObjectEntry]) -> None:
        """The target ends mid-page: the remaining entries keep their own reason, and the
        accepted ones (never tried) count as download_failed, so the R6-6 invariant holds."""
        for entry in rest:
            reason = self._classify(entry)
            if reason == "folder_marker":
                self._stats.folder_marker += 1
            elif reason == "extension":
                self._stats.extension += 1
            else:
                self._not_scanned(entry, reason or "download_failed", None)

    # -------------------------------------------------------------- download

    def _download_and_scan(self, client: httpx.Client, entry: ObjectEntry) -> bool:
        """Download one accepted object and run the file pipeline on it.

        Returns True when the retries ran out (for the "three in a row" rule).
        """
        driver, settings = self._require()
        creds = self._creds_now()
        key = entry.key
        assert key is not None
        response, ec, net = self._send(
            client, lambda now: driver.get_request(settings, creds, key, now), "get"
        )
        if net is not None:
            self._not_scanned(
                entry, "download_failed", f"download failed after retries ({net})"
            )
            return True
        if ec is not None:
            if ec.ends_target and ec.reason != "download_failed":
                raise _Stop(ec.reason, ec.message)
            reason = (
                ec.reason if ec.reason in _NOT_SCANNED_REASONS else "download_failed"
            )
            self._not_scanned(entry, reason, ec.message)
            return ec.retryable
        assert response is not None
        self._obj_counter += 1
        assert self._tmpdir is not None
        ext = _key_ext(key)
        local = os.path.join(self._tmpdir, f"obj-{self._obj_counter}{ext}")
        try:
            try:
                self._stream_to_file(response, entry, local)
            finally:
                response.close()
            self._stats.bytes_downloaded += os.path.getsize(local)
            self._extract(local, key, ext)
            self._stats.scanned += 1
        except _ObjectFailed as failed:
            self._not_scanned(entry, failed.reason, failed.message)
        finally:
            try:
                os.remove(local)
            except FileNotFoundError:
                pass
        return False

    def _ceiling(self, entry: ObjectEntry) -> int | None:
        limits = self._limits
        assert limits is not None
        caps = [
            c
            for c in (entry.size, limits.max_object_bytes, self._budget_left)
            if c is not None
        ]
        return min(caps) if caps else None

    def _overflow(self, entry: ObjectEntry, amount: int) -> _ObjectFailed:
        """The reason for passing the ceiling (R6-2: no size_mismatch without a size)."""
        limits = self._limits
        assert limits is not None
        if entry.size is not None:
            return _ObjectFailed("size_mismatch", _OBJECT_MESSAGES["size_mismatch"])
        if limits.max_object_bytes is not None and amount > limits.max_object_bytes:
            return _ObjectFailed("too_large", _OBJECT_MESSAGES["too_large"])
        return _ObjectFailed("over_budget", "max_download_bytes balance exhausted")

    def _stream_to_file(
        self, response: httpx.Response, entry: ObjectEntry, local: str
    ) -> None:
        ceiling = self._ceiling(entry)
        declared = response.headers.get("content-length")
        if declared is not None and declared.strip().isdigit():
            length = int(declared.strip())
            if ceiling is not None and length > ceiling:
                raise self._overflow(entry, length)
        read = 0
        fd = os.open(local, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as out:
                for chunk in response.iter_bytes():
                    read += len(chunk)
                    if self._budget_left is not None:
                        self._budget_left = max(0, self._budget_left - len(chunk))
                    if ceiling is not None and read > ceiling:
                        raise self._overflow(entry, read)
                    out.write(chunk)
        except OSError:
            raise _ObjectFailed(
                "download_failed", "object could not be written to disk"
            ) from None
        except httpx.TransportError as net:
            raise _ObjectFailed(
                "download_failed", f"download interrupted ({type(net).__name__})"
            ) from None
        if entry.size is not None and read != entry.size:
            raise _ObjectFailed("size_mismatch", _OBJECT_MESSAGES["size_mismatch"])

    # ------------------------------------------------------------ extraction

    def _display(self, key: str) -> str:
        driver, settings = self._require()
        return _printable(driver.display_path(settings, key))

    def _extract(self, temp_path: str, key: str, ext: str) -> None:
        """Same extraction and detection as the file connectors (section 9)."""
        from utils.audit_log_display import audit_log_target_label

        display = self._display(key)
        file_name = _printable(key.rsplit("/", 1)[-1])
        if (
            self.scan_compressed
            and ext in self.compressed_extensions
            and is_supported_archive(Path(temp_path), exts=self.compressed_extensions)
        ):
            scan_archive_at_path(
                archive_path=Path(temp_path),
                archive_display_name=file_name,
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
                    self.config, default="object storage"
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
        res = self.scanner.scan_file_content(text, Path(file_name))
        if res is not None:
            self.db_manager.save_finding(
                "filesystem",
                target_name=self._name,
                path=display,
                file_name=file_name,
                data_type=ext.replace(".", "").upper(),
                sensitivity_level=res["sensitivity_level"],
                pattern_detected=res["pattern_detected"],
                norm_tag=res.get("norm_tag", ""),
                ml_confidence=res.get("ml_confidence", 0),
            )

    # --------------------------------------------------------------- outputs

    def _failure(self, reason: str, detail: str) -> None:
        if self.db_manager is not None:
            self.db_manager.save_failure(self._name, reason, detail)

    def _not_scanned(
        self, entry: ObjectEntry, reason: str, message: str | None
    ) -> None:
        stats = self._stats
        stats.not_scanned[reason] += 1
        if entry.size is None:
            stats.unknown_size += 1
        elif reason in _SIZED_REASONS:
            stats.bytes_not_scanned += entry.size
        # DEC-11: per-object failures only with report_object_names, never out_of_prefix
        # nor invalid_key (no readable or authorised name), at most 100 per reason.
        if (
            self._report_names
            and message is not None
            and entry.key is not None
            and reason not in ("out_of_prefix", "invalid_key", "over_budget")
        ):
            done = stats.per_object.get(reason, 0)
            if done < _MAX_FAILURES_PER_REASON:
                stats.per_object[reason] = done + 1
                display = _printable(self._display(entry.key), _DISPLAY_MAX)
                self._failure(reason, f"{display}: {message}")

    def _write_summaries(self) -> None:
        stats = self._stats
        for text in self._limit_failures:
            self._failure("limit_reached", text)
        over = stats.not_scanned["over_budget"]
        if over:
            self._failure(
                "limit_reached",
                f"max_download_bytes reached; {over} objects not downloaded",
            )
        skipped = {r: stats.not_scanned[r] for r in _SKIPPED_SUMMARY}
        total = sum(skipped.values())
        if total:
            parts = ", ".join(f"{r}={n}" for r, n in skipped.items())
            self._failure("skipped", f"{total} objects skipped: {parts}")

    def _coverage(self) -> dict[str, Any]:
        stats = self._stats
        not_scanned = sum(stats.not_scanned.values())
        complete = not_scanned == 0 and stats.listing_complete and self._ended is None
        return {
            "coverage": "complete" if complete else "partial",
            "listing_complete": stats.listing_complete,
            "objects_listed": stats.listed,
            "objects_scanned": stats.scanned,
            "objects_not_scanned": not_scanned,
            "bytes_not_scanned": stats.bytes_not_scanned,
            "objects_unknown_size": stats.unknown_size,
            "not_scanned_by_reason": {
                r: n for r, n in sorted(stats.not_scanned.items()) if n
            },
            "limits_disabled": list(self._limits.disabled) if self._limits else [],
        }

    def _write_inventory(self) -> None:
        import json

        if self.db_manager is None or not hasattr(
            self.db_manager, "save_data_source_inventory"
        ):
            return
        engine = self._driver_name if self._driver is not None else "unknown"
        product: str | None = None
        protocol: str | None = None
        technical: dict[str, Any] = {}
        if not self._validated or self._settings is None or self._driver is None:
            # Section 10 and R6-3: nothing from the (invalid) config; zeroed coverage.
            executive: dict[str, Any] = {
                "engine": engine,
                "status": f"failed:{self._ended or 'config_error'}",
                "coverage": "partial",
                "listing_complete": False,
                "objects_listed": 0,
                "objects_scanned": 0,
                "objects_not_scanned": 0,
                "bytes_not_scanned": 0,
                "objects_unknown_size": 0,
                "not_scanned_by_reason": {},
                "limits_disabled": [],
            }
            transport = "unknown"
        else:
            identity = dict(self._driver.inventory_identity(self._settings))
            product = identity.pop("product", None)
            protocol = identity.pop("protocol_or_api_version", None)
            if self._ended is not None:
                status = f"failed:{self._ended}"
            elif self._limit_failures or self._stats.not_scanned["over_budget"]:
                status = "limited"
            else:
                status = "completed"
            executive = {
                **identity,
                "engine": engine,  # R6-3: the registry name, over the driver's value
                "prefix": self._prefix,
                "objects_downloaded": self._stats.scanned,
                "bytes_downloaded": self._stats.bytes_downloaded,
                "status": status,
                **self._coverage(),
            }
            transport = "tls=https" if self._responses else "unknown"
            if self._server_header is not None:
                technical["server_header"] = self._server_header
        raw: dict[str, Any] = {"executive": executive}
        if technical:
            raw["technical"] = technical
        try:
            self.db_manager.save_data_source_inventory(
                self._name,
                SOURCE_TYPE,
                product,
                None,
                protocol,
                transport,
                json.dumps(raw, sort_keys=True),
            )
        except KeyboardInterrupt:
            raise
        except Exception:
            self._failure("error", "inventory snapshot not saved")

    def _log_summary(self) -> None:
        """One INFO line with counts only (section 12): no object key, no URL."""
        try:
            from utils.audit_log_display import audit_log_target_label
            from utils.logger import get_logger

            stats = self._stats
            get_logger().info(
                "object_storage %s: listed=%d scanned=%d bytes=%d not_scanned %s",
                audit_log_target_label(self.config, default="object storage"),
                stats.listed,
                stats.scanned,
                stats.bytes_downloaded,
                " ".join(f"{r}={n}" for r, n in sorted(stats.not_scanned.items())),
            )
        except KeyboardInterrupt:
            raise
        except Exception:
            return


register("object_storage", ObjectStorageConnector, REQUIRED_KEYS)
