"""
Power BI connector: discover datasets and tables via Power BI REST API, sample with DAX,
run sensitivity detection on column names and sample values. Uses Azure AD OAuth2
(client credentials). Optional: register only when httpx is available.
Target type: powerbi. Required: name, tenant_id, client_id, client_secret (or auth block).
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

_PBI_BASE = "https://api.powerbi.com/v1.0"
_AZURE_TOKEN_URL_TMPL = (
    "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
)
_PBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"


def _get_access_token(target: dict[str, Any]) -> str | None:
    """Obtain Power BI access token via Azure AD client credentials."""
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
    if not tenant_id or not client_id or not client_secret:
        return None
    token_url = auth.get("token_url") or _AZURE_TOKEN_URL_TMPL.format(
        tenant_id=tenant_id
    )
    resp = httpx.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": _PBI_SCOPE,
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


class PowerBIConnector:
    """
    Connect to Power BI REST API (Azure AD OAuth2), list workspaces/datasets/tables,
    sample table data via Execute Queries (DAX), run sensitivity detection. Findings
    saved as database findings (schema = dataset name, table = table name, column = column).
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
                "httpx is required for Power BI connector. Install with: pip install httpx"
            )
        self._token = _get_access_token(self.config)
        if not self._token:
            raise ValueError(
                "Power BI auth failed: provide tenant_id, client_id, client_secret (or auth block)"
            )
        connect_s = float(self.config.get("connect_timeout_seconds", 25))
        read_s = float(self.config.get("read_timeout_seconds", 90))
        timeout = httpx.Timeout(read_s, connect=connect_s, read=read_s)
        self._client = httpx.Client(
            base_url=_PBI_BASE,
            headers={
                "User-Agent": get_http_user_agent(),
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                # Best-effort close; always drop the handle.
                pass
            self._client = None
        self._token = None

    def _get_workspace_ids(self) -> list[str]:
        """Return list of group (workspace) IDs; empty means use 'myorg' only."""
        workspace_ids = (
            self.config.get("workspace_ids") or self.config.get("group_ids") or []
        )
        if workspace_ids:
            return list(workspace_ids)
        r = self._client.get("/myorg/groups")
        r.raise_for_status()
        data = r.json()
        return [g["id"] for g in data.get("value", [])]

    def _get_datasets(self, group_id: str | None) -> list[dict]:
        if group_id:
            r = self._client.get(f"/myorg/groups/{group_id}/datasets")
        else:
            r = self._client.get("/myorg/datasets")
        r.raise_for_status()
        data = r.json()
        return data.get("value", [])

    def _get_tables(self, dataset_id: str, group_id: str | None) -> list[dict]:
        """Get tables for a dataset. Works for push datasets; others may return empty."""
        if group_id:
            r = self._client.get(
                f"/myorg/groups/{group_id}/datasets/{dataset_id}/tables"
            )
        else:
            r = self._client.get(f"/myorg/datasets/{dataset_id}/tables")
        r.raise_for_status()
        data = r.json()
        return data.get("value", [])

    def _execute_dax(
        self, dataset_id: str, group_id: str | None, dax_query: str
    ) -> list[dict]:
        """Execute a DAX query; returns list of rows (dicts). One table per query."""
        if group_id:
            url = f"/myorg/groups/{group_id}/datasets/{dataset_id}/executeQueries"
        else:
            url = f"/myorg/datasets/{dataset_id}/executeQueries"
        payload = {
            "queries": [{"query": dax_query}],
            "serializerSettings": {"includeNulls": True},
        }
        r = self._client.post(url, json=payload)
        r.raise_for_status()
        try:
            data = r.json()
            results = data.get("results", [])
            if not results or results[0].get("error"):
                return []
            tables = results[0].get("tables", [])
            if not tables:
                return []
            return tables[0].get("rows", [])
        except Exception:
            return []

    def run(self) -> None:
        target_name = self.config.get("name", "Power BI")
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
            workspace_ids = self._get_workspace_ids()
            if not workspace_ids:
                workspace_ids = [None]
            for group_id in workspace_ids:
                datasets = self._get_datasets(group_id)
                for ds in datasets:
                    ds_id = ds.get("id")
                    ds_name = ds.get("name", "Dataset")
                    if not ds_id:
                        continue
                    tables = self._get_tables(ds_id, group_id)
                    if not tables:
                        continue
                    for tbl in tables:
                        tname = tbl.get("name")
                        if not tname:
                            continue
                        columns = tbl.get("columns", [])
                        if not columns:
                            try:
                                rows = self._execute_dax(
                                    ds_id,
                                    group_id,
                                    f"EVALUATE TOPN({self.sample_limit}, {tname})",
                                )
                                if rows:
                                    for key in rows[0].keys():
                                        sample = " ".join(
                                            str(r.get(key, ""))[:200]
                                            for r in rows[: self.sample_limit]
                                        )
                                        cname = key.split("[")[-1].rstrip("]")
                                        res = self.scanner.scan_column(
                                            cname, sample, connector_data_type=None
                                        )
                                        res = augment_low_id_like_for_persist(
                                            res, cname, self.detection_config
                                        )
                                        if (
                                            res.get("sensitivity_level") == "LOW"
                                            and res.get("pattern_detected")
                                            != SUGGESTED_REVIEW_PATTERN
                                        ):
                                            continue
                                        self.db_manager.save_finding(
                                            source_type="database",
                                            target_name=target_name,
                                            server_ip="api.powerbi.com",
                                            engine_details="Power BI",
                                            schema_name=ds_name,
                                            table_name=tname,
                                            column_name=key.split("[")[-1].rstrip("]"),
                                            data_type="",
                                            sensitivity_level=res.get(
                                                "sensitivity_level", "MEDIUM"
                                            ),
                                            pattern_detected=res.get(
                                                "pattern_detected", ""
                                            ),
                                            norm_tag=res.get("norm_tag", ""),
                                            ml_confidence=res.get("ml_confidence", 0),
                                        )
                            except Exception:
                                # Sampling fallback is best-effort for table metadata gaps.
                                continue
                            continue
                        sample_rows = self._execute_dax(
                            ds_id,
                            group_id,
                            f"EVALUATE TOPN({self.sample_limit}, {tname})",
                        )
                        for col in columns:
                            cname = col.get("name", "")
                            if not cname:
                                continue
                            sample = ""
                            if sample_rows:
                                full_key = f"{tname}[{cname}]"
                                for row in sample_rows[: self.sample_limit]:
                                    sample += (
                                        str(row.get(full_key, row.get(cname, "")))[:200]
                                        + " "
                                    )
                            pbi_dtype = str(col.get("dataType", "") or "") or None
                            res = self.scanner.scan_column(
                                cname, sample, connector_data_type=pbi_dtype
                            )
                            res = augment_low_id_like_for_persist(
                                res, cname, self.detection_config
                            )
                            if (
                                res.get("sensitivity_level") == "LOW"
                                and res.get("pattern_detected")
                                != SUGGESTED_REVIEW_PATTERN
                            ):
                                continue
                            self.db_manager.save_finding(
                                source_type="database",
                                target_name=target_name,
                                server_ip="api.powerbi.com",
                                engine_details="Power BI",
                                schema_name=ds_name,
                                table_name=tname,
                                column_name=cname,
                                data_type=str(col.get("dataType", "")),
                                sensitivity_level=res.get(
                                    "sensitivity_level", "MEDIUM"
                                ),
                                pattern_detected=res.get("pattern_detected", ""),
                                norm_tag=res.get("norm_tag", ""),
                                ml_confidence=res.get("ml_confidence", 0),
                            )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()

    def _save_inventory_snapshot(self, target_name: str) -> None:
        """Persist one Power BI API inventory row."""
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        details = {
            "api_base": _PBI_BASE,
            "scope": _PBI_SCOPE,
            "tenant_id": str(
                (self.config.get("auth") or {}).get("tenant_id")
                or self.config.get("tenant_id")
                or ""
            ),
        }
        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="bi",
                product="powerbi",
                product_version=None,
                protocol_or_api_version="v1.0",
                transport_security="tls=https",
                raw_details=json.dumps(details, ensure_ascii=False),
            )
        except Exception:
            # Inventory snapshot is best-effort; do not interrupt scanning.
            return


if _HTTPX_AVAILABLE:
    register(
        "powerbi", PowerBIConnector, ["name", "tenant_id", "client_id", "client_secret"]
    )
