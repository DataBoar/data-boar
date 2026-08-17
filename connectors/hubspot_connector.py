"""
HubSpot CRM connector (#1229): discover object properties (including custom fields),
sample CRM objects, and run sensitivity detection.

Auth: Private App Token (PAT) via environment variable — never commit tokens.
Default env name: ``HUBSPOT_PRIVATE_APP_TOKEN``. Header: ``Authorization: Bearer <token>``.

Least-privilege scopes (read-only) for the Private App:
  - crm.objects.contacts.read
  - crm.objects.companies.read
  - crm.objects.deals.read
  - crm.schemas.contacts.read (properties discovery)
  - crm.schemas.companies.read
  - crm.schemas.deals.read

Outbound HTTP uses ``connectors.url_guard`` host pinning (#1552) — same posture as
``rest_connector`` / Power BI. Never use raw httpx/requests without the guard.

Target type: ``hubspot``. Required config keys: ``name``, ``type``.
Optional: ``objects`` (default contacts/companies/deals), ``base_url``,
``token_from_env``, ``allow_private_networks``.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any
from urllib.parse import urlencode

from core.about import get_http_user_agent
from core.connector_registry import register
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)

from .url_guard import (
    build_pinned_httpx_client,
    merge_host_pins,
    resolve_and_validate_outbound_url,
    target_allows_private,
)

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    httpx = None

_DEFAULT_API_BASE = "https://api.hubapi.com"
_DEFAULT_OBJECTS = ("contacts", "companies", "deals")
_DEFAULT_TOKEN_ENV = "HUBSPOT_PRIVATE_APP_TOKEN"
_MAX_429_RETRIES = 5


def _token_from_config(target: dict[str, Any]) -> str | None:
    """Resolve Private App Token from env (never from committed config values)."""
    auth = target.get("auth") or {}
    env_name = (
        auth.get("token_from_env") or target.get("token_from_env") or _DEFAULT_TOKEN_ENV
    )
    token = os.environ.get(str(env_name), "").strip()
    return token or None


class HubSpotConnector:
    """
    HubSpot CRM scanner: property schema discovery + object sampling.

    Two-step flow per object type (contacts / companies / deals by default):
      1. GET /crm/v3/properties/{objectType} — all property names (incl. custom).
      2. GET /crm/v3/objects/{objectType}?properties=... — paginate via ``after``.

    Each property is treated as a column: ``scan_column`` → application finding
    (``save_finding("application", …)``) with ``path=object_type`` and ``file_name=prop_name``.
    Excel sheet: **Application findings** (not Filesystem findings — #1613).
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
        self.sample_limit = min(max(int(sample_limit), 1), 100)
        self.detection_config = detection_config or {}
        self._client: httpx.Client | None = None
        self._base_url = (self.config.get("base_url") or _DEFAULT_API_BASE).rstrip("/")

    def connect(self) -> None:
        if not _HTTPX_AVAILABLE:
            raise RuntimeError(
                "httpx is required for HubSpot connector. Install with: pip install httpx"
            )
        token = _token_from_config(self.config)
        if not token:
            raise ValueError(
                "HubSpot auth failed: set env "
                f"{self.config.get('token_from_env') or _DEFAULT_TOKEN_ENV} "
                "to a Private App Token (read-only CRM scopes). "
                "Never put the token in committed config."
            )
        allow_private = target_allows_private(self.config)
        err, ips = resolve_and_validate_outbound_url(
            self._base_url, allow_private=allow_private, label="base_url"
        )
        if err:
            raise ValueError(err)
        host_pins: dict[str, list[str]] = {}
        merge_host_pins(host_pins, self._base_url, ips)
        connect_s = float(self.config.get("connect_timeout_seconds", 25))
        read_s = float(self.config.get("read_timeout_seconds", 90))
        timeout = httpx.Timeout(read_s, connect=connect_s, read=read_s)
        client_kwargs: dict[str, Any] = {
            "base_url": self._base_url,
            "headers": {
                "User-Agent": get_http_user_agent(),
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            "timeout": timeout,
        }
        self._client = build_pinned_httpx_client(host_to_ips=host_pins, **client_kwargs)

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                # Best-effort close; always drop the handle.
                pass
            self._client = None

    def _object_types(self) -> list[str]:
        raw = self.config.get("objects") or self.config.get("object_types")
        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]
        if isinstance(raw, (list, tuple)) and raw:
            return [str(x).strip() for x in raw if str(x).strip()]
        return list(_DEFAULT_OBJECTS)

    def _get_json(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET with 429 backoff. Client must already be pin-built in connect()."""
        if not self._client:
            raise RuntimeError("HubSpot client not connected")
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url_path = path if path.startswith("/") else f"/{path}"
        last_exc: Exception | None = None
        for attempt in range(_MAX_429_RETRIES + 1):
            r = self._client.get(f"{url_path}{query}")
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                try:
                    wait_s = float(retry_after) if retry_after else (2**attempt)
                except ValueError:
                    wait_s = float(2**attempt)
                wait_s = min(max(wait_s, 0.5), 60.0)
                time.sleep(wait_s)
                last_exc = httpx.HTTPStatusError(
                    f"HubSpot rate limit (429) after {attempt + 1} attempts",
                    request=r.request,
                    response=r,
                )
                continue
            r.raise_for_status()
            return r.json() if r.content else {}
        assert last_exc is not None
        raise last_exc

    def _list_property_names(self, object_type: str) -> list[str]:
        """Step 1: discover all property names including custom fields (#1166 gap)."""
        data = self._get_json(f"/crm/v3/properties/{object_type}")
        results = data.get("results") or []
        names: list[str] = []
        seen: set[str] = set()
        for item in results:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if isinstance(name, str) and name and name not in seen:
                seen.add(name)
                names.append(name)
        return names

    def _iter_object_properties(
        self, object_type: str, property_names: list[str]
    ) -> list[dict[str, Any]]:
        """Step 2: paginate objects; return list of property dicts per object."""
        if not property_names:
            return []
        # HubSpot accepts comma-separated property names; keep batches reasonable.
        props_param = ",".join(property_names)
        collected: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            params: dict[str, Any] = {
                "limit": 100,
                "properties": props_param,
            }
            if after:
                params["after"] = after
            data = self._get_json(f"/crm/v3/objects/{object_type}", params=params)
            for row in data.get("results") or []:
                if isinstance(row, dict):
                    props = row.get("properties") or {}
                    if isinstance(props, dict):
                        collected.append(props)
            paging = data.get("paging") or {}
            next_page = paging.get("next") if isinstance(paging, dict) else None
            after = None
            if isinstance(next_page, dict):
                after = next_page.get("after")
            if not after:
                break
        return collected

    def _scan_object_type(self, target_name: str, object_type: str) -> None:
        prop_names = self._list_property_names(object_type)
        if not prop_names:
            return
        rows = self._iter_object_properties(object_type, prop_names)
        samples: dict[str, list[str]] = defaultdict(list)
        for props in rows:
            for name in prop_names:
                if len(samples[name]) >= self.sample_limit:
                    continue
                raw = props.get(name)
                if raw is None or raw == "":
                    continue
                samples[name].append(str(raw)[:500])

        for prop_name in prop_names:
            values = samples.get(prop_name) or []
            # Always scan the property name itself (custom field names can hint PII).
            name_sample = prop_name
            value_sample = " ".join(values) if values else ""
            sample_text = f"{name_sample} {value_sample}".strip()
            result = self.scanner.scan_column(prop_name, sample_text)
            result = augment_low_id_like_for_persist(
                result, prop_name, self.detection_config
            )
            hi_med = result.get("sensitivity_level") in ("HIGH", "MEDIUM")
            suggested = result.get("pattern_detected") == SUGGESTED_REVIEW_PATTERN
            if not hi_med and not suggested:
                continue
            self.db_manager.save_finding(
                "application",
                target_name=target_name,
                path=object_type,
                file_name=prop_name,
                data_type="application/json",
                sensitivity_level=result.get("sensitivity_level", "MEDIUM"),
                pattern_detected=result.get("pattern_detected", ""),
                norm_tag=result.get("norm_tag", ""),
                ml_confidence=result.get("ml_confidence") or 0,
            )

    def run(self) -> None:
        target_name = self.config.get("name", "HubSpot")
        if not _HTTPX_AVAILABLE:
            self.db_manager.save_failure(
                target_name,
                "error",
                "httpx not installed. Install with: pip install httpx",
            )
            return
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            for object_type in self._object_types():
                try:
                    self._scan_object_type(target_name, object_type)
                except Exception as e:
                    self.db_manager.save_failure(
                        target_name,
                        "error",
                        f"HubSpot {object_type}: {e}",
                    )
        finally:
            self.close()


if _HTTPX_AVAILABLE:
    register("hubspot", HubSpotConnector, ["name", "type"])
