-- Data Boar findings sink DDL (#552)
-- Customer-owned store: create these objects before enabling findings_sink.
-- SQLite remains the engine primary; this schema is the echo target only.
-- Default contract is metadata-only. Do NOT add sample_content unless Legal
-- signed off (LGPD Art. 46). The product refuses sample export on the CLI
-- unless --allow-sample-export is passed.

-- ---------------------------------------------------------------------------
-- PostgreSQL
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS data_boar_sessions (
    session_id       TEXT PRIMARY KEY,
    started_at       TIMESTAMPTZ,
    finished_at      TIMESTAMPTZ,
    tool_version     TEXT,
    config_hash      TEXT,
    total_findings   INTEGER,
    exported_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_boar_findings (
    id               BIGSERIAL PRIMARY KEY,
    session_id       TEXT REFERENCES data_boar_sessions(session_id),
    source_type      TEXT NOT NULL DEFAULT '',  -- database | filesystem | application
    target_name      TEXT NOT NULL DEFAULT '',
    schema_name      TEXT,
    table_name       TEXT NOT NULL DEFAULT '',
    column_name      TEXT NOT NULL DEFAULT '',
    file_path        TEXT NOT NULL DEFAULT '',
    file_name        TEXT,
    pattern_detected TEXT,
    norm_tag         TEXT,
    occurrences      INTEGER,
    risk_level       TEXT,
    UNIQUE (session_id, source_type, target_name, table_name, column_name, file_path)
);

-- Optional (explicit legal sign-off only):
-- ALTER TABLE data_boar_findings ADD COLUMN sample_content TEXT;

-- ---------------------------------------------------------------------------
-- MySQL / MariaDB
-- ---------------------------------------------------------------------------
-- DATETIME (no TIMESTAMPTZ). Empty strings stand in for NULL on UNIQUE keys
-- so conflict detection is stable across engines.

-- CREATE TABLE IF NOT EXISTS data_boar_sessions (
--     session_id       VARCHAR(64) PRIMARY KEY,
--     started_at       DATETIME NULL,
--     finished_at      DATETIME NULL,
--     tool_version     VARCHAR(64) NULL,
--     config_hash      VARCHAR(64) NULL,
--     total_findings   INT NULL,
--     exported_at      DATETIME DEFAULT CURRENT_TIMESTAMP
-- );
--
-- CREATE TABLE IF NOT EXISTS data_boar_findings (
--     id               BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
--     session_id       VARCHAR(64) NULL,
--     source_type      VARCHAR(32) NOT NULL DEFAULT '',
--     target_name      VARCHAR(255) NOT NULL DEFAULT '',
--     schema_name      VARCHAR(255) NULL,
--     table_name       VARCHAR(255) NOT NULL DEFAULT '',
--     column_name      VARCHAR(255) NOT NULL DEFAULT '',
--     file_path        VARCHAR(1024) NOT NULL DEFAULT '',
--     file_name        VARCHAR(255) NULL,
--     pattern_detected VARCHAR(255) NULL,
--     norm_tag         VARCHAR(255) NULL,
--     occurrences      INT NULL,
--     risk_level       VARCHAR(32) NULL,
--     UNIQUE KEY uq_data_boar_finding (
--         session_id, source_type, target_name, table_name, column_name, file_path(255)
--     ),
--     CONSTRAINT fk_data_boar_findings_session
--         FOREIGN KEY (session_id) REFERENCES data_boar_sessions(session_id)
-- );
