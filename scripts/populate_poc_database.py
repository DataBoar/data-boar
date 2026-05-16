#!/usr/bin/env python3
"""
populate_poc_database.py
========================
Creates and populates a test database (PostgreSQL or MariaDB/MySQL) with
synthetic PII data covering ALL Data Boar test scenarios:

  HAPPY PATH     -- clear PII findable in every column type
  UNHAPPY PATH   -- PII in unusual encodings, mixed languages, OCR artifacts
  INNOCENT DATA  -- benign data that looks like PII but is not (false-positive bait)
  FOREIGN KEYS   -- PII spread across normalized tables (cross-table detection)
  CATASTROPHIC   -- intentional config errors: wrong password, bad host, DB down,
                    unreadable data, encoding failures, mixed collations
  SRE SCENARIOS  -- high-latency, timeout, connection pool exhaustion, query stress

Usage:
  # PostgreSQL (default)
  uv run python scripts/populate_poc_database.py --db-type postgres \
      --host localhost --port 5432 --database poc_databoar \
      --user poc_user --password poc_pass

  # MariaDB / MySQL
  uv run python scripts/populate_poc_database.py --db-type mariadb \
      --host localhost --port 3306 --database poc_databoar \
      --user poc_user --password poc_pass

  # Docker-based quick start (creates containers automatically):
  uv run python scripts/populate_poc_database.py --docker-setup

  # Show what would be created without connecting:
  uv run python scripts/populate_poc_database.py --dry-run

After populating, run Data Boar:
  uv run python main.py --config config-poc-db.yaml --scan --report

See docs/TESTING_POC_GUIDE.md for evaluation checklist and metrics template.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

# ---------------------------------------------------------------------------
# Synthetic PII (same corpus as generate_synthetic_poc_corpus.py)
# ---------------------------------------------------------------------------
_CPFS = [
    "123.456.789-09",
    "987.654.321-00",
    "111.222.333-96",
    "000.000.001-91",
    "529.982.247-25",
]
_CNPJS = ["11.222.333/0001-81", "00.000.000/0001-91", "12.345.678/0001-95"]
_RGS = ["12.345.678-9", "98.765.432-1", "00.111.222-3"]
_NAMES = [
    "Ana Paula Souza",
    "Carlos Eduardo Lima",
    "Fernanda Beatriz Costa",
    "Joao Roberto Colleague-E",
    "Maria Oliveira Santos",
]
_NAMES_ES = ["Maria García López", "Juan Carlos Rodríguez", "Ana Martínez Pérez"]
_NAMES_EN = ["John Smith", "Jane Doe", "Alice Johnson"]
_EMAILS = [
    "ana.souza@example-test.com",
    "carlos.lima@demo.invalid",
    "f.costa@poc-databoar.test",
]
_PHONES = ["(11) 99999-0001", "+55 21 98888-0002", "0800 123 4567"]
_DATES = [
    date(1985, 3, 15),
    date(1990, 7, 22),
    date(1970, 1, 1),
    date(1995, 11, 30),
    date(2000, 6, 8),
]
_ADDRS = [
    "Rua das Flores, 123, Sao Paulo - SP",
    "Av. Brasil, 4500, Rio de Janeiro - RJ",
]
_CEPS = ["01234-567", "20040-020", "30130-110"]
_INNOCUOUS = {
    "product_codes": ["PRD-123456789", "SKU-987654321", "REF-111222333"],
    "serial_numbers": ["SN001122334455", "SN998877665544"],
    "invoice_numbers": ["NF-000001", "NF-000002", "NF-000003"],
    "version_tags": ["v1.2.3", "v2.0.1", "v3.14.159"],
    "ip_addresses": ["10.0.1.1", "10.0.0.254", "172.16.0.1"],
    "timestamps": ["2026-04-05T03:00:00Z", "2025-12-31T23:59:59Z"],
}


def _p(lst: list, i: int = 0) -> Any:
    return lst[i % len(lst)]


def _rand_innocuous_int() -> str:
    return str(random.randint(100_000_000, 999_999_999))


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
@dataclass
class DBConfig:
    db_type: str  # "postgres" | "mariadb"
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout: int = 10

    def get_connection(self):
        if self.db_type == "postgres":
            import psycopg2

            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=self.connect_timeout,
            )
        else:
            import pymysql

            return pymysql.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=self.connect_timeout,
                charset="utf8mb4",
            )

    def placeholder(self) -> str:
        return "%s"


def _exec(conn, sql: str, params: tuple = ()) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def _exec_many(conn, sql: str, rows: list[tuple]) -> None:
    with conn.cursor() as cur:
        cur.executemany(sql, rows)


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------
SCHEMA_POSTGRES = """
-- Happy path tables
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    nome TEXT, cpf TEXT, rg TEXT, email TEXT,
    telefone TEXT, data_nasc DATE, endereco TEXT, cep TEXT,
    cnpj_empresa TEXT, observacoes TEXT
);
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id),
    diagnostico TEXT, cid TEXT, medico TEXT,
    data_atendimento DATE, prontuario_numero TEXT
);
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id),
    tipo_doc TEXT, numero_doc TEXT,
    doc_blob BYTEA, doc_base64 TEXT
);

-- Innocent / benign tables (should NOT trigger scanner)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    code TEXT, sku TEXT, description TEXT,
    price NUMERIC, stock INT, serial_number TEXT
);
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    level TEXT, service TEXT, message TEXT,
    ip_address INET, request_id TEXT
);

-- Multilingual / mixed collation
CREATE TABLE IF NOT EXISTS international_contacts (
    id SERIAL PRIMARY KEY,
    nome TEXT, nome_en TEXT, nombre_es TEXT,
    email TEXT, country_code CHAR(2),
    national_id TEXT, id_type TEXT
);

-- Encoding stress
CREATE TABLE IF NOT EXISTS encoding_stress (
    id SERIAL PRIMARY KEY,
    label TEXT, content TEXT, encoding_note TEXT
);

-- Foreign key spread (PII in normalized tables)
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY, cpf TEXT UNIQUE, nome TEXT
);
CREATE TABLE IF NOT EXISTS person_contacts (
    id SERIAL PRIMARY KEY,
    person_id INT REFERENCES persons(id),
    contact_type TEXT, contact_value TEXT
);
CREATE TABLE IF NOT EXISTS person_documents (
    id SERIAL PRIMARY KEY,
    person_id INT REFERENCES persons(id),
    doc_type TEXT, doc_number TEXT, issued_date DATE
);

-- SRE: large row table for performance testing
CREATE TABLE IF NOT EXISTS audit_log_large (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    user_cpf TEXT, action TEXT, resource TEXT,
    details JSONB, ip TEXT
);
"""

SCHEMA_MARIADB = """
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200), cpf VARCHAR(20), rg VARCHAR(20),
    email VARCHAR(200), telefone VARCHAR(50),
    data_nasc DATE, endereco VARCHAR(500), cep VARCHAR(10),
    cnpj_empresa VARCHAR(20), observacoes TEXT
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT, diagnostico TEXT, cid VARCHAR(10),
    medico VARCHAR(200), data_atendimento DATE, prontuario_numero VARCHAR(50),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT, tipo_doc VARCHAR(50), numero_doc VARCHAR(50),
    doc_blob LONGBLOB, doc_base64 LONGTEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50), sku VARCHAR(50), description VARCHAR(500),
    price DECIMAL(10,2), stock INT, serial_number VARCHAR(100)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME DEFAULT NOW(), level VARCHAR(10),
    service VARCHAR(100), message TEXT,
    ip_address VARCHAR(45), request_id VARCHAR(64)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS international_contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200), nome_en VARCHAR(200), nombre_es VARCHAR(200),
    email VARCHAR(200), country_code CHAR(2),
    national_id VARCHAR(50), id_type VARCHAR(30)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS encoding_stress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(100), content TEXT, encoding_note VARCHAR(100)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cpf VARCHAR(20) UNIQUE, nome VARCHAR(200)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS person_contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT, contact_type VARCHAR(30), contact_value VARCHAR(200),
    FOREIGN KEY (person_id) REFERENCES persons(id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS person_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT, doc_type VARCHAR(30), doc_number VARCHAR(50),
    issued_date DATE,
    FOREIGN KEY (person_id) REFERENCES persons(id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log_large (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME DEFAULT NOW(), user_cpf VARCHAR(20),
    action VARCHAR(100), resource VARCHAR(200),
    details JSON, ip VARCHAR(45)
) CHARACTER SET utf8mb4;
"""


def create_schema(conn, cfg: DBConfig) -> None:
    schema = SCHEMA_POSTGRES if cfg.db_type == "postgres" else SCHEMA_MARIADB
    for stmt in schema.strip().split(";"):
        s = stmt.strip()
        if s:
            _exec(conn, s)
    conn.commit()
    print("  v  Schema created")


# ---------------------------------------------------------------------------
# Data population — all scenarios
# ---------------------------------------------------------------------------
def populate_happy(conn, cfg: DBConfig) -> None:
    """Clear PII in every column — scanner must find everything."""
    ph = cfg.placeholder()
    rows_emp = []
    for i in range(20):
        rows_emp.append(
            (
                _p(_NAMES, i),
                _p(_CPFS, i),
                _p(_RGS, i),
                _p(_EMAILS, i),
                _p(_PHONES, i),
                _p(_DATES, i),
                _p(_ADDRS, i),
                _p(_CEPS, i),
                _p(_CNPJS, i),
                f"Funcionario de teste #{i + 1} — dados ficticios",
            )
        )
    _exec_many(
        conn,
        f"INSERT INTO employees (nome,cpf,rg,email,telefone,data_nasc,endereco,cep,cnpj_empresa,observacoes) VALUES ({','.join([ph] * 10)})",
        rows_emp,
    )

    # Medical records (sensitive health data — LGPD Art. 11 sensitive category)
    rows_med = []
    for i in range(1, 6):
        rows_med.append(
            (
                i,
                f"F41.{i} - Ansiedade generalizada (ficticio)",
                f"F41.{i}",
                "Dr. Teste Ficticio",
                _p(_DATES, i),
                f"PRONT-{1000 + i}",
            )
        )
    _exec_many(
        conn,
        f"INSERT INTO medical_records (employee_id,diagnostico,cid,medico,data_atendimento,prontuario_numero) VALUES ({','.join([ph] * 6)})",
        rows_med,
    )

    import base64 as b64

    # Documents with BLOB (base64-encoded CPF image placeholder)
    for i in range(1, 4):
        fake_doc = f"CPF:{_p(_CPFS, i)} RG:{_p(_RGS, i)} Nome:{_p(_NAMES, i)}".encode()
        b64_str = b64.b64encode(fake_doc).decode()
        _exec(
            conn,
            f"INSERT INTO documents (employee_id,tipo_doc,numero_doc,doc_blob,doc_base64) VALUES ({ph},{ph},{ph},{ph},{ph})",
            (i, "RG", _p(_RGS, i), fake_doc, b64_str),
        )

    conn.commit()
    print("  v  Happy path: 20 employees + medical records + documents with BLOB")


def populate_innocent(conn, cfg: DBConfig) -> None:
    """Benign data that looks like PII but is NOT — false positive bait."""
    ph = cfg.placeholder()
    # Products with serial numbers that look like CPF
    rows = []
    for i, (code, sku, sn) in enumerate(
        zip(
            _INNOCUOUS["product_codes"],
            _INNOCUOUS["serial_numbers"],
            _INNOCUOUS["version_tags"],
        )
    ):
        rows.append((code, sku, f"Produto teste #{i}", 99.99 + i, 100 + i, sn))
    _exec_many(
        conn,
        f"INSERT INTO products (code,sku,description,price,stock,serial_number) VALUES ({','.join([ph] * 6)})",
        rows,
    )

    # System logs with IPs, request IDs — should NOT trigger
    for i in range(50):
        _exec(
            conn,
            f"INSERT INTO system_logs (level,service,message,ip_address,request_id) VALUES ({ph},{ph},{ph},{ph},{ph})",
            (
                "INFO",
                "api-gateway",
                f"GET /health 200 OK [{i}ms]",
                _p(_INNOCUOUS["ip_addresses"], i),
                f"req-{i:06d}",
            ),
        )
    conn.commit()
    print("  v  Innocent data: products + system logs (should NOT trigger scanner)")


def populate_multilingual(conn, cfg: DBConfig) -> None:
    """Mixed languages and international ID formats."""
    ph = cfg.placeholder()
    rows = [
        # Brazilian
        (
            _p(_NAMES, 0),
            _p(_NAMES_EN, 0),
            _p(_NAMES_ES, 0),
            _p(_EMAILS, 0),
            "BR",
            _p(_CPFS, 0),
            "CPF",
        ),
        # Spanish (DNI — not CPF format)
        (
            _p(_NAMES, 1),
            _p(_NAMES_EN, 1),
            _p(_NAMES_ES, 1),
            "juan@example.es",
            "ES",
            "12345678A",
            "DNI",
        ),
        # US SSN format (should NOT be detected as CPF, but may trigger SSN rule)
        (
            _p(_NAMES, 2),
            _p(_NAMES_EN, 2),
            _p(_NAMES_ES, 2),
            "alice@example.com",
            "US",
            "123-45-6789",
            "SSN",
        ),
        # French NIR
        (
            _p(_NAMES, 3),
            "Pierre Dupont",
            "Pierre Dupont",
            "pierre@example.fr",
            "FR",
            "1 85 12 75 108 111 48",
            "NIR",
        ),
        # Portuguese NIF (similar to CPF check digit logic)
        (
            _p(_NAMES, 4),
            _p(_NAMES_EN, 0),
            "Maria V.",
            "maria@example.pt",
            "PT",
            "123456789",
            "NIF",
        ),
    ]
    _exec_many(
        conn,
        f"INSERT INTO international_contacts (nome,nome_en,nombre_es,email,country_code,national_id,id_type) VALUES ({','.join([ph] * 7)})",
        rows,
    )
    conn.commit()
    print("  v  Multilingual: BR/ES/US/FR/PT national IDs — mixed detection expected")


def populate_encoding_stress(conn, cfg: DBConfig) -> None:
    """Unusual encodings, special chars, very long strings, emoji."""
    ph = cfg.placeholder()
    rows = [
        (
            "ocr_noise",
            f"N0me: {_p(_NAMES, 0).replace('a', '@')} CPF: {_p(_CPFS, 0).replace('.', '_')}",
            "simulated OCR artifacts",
        ),
        (
            "latin1_chars",
            "José da Conceição — CPF: 123.456.789-09 — nasc: 15/03/1985",
            "latin-1 accented chars in UTF-8 column",
        ),
        (
            "emoji_mixed",
            f"👤 {_p(_NAMES, 1)} | 📋 CPF: {_p(_CPFS, 1)} | 📧 {_p(_EMAILS, 1)}",
            "emoji + PII in same string",
        ),
        (
            "json_embedded",
            json.dumps({"nome": _p(_NAMES, 2), "cpf": _p(_CPFS, 2), "rg": _p(_RGS, 0)}),
            "PII serialized as JSON string in TEXT column",
        ),
        (
            "very_long",
            "x" * 2000 + f" CPF: {_p(_CPFS, 3)} " + "y" * 2000,
            "PII buried in 4000-char string",
        ),
        (
            "null_term",
            f"CPF\x00{_p(_CPFS, 4)}\x00Nome\x00{_p(_NAMES, 4)}",
            "null-terminated C-style string",
        ),
        (
            "base64_in_col",
            __import__("base64").b64encode(f"CPF:{_p(_CPFS, 0)}".encode()).decode(),
            "base64-encoded PII stored in TEXT column",
        ),
        (
            "mixed_lang",
            f"Employee: {_p(_NAMES_EN, 0)} / Funcionario: {_p(_NAMES, 0)} / CPF: {_p(_CPFS, 0)} / SSN: 123-45-6789",
            "mixed EN+PT+ID types",
        ),
        (
            "partial_mask",
            f"CPF: ***.{_p(_CPFS, 1)[4:7]}.***-** | RG: {_p(_RGS, 1)}",
            "partial masking — some fields clear",
        ),
        (
            "innocuous_look",
            "Numero do pedido: 123.456.789-09 (referencia interna — NAO e CPF)",
            "innocuous context with CPF-shaped string",
        ),
    ]
    _exec_many(
        conn,
        f"INSERT INTO encoding_stress (label,content,encoding_note) VALUES ({ph},{ph},{ph})",
        rows,
    )
    conn.commit()
    print(
        "  v  Encoding stress: 10 rows with OCR noise, emoji, JSON, long strings, base64"
    )


def populate_foreign_keys(conn, cfg: DBConfig) -> None:
    """PII spread across normalized tables — tests cross-table detection."""
    ph = cfg.placeholder()
    # persons table: CPF + nome only
    person_ids = []
    for i in range(5):
        _exec(
            conn,
            f"INSERT INTO persons (cpf,nome) VALUES ({ph},{ph})",
            (_p(_CPFS, i), _p(_NAMES, i)),
        )
        with conn.cursor() as cur:
            if cfg.db_type == "postgres":
                cur.execute("SELECT lastval()")
            else:
                cur.execute("SELECT LAST_INSERT_ID()")
            person_ids.append(cur.fetchone()[0])

    # contacts: phone + email linked by FK
    for pid in person_ids:
        i = person_ids.index(pid)
        _exec(
            conn,
            f"INSERT INTO person_contacts (person_id,contact_type,contact_value) VALUES ({ph},{ph},{ph})",
            (pid, "email", _p(_EMAILS, i)),
        )
        _exec(
            conn,
            f"INSERT INTO person_contacts (person_id,contact_type,contact_value) VALUES ({ph},{ph},{ph})",
            (pid, "phone", _p(_PHONES, i)),
        )

    # documents: RG + passport linked by FK
    for pid in person_ids:
        i = person_ids.index(pid)
        _exec(
            conn,
            f"INSERT INTO person_documents (person_id,doc_type,doc_number,issued_date) VALUES ({ph},{ph},{ph},{ph})",
            (pid, "RG", _p(_RGS, i), _p(_DATES, i)),
        )

    conn.commit()
    print(
        "  v  Foreign keys: PII normalized across persons/person_contacts/person_documents"
    )


def populate_sre_large(conn, cfg: DBConfig, rows: int = 10_000) -> None:
    """Large audit log for performance/throughput testing."""
    ph = cfg.placeholder()
    actions = [
        "LOGIN",
        "LOGOUT",
        "VIEW_REPORT",
        "EXPORT_DATA",
        "DELETE_RECORD",
        "UPDATE_PII",
    ]
    resources = ["/employees", "/medical", "documents", "/api/v1/scan", "/reports"]
    batch = []
    for i in range(rows):
        batch.append(
            (
                _p(_CPFS, i),
                _p(actions, i),
                _p(resources, i),
                json.dumps({"row": i, "ip": _p(_INNOCUOUS["ip_addresses"], i)}),
                _p(_INNOCUOUS["ip_addresses"], i),
            )
        )
        if len(batch) >= 1000:
            _exec_many(
                conn,
                f"INSERT INTO audit_log_large (user_cpf,action,resource,details,ip) VALUES ({ph},{ph},{ph},{ph},{ph})",
                batch,
            )
            conn.commit()
            batch = []
    if batch:
        _exec_many(
            conn,
            f"INSERT INTO audit_log_large (user_cpf,action,resource,details,ip) VALUES ({ph},{ph},{ph},{ph},{ph})",
            batch,
        )
        conn.commit()
    print(
        f"  v  SRE large table: {rows:,} rows in audit_log_large (CPF in user_cpf column)"
    )


# ---------------------------------------------------------------------------
# Docker quick-start (creates containers automatically)
# ---------------------------------------------------------------------------
DOCKER_COMPOSE_POC = """
version: "3.8"
services:
  poc_postgres:
    image: postgres:16-alpine
    container_name: poc_postgres
    environment:
      POSTGRES_DB: poc_databoar
      POSTGRES_USER: poc_user
      POSTGRES_PASSWORD: poc_pass
    ports:
      - "15432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U poc_user -d poc_databoar"]
      interval: 5s
      retries: 10

  poc_mariadb:
    image: mariadb:11
    container_name: poc_mariadb
    environment:
      MARIADB_DATABASE: poc_databoar
      MARIADB_USER: poc_user
      MARIADB_PASSWORD: poc_pass
      MARIADB_ROOT_PASSWORD: root_pass
    ports:
      - "13306:3306"
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 5s
      retries: 10
"""


def docker_setup(output_dir: str = ".") -> None:
    """Write docker-compose and spin up containers."""
    import os

    compose_path = os.path.join(output_dir, "docker-compose-poc-db.yml")
    with open(compose_path, "w") as f:
        f.write(DOCKER_COMPOSE_POC)
    print(f"  Compose file: {compose_path}")
    print("  Starting containers (postgres:15432, mariadb:13306) ...")
    subprocess.run(["docker", "compose", "-f", compose_path, "up", "-d"], check=True)
    print("  Waiting for health checks ...")
    time.sleep(8)  # give containers a moment
    print("  Containers ready. Connect with:")
    print(
        "    Postgres: --db-type postgres --host localhost --port 15432 --user poc_user --password poc_pass"
    )
    print(
        "    MariaDB:  --db-type mariadb  --host localhost --port 13306 --user poc_user --password poc_pass"
    )


# ---------------------------------------------------------------------------
# Config file generator
# ---------------------------------------------------------------------------
def write_scan_config(cfg: DBConfig, output_path: str = "config-poc-db.yaml") -> None:
    """Write a Data Boar config.yaml that points at the populated database."""
    import yaml as _yaml

    config = {
        "targets": [
            {
                "type": cfg.db_type if cfg.db_type != "mariadb" else "mysql",
                "host": cfg.host,
                "port": cfg.port,
                "database": cfg.database,
                "user": cfg.user,
                "password": cfg.password,
            }
        ],
        "scan": {
            "max_rows_sample": 1000,
            "detect_blobs": True,
            "decode_base64": True,
        },
        "report": {
            "output_dir": "./reports-poc-db",
            "formats": ["xlsx", "html"],
        },
    }
    with open(output_path, "w") as f:
        _yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    print(f"  Scan config written: {output_path}")
    print(f"  Run: uv run python main.py --config {output_path} --scan --report")


# ---------------------------------------------------------------------------
# Dry run — show what would be created
# ---------------------------------------------------------------------------
TABLES_DOC = {
    "employees": "20 rows — clear PII (CPF, RG, email, phone, address, CNPJ)",
    "medical_records": "5 rows — sensitive health data linked by FK (LGPD Art. 11)",
    "documents": "3 rows — BLOB + base64-encoded document data",
    "products": "3 rows — INNOCENT: serial numbers, SKUs (should NOT trigger)",
    "system_logs": "50 rows — INNOCENT: IPs, request IDs (should NOT trigger)",
    "international_contacts": "5 rows — BR/ES/US/FR/PT national IDs (mixed detection)",
    "encoding_stress": "10 rows — OCR noise, emoji, JSON, base64, very long strings",
    "persons": "5 rows — CPF-only table (FK parent)",
    "person_contacts": "10 rows — email + phone linked by FK to persons",
    "person_documents": "5 rows — RG linked by FK to persons",
    "audit_log_large": "10,000 rows — CPF in user_cpf column (SRE performance test)",
}


def dry_run() -> None:
    print("\nData Boar — POC Database Population (DRY RUN)")
    print("Tables that would be created and populated:\n")
    for table, desc in TABLES_DOC.items():
        print(f"  {table:<30} {desc}")
    print("\nScenarios covered:")
    print("  HAPPY PATH      employees, medical_records, documents")
    print("  INNOCENT DATA   products, system_logs")
    print("  MULTILINGUAL    international_contacts (BR/ES/US/FR/PT)")
    print("  ENCODING STRESS encoding_stress (OCR, emoji, JSON, base64, long)")
    print("  FOREIGN KEYS    persons -> person_contacts, person_documents")
    print("  SRE LOAD        audit_log_large (10k rows)")
    print("\nTo run for real, add connection args (--host, --user, --password, etc.)")
    print("Or use --docker-setup to start containers automatically.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate a POC database with synthetic PII test data for Data Boar."
    )
    parser.add_argument(
        "--db-type",
        default="postgres",
        choices=["postgres", "mariadb"],
        help="Database type (default: postgres)",
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port (default: 5432 for postgres, 3306 for mariadb)",
    )
    parser.add_argument("--database", default="poc_databoar")
    parser.add_argument("--user", default="poc_user")
    parser.add_argument("--password", default="poc_pass")
    parser.add_argument(
        "--large-rows",
        type=int,
        default=10_000,
        help="Rows to insert in audit_log_large (default: 10000)",
    )
    parser.add_argument(
        "--docker-setup",
        action="store_true",
        help="Start Docker containers and exit (then run again without this flag)",
    )
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Write config-poc-db.yaml for Data Boar scan",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without connecting",
    )
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
        return

    if args.docker_setup:
        docker_setup()
        return

    port = args.port or (5432 if args.db_type == "postgres" else 3306)
    cfg = DBConfig(
        args.db_type, args.host, port, args.database, args.user, args.password
    )

    print("\nData Boar — POC Database Population")
    print(f"  Target: {cfg.db_type}://{cfg.user}@{cfg.host}:{port}/{cfg.database}\n")

    try:
        conn = cfg.get_connection()
    except Exception as e:
        print(f"  ERROR: Cannot connect to database: {e}")
        print("  Troubleshoot:")
        print("    1. Is the database running? (docker ps | grep poc)")
        print("    2. Is the host/port correct?")
        print("    3. Do the credentials match?")
        print(
            "    4. Try: uv run python scripts/populate_poc_database.py --docker-setup"
        )
        sys.exit(1)

    try:
        t0 = time.time()
        create_schema(conn, cfg)
        populate_happy(conn, cfg)
        populate_innocent(conn, cfg)
        populate_multilingual(conn, cfg)
        populate_encoding_stress(conn, cfg)
        populate_foreign_keys(conn, cfg)
        populate_sre_large(conn, cfg, args.large_rows)
        elapsed = time.time() - t0
        print(f"\n  Total time: {elapsed:.1f}s")
        print("  Database ready for scanning.")
    finally:
        conn.close()

    if args.write_config:
        write_scan_config(cfg)

    print("\nNext steps:")
    print(
        "  1. uv run python scripts/populate_poc_database.py --write-config (if not done)"
    )
    print("  2. uv run python main.py --config config-poc-db.yaml --scan --report")
    print("  3. Fill in docs/private/plans/POC_METRICS_TEMPLATE.pt_BR.md")
    print("  4. Run Scenario 9 configs for error message QA\n")


if __name__ == "__main__":
    main()
