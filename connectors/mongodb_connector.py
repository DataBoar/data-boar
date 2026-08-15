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
from core.crypto_audit import (
    collect_mongodb_crypto_facts,
    evaluate_strong_crypto,
    infer_controls_from_identifiers,
    resolve_nosql_tls_connect_options,
)
from connectors.inventory_details import build_mongodb_inventory_details
from connectors.sample_value_dedup import (
    resolve_fetch_row_budget,
)
from connectors.sql_sampling import resolve_sql_sample_limit
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
        self._tls_enabled = False

    def connect(self) -> None:
        if not _MONGO_AVAILABLE:
            from core.extras_runtime import missing_optional_message

            raise RuntimeError(
                missing_optional_message(
                    subject="MongoDB connector",
                    extra="nosql",
                )
            )
        host = self.config.get("host", "localhost")
        port = int(self.config.get("port", 27017))
        from .url_guard import target_allows_private, validate_outbound_url

        # SSRF guard (#1559): bare host:port — do not use tcp:// (not in allowlist).
        err = validate_outbound_url(
            f"{host}:{port}",
            allow_private=target_allows_private(self.config),
            label="host",
        )
        if err:
            raise ValueError(err)
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
        tls_enabled, sslmode_posture, _cert = resolve_nosql_tls_connect_options(
            self.config
        )
        self._tls_enabled = bool(tls_enabled)
        client_kwargs: dict[str, Any] = {
            "serverSelectionTimeoutMS": connect_s * 1000,
            "connectTimeoutMS": connect_s * 1000,
            "socketTimeoutMS": read_s * 1000,
        }
        if tls_enabled:
            client_kwargs["tls"] = True
            # require / prefer → encrypted without full CA/hostname verify.
            if sslmode_posture in ("require", "prefer", "allow"):
                client_kwargs["tlsAllowInvalidCertificates"] = True
        self._client = MongoClient(uri, **client_kwargs)
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
        identifier_names: list[str] = []
        try:
            from utils.logger import log_connection

            log_connection(audit_name, "mongodb", self.config.get("host", "localhost"))
            self._save_inventory_snapshot(target_name)
            self._save_crypto_controls_audit(target_name)
            distinct_cap = resolve_sql_sample_limit(int(self.sample_limit))
            fetch_budget = resolve_fetch_row_budget(distinct_cap)
            for coll_name in self._db.list_collection_names():
                coll = self._db[coll_name]
                sample_docs = list(coll.find().limit(fetch_budget))
                if not sample_docs:
                    continue
                all_keys: set[str] = set()
                field_values: dict[str, list[str]] = {}
                for doc in sample_docs:
                    for k, v in doc.items():
                        if k.startswith("_"):
                            continue
                        all_keys.add(k)
                        if v is None:
                            continue
                        bucket = field_values.setdefault(k, [])
                        sv = str(v)[:100]
                        if sv in bucket:
                            continue
                        if len(bucket) >= distinct_cap:
                            continue
                        bucket.append(sv)
                identifier_names.extend(all_keys)
                sample_texts = [
                    f"{k} {v}" for k, vals in field_values.items() for v in vals
                ]
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
            # Best-effort even when mid-loop sampling/detection raises.
            self._save_inferred_controls_summary(target_name, identifier_names)
            self.close()

    def _save_inferred_controls_summary(
        self, target_name: str, identifier_names: list[str]
    ) -> None:
        """Phase 3: attach count-by-category inference to the crypto audit row."""
        if not self.config.get("_validate_crypto"):
            return
        if not hasattr(self.db_manager, "update_crypto_controls_inferred_summary"):
            return
        try:
            summary = infer_controls_from_identifiers(identifier_names)
            if not summary:
                return
            self.db_manager.update_crypto_controls_inferred_summary(
                target_name, summary
            )
        except Exception:
            # Fail-soft: inference never fails the scan.
            pass

    def _save_crypto_controls_audit(self, target_name: str) -> None:
        """Opt-in strong-crypto validation after connect (Order 5 Phase 2c)."""
        if not self.config.get("_validate_crypto"):
            return
        if not hasattr(self.db_manager, "save_crypto_controls_audit"):
            return
        if not self._client:
            return
        try:
            facts = collect_mongodb_crypto_facts(self._client, self.config)
            result, details = evaluate_strong_crypto(facts)
            self.db_manager.save_crypto_controls_audit(
                target_name=target_name,
                connection_type="mongodb",
                strong_crypto_result=result.value,
                strong_crypto_details=details[:512],
                inferred_controls_summary=None,
            )
        except Exception:
            # Fail-soft: probe/persist errors never fail the scan.
            pass

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
        if self._tls_enabled or self.config.get("tls"):
            transport = "tls=enabled"
        else:
            transport = "tls=disabled"
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
