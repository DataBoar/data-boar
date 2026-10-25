# Primer: Observability (metrics, logs, traces) and Data Boar

**Português (Brasil):** [OBSERVABILITY_PRIMER.pt_BR.md](OBSERVABILITY_PRIMER.pt_BR.md)

Conceptual primer on **OpenTelemetry-style observability** and what the **public** `data-boar` tree actually emits. It does **not** describe private lab collector topologies.

---

## 1. Pillars (vocabulary)

| Pillar | Question it answers | In this repo |
| ------ | ------------------- | ------------ |
| **Metrics** | Rates, errors, duration (RED) | Opt-in OTel meters when enabled |
| **Logs** | Structured or bridged log records | Opt-in logging bridge (`opentelemetry-instrumentation-logging` extra in `pyproject.toml`) |
| **Traces** | Request/scan spans across components | Opt-in traces from `core/otel_setup.py` / FastAPI instrumentation |

All product OTel paths are **off by default** until `DATA_BOAR_OTEL_ENABLED` is set (see `tests/test_otel_setup_1500.py`).

---

## 2. Shipped integration points (verify in tree)

| Area | Evidence |
| ---- | -------- |
| Setup gate | `core/otel_setup.py` — `maybe_setup_otel(app=None)` for CLI; `api/routes.py` passes FastAPI `app` when dashboard runs |
| CLI hook | `main.py` calls `maybe_setup_otel(app=None)` early for oneshot commands |
| Dependencies | `[project.optional-dependencies]` OTel packages in `pyproject.toml` (`opentelemetry-api`, `sdk`, `exporter-otlp`, FastAPI/SQLAlchemy/logging instrumentations) |
| Tests | `tests/test_otel_setup_1500.py` |
| Audit trail (not OTel) | `--export-audit-trail` JSON from SQLite — session evidence, not a full observability backend |

---

## 3. What is **not** in this public tree

- No checked-in Grafana/Prometheus/Loki **stack** for operators (lab stacks live outside this repo).
- No guarantee that every subcommand exports spans — coverage follows completed plans in shipped code, not roadmap prose.
- Portuguese word **tempo** (time) is unrelated to Grafana Tempo unless you explicitly wire OTLP to such a backend yourself.

---

## 4. Where to go next

| Need | Doc |
| ---- | --- |
| Enable flags / behaviour | `core/otel_setup.py`, [USAGE.md](../USAGE.md) |
| IaC deploy (where the app runs) | [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md) |
