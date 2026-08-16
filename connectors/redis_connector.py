"""
Optional Redis connector: connect, scan keys (or sample), run detector on key names and types.
Register as type 'redis'. Install: pip install redis
Config target: type: database, driver: redis, host, port, (optional password).
"""

import json
from typing import Any

try:
    import redis
    from redis.connection import Connection as _RedisConnection
    from redis.connection import ConnectionPool as _RedisConnectionPool
    from redis.connection import SSLConnection as _RedisSSLConnection
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import ResponseError as RedisResponseError
    from redis.exceptions import TimeoutError as RedisTimeoutError

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    redis = None
    _RedisConnection = None  # type: ignore[misc, assignment]
    _RedisConnectionPool = None  # type: ignore[misc, assignment]
    _RedisSSLConnection = None  # type: ignore[misc, assignment]
    RedisConnectionError = Exception  # type: ignore[misc, assignment]
    RedisResponseError = Exception  # type: ignore[misc, assignment]
    RedisTimeoutError = Exception  # type: ignore[misc, assignment]

from connectors.inventory_details import build_redis_inventory_details
from core.connector_registry import register
from core.crypto_audit import (
    collect_redis_crypto_facts,
    evaluate_strong_crypto,
    infer_controls_from_identifiers,
    resolve_nosql_tls_connect_options,
)
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)

REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED = "redis_value_not_sampled"


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
        self._tls_enabled = False

    def connect(self) -> None:
        if not _REDIS_AVAILABLE:
            from core.extras_runtime import missing_optional_message

            raise RuntimeError(
                missing_optional_message(
                    subject="Redis connector",
                    extra="nosql",
                )
            )
        host = self.config.get("host", "localhost")
        port = int(self.config.get("port", 6379))
        from .tcp_pin import is_ip_literal, make_pinned_redis_connection_class
        from .url_guard import resolve_and_validate_outbound_url, target_allows_private

        # SSRF guard (#1559): bare host:port — do not use tcp:// (not in allowlist).
        # Capture validated IPs for TCP pin (#1586) so redis-py cannot re-resolve
        # to a different peer after the guard (Connection._connect → getaddrinfo).
        err, pin_ips = resolve_and_validate_outbound_url(
            f"{host}:{port}",
            allow_private=target_allows_private(self.config),
            label="host",
        )
        if err:
            raise ValueError(err)
        password = self.config.get("pass") or self.config.get("password")
        connect_s = max(1, int(self.config.get("connect_timeout_seconds", 25)))
        read_s = max(1, int(self.config.get("read_timeout_seconds", 90)))
        tls_enabled, _sslmode, cert_reqs = resolve_nosql_tls_connect_options(
            self.config
        )
        self._tls_enabled = bool(tls_enabled)
        # Connection types come from the optional redis import at module load.
        # CI matrices without the nosql extra still run crypto tests that stub
        # ``redis`` + ``_REDIS_AVAILABLE`` — fall back to Redis(**kwargs) then
        # (no pin subclass without real connection classes).
        if _RedisConnectionPool is None or _RedisConnection is None:
            client_kwargs: dict[str, Any] = {
                "host": host,
                "port": port,
                "password": password or None,
                "decode_responses": True,
                "socket_connect_timeout": connect_s,
                "socket_timeout": read_s,
            }
            if tls_enabled:
                client_kwargs["ssl"] = True
                if cert_reqs is not None:
                    client_kwargs["ssl_cert_reqs"] = cert_reqs
            self._client = redis.Redis(**client_kwargs)
            return

        base_cls: type = _RedisSSLConnection if tls_enabled else _RedisConnection
        # Hostname stays on the connection for TLS server_hostname; pin TCP peers
        # via connection_class (#1586). IP literals have no DNS rebinding window.
        if is_ip_literal(str(host)):
            connection_class = base_cls
        else:
            connection_class = make_pinned_redis_connection_class(base_cls, pin_ips)
        pool_kwargs: dict[str, Any] = {
            "connection_class": connection_class,
            "host": host,
            "port": port,
            "password": password or None,
            "decode_responses": True,
            "socket_connect_timeout": connect_s,
            "socket_timeout": read_s,
        }
        if tls_enabled and cert_reqs is not None:
            pool_kwargs["ssl_cert_reqs"] = cert_reqs
        self._client = redis.Redis(connection_pool=_RedisConnectionPool(**pool_kwargs))

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
        keys: list[Any] = []
        try:
            from utils.logger import log_connection

            log_connection(audit_name, "redis", self.config.get("host", "localhost"))
            self._save_inventory_snapshot(target_name)
            self._save_crypto_controls_audit(target_name)
            for k in self._client.scan_iter(count=self.sample_limit):
                keys.append(k)
                if len(keys) >= self.sample_limit:
                    break
            # Pass the sampled keyspace as shared context for name-based detection on
            # each key (cross-key co-occurrence in this SCAN window).
            combined = " ".join(keys)
            per_key_limit = min(self.sample_limit, len(keys))
            values_sampled = 0
            value_not_sampled_by_type: dict[str, int] = {}
            for key in keys[:per_key_limit]:
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
                        except RedisResponseError as exc:
                            if "WRONGTYPE" in str(exc).upper():
                                key_type = str(self._client.type(key) or "unknown")
                                value_not_sampled_by_type[key_type] = (
                                    value_not_sampled_by_type.get(key_type, 0) + 1
                                )
                                raw_val = None
                            else:
                                self.db_manager.save_failure(
                                    target_name, "redis_error", f"{key}: {exc}"
                                )
                                raw_val = None
                        except (
                            RedisConnectionError,
                            RedisTimeoutError,
                            OSError,
                        ) as exc:
                            self.db_manager.save_failure(
                                target_name, "unreachable", f"{key}: {exc}"
                            )
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
            if value_not_sampled_by_type:
                self.db_manager.save_failure(
                    target_name,
                    REDIS_SCAN_FAILURE_VALUE_NOT_SAMPLED,
                    json.dumps(
                        {
                            "keys_discovered": len(keys),
                            "keys_name_classified": per_key_limit,
                            "values_sampled": values_sampled,
                            "value_not_sampled_by_type": value_not_sampled_by_type,
                        },
                        ensure_ascii=False,
                    ),
                )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            # Best-effort even when mid-loop sampling/detection raises.
            self._save_inferred_controls_summary(target_name, keys)
            self.close()

    def _save_inferred_controls_summary(
        self, target_name: str, identifier_names: list[Any]
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
            facts = collect_redis_crypto_facts(self._client, self.config)
            result, details = evaluate_strong_crypto(facts)
            self.db_manager.save_crypto_controls_audit(
                target_name=target_name,
                connection_type="redis",
                strong_crypto_result=result.value,
                strong_crypto_details=details[:512],
                inferred_controls_summary=None,
            )
        except Exception:
            # Fail-soft: probe/persist errors never fail the scan.
            pass

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
        if self._tls_enabled or self.config.get("tls"):
            transport = "tls=enabled"
        else:
            transport = "tls=disabled"
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


# Always register so YAML resolves; connect() fails with named extra (#1402).
register("redis", RedisConnector, ["name", "type"])
