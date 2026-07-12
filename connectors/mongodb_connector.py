"""
Optional MongoDB connector: connect, list collections, sample documents, run detector, save_finding.
Register as type 'mongodb'. Install: pip install pymongo
Config target: type: database, driver: mongodb, host, port, database (and optional user/pass).
"""

from typing import Any
from urllib.parse import quote
import json

try:
    from pymongo import MongoClient

    _MONGO_AVAILABLE = True
except ImportError:
    _MONGO_AVAILABLE = False
    MongoClient = None

from core.connector_registry import register
from connectors.inventory_details import build_mongodb_inventory_details
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)


class MongoDBConnector:
    """Scan MongoDB: list collections, sample docs, detect sensitive field names and sample values."""

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
        self._client = None

    def connect(self) -> None:
        if not _MONGO_AVAILABLE:
            raise RuntimeError(
                "pymongo is not installed. Install with: pip install pymongo"
            )
        host = self.config.get("host", "localhost")
        port = int(self.config.get("port", 27017))
        user = self.config.get("user") or self.config.get("username")
        password = self.config.get("pass") or self.config.get("password")
        database = self.config.get("database", "test")
        if user and password:
            # URL-encode credentials so @, :, /, # in password do not break URI parsing
            user_enc = quote(str(user), safe="")
            password_enc = quote(str(password), safe="")
            uri = f"mongodb://{user_enc}:{password_enc}@{host}:{port}/{database}"
        else:
            uri = f"mongodb://{host}:{port}"
        connect_s = max(1, int(self.config.get("connect_timeout_seconds", 25)))
        read_s = max(1, int(self.config.get("read_timeout_seconds", 90)))
        self._client = MongoClient(
            uri,
            serverSelectionTimeoutMS=connect_s * 1000,
            connectTimeoutMS=connect_s * 1000,
            socketTimeoutMS=read_s * 1000,
        )
        self._db = self._client[database]

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                # Best-effort close: ignore client shutdown errors.
                return
            self._client = None

    def run(self) -> None:
        from utils.audit_log_display import audit_log_target_label

        target_name = self.config.get("name", "mongodb")
        audit_name = audit_log_target_label(self.config, default="mongodb")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            from utils.logger import log_connection

            log_connection(audit_name, "mongodb", self.config.get("host", "localhost"))
            self._save_inventory_snapshot(target_name)
            for coll_name in self._db.list_collection_names():
                coll = self._db[coll_name]
                sample_docs = list(coll.find().limit(self.sample_limit))
                if not sample_docs:
                    continue
                # Flatten keys from sample docs
                all_keys = set()
                sample_texts = []
                for doc in sample_docs:
                    for k, v in doc.items():
                        if k.startswith("_"):
                            continue
                        all_keys.add(k)
                        if v is not None:
                            sample_texts.append(f"{k} {str(v)[:100]}")
                combined = " ".join(sample_texts)
                for key in all_keys:
                    res = self.scanner.scan_column(key, combined)
                    res = augment_low_id_like_for_persist(
                        res, key, self.detection_config
                    )
                    if (
                        res["sensitivity_level"] == "LOW"
                        and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
                    ):
                        continue
                    self.db_manager.save_finding(
                        source_type="database",
                        target_name=target_name,
                        server_ip=self.config.get("host", "localhost"),
                        engine_details="mongodb",
                        schema_name="",
                        table_name=coll_name,
                        column_name=key,
                        data_type="document",
                        sensitivity_level=res["sensitivity_level"],
                        pattern_detected=res["pattern_detected"],
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
                    try:
                        from utils.logger import log_finding

                        log_finding(
                            "database",
                            audit_name,
                            f"{coll_name}.{key}",
                            res["sensitivity_level"],
                            res["pattern_detected"],
                        )
                    except Exception:
                        # Finding log is optional telemetry and must not fail the connector flow.
                        continue
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()

    def _save_inventory_snapshot(self, target_name: str) -> None:
        """Persist one MongoDB inventory row (best effort; must not break scanning)."""
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        product_version = None
        raw_details: dict[str, dict[str, str]] = {
            "executive": {"driver": "mongodb"},
            "technical": {},
        }
        try:
            info = self._db.command("buildInfo")
            product_version = str(info.get("version", "") or "") or None
            details = build_mongodb_inventory_details(info)
            raw_details["executive"].update(details.get("executive") or {})
            raw_details["technical"].update(details.get("technical") or {})
        except Exception as e:
            # Probe is optional; preserve scan flow when buildInfo is unavailable.
            raw_details["technical"]["version_probe_error"] = str(e)[:200]
        transport = "tls=enabled" if self.config.get("tls") else "unknown"
        raw_details["executive"]["transport_hint"] = transport
        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="database",
                product="mongodb",
                product_version=product_version,
                protocol_or_api_version="mongodb",
                transport_security=transport,
                raw_details=json.dumps(raw_details, ensure_ascii=False),
            )
        except Exception:
            # Inventory snapshot is best-effort; keep scan flow resilient.
            return


# Always register so YAML with driver: mongodb resolves; connect() errors if pymongo is missing.
register("mongodb", MongoDBConnector, ["name", "type"])
