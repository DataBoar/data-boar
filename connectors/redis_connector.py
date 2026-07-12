"""
Optional Redis connector: connect, scan keys (or sample), run detector on key names and types.
Register as type 'redis'. Install: pip install redis
Config target: type: database, driver: redis, host, port, (optional password).
"""

from typing import Any
import json

try:
    import redis

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    redis = None

from core.connector_registry import register
from connectors.inventory_details import build_redis_inventory_details
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)


class RedisConnector:
    """Scan Redis: sample keys (e.g. SCAN), detect sensitive key names; no value storage."""

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        sample_limit: int = 100,
        value_sample_limit: int = 100,
        detection_config: dict[str, Any] | None = None,
    ):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.sample_limit = sample_limit
        self.value_sample_limit = max(1, value_sample_limit)
        self.detection_config = detection_config or {}
        self._client = None

    def connect(self) -> None:
        if not _REDIS_AVAILABLE:
            raise RuntimeError(
                "redis is not installed. Install with: pip install redis"
            )
        host = self.config.get("host", "localhost")
        port = int(self.config.get("port", 6379))
        password = self.config.get("pass") or self.config.get("password")
        connect_s = max(1, int(self.config.get("connect_timeout_seconds", 25)))
        read_s = max(1, int(self.config.get("read_timeout_seconds", 90)))
        self._client = redis.Redis(
            host=host,
            port=port,
            password=password or None,
            decode_responses=True,
            socket_connect_timeout=connect_s,
            socket_timeout=read_s,
        )

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

        target_name = self.config.get("name", "redis")
        audit_name = audit_log_target_label(self.config, default="redis")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            from utils.logger import log_connection

            log_connection(audit_name, "redis", self.config.get("host", "localhost"))
            self._save_inventory_snapshot(target_name)
            keys = []
            for k in self._client.scan_iter(count=self.sample_limit):
                keys.append(k)
                if len(keys) >= self.sample_limit:
                    break
            combined = " ".join(keys)
            per_key_limit = min(50, len(keys))
            values_sampled = 0
            for key in keys[:per_key_limit]:  # per-key classification
                res = self.scanner.scan_column(key, combined)
                res = augment_low_id_like_for_persist(res, key, self.detection_config)
                if (
                    res["sensitivity_level"] == "LOW"
                    and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
                ):
                    # Bounded value sampling (audit v2): inspect key payloads when names are clean.
                    if values_sampled < self.value_sample_limit:
                        try:
                            raw_val = self._client.get(key)
                        except Exception:
                            raw_val = None
                        if raw_val:
                            values_sampled += 1
                            val_preview = str(raw_val)[:500]
                            vres = self.scanner.scan_column(f"{key}:value", val_preview)
                            vres = augment_low_id_like_for_persist(
                                vres, val_preview, self.detection_config
                            )
                            if (
                                vres["sensitivity_level"] != "LOW"
                                or vres.get("pattern_detected")
                                == SUGGESTED_REVIEW_PATTERN
                            ):
                                res = vres
                    if (
                        res["sensitivity_level"] == "LOW"
                        and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
                    ):
                        continue
                self.db_manager.save_finding(
                    source_type="database",
                    target_name=target_name,
                    server_ip=self.config.get("host", "localhost"),
                    engine_details="redis",
                    schema_name="",
                    table_name="keys",
                    column_name=key,
                    data_type="key",
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
                        f"keys.{key}",
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
        """Persist one Redis inventory row (best effort)."""
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        product_version = None
        raw_details: dict[str, dict[str, str]] = {
            "executive": {"driver": "redis"},
            "technical": {},
        }
        try:
            info = self._client.info("server")
            product_version = str(info.get("redis_version", "") or "") or None
            details = build_redis_inventory_details(info)
            raw_details["executive"].update(details.get("executive") or {})
            raw_details["technical"].update(details.get("technical") or {})
        except Exception as e:
            # Probe is optional; preserve scan flow when INFO is unavailable.
            raw_details["technical"]["version_probe_error"] = str(e)[:200]
        transport = "tls=enabled" if self.config.get("tls") else "unknown"
        raw_details["executive"]["transport_hint"] = transport
        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="database",
                product="redis",
                product_version=product_version,
                protocol_or_api_version="redis",
                transport_security=transport,
                raw_details=json.dumps(raw_details, ensure_ascii=False),
            )
        except Exception:
            # Inventory snapshot is best-effort; keep scan flow resilient.
            return


if _REDIS_AVAILABLE:
    register("redis", RedisConnector, ["name", "type"])
