"""
Data Boar core engine — risk discovery and governance orchestration.

AuditEngine: orchestrates targets from config via connector registry; uses LocalDBManager and DataScanner.
Supports sequential or parallel (max_workers) scan; start_audit(), generate_final_reports(session_id).
Exposes db_manager, is_running, get_current_findings_count() for API.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from config.scan_defaults import DEFAULT_FILE_SAMPLE_MAX_CHARS


def _compute_config_scope_hash(config: dict[str, Any]) -> str:
    """
    Compute a non-reversible digest of the scan scope (target names, types, file_scan.extensions only).

    **Why PBKDF2, not SHA-256 / BLAKE2:** CodeQL ``py/weak-sensitive-data-hashing`` treats
    configuration-derived strings (including target ``name``) as potentially sensitive and flags
    *fast* digests (MD5/SHA/BLAKE2, etc.) as unsafe “password hashing.” This value is **not** a
    password store—it is audit metadata only—but we use **PBKDF2-HMAC-SHA256** with a fixed salt
    and high iteration count so the query suite is satisfied without changing semantics beyond the
    digest function.

    No secrets or credentials are included in the scope material.
    """
    parts: list[str] = []
    for t in config.get("targets", []):
        name = (t.get("name") or "").strip()
        typ = (t.get("type") or "").strip()
        if name or typ:
            parts.append(f"{name}:{typ}")
    exts = config.get("file_scan", {}).get("extensions", [])
    if exts:
        parts.append("extensions:" + ",".join(sorted(str(e) for e in exts)))
    blob = "\n".join(sorted(parts)).encode("utf-8")
    # Fixed application salt (not secret); iteration count is the work factor for CodeQL / KDF posture.
    salt = b"data-boar|config-scope|v1"
    derived = hashlib.pbkdf2_hmac("sha256", blob, salt, 120_000, dklen=32)
    return derived.hex()


# Import connectors so they register themselves
import connectors.filesystem_connector  # noqa: F401
from connectors.sql_connector import SQLConnector

try:
    import connectors.mongodb_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.redis_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.rest_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.smb_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.webdav_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.sharepoint_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.nfs_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.powerbi_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed
try:
    import connectors.dataverse_connector  # noqa: F401
except ImportError:  # noqa: BLE001
    pass  # optional connector not installed

from core.connector_registry import connector_for_target
from core.crypto_audit import StrongCryptoSignal, summarize_crypto_from_connection_info
from core.database import LocalDBManager
from core.sampling import SamplingPolicy
from core.scanner import DataScanner
from core.session import new_session_id

_CONNECTOR_SAMPLING_POLICY_BASES: tuple[type, ...] = (SQLConnector,)
try:
    from connectors.snowflake_connector import SnowflakeConnector

    _CONNECTOR_SAMPLING_POLICY_BASES = (SQLConnector, SnowflakeConnector)
except ImportError:  # noqa: BLE001
    pass  # optional Snowflake connector not installed


class AuditEngine:
    def __init__(self, config: dict[str, Any], db_path: str | None = None):
        self.config = config
        self._sampling_policy = SamplingPolicy.from_config(config)
        self.db_path = db_path or config.get("sqlite_path", "audit_results.db")
        self.db_manager = LocalDBManager(self.db_path)
        sens = config.get("sensitivity_detection") or {}
        detection = dict(config.get("detection") or {})
        # ML/DL MEDIUM band threshold lives under sensitivity_detection; detector reads flat keys.
        if "medium_confidence_threshold" in sens:
            detection["medium_confidence_threshold"] = sens[
                "medium_confidence_threshold"
            ]
        if "column_name_normalize_for_ml" in sens:
            detection["column_name_normalize_for_ml"] = sens[
                "column_name_normalize_for_ml"
            ]
        for _fuzzy_key in (
            "fuzzy_column_match",
            "fuzzy_column_match_min_confidence",
            "fuzzy_column_match_max_confidence",
            "fuzzy_column_match_min_ratio",
        ):
            if _fuzzy_key in sens:
                detection[_fuzzy_key] = sens[_fuzzy_key]
        self.scanner = DataScanner(
            regex_overrides_path=config.get("regex_overrides_file") or None,
            ml_patterns_path=config.get("ml_patterns_file") or None,
            ml_terms_inline=sens.get("ml_terms") or None,
            dl_patterns_path=config.get("dl_patterns_file") or None,
            dl_terms_inline=sens.get("dl_terms") or None,
            detection_config=detection,
            file_encoding=config.get("pattern_files_encoding", "utf-8"),
        )
        self._is_running = False
        self._last_report_path: str | None = None
        self._max_workers = int(config.get("scan", {}).get("max_workers", 1))
        self._extensions = config.get("file_scan", {}).get("extensions", [])
        # Internal: best-effort strong-crypto signals collected per-target during this run.
        # Phase 1: populated for database-style targets only; not yet persisted or exposed.
        self._crypto_signals: list[tuple[str, set[StrongCryptoSignal]]] = []
        # Declarative sampling / SRE posture for API ``audit_log`` (refreshed after each scan).
        self._scan_audit_log: dict[str, Any] | None = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_current_findings_count(self) -> int:
        return self.db_manager.get_current_findings_count()

    @property
    def crypto_signals(self) -> list[tuple[str, set[StrongCryptoSignal]]]:
        """
        Read-only view of best-effort strong-crypto signals collected for this run.

        Each entry is (target_name, {StrongCryptoSignal, ...}). Currently populated
        only for database-style targets and not persisted or exposed via API/CLI.
        """

        return list(self._crypto_signals)

    def get_scan_audit_log(self) -> dict[str, Any]:
        """
        JSON-serializable security/sampling posture for the current config.

        After at least one ``_run_audit_targets`` completion, reflects the same snapshot
        captured at end-of-run; before that, returns a fresh build from ``self.config``.
        """
        from core.scan_audit_log import build_scan_audit_log

        if self._scan_audit_log is not None:
            return dict(self._scan_audit_log)
        return build_scan_audit_log(self.config)

    def start_audit(
        self,
        tenant_name: str | None = None,
        technician_name: str | None = None,
        jurisdiction_hint: bool = False,
    ) -> str:
        """
        Run audit for all targets (sequential or parallel). Returns session_id (UUID + timestamp).
        """
        from core.licensing import LicenseBlockedError, get_license_guard

        guard = get_license_guard(self.config)
        if not guard.allows_scan():
            c = guard.context
            raise LicenseBlockedError(
                c.state,
                f"Licensing blocks scan: state={c.state} detail={c.detail}",
            )

        # #551: licensing worker cap — effective = min(scan.max_workers, tier cap).
        # Enforced mode only (open mode returns None = no cap). Fail-soft: a cap
        # resolution error must never abort a scan the license gate already
        # allowed — warn and run uncapped instead.
        import logging

        try:
            cap = guard.worker_cap()
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).warning(
                "Licensing worker cap resolution failed (fail-soft, no cap): %s", e
            )
            cap = None
        if cap is not None and self._max_workers > cap:
            from core.licensing.audit import audit_enforcement_event

            c = guard.context
            audit_enforcement_event(
                "workers_clamped",
                mode=c.mode,
                state=c.state,
                allowed=False,
                detail=f"requested={self._max_workers} cap={cap}",
                level=logging.WARNING,
            )
            self._max_workers = cap

        session_id = new_session_id()
        self.db_manager.set_current_session_id(session_id)
        scope_hash = _compute_config_scope_hash(self.config)
        self.db_manager.create_session_record(
            session_id,
            tenant_name=tenant_name,
            technician_name=technician_name,
            config_scope_hash=scope_hash,
            jurisdiction_hint=jurisdiction_hint,
        )
        self._run_audit_targets()
        return session_id

    def _run_audit_targets(self) -> None:
        """Run all targets; caller must set session_id and create_session_record before."""
        self._is_running = True
        session_id = self.db_manager.current_session_id
        targets = self.config.get("targets", [])
        final_status = "completed"
        try:
            if self._max_workers <= 1:
                for target in targets:
                    self._run_target(target)
            else:
                with ThreadPoolExecutor(
                    max_workers=min(self._max_workers, len(targets) or 1)
                ) as ex:
                    futures = {ex.submit(self._run_target, t): t for t in targets}
                    for fut in as_completed(futures):
                        try:
                            fut.result()
                        except Exception as e:
                            # Target-level errors are usually caught inside _run_target; this
                            # path handles unexpected worker failures so sessions are not
                            # silently marked completed without trace.
                            tgt = futures.get(fut) or {}
                            tname = (
                                tgt.get("name", "unknown")
                                if isinstance(tgt, dict)
                                else "unknown"
                            )
                            try:
                                from utils.logger import get_logger

                                get_logger().exception(
                                    "Parallel target worker failed: session=%s",
                                    session_id,
                                )
                            except Exception as log_err:
                                # Best effort: logging failures must not interrupt worker cleanup.
                                _ = str(log_err)
                            try:
                                from core.validation import clean_error

                                self.db_manager.save_failure(
                                    tname,
                                    "error",
                                    f"Uncaught worker error: {clean_error(e)}",
                                )
                            except Exception as save_err:
                                # Best effort: persist failures when possible, but don't break session flow.
                                _ = str(save_err)
                            final_status = "completed_errors"
        finally:
            self._is_running = False
            from core.scan_audit_log import build_scan_audit_log

            self._scan_audit_log = build_scan_audit_log(self.config)
            self.db_manager.finish_session(session_id, final_status)

    def _run_target(self, target: dict[str, Any]) -> None:
        """Run one target: resolve connector, instantiate, run()."""
        from core.connector_registry import require_connector_allowed
        from core.licensing.errors import FeatureTierBlockedError

        # Connector tier gate (#843): fail-loud + scan_failures row in enforced
        # mode; free in Tier.OPEN and for open-core connectors.
        try:
            require_connector_allowed(self.config, target)
        except FeatureTierBlockedError as exc:
            tname = target.get("name", "unknown")
            self.db_manager.save_failure(tname, "tier_blocked", exc.reason)
            return

        resolved = connector_for_target(target)
        if not resolved:
            tname = target.get("name", "unknown")
            ttype = target.get("type", "?")
            self.db_manager.save_failure(
                tname,
                "unknown_connector_type",
                (
                    f"No connector registered for type '{ttype}'. "
                    "Check config.yaml — possible typo or missing optional dependency."
                ),
            )
            return
        connector_class, _ = resolved
        t = target.get("type")
        fs_config = self.config.get("file_scan", {})
        # Inject file_scan into target so connectors (filesystem, shares) see scan_compressed, etc.
        target_with_fs = {**target, "file_scan": fs_config}
        scan_sqlite_as_db = fs_config.get("scan_sqlite_as_db", True)
        sample_limit = fs_config.get("sample_limit", 5)
        file_sample_max_chars = int(
            fs_config.get("file_sample_max_chars", DEFAULT_FILE_SAMPLE_MAX_CHARS)
        )
        file_passwords = fs_config.get("file_passwords") or {}
        ext = fs_config.get("extensions")
        from core.validation import clean_error

        try:
            if t == "filesystem":
                if ext is not None:
                    connector = connector_class(
                        target_with_fs,
                        self.scanner,
                        self.db_manager,
                        extensions=ext,
                        scan_sqlite_as_db=scan_sqlite_as_db,
                        sample_limit=sample_limit,
                        file_sample_max_chars=file_sample_max_chars,
                        file_passwords=file_passwords,
                    )
                else:
                    connector = connector_class(
                        target_with_fs,
                        self.scanner,
                        self.db_manager,
                        scan_sqlite_as_db=scan_sqlite_as_db,
                        sample_limit=sample_limit,
                        file_sample_max_chars=file_sample_max_chars,
                        file_passwords=file_passwords,
                    )
            elif t in ("sharepoint", "webdav", "smb", "cifs", "nfs"):
                connector = connector_class(
                    target_with_fs,
                    self.scanner,
                    self.db_manager,
                    extensions=ext,
                    scan_sqlite_as_db=scan_sqlite_as_db,
                    sample_limit=sample_limit,
                    file_sample_max_chars=file_sample_max_chars,
                    file_passwords=file_passwords,
                )
            elif t in ("powerbi", "dataverse", "powerapps"):
                connector = connector_class(
                    target,
                    self.scanner,
                    self.db_manager,
                    sample_limit=sample_limit,
                    detection_config=self.config.get("detection"),
                )
            else:
                # Database targets (postgresql, mysql, sqlite, mssql, oracle, mongodb, etc.): pass
                # sample_limit from file_scan (row/doc caps) and detection config for optional probes.
                extra_kw: dict[str, Any] = {}
                if issubclass(connector_class, _CONNECTOR_SAMPLING_POLICY_BASES):
                    extra_kw["sampling_policy"] = self._sampling_policy
                connector = connector_class(
                    target,
                    self.scanner,
                    self.db_manager,
                    sample_limit=sample_limit,
                    detection_config=self.config.get("detection"),
                    **extra_kw,
                )
                # Phase 1: inspect connection info to collect coarse crypto/transport hints.
                name = (target.get("name") or "").strip() or "database"
                driver = (target.get("driver") or "").strip()
                dsn = (target.get("dsn") or "").strip()
                sslmode = (target.get("sslmode") or "").strip()
                conn_info = {
                    "type": "database",
                    "name": name,
                    "driver": driver,
                    "dsn": dsn,
                    "sslmode": sslmode,
                }
                signals = summarize_crypto_from_connection_info(conn_info)
                if signals:
                    self._crypto_signals.append((name, signals))
            connector.run()
        except Exception as e:
            self.db_manager.save_failure(
                target.get("name", "unknown"), "error", clean_error(e)
            )

    def generate_final_reports(self, session_id: str | None = None) -> str | None:
        """
        Build Excel + heatmap from SQLite for session_id (or current). Return report file path or None.
        If learned_patterns.enabled, also writes learned_patterns.yaml from findings.
        """
        from report.generator import generate_report

        sid = session_id or self.db_manager.current_session_id
        if not sid:
            return None
        out_dir = self.config.get("report", {}).get("output_dir", ".")
        path = generate_report(
            self.db_manager,
            sid,
            output_dir=out_dir,
            config=self.config,
        )
        if path:
            self._last_report_path = path
        # Optional: write learned patterns for merging into ml_patterns_file (2.2)
        from core.learned_patterns import write_learned_patterns

        learned_path = write_learned_patterns(self.db_manager, sid, self.config)
        if learned_path:
            from utils.logger import get_logger

            get_logger().info(
                "Learned patterns written to %s (merge into ml_patterns_file for next run)",
                learned_path,
            )
        return path

    def get_last_report_path(self) -> str | None:
        return self._last_report_path
