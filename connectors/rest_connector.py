"""
REST/API connector: call remote HTTP(S) endpoints with configurable authentication
(basic, bearer token, OAuth2 client credentials, or custom headers) to discover
and scan response payloads for personal or sensitive data.
Optional: register only when httpx is available. Used for type "api" or "rest" targets.
"""

import os
from typing import Any
import json

from core.about import get_http_user_agent
from core.connector_registry import register
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)

from .url_guard import target_allows_private, validate_outbound_url

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    httpx = None


def _build_auth(client: "httpx.Client", target: dict[str, Any]) -> None:
    """
    Configure auth on the client from target["auth"].
    Supports: basic (username/password), bearer (token), oauth2_client (token_url, client_id, client_secret),
    custom (headers with Authorization or other). Negotiated tokens (e.g. Kerberos) can be passed via custom.
    """
    auth = target.get("auth") or {}
    auth_type = (auth.get("type") or "none").lower()

    if auth_type == "basic":
        username = auth.get("username", auth.get("user", ""))
        password = auth.get("password", auth.get("pass", ""))
        if username or password:
            client.auth = httpx.BasicAuth(username, password)
        return

    if auth_type == "bearer":
        token = auth.get("token") or (
            os.environ.get(auth.get("token_from_env", ""))
            if auth.get("token_from_env")
            else None
        )
        if token:
            client.headers["Authorization"] = f"Bearer {token}"
        return

    if auth_type == "oauth2_client":
        token_url = auth.get("token_url")
        client_id = auth.get("client_id", "")
        client_secret = auth.get("client_secret", "")
        if (
            isinstance(client_secret, str)
            and client_secret.startswith("${")
            and client_secret.endswith("}")
        ):
            client_secret = os.environ.get(client_secret[2:-1], "")
        scope = auth.get("scope", "")
        if token_url and client_id and client_secret:
            # One-off request to token endpoint (no client auth)
            resp = httpx.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    **({"scope": scope} if scope else {}),
                },
                headers={
                    "Accept": "application/json",
                    "User-Agent": get_http_user_agent(),
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            access_token = data.get("access_token")
            if access_token:
                client.headers["Authorization"] = f"Bearer {access_token}"
        return

    if auth_type == "custom":
        for key, value in (auth.get("headers") or {}).items():
            if value is not None:
                client.headers[key] = str(value)
        return

    # Static username/password in target (no auth block): use as Basic
    user = target.get("user", target.get("username", ""))
    password = target.get("pass", target.get("password", ""))
    if user or password:
        client.auth = httpx.BasicAuth(user, password)


def _scalar_to_connector_data_type(value: Any, max_varchar: int = 4000) -> str | None:
    """
    Infer SQL-style declared type from JSON scalars for Plan §4 ``connector_format_id_hint``.

    Integers map to BIGINT; strings map to VARCHAR(n) capped by ``max_varchar`` (sample length).
    Booleans and floats are skipped (no stable schema hint).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return None
    if isinstance(value, str):
        n = min(len(value), max_varchar)
        return f"VARCHAR({max(n, 1)})"
    return None


def _flatten_sample(
    obj: Any, prefix: str = "", max_len: int = 500
) -> list[tuple[str, str, Any | None]]:
    """
    Recursively flatten JSON-like structure into (key_path, string_value, raw_scalar).

    ``raw_scalar`` is the leaf JSON value before string coercion when applicable (used with
    :func:`_scalar_to_connector_data_type`). Non-leaf paths use ``None``.
    """
    out: list[tuple[str, str, Any | None]] = []
    if obj is None:
        out.append((prefix or "value", "", None))
        return out
    if isinstance(obj, bool):
        out.append((prefix or "value", "true" if obj else "false", obj))
        return out
    if isinstance(obj, int):
        out.append((prefix or "value", str(obj)[:max_len], obj))
        return out
    if isinstance(obj, float):
        out.append((prefix or "value", str(obj)[:max_len], obj))
        return out
    if isinstance(obj, str):
        out.append((prefix or "value", obj[:max_len], obj))
        return out
    if isinstance(obj, list):
        for i, item in enumerate(obj[:3]):  # sample first 3
            out.extend(
                _flatten_sample(item, f"{prefix}[{i}]" if prefix else f"[{i}]", max_len)
            )
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and v:
                out.extend(_flatten_sample(v, key, max_len))
            else:
                if v is None:
                    out.append((key, "", None))
                elif isinstance(v, (dict, list)) and not v:
                    out.append((key, str(v)[:max_len], None))
                else:
                    out.append((key, str(v)[:max_len], v))
        return out
    out.append((prefix or "value", str(obj)[:max_len], None))
    return out


class RESTConnector:
    """
    Connect to REST/API endpoints with configurable auth (basic, bearer, OAuth2 client, custom headers),
    GET configured paths, parse JSON responses, and run sensitivity detection on field names and sample values.
    Findings are saved as filesystem_findings with file_name encoding path and field (e.g. "GET /users | email").
    """

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        sample_limit: int = 5,
        detection_config: dict[str, Any] | None = None,
    ):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.sample_limit = sample_limit
        self.detection_config = detection_config or {}
        self._client: "httpx.Client | None" = None

    def connect(self) -> None:
        if not _HTTPX_AVAILABLE:
            raise RuntimeError(
                "httpx is required for REST connector. Install with: pip install httpx"
            )
        base_url = (self.config.get("base_url") or self.config.get("url", "")).rstrip(
            "/"
        )
        # SSRF guard (#832): reject link-local/private/loopback hosts unless the
        # target config opts in with allow_private_networks: true.
        allow_private = target_allows_private(self.config)
        for candidate, label in (
            (base_url, "base_url"),
            (self.config.get("discover_url", ""), "discover_url"),
            ((self.config.get("auth") or {}).get("token_url", ""), "auth.token_url"),
        ):
            err = validate_outbound_url(
                candidate, allow_private=allow_private, label=label
            )
            if err:
                raise ValueError(err)
        connect_s = float(self.config.get("connect_timeout_seconds", 25))
        read_s = float(self.config.get("read_timeout_seconds", 90))
        # Default (first arg) used for write/pool; connect and read set explicitly (httpx requires default or all four).
        timeout = httpx.Timeout(read_s, connect=connect_s, read=read_s)
        cfg_headers = self.config.get("headers") or {}
        has_ua = any(str(k).lower() == "user-agent" for k in cfg_headers)
        default_headers: dict[str, str] = {}
        if not has_ua:
            default_headers["User-Agent"] = get_http_user_agent()
        self._client = httpx.Client(
            base_url=base_url, timeout=timeout, headers=default_headers or None
        )
        _build_auth(self._client, self.config)
        # Optional extra headers (e.g. API key, negotiated token); may override User-Agent.
        for key, value in cfg_headers.items():
            if value is not None:
                self._client.headers[str(key)] = str(value)

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                # Best-effort close: ignore client shutdown errors.
                return
            self._client = None

    def run(self) -> None:
        if not _HTTPX_AVAILABLE:
            self.db_manager.save_failure(
                self.config.get("name", "api"),
                "error",
                "httpx not installed. Install with: pip install httpx",
            )
            return
        try:
            self.connect()
        except ValueError as e:
            # SSRF guard rejection (#832) — record and stop, never request.
            self.db_manager.save_failure(
                self.config.get("name", "api"), "error", str(e)
            )
            return
        try:
            paths = self.config.get("paths") or self.config.get("endpoints") or []
            discover_url = self.config.get("discover_url")
            if discover_url and not paths:
                try:
                    r = self._client.get(discover_url)
                    r.raise_for_status()
                    data = r.json()
                    if isinstance(data, list):
                        paths = [
                            p if isinstance(p, str) else p.get("path", p.get("url", ""))
                            for p in data
                        ]
                    elif isinstance(data, dict) and "paths" in data:
                        paths = data["paths"]
                    elif isinstance(data, dict) and "endpoints" in data:
                        paths = data["endpoints"]
                except Exception as e:
                    self.db_manager.save_failure(
                        self.config.get("name", "api"), "error", f"Discover failed: {e}"
                    )
                    return
            if not paths:
                self.db_manager.save_failure(
                    self.config.get("name", "api"),
                    "error",
                    "No paths or discover_url configured",
                )
                return
            target_name = self.config.get("name", "API")
            self._save_inventory_snapshot(target_name)
            seen_path_key: set[tuple[str, str]] = (
                set()
            )  # (path_str, key) to avoid duplicate findings per field
            for path in paths:
                path_str = (
                    path
                    if isinstance(path, str)
                    else path.get("path", path.get("url", ""))
                )
                if not path_str:
                    continue
                path_str = path_str if path_str.startswith("/") else "/" + path_str
                try:
                    r = self._client.get(path_str)
                    r.raise_for_status()
                except Exception as e:
                    self.db_manager.save_failure(
                        target_name, "error", f"GET {path_str}: {e}"
                    )
                    continue
                try:
                    payload = r.json()
                except Exception:
                    payload = {"_raw": r.text[:2000]}

                def _save_if_sensitive(
                    key: str, sample: str, raw_scalar: Any | None = None
                ) -> None:
                    if (path_str, key) in seen_path_key:
                        return
                    ctype = _scalar_to_connector_data_type(raw_scalar)
                    result = self.scanner.scan_column(
                        key, sample, connector_data_type=ctype
                    )
                    result = augment_low_id_like_for_persist(
                        result, key, self.detection_config
                    )
                    hi_med = result.get("sensitivity_level") in ("HIGH", "MEDIUM")
                    suggested = (
                        result.get("pattern_detected") == SUGGESTED_REVIEW_PATTERN
                    )
                    if not hi_med and not suggested:
                        return
                    seen_path_key.add((path_str, key))
                    self.db_manager.save_finding(
                        "filesystem",
                        target_name=target_name,
                        path=self.config.get("base_url", "") + path_str,
                        file_name=f"GET {path_str} | {key}",
                        data_type="application/json",
                        sensitivity_level=result.get("sensitivity_level", "MEDIUM"),
                        pattern_detected=result.get("pattern_detected", ""),
                        norm_tag=result.get("norm_tag", ""),
                        ml_confidence=result.get("ml_confidence") or 0,
                    )

                if isinstance(payload, list):
                    for item in payload[: self.sample_limit]:
                        if isinstance(item, dict):
                            for key, sample, raw_scalar in _flatten_sample(
                                item, prefix="", max_len=500
                            ):
                                _save_if_sensitive(key, sample, raw_scalar)
                    if not payload:
                        for key, sample, raw_scalar in _flatten_sample(
                            {}, prefix="(empty)", max_len=500
                        ):
                            _save_if_sensitive(key, sample, raw_scalar)
                else:
                    for key, sample, raw_scalar in _flatten_sample(
                        payload, max_len=500
                    ):
                        _save_if_sensitive(key, sample, raw_scalar)
        finally:
            self.close()

    def _save_inventory_snapshot(self, target_name: str) -> None:
        """Persist one REST/API inventory row with API version hints."""
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        version_hint = (
            self.config.get("api_version")
            or self.config.get("version")
            or self._infer_api_version_from_paths()
        )
        transport = (
            "tls=https"
            if str(self.config.get("base_url", "")).lower().startswith("https://")
            else "unknown"
        )
        details = {
            "base_url": str(
                self.config.get("base_url") or self.config.get("url") or ""
            ),
            "auth_type": str((self.config.get("auth") or {}).get("type") or "none"),
        }
        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="api",
                product=self.config.get("product") or "rest-api",
                product_version=None,
                protocol_or_api_version=str(version_hint or "") or None,
                transport_security=transport,
                raw_details=json.dumps(details, ensure_ascii=False),
            )
        except Exception:
            # Inventory snapshot is best-effort; scan should continue without it.
            return

    def _infer_api_version_from_paths(self) -> str | None:
        paths = self.config.get("paths") or self.config.get("endpoints") or []
        for p in paths:
            path_str = p if isinstance(p, str) else p.get("path", p.get("url", ""))
            low = str(path_str).lower()
            for token in ("/v1", "/v2", "/v3", "/v4"):
                if token in low:
                    return token.strip("/")
        return None


if _HTTPX_AVAILABLE:
    register("api", RESTConnector, ["name", "base_url"])
    register("rest", RESTConnector, ["name", "base_url"])
