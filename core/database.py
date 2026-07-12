"""
Single SQLite schema for audit results: sessions, findings/failures and inventory metadata.
LocalDBManager persists findings, failures, and data-source inventory rows by session.
Session id comes from core.session (UUID + timestamp); set via set_current_session_id.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    desc,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

Base = declarative_base()


def _utc_now() -> datetime:
    """Timezone-aware UTC now for SQLAlchemy column defaults."""
    return datetime.now(timezone.utc)


class ScanSession(Base):
    """
    One scan run: UUID + timestamp, status.
    Optional tenant_name for customer/tenant attribution and technician_name for operator identification.
    """

    __tablename__ = "scan_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    started_at = Column(DateTime, default=_utc_now)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed
    tenant_name = Column(
        String(255), nullable=True
    )  # optional customer/tenant for this scan
    technician_name = Column(
        String(255), nullable=True
    )  # optional technician/operator for this scan
    config_scope_hash = Column(
        String(64), nullable=True
    )  # optional SHA-256 of scan scope (targets, types, extensions) for audit evidence
    jurisdiction_hint = Column(
        Integer, default=0
    )  # 1 = operator opted in to heuristic jurisdiction Report info rows for this session


class DatabaseFinding(Base):
    """A single finding from a database target (metadata only, no raw content)."""

    __tablename__ = "database_findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    target_name = Column(String(100))
    server_ip = Column(String(50))
    engine_details = Column(String(100))
    schema_name = Column(String(100))
    table_name = Column(String(100))
    column_name = Column(String(100))
    data_type = Column(String(50))
    sensitivity_level = Column(String(20))
    pattern_detected = Column(String(100))
    norm_tag = Column(String(100))  # e.g. LGPD Art. 5, GDPR Art. 4(1)
    ml_confidence = Column(Integer)
    created_at = Column(DateTime, default=_utc_now)


class FilesystemFinding(Base):
    """A single finding from a filesystem target."""

    __tablename__ = "filesystem_findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    target_name = Column(String(100))
    path = Column(String(512))
    file_name = Column(String(255))
    data_type = Column(String(50))  # extension / format
    sensitivity_level = Column(String(20))
    pattern_detected = Column(String(100))
    norm_tag = Column(String(100))
    ml_confidence = Column(Integer)
    # File-identity fields for incremental scan (Phase 1 — additive, nullable).
    # NULL means the scan predates Phase 1 or stat/fingerprint collection failed.
    source_mtime_ns = Column(BigInteger, nullable=True)
    # st_mtime_ns at scan time (nanoseconds since epoch).
    source_size = Column(BigInteger, nullable=True)
    # st_size at scan time (bytes).
    content_fingerprint = Column(String(16), nullable=True)
    # blake2s(sampled_bytes, digest_size=8).hexdigest() — change detection, not
    # cryptographic evidence. See ADR-0051.
    created_at = Column(DateTime, default=_utc_now)


class NotificationSendLog(Base):
    """
    Append-only log of outbound notification attempts (webhooks).
    Does not store message body; error_summary is redacted/truncated for operator review only.
    """

    __tablename__ = "notification_send_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=True, index=True)
    trigger = Column(String(32), nullable=False)  # scan_complete, manual
    recipient = Column(String(16), nullable=False)  # operator, tenant
    channel = Column(String(32), nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)


class ScanFailure(Base):
    """Record of a target that could not be scanned (unreachable, auth, permission)."""

    __tablename__ = "scan_failures"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    target_name = Column(String(100))
    reason = Column(
        String(50)
    )  # unreachable, auth_failed, permission_denied, timeout, sampling_error, error
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)


def failure_hint(reason: str) -> str:
    """
    Map a failure reason into a human-friendly next step.
    Used in reports and logs to help operators fix issues before re-running.
    """
    r = (reason or "").lower()
    if r == "unreachable":
        return (
            "Target did not respond. Check network connectivity (DNS, VPN, routing, firewall rules) "
            "and that the host/path is reachable from the audit host or container."
        )
    if r in {"auth_failed", "authentication_failed"}:
        return (
            "Authentication failed. Verify username/password, tokens or OAuth client credentials, "
            "and check for account lockouts or IP restrictions."
        )
    if r == "permission_denied":
        return (
            "Permission denied. Grant the scanner read access to this resource (filesystem/share/endpoint) "
            "or run it as a user/service account that already has permission."
        )
    if r == "timeout":
        return (
            "Operation timed out. Check for high latency, overloaded target, or too strict timeouts. "
            "Consider increasing timeout values and re-running during off-peak hours. "
            "You can set timeouts in config (timeouts.connect_seconds, timeouts.read_seconds) or per target; see USAGE.md."
        )
    if r == "sampling_error":
        return (
            "Column sampling failed (SQL syntax, permissions, or connectivity). The column was not "
            "evaluated — this is not a clean result. Check dialect-specific sampling notes, credentials, "
            "and the detailed message; fix the target or sampling plan before re-running."
        )
    if r == "encrypted_no_password":
        return (
            "File or archive member is encrypted and no password was configured. This is not a clean "
            "result — add the password under file_scan.file_passwords (or the matching extension key) "
            "and re-run, or exclude the path if decryption is out of scope."
        )
    if r == "wrong_password":
        return (
            "Password was provided but decryption failed. Verify file_scan.file_passwords for this "
            "extension; a wrong password is not a clean scan result."
        )
    return (
        "Unexpected error. Review the detailed message and audit log, verify the target configuration "
        "(host, port, path, credentials) and test connectivity manually before re-running."
    )


class DataWipeLog(Base):
    """
    Audit log for destructive maintenance operations (e.g. wiping all scan data).
    Rows in this table are preserved when wipe_all_data() is called so that there is a trace
    of when and why previous history was cleared.
    """

    __tablename__ = "data_wipe_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    wiped_at = Column(DateTime, default=_utc_now)
    reason = Column(Text, nullable=False)


class AggregatedIdentificationRisk(Base):
    """
    One record per (session, target, table-or-file) where multiple quasi-identifier
    categories (gender, job_position, health, address, phone, etc.) were found together,
    indicating possible identification or re-identification risk (LGPD Art. 5, GDPR Recital 26).
    """

    __tablename__ = "aggregated_identification_risk"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    target_name = Column(String(100))
    source_type = Column(String(20))  # database | filesystem
    table_or_file = Column(String(512))  # schema.table or file name
    columns_involved = Column(Text)  # comma-separated column/file names
    categories = Column(Text)  # comma-separated category names
    explanation = Column(Text)
    sensitivity_level = Column(String(20))
    created_at = Column(DateTime, default=_utc_now)


class DataSourceInventory(Base):
    """
    Best-effort inventory of source technology/version/protocol for a scan target.

    Phase 1 scope: keep schema generic and additive so connectors can populate partially
    (unknown values are allowed). Hardening/CVE correlation can build on top later.
    """

    __tablename__ = "data_source_inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    target_name = Column(String(100), nullable=False)
    source_type = Column(String(40), nullable=False)  # database, api, bi, share, etc.
    product = Column(String(120), nullable=True)
    product_version = Column(String(120), nullable=True)
    protocol_or_api_version = Column(String(120), nullable=True)
    transport_security = Column(String(120), nullable=True)
    raw_details = Column(Text, nullable=True)  # JSON/text payload from connector probe
    created_at = Column(DateTime, default=_utc_now)


class ScanObjectState(Base):
    """Cross-session file identity index — Phase 2 of incremental scan (ADR-0051).

    One row per (target_name, abs_path); upserted after each filesystem finding.
    Enables cross-session diff queries: "which files changed since the last scan?"
    without scanning the full corpus again.

    NULL fields mean either the column was not collected (pre-Phase-1 row) or stat
    failed at scan time.  ``updated_at`` is refreshed on every upsert.
    """

    __tablename__ = "scan_object_state"
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_name = Column(String(100), nullable=False, index=True)
    abs_path = Column(String(512), nullable=False, index=True)
    last_session_id = Column(String(64), nullable=False)
    # File identity collected at the last scan (mirrors FilesystemFinding Phase 1 fields).
    mtime_ns = Column(BigInteger, nullable=True)
    size = Column(BigInteger, nullable=True)
    content_fingerprint = Column(String(16), nullable=True)
    last_sensitivity = Column(String(20), nullable=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    __table_args__ = (
        UniqueConstraint("target_name", "abs_path", name="uq_scan_object_path"),
    )


class WebAuthnCredential(Base):
    """
    One registered WebAuthn passkey for dashboard session auth (Phase 1, vendor-neutral RP).
    Single-operator deployments typically store one row; sign_count updates on each authentication.
    """

    __tablename__ = "webauthn_credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(LargeBinary(64), nullable=False, index=True)
    credential_id = Column(LargeBinary(512), nullable=False, unique=True)
    public_key = Column(LargeBinary(2048), nullable=False)
    sign_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utc_now)
    # JSON array of role names, e.g. ["reports_reader","dashboard"]. NULL = use config api.rbac.default_roles.
    roles_json = Column(String(512), nullable=True)


class MaturityAssessmentAnswer(Base):
    """
    One answer line for the organizational maturity self-assessment POC (GRC-style).
    Not scan findings; grouped by ``batch_id`` (one browser submit).
    ``row_hmac`` is HMAC-SHA256 (hex) when ``api.maturity_integrity_secret_from_env`` /
    ``DATA_BOAR_MATURITY_INTEGRITY_SECRET`` was set at write time; empty otherwise.
    """

    __tablename__ = "maturity_assessment_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=_utc_now)
    locale_slug = Column(String(32), nullable=False)
    pack_version = Column(Integer, nullable=False, default=1)
    question_id = Column(String(128), nullable=False)
    answer_text = Column(Text, nullable=False)
    row_hmac = Column(String(64), nullable=False, default="")


class LocalDBManager:
    """Single SQLite DB for all audit results; session id set externally (core.session)."""

    def __init__(self, db_path: str = "audit_results.db"):
        # NullPool so each connection is closed when returned (avoids ResourceWarning on Python 3.13+)
        self.engine = create_engine(f"sqlite:///{db_path}", poolclass=NullPool)
        Base.metadata.create_all(self.engine)
        self._ensure_aggregated_table()
        self._ensure_tenant_column()
        self._ensure_technician_column()
        self._ensure_config_scope_hash_column()
        self._ensure_jurisdiction_hint_column()
        self._ensure_data_source_inventory_table()
        self._ensure_notification_send_log_table()
        self._ensure_maturity_assessment_answers_table()
        self._ensure_maturity_row_hmac_column()
        self._ensure_webauthn_credentials_table()
        self._ensure_webauthn_roles_json_column()
        self._ensure_source_mtime_ns_column()
        self._ensure_source_size_column()
        self._ensure_content_fingerprint_column()
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._current_session_id: str | None = None

    def _ensure_tenant_column(self) -> None:
        """Add tenant_name column to scan_sessions if missing (migration for existing DBs)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('scan_sessions') WHERE name='tenant_name'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE scan_sessions ADD COLUMN tenant_name VARCHAR(255)"
                    )
                )
                conn.commit()

    def _ensure_technician_column(self) -> None:
        """Add technician_name column to scan_sessions if missing (migration for existing DBs)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('scan_sessions') WHERE name='technician_name'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE scan_sessions ADD COLUMN technician_name VARCHAR(255)"
                    )
                )
                conn.commit()

    def _ensure_config_scope_hash_column(self) -> None:
        """Add config_scope_hash column to scan_sessions if missing (migration for existing DBs)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('scan_sessions') WHERE name='config_scope_hash'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE scan_sessions ADD COLUMN config_scope_hash VARCHAR(64)"
                    )
                )
                conn.commit()

    def _ensure_jurisdiction_hint_column(self) -> None:
        """Add jurisdiction_hint column to scan_sessions if missing (migration)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('scan_sessions') WHERE name='jurisdiction_hint'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE scan_sessions ADD COLUMN jurisdiction_hint INTEGER DEFAULT 0"
                    )
                )
                conn.commit()

    def _ensure_aggregated_table(self) -> None:
        """Create aggregated_identification_risk table if it does not exist."""
        AggregatedIdentificationRisk.__table__.create(self.engine, checkfirst=True)

    def _ensure_data_source_inventory_table(self) -> None:
        """Create data_source_inventory table if it does not exist."""
        DataSourceInventory.__table__.create(self.engine, checkfirst=True)

    def _ensure_notification_send_log_table(self) -> None:
        """Create notification_send_log table if it does not exist (additive migration)."""
        NotificationSendLog.__table__.create(self.engine, checkfirst=True)

    def _ensure_maturity_assessment_answers_table(self) -> None:
        """Create maturity_assessment_answers table if it does not exist (additive migration)."""
        MaturityAssessmentAnswer.__table__.create(self.engine, checkfirst=True)

    def _ensure_maturity_row_hmac_column(self) -> None:
        """Add row_hmac column for tamper-evident MAC (additive migration)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('maturity_assessment_answers') "
                    "WHERE name='row_hmac'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE maturity_assessment_answers "
                        "ADD COLUMN row_hmac VARCHAR(64) DEFAULT '' NOT NULL"
                    )
                )
                conn.commit()

    def _ensure_webauthn_credentials_table(self) -> None:
        """Create webauthn_credentials table if missing (additive migration)."""
        WebAuthnCredential.__table__.create(self.engine, checkfirst=True)

    def _ensure_webauthn_roles_json_column(self) -> None:
        """Add roles_json column for RBAC (#86 Phase 2) when missing."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('webauthn_credentials') "
                    "WHERE name='roles_json'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE webauthn_credentials ADD COLUMN roles_json VARCHAR(512)"
                    )
                )
                conn.commit()

    def _ensure_source_mtime_ns_column(self) -> None:
        """Add source_mtime_ns to filesystem_findings if missing (Phase 1 migration)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('filesystem_findings') "
                    "WHERE name='source_mtime_ns'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE filesystem_findings "
                        "ADD COLUMN source_mtime_ns BIGINT"
                    )
                )
                conn.commit()

    def _ensure_source_size_column(self) -> None:
        """Add source_size to filesystem_findings if missing (Phase 1 migration)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('filesystem_findings') "
                    "WHERE name='source_size'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE filesystem_findings ADD COLUMN source_size BIGINT"
                    )
                )
                conn.commit()

    def _ensure_content_fingerprint_column(self) -> None:
        """Add content_fingerprint to filesystem_findings if missing (Phase 1 migration)."""
        with self.engine.connect() as conn:
            r = conn.execute(
                text(
                    "SELECT 1 FROM pragma_table_info('filesystem_findings') "
                    "WHERE name='content_fingerprint'"
                )
            )
            if r.fetchone() is None:
                conn.execute(
                    text(
                        "ALTER TABLE filesystem_findings "
                        "ADD COLUMN content_fingerprint VARCHAR(16)"
                    )
                )
                conn.commit()

    def webauthn_credential_count(self) -> int:
        """Return number of registered WebAuthn credentials."""
        session = self._session_factory()
        try:
            return int(session.query(func.count(WebAuthnCredential.id)).scalar() or 0)
        finally:
            session.close()

    def webauthn_list_credentials(self) -> list[dict[str, object]]:
        """Return all credentials for authentication allowCredentials."""
        session = self._session_factory()
        try:
            rows = session.query(WebAuthnCredential).all()
            out: list[dict[str, object]] = []
            for r in rows:
                out.append(
                    {
                        "credential_id": bytes(r.credential_id),
                        "public_key": bytes(r.public_key),
                        "sign_count": int(r.sign_count),
                        "user_id": bytes(r.user_id),
                    }
                )
            return out
        finally:
            session.close()

    def webauthn_save_credential(
        self,
        *,
        user_id: bytes,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
    ) -> None:
        """Persist a verified registration credential."""
        uid = user_id[:64]
        cid = credential_id[:512]
        pk = public_key[:2048]
        sc = int(sign_count)
        session = self._session_factory()
        try:
            row = WebAuthnCredential(
                user_id=uid,
                credential_id=cid,
                public_key=pk,
                sign_count=sc,
            )
            session.add(row)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def webauthn_update_sign_count(self, credential_id: bytes, new_count: int) -> None:
        """Update sign_count after successful authentication."""
        cid = credential_id[:512]
        session = self._session_factory()
        try:
            row = (
                session.query(WebAuthnCredential)
                .filter(WebAuthnCredential.credential_id == cid)
                .one_or_none()
            )
            if row is None:
                return
            row.sign_count = int(new_count)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def webauthn_roles_json_for_user_id(self, user_id: bytes) -> str | None:
        """Return stored ``roles_json`` for the WebAuthn user id, or None if unknown / unset."""
        uid = user_id[:64]
        session = self._session_factory()
        try:
            row = (
                session.query(WebAuthnCredential)
                .filter(WebAuthnCredential.user_id == uid)
                .one_or_none()
            )
            if row is None:
                return None
            rj = row.roles_json
            if rj is None:
                return None
            s = str(rj).strip()
            return s if s else None
        finally:
            session.close()

    def save_maturity_assessment_answers(
        self,
        *,
        batch_id: str,
        locale_slug: str,
        pack_version: int,
        answers: dict[str, str],
        integrity_secret: bytes | None = None,
    ) -> None:
        """Persist questionnaire answers for one submit. Skips when ``answers`` is empty."""
        if not answers:
            return
        from core.maturity_assessment.integrity import compute_answer_hmac

        bid = (batch_id or "")[:64]
        loc = (locale_slug or "")[:32]
        pv = int(pack_version)
        session = self._session_factory()
        try:
            for qid, answer_text in answers.items():
                qkey = (qid or "")[:128]
                if not qkey:
                    continue
                atext = (answer_text or "")[:4000]
                mac = ""
                if integrity_secret:
                    mac = compute_answer_hmac(
                        integrity_secret,
                        batch_id=bid,
                        locale_slug=loc,
                        pack_version=pv,
                        question_id=qkey,
                        answer_text=atext,
                    )
                row = MaturityAssessmentAnswer(
                    batch_id=bid,
                    locale_slug=loc,
                    pack_version=pv,
                    question_id=qkey,
                    answer_text=atext,
                    row_hmac=mac,
                )
                session.add(row)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def maturity_assessment_rows_for_integrity(self) -> list[dict[str, object]]:
        """Return all maturity answer rows as dicts for HMAC verification."""
        session = self._session_factory()
        try:
            rows = session.query(MaturityAssessmentAnswer).all()
            return self._maturity_rows_to_integrity_dicts(rows)
        finally:
            session.close()

    def maturity_assessment_rows_for_integrity_batch(
        self, batch_id: str
    ) -> list[dict[str, object]]:
        """Return maturity answer rows for one ``batch_id`` (submit batch) for HMAC verification."""
        bid = (batch_id or "")[:64]
        session = self._session_factory()
        try:
            rows = (
                session.query(MaturityAssessmentAnswer)
                .filter(MaturityAssessmentAnswer.batch_id == bid)
                .all()
            )
            return self._maturity_rows_to_integrity_dicts(rows)
        finally:
            session.close()

    @staticmethod
    def _maturity_rows_to_integrity_dicts(
        rows: list[MaturityAssessmentAnswer],
    ) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for r in rows:
            out.append(
                {
                    "batch_id": r.batch_id,
                    "locale_slug": r.locale_slug,
                    "pack_version": r.pack_version,
                    "question_id": r.question_id,
                    "answer_text": r.answer_text,
                    "row_hmac": r.row_hmac or "",
                }
            )
        return out

    def verify_maturity_assessment_integrity(self, secret: bytes | None) -> dict:
        """Recompute HMACs and compare to stored ``row_hmac`` (see ``integrity.verify_maturity_assessment_rows``)."""
        from core.maturity_assessment.integrity import verify_maturity_assessment_rows

        rows = self.maturity_assessment_rows_for_integrity()
        return verify_maturity_assessment_rows(secret=secret, rows=rows)

    def count_maturity_assessment_answers(self) -> int:
        """Row count for tests / diagnostics."""
        session = self._session_factory()
        try:
            return session.query(MaturityAssessmentAnswer).count()
        finally:
            session.close()

    def maturity_assessment_batch_summaries(
        self, *, limit: int = 50
    ) -> list[dict[str, object]]:
        """
        One row per distinct ``batch_id`` (newest submit first): time, locale, pack version, answer rows.

        Used for POC dashboard history; cap ``limit`` to keep the HTML table bounded.
        """
        cap = max(1, min(int(limit), 500))
        session = self._session_factory()
        try:
            q = (
                session.query(
                    MaturityAssessmentAnswer.batch_id,
                    func.min(MaturityAssessmentAnswer.created_at).label("submitted_at"),
                    func.count(MaturityAssessmentAnswer.id).label("answer_count"),
                    func.max(MaturityAssessmentAnswer.locale_slug).label("locale_slug"),
                    func.max(MaturityAssessmentAnswer.pack_version).label(
                        "pack_version"
                    ),
                )
                .group_by(MaturityAssessmentAnswer.batch_id)
                .order_by(desc(func.min(MaturityAssessmentAnswer.created_at)))
                .limit(cap)
            )
            out: list[dict[str, object]] = []
            for row in q.all():
                out.append(
                    {
                        "batch_id": str(row.batch_id),
                        "submitted_at": row.submitted_at,
                        "answer_count": int(row.answer_count),
                        "locale_slug": str(row.locale_slug),
                        "pack_version": int(row.pack_version),
                    }
                )
            return out
        finally:
            session.close()

    def record_notification_send_log(
        self,
        *,
        session_id: str | None,
        trigger: str,
        recipient: str,
        channel: str | None,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """
        Persist one outbound notification attempt. Safe to call from notify path; failures are swallowed.
        """
        from core.validation import sanitize_log_text

        err_stored: str | None = None
        if error_message:
            err_stored = sanitize_log_text(error_message)[:500]

        session = self._session_factory()
        try:
            row = NotificationSendLog(
                session_id=session_id or None,
                trigger=trigger[:32],
                recipient=recipient[:16],
                channel=(channel[:32] if channel else None),
                success=bool(success),
                error_summary=err_stored,
            )
            session.add(row)
            session.commit()
        except Exception:
            session.rollback()
            # Do not break scan/notify flow if audit insert fails
        finally:
            session.close()

    def set_current_session_id(self, session_id: str) -> None:
        self._current_session_id = session_id

    @property
    def current_session_id(self) -> str:
        return self._current_session_id or ""

    # --- Helpers for rate limiting and session state ---

    def get_running_sessions_count(self) -> int:
        """Return the number of sessions currently marked as running."""
        session = self._session_factory()
        try:
            return (
                session.query(ScanSession)
                .filter(ScanSession.status == "running")
                .count()
            )
        finally:
            session.close()

    def get_last_session(self) -> dict | None:
        """
        Return the most recent session by started_at (or None).
        Dict contains session_id, started_at (datetime) and status.
        """
        session = self._session_factory()
        try:
            s = (
                session.query(ScanSession)
                .order_by(ScanSession.started_at.desc())
                .first()
            )
            if not s:
                return None
            return {
                "session_id": s.session_id,
                "started_at": s.started_at,
                "status": s.status,
            }
        finally:
            session.close()

    def save_finding(self, source_type: str, **kwargs: Any) -> None:
        sid = self._current_session_id
        if not sid:
            return
        session = self._session_factory()
        try:
            if source_type == "database":
                kwargs["session_id"] = sid
                finding = DatabaseFinding(
                    **{k: v for k, v in kwargs.items() if hasattr(DatabaseFinding, k)}
                )
                session.add(finding)
            elif source_type == "filesystem":
                kwargs["session_id"] = sid
                finding = FilesystemFinding(
                    **{k: v for k, v in kwargs.items() if hasattr(FilesystemFinding, k)}
                )
                session.add(finding)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def upsert_object_state(
        self,
        target_name: str,
        abs_path: str,
        session_id: str,
        mtime_ns: int | None,
        size: int | None,
        content_fingerprint: str | None,
        sensitivity_level: str | None,
    ) -> None:
        """Upsert one row in scan_object_state (cross-session file identity index).

        Uses SQLite ``INSERT OR REPLACE`` semantics: if a row with the same
        ``(target_name, abs_path)`` exists it is replaced; otherwise inserted.
        This is Phase 2 of the incremental scan plan (ADR-0051).
        """
        session = self._session_factory()
        try:
            existing = (
                session.query(ScanObjectState)
                .filter_by(target_name=target_name, abs_path=abs_path)
                .first()
            )
            if existing is not None:
                existing.last_session_id = session_id
                existing.mtime_ns = mtime_ns
                existing.size = size
                existing.content_fingerprint = content_fingerprint
                existing.last_sensitivity = sensitivity_level
                existing.updated_at = _utc_now()
            else:
                session.add(
                    ScanObjectState(
                        target_name=target_name,
                        abs_path=abs_path,
                        last_session_id=session_id,
                        mtime_ns=mtime_ns,
                        size=size,
                        content_fingerprint=content_fingerprint,
                        last_sensitivity=sensitivity_level,
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_object_state(
        self,
        target_name: str,
        abs_path: str,
    ) -> dict[str, Any] | None:
        """Return the latest identity record for (target_name, abs_path), or None.

        Used by Phase 3 (short-circuit) to check if a file changed since the last scan.
        """
        session = self._session_factory()
        try:
            row = (
                session.query(ScanObjectState)
                .filter_by(target_name=target_name, abs_path=abs_path)
                .first()
            )
            if row is None:
                return None
            return {
                "target_name": row.target_name,
                "abs_path": row.abs_path,
                "last_session_id": row.last_session_id,
                "mtime_ns": row.mtime_ns,
                "size": row.size,
                "content_fingerprint": row.content_fingerprint,
                "last_sensitivity": row.last_sensitivity,
                "updated_at": row.updated_at,
            }
        finally:
            session.close()

    def save_failure(
        self, target_name: str, reason: str, details: str | None = None
    ) -> None:
        sid = self._current_session_id
        if not sid:
            return
        from core.validation import sanitize_log_text

        # Same redaction for log line and SQLite (drivers/httpx may embed SQL or bodies in str(e)).
        stored_details = sanitize_log_text((details or "").strip())[:10000]
        # Best-effort logging: mirror failures into the unified audit log so operators
        # can see which target was skipped and why.
        try:
            from utils.logger import get_logger

            logger = get_logger()
            logger.error(
                "Scan failure: session=%s target=%s reason=%s details=%s",
                sid,
                target_name,
                reason,
                stored_details,
            )
        except Exception:
            # Logging must not break persistence.
            pass
        session = self._session_factory()
        try:
            session.add(
                ScanFailure(
                    session_id=sid,
                    target_name=target_name,
                    reason=reason,
                    details=stored_details,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_findings(
        self, session_id: str | None = None
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Return (database_findings, filesystem_findings, failures) for session_id or current."""
        sid = session_id or self._current_session_id
        if not sid:
            return [], [], []
        session = self._session_factory()
        try:
            db_rows = (
                session.query(DatabaseFinding)
                .filter(DatabaseFinding.session_id == sid)
                .all()
            )
            fs_rows = (
                session.query(FilesystemFinding)
                .filter(FilesystemFinding.session_id == sid)
                .all()
            )
            fail_rows = (
                session.query(ScanFailure).filter(ScanFailure.session_id == sid).all()
            )

            def db_to_dict(r):
                return {c.key: getattr(r, c.key) for c in r.__table__.columns}

            return (
                [db_to_dict(r) for r in db_rows],
                [db_to_dict(r) for r in fs_rows],
                [db_to_dict(r) for r in fail_rows],
            )
        finally:
            session.close()

    def _session_exists(self, session_id: str) -> bool:
        sid = (session_id or "").strip()
        if not sid:
            return False
        session = self._session_factory()
        try:
            return (
                session.query(ScanSession).filter(ScanSession.session_id == sid).first()
                is not None
            )
        finally:
            session.close()

    def diff_sessions(self, session_a: str, session_b: str) -> dict[str, Any]:
        """Return new/resolved/changed findings between two scan sessions."""
        a = (session_a or "").strip()
        b = (session_b or "").strip()
        if not self._session_exists(a):
            raise ValueError(f"Unknown session: {a}")
        if not self._session_exists(b):
            raise ValueError(f"Unknown session: {b}")

        def _db_key(f: DatabaseFinding) -> tuple:
            return (
                f.target_name,
                f.schema_name,
                f.table_name,
                f.column_name,
                f.pattern_detected,
            )

        def _fs_key(f: FilesystemFinding) -> tuple:
            return (f.target_name, f.path, f.file_name, f.pattern_detected)

        session = self._session_factory()
        try:
            db_a = {
                _db_key(f): f
                for f in session.query(DatabaseFinding)
                .filter(DatabaseFinding.session_id == a)
                .all()
            }
            db_b = {
                _db_key(f): f
                for f in session.query(DatabaseFinding)
                .filter(DatabaseFinding.session_id == b)
                .all()
            }
            fs_a = {
                _fs_key(f): f
                for f in session.query(FilesystemFinding)
                .filter(FilesystemFinding.session_id == a)
                .all()
            }
            fs_b = {
                _fs_key(f): f
                for f in session.query(FilesystemFinding)
                .filter(FilesystemFinding.session_id == b)
                .all()
            }
        finally:
            session.close()

        def _diff(dict_a: dict, dict_b: dict) -> tuple[dict, dict, dict]:
            new = {k: dict_b[k] for k in dict_b if k not in dict_a}
            resolved = {k: dict_a[k] for k in dict_a if k not in dict_b}
            changed = {
                k: (dict_a[k], dict_b[k])
                for k in dict_a
                if k in dict_b
                and (dict_a[k].sensitivity_level or "")
                != (dict_b[k].sensitivity_level or "")
            }
            return new, resolved, changed

        db_new, db_resolved, db_changed = _diff(db_a, db_b)
        fs_new, fs_resolved, fs_changed = _diff(fs_a, fs_b)

        new_high_count = sum(
            1
            for f in list(db_new.values()) + list(fs_new.values())
            if (f.sensitivity_level or "").upper() == "HIGH"
        )

        return {
            "session_a": a,
            "session_b": b,
            "database": {
                "new": db_new,
                "resolved": db_resolved,
                "changed": db_changed,
            },
            "filesystem": {
                "new": fs_new,
                "resolved": fs_resolved,
                "changed": fs_changed,
            },
            "new_high_count": new_high_count,
        }

    def get_session_scan_summary_for_notification(
        self, session_id: str
    ) -> dict[str, Any]:
        """
        Aggregate counts for operator scan-complete notifications (brief text, not full export).

        sensitivity_level buckets: HIGH, MEDIUM, LOW. DOB_POSSIBLE_MINOR counts pattern_detected matches.
        """
        sid = (session_id or "").strip()
        out: dict[str, Any] = {
            "session_id": sid,
            "status": "unknown",
            "tenant_name": None,
            "technician_name": None,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total_findings": 0,
            "dob_possible_minor": 0,
            "scan_failures": 0,
        }
        if not sid:
            return out
        session = self._session_factory()
        try:
            rec = (
                session.query(ScanSession).filter(ScanSession.session_id == sid).first()
            )
            if rec:
                out["status"] = (rec.status or "unknown").strip()
                out["tenant_name"] = rec.tenant_name
                out["technician_name"] = rec.technician_name
            buckets = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for model in (DatabaseFinding, FilesystemFinding):
                rows = (
                    session.query(model.sensitivity_level, func.count(model.id))
                    .filter(model.session_id == sid)
                    .group_by(model.sensitivity_level)
                    .all()
                )
                for lev, cnt in rows:
                    k = (lev or "").strip().upper()
                    if k in buckets:
                        buckets[k] += int(cnt)
            out["high"] = buckets["HIGH"]
            out["medium"] = buckets["MEDIUM"]
            out["low"] = buckets["LOW"]
            out["total_findings"] = out["high"] + out["medium"] + out["low"]
            dob_db = (
                session.query(func.count(DatabaseFinding.id))
                .filter(
                    DatabaseFinding.session_id == sid,
                    DatabaseFinding.pattern_detected.like("%DOB_POSSIBLE_MINOR%"),
                )
                .scalar()
            )
            dob_fs = (
                session.query(func.count(FilesystemFinding.id))
                .filter(
                    FilesystemFinding.session_id == sid,
                    FilesystemFinding.pattern_detected.like("%DOB_POSSIBLE_MINOR%"),
                )
                .scalar()
            )
            out["dob_possible_minor"] = int(dob_db or 0) + int(dob_fs or 0)
            fail_n = (
                session.query(func.count(ScanFailure.id))
                .filter(ScanFailure.session_id == sid)
                .scalar()
            )
            out["scan_failures"] = int(fail_n or 0)
            return out
        finally:
            session.close()

    def save_aggregated_identification_risks(
        self,
        session_id: str,
        records: list[dict[str, Any]],
    ) -> None:
        """Replace aggregated identification risk rows for this session with the given records."""
        sess = self._session_factory()
        try:
            sess.query(AggregatedIdentificationRisk).filter(
                AggregatedIdentificationRisk.session_id == session_id,
            ).delete(synchronize_session=False)
            for rec in records:
                row = AggregatedIdentificationRisk(
                    session_id=session_id,
                    target_name=rec.get("target_name"),
                    source_type=rec.get("source_type"),
                    table_or_file=rec.get("table_or_file"),
                    columns_involved=rec.get("columns_involved"),
                    categories=rec.get("categories"),
                    explanation=rec.get("explanation"),
                    sensitivity_level=rec.get("sensitivity_level"),
                )
                sess.add(row)
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    def save_data_source_inventory(
        self,
        target_name: str,
        source_type: str,
        product: str | None = None,
        product_version: str | None = None,
        protocol_or_api_version: str | None = None,
        transport_security: str | None = None,
        raw_details: str | None = None,
    ) -> None:
        """Persist one inventory row for the current session (best effort metadata)."""
        sid = self._current_session_id
        if not sid:
            return
        sess = self._session_factory()
        try:
            sess.add(
                DataSourceInventory(
                    session_id=sid,
                    target_name=target_name,
                    source_type=source_type,
                    product=product,
                    product_version=product_version,
                    protocol_or_api_version=protocol_or_api_version,
                    transport_security=transport_security,
                    raw_details=raw_details,
                )
            )
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    def get_data_source_inventory(self, session_id: str | None = None) -> list[dict]:
        """Return inventory rows for session_id or current session."""
        sid = session_id or self._current_session_id
        if not sid:
            return []
        sess = self._session_factory()
        try:
            rows = (
                sess.query(DataSourceInventory)
                .filter(DataSourceInventory.session_id == sid)
                .all()
            )
            return [
                {
                    c.key: getattr(r, c.key)
                    for c in DataSourceInventory.__table__.columns
                }
                for r in rows
            ]
        finally:
            sess.close()

    def get_aggregated_identification_risks(
        self, session_id: str | None = None
    ) -> list[dict]:
        """Return aggregated identification risk rows for session_id or current session."""
        sid = session_id or self._current_session_id
        if not sid:
            return []
        sess = self._session_factory()
        try:
            rows = (
                sess.query(AggregatedIdentificationRisk)
                .filter(
                    AggregatedIdentificationRisk.session_id == sid,
                )
                .all()
            )
            return [
                {
                    c.key: getattr(r, c.key)
                    for c in AggregatedIdentificationRisk.__table__.columns
                }
                for r in rows
            ]
        finally:
            sess.close()

    def list_sessions(self) -> list[dict]:
        """List all scan sessions with summary (session_id, started_at, status, counts including scan_failures)."""
        session = self._session_factory()
        try:
            sessions = (
                session.query(ScanSession).order_by(ScanSession.started_at.desc()).all()
            )
            out = []
            for s in sessions:
                db_count = (
                    session.query(DatabaseFinding)
                    .filter(DatabaseFinding.session_id == s.session_id)
                    .count()
                )
                fs_count = (
                    session.query(FilesystemFinding)
                    .filter(FilesystemFinding.session_id == s.session_id)
                    .count()
                )
                fail_count = (
                    session.query(ScanFailure)
                    .filter(ScanFailure.session_id == s.session_id)
                    .count()
                )
                out.append(
                    {
                        "session_id": s.session_id,
                        "started_at": s.started_at.isoformat()
                        if s.started_at
                        else None,
                        "finished_at": s.finished_at.isoformat()
                        if s.finished_at
                        else None,
                        "status": s.status,
                        "tenant_name": getattr(s, "tenant_name", None),
                        "technician_name": getattr(s, "technician_name", None),
                        "config_scope_hash": getattr(s, "config_scope_hash", None),
                        "jurisdiction_hint": bool(getattr(s, "jurisdiction_hint", 0)),
                        "database_findings": db_count,
                        "filesystem_findings": fs_count,
                        "scan_failures": fail_count,
                    }
                )
            return out
        finally:
            session.close()

    def get_previous_session(self, session_id: str) -> dict | None:
        """
        Return the session immediately before the given one (by started_at desc), for trend comparison.
        Returns dict with session_id, started_at, database_findings, filesystem_findings, scan_failures, or None.
        """
        prev_list = self.get_previous_sessions(session_id, limit=1)
        return prev_list[0] if prev_list else None

    def get_previous_sessions(self, session_id: str, limit: int = 3) -> list[dict]:
        """
        Return up to `limit` sessions immediately before the given one (by started_at desc), for trend comparison.
        Most recent previous session first. Each dict has session_id, started_at, database_findings,
        filesystem_findings, scan_failures.
        """
        sessions = self.list_sessions()
        for i, s in enumerate(sessions):
            if s["session_id"] == session_id:
                return sessions[i + 1 : i + 1 + limit]
        return []

    def create_session_record(
        self,
        session_id: str,
        tenant_name: str | None = None,
        technician_name: str | None = None,
        config_scope_hash: str | None = None,
        jurisdiction_hint: bool = False,
    ) -> None:
        """Create a scan_sessions row. Optional tenant_name, technician_name, config_scope_hash, jurisdiction_hint."""
        session = self._session_factory()
        try:
            session.add(
                ScanSession(
                    session_id=session_id,
                    status="running",
                    tenant_name=(tenant_name or None),
                    technician_name=(technician_name or None),
                    config_scope_hash=(config_scope_hash or None),
                    jurisdiction_hint=1 if jurisdiction_hint else 0,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_session_config_scope_hash(
        self, session_id: str, config_scope_hash: str | None
    ) -> None:
        """Set or clear config_scope_hash for an existing session."""
        session = self._session_factory()
        try:
            rec = (
                session.query(ScanSession)
                .filter(ScanSession.session_id == session_id)
                .first()
            )
            if rec and hasattr(rec, "config_scope_hash"):
                rec.config_scope_hash = config_scope_hash or None
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_session_tenant(self, session_id: str, tenant_name: str | None) -> None:
        """Set or clear tenant_name for an existing session."""
        session = self._session_factory()
        try:
            rec = (
                session.query(ScanSession)
                .filter(ScanSession.session_id == session_id)
                .first()
            )
            if rec:
                rec.tenant_name = tenant_name or None
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_session_technician(
        self, session_id: str, technician_name: str | None
    ) -> None:
        """Set or clear technician_name for an existing session."""
        session = self._session_factory()
        try:
            rec = (
                session.query(ScanSession)
                .filter(ScanSession.session_id == session_id)
                .first()
            )
            if rec:
                rec.technician_name = technician_name or None
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def finish_session(self, session_id: str, status: str = "completed") -> None:
        session = self._session_factory()
        try:
            rec = (
                session.query(ScanSession)
                .filter(ScanSession.session_id == session_id)
                .first()
            )
            if rec:
                rec.finished_at = datetime.now(timezone.utc)
                rec.status = status
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_current_findings_count(self) -> int:
        sid = self._current_session_id
        if not sid:
            return 0
        session = self._session_factory()
        try:
            db_c = (
                session.query(DatabaseFinding)
                .filter(DatabaseFinding.session_id == sid)
                .count()
            )
            fs_c = (
                session.query(FilesystemFinding)
                .filter(FilesystemFinding.session_id == sid)
                .count()
            )
            return db_c + fs_c
        finally:
            session.close()

    def list_data_wipe_log_entries(self) -> list[dict[str, Any]]:
        """Return all rows from data_wipe_log (newest last), ISO timestamps, for audit export."""
        session = self._session_factory()
        try:
            rows = session.query(DataWipeLog).order_by(DataWipeLog.id.asc()).all()
            out: list[dict[str, Any]] = []
            for r in rows:
                wiped = r.wiped_at
                out.append(
                    {
                        "id": r.id,
                        "wiped_at": wiped.isoformat() if wiped else None,
                        "reason": r.reason,
                    }
                )
            return out
        finally:
            session.close()

    def get_scan_sessions_summary(self) -> dict[str, Any]:
        """Aggregate counts for audit export (sessions may be empty after a wipe)."""
        session = self._session_factory()
        try:
            n = session.query(ScanSession).count()
            if n == 0:
                return {
                    "count": 0,
                    "first_started_at": None,
                    "last_started_at": None,
                }
            first = (
                session.query(ScanSession)
                .order_by(ScanSession.started_at.asc())
                .first()
            )
            last = (
                session.query(ScanSession)
                .order_by(ScanSession.started_at.desc())
                .first()
            )
            fa = first.started_at if first else None
            la = last.started_at if last else None
            return {
                "count": n,
                "first_started_at": fa.isoformat() if fa else None,
                "last_started_at": la.isoformat() if la else None,
            }
        finally:
            session.close()

    def wipe_all_data(self, reason: str) -> None:
        """
        Delete all scan sessions and findings from the SQLite database, but keep an audit entry
        in data_wipe_log so there is a record of when and why the wipe happened.
        Intended to be called from maintenance/CLI tooling (e.g. --reset-data).

        Rows in ``data_wipe_log`` are **append-only** (never deleted here). Future
        integrity/audit tables (see PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY) must also
        be preserved by this method unless a separate explicit maintenance flag exists.
        """
        session = self._session_factory()
        try:
            # Delete findings and failures for all sessions
            session.query(DatabaseFinding).delete(synchronize_session=False)
            session.query(FilesystemFinding).delete(synchronize_session=False)
            session.query(AggregatedIdentificationRisk).delete(
                synchronize_session=False
            )
            session.query(DataSourceInventory).delete(synchronize_session=False)
            session.query(ScanFailure).delete(synchronize_session=False)
            # Delete all scan session rows
            session.query(ScanSession).delete(synchronize_session=False)
            session.query(MaturityAssessmentAnswer).delete(synchronize_session=False)
            session.query(WebAuthnCredential).delete(synchronize_session=False)
            # Record the wipe event itself
            session.add(DataWipeLog(reason=reason))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Release engine connections. Call when done with the manager (e.g. in tests)."""
        self.engine.dispose()
