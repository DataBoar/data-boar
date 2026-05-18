"""
Dataverse (Power Apps) connector: discover entities and attributes via Dataverse Web API,
sample rows, run sensitivity detection. Uses Azure AD OAuth2 (client credentials).
Target type: dataverse or powerapps. Required: name, org_url (or environment_url),
tenant_id, client_id, client_secret (or auth block).
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

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    httpx = None

_HTTPS_PREFIX = "https://"


def _dataverse_token(target: dict[str, Any]) -> str | None:
    """Obtain Dataverse access token via Azure AD client credentials. Scope = org .default."""
    auth = target.get("auth") or {}
    tenant_id = auth.get("tenant_id") or target.get("tenant_id", "")
    client_id = auth.get("client_id") or target.get("client_id", "")
    client_secret = auth.get("client_secret") or target.get("client_secret", "")
    if (
        isinstance(client_secret, str)
        and client_secret.startswith("${")
        and client_secret.endswith("}")
    ):
        client_secret = os.environ.get(client_secret[2:-1], "")
    org_url = (
        auth.get("org_url")
        or target.get("org_url")
        or target.get("environment_url")
        or ""
    ).rstrip("/")
    if not org_url:
        return None
    if org_url.startswith(_HTTPS_PREFIX):
        resource = org_url.replace(_HTTPS_PREFIX, "").split("/")[0]
    else:
        resource = org_url
    scope = (
        f"{_HTTPS_PREFIX}{resource}/.default"
        if not resource.startswith("http")
        else f"{org_url}/.default"
    )
    if not tenant_id or not client_id or not client_secret:
        return None
    token_url = (
        auth.get("token_url")
        or f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    )
    resp = httpx.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
        headers={
            "Accept": "application/json",
            "User-Agent": get_http_user_agent(),
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("access_token")


def _api_base(org_url: str) -> str:
    """Derive Web API base from org URL (e.g. https://org.crm.dynamics.com -> https://org.api.crm.dynamics.com/api/data/v9.2)."""
    url = org_url.rstrip("/")
    if not url.startswith(_HTTPS_PREFIX):
        url = _HTTPS_PREFIX + url
    host = url.replace(_HTTPS_PREFIX, "").split("/")[0]
    if ".api." in host:
        return f"{_HTTPS_PREFIX}{host}/api/data/v9.2"
    org = host.split(".")[0]
    return f"{_HTTPS_PREFIX}{org}.api.crm.dynamics.com/api/data/v9.2"


class DataverseConnector:
    """
    Connect to Microsoft Dataverse (Power Apps) Web API, list entities, sample rows,
    run sensitivity detection on column names and values. Findings saved as database
    findings (schema = logical name, table = entity set, column = attribute).
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
        self._client: "httpx.Client | None" = None
        self._token: str | None = None

    def connect(self) -> None:
        if not _HTTPX_AVAILABLE:
            raise RuntimeError(
                "httpx is required for Dataverse connector. Install with: pip install httpx"
            )
        org_url = self.config.get("org_url") or self.config.get("environment_url", "")
        if not org_url:
            raise ValueError("Dataverse requires org_url (or environment_url)")
        self._token = _dataverse_token(self.config)
        if not self._token:
            raise ValueError(
                "Dataverse auth failed: provide tenant_id, client_id, client_secret (or auth block)"
            )
        base = _api_base(org_url)
        connect_s = float(self.config.get("connect_timeout_seconds", 25))
        read_s = float(self.config.get("read_timeout_seconds", 90))
        timeout = httpx.Timeout(read_s, connect=connect_s, read=read_s)
        self._client = httpx.Client(
            base_url=base,
            headers={
                "User-Agent": get_http_user_agent(),
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception as close_err:
                # Best-effort close; connector teardown must stay non-fatal.
                _ = str(close_err)
            self._client = None
        self._token = None

    def _get_entity_definitions(self) -> list[dict]:
        """Return list of entity definitions (LogicalName, EntitySetName)."""
        r = self._client.get(
            "/EntityDefinitions",
            params={
                "$select": "LogicalName,EntitySetName",
                "$filter": "IsValidForAdvancedFind eq true",
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("value", [])

    def _get_attributes(self, logical_name: str) -> list[dict]:
        """Return attributes for an entity (SchemaName, AttributeType)."""
        r = self._client.get(
            f"/EntityDefinitions(LogicalName='{logical_name}')/Attributes",
            params={"$select": "LogicalName,SchemaName,AttributeType"},
        )
        r.raise_for_status()
        data = r.json()
        return data.get("value", [])

    def _sample_entity(self, entity_set: str) -> list[dict]:
        """Fetch top N rows from an entity set."""
        r = self._client.get(f"/{entity_set}", params={"$top": self.sample_limit})
        r.raise_for_status()
        data = r.json()
        return data.get("value", [])

    def run(self) -> None:
        target_name = self.config.get("name", "Dataverse")
        if not _HTTPX_AVAILABLE:
            self.db_manager.save_failure(target_name, "error", "httpx not installed")
            return
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            self._save_inventory_snapshot(target_name)
            entities = self._get_entity_definitions()
            for ent in entities:
                logical = ent.get("LogicalName", "")
                entity_set = ent.get("EntitySetName", "")
                if not logical or not entity_set:
                    continue
                attrs = self._get_attributes(logical)
                rows = self._sample_entity(entity_set)
                if not attrs and not rows:
                    continue
                columns_to_scan = []
                if attrs:
                    for a in attrs:
                        if a.get("AttributeType") in (
                            "String",
                            "Memo",
                            "Integer",
                            "DateTime",
                            "Double",
                            "Decimal",
                            "Lookup",
                            "Uniqueidentifier",
                        ):
                            columns_to_scan.append(
                                (
                                    a.get("LogicalName", a.get("SchemaName", "")),
                                    str(a.get("AttributeType", "")),
                                )
                            )
                if not columns_to_scan and rows:
                    for key in rows[0].keys():
                        if key.startswith("@"):
                            continue
                        columns_to_scan.append((key, ""))
                for col_name, col_type in columns_to_scan:
                    if not col_name:
                        continue
                    sample = ""
                    if rows:
                        for row in rows[: self.sample_limit]:
                            val = row.get(col_name)
                            if val is not None:
                                sample += str(val)[:200] + " "
                    res = self.scanner.scan_column(
                        col_name, sample, connector_data_type=col_type or None
                    )
                    res = augment_low_id_like_for_persist(
                        res, col_name, self.detection_config
                    )
                    if (
                        res.get("sensitivity_level") == "LOW"
                        and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
                    ):
                        continue
                    self.db_manager.save_finding(
                        source_type="database",
                        target_name=target_name,
                        server_ip=self.config.get("org_url", "").split("/")[0]
                        if self.config.get("org_url")
                        else "dataverse",
                        engine_details="Dataverse",
                        schema_name=logical,
                        table_name=entity_set,
                        column_name=col_name,
                        data_type=col_type,
                        sensitivity_level=res.get("sensitivity_level", "MEDIUM"),
                        pattern_detected=res.get("pattern_detected", ""),
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()

    def _save_inventory_snapshot(self, target_name: str) -> None:
        """Persist one Dataverse API inventory row."""
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        org_url = self.config.get("org_url") or self.config.get("environment_url") or ""
        base = _api_base(org_url) if org_url else ""
        details = {
            "org_url": org_url,
            "api_base": base,
            "tenant_id": str(
                (self.config.get("auth") or {}).get("tenant_id")
                or self.config.get("tenant_id")
                or ""
            ),
        }
        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="api",
                product="dataverse",
                product_version=None,
                protocol_or_api_version="v9.2",
                transport_security="tls=https",
                raw_details=json.dumps(details, ensure_ascii=False),
            )
        except Exception:
            # Inventory snapshot is best-effort; never break scan execution on persist errors.
            return


if _HTTPX_AVAILABLE:
    register(
        "dataverse",
        DataverseConnector,
        ["name", "org_url", "tenant_id", "client_id", "client_secret"],
    )
    register(
        "powerapps",
        DataverseConnector,
        ["name", "org_url", "tenant_id", "client_id", "client_secret"],
    )
