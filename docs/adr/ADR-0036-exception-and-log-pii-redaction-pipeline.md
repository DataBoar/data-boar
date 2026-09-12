# ADR 0036 — Exception and log PII redaction pipeline

- **Status:** Accepted
- **Date (UTC):** 2026-04-22
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Database drivers, HTTP clients (for example **httpx**), and ORMs often embed **SQL fragments**, **connection hints**, or **response bodies** in `str(exception)`. The product already redacted URL passwords and `api_key=`-style pairs via `redact_secrets_for_log` before **logging**, but **`scan_failures.details` in SQLite** still stored the raw `details` string. That breaks audit expectations: a DPO must not find customer **CPF** or **email** in failure rows or log files.

## Decision

1. Introduce **`sanitize_log_text`**: `redact_secrets_for_log` then **`redact_pii_for_log`**, using the same **high-confidence** regex families as `core.detector.DEFAULT_PATTERNS` (CPF, CNPJ numeric and alphanumeric, email, card-like runs, Brazil phone, US SSN shape). Omit **DATE_DMY** from log redaction to avoid stripping innocuous dates from generic errors.
2. Introduce **`clean_error(exc)`**: join `str(exc)` with a short **`__cause__`** chain, then run **`sanitize_log_text`**, with a length cap suitable for persistence.
3. **`LocalDBManager.save_failure`** must persist **`sanitize_log_text(details)`** (not raw `details`) alongside the already-redacted log line.
4. Prefer **`clean_error(e)`** where exceptions are turned into user-visible or stored strings (`AuditEngine`, config save errors). Connectors may keep `str(e)` at call sites **only because both sinks are sanitized centrally**: **`save_failure`** (persistence) **and** **`SanitizeLogFilter`** on **`get_logger()`** (logging). Decision 4 never applied to a raw logger call by itself.

## Amendment (2026-09-12) — logging Filter + anti-`str(e)` gate (#1722)

CodeQL #301 on `wrong_password` was a false positive; the investigation showed ADR-0036 decision 4 had an **unwritten premise**: it only covered the persistence sink. Direct `get_logger().warning(..., str(e))` bypassed `sanitize_log_text`.

### Decision (amendment #1722)

5. **Mandatory `logging.Filter` on `get_logger()`.** `utils.logger.SanitizeLogFilter` runs `sanitize_log_text` on `record.msg` and string `record.args` **before** any handler emits. Filter the **Logger** (not only FileHandler/StreamHandler) so file, console, and test `caplog` share one choke point. Lazy `%s` formatting is covered by sanitizing args before `getMessage()`.
6. **Anti-regression gate** in `tests/test_logger_pii_filter.py` (+ AST helper `tests/str_e_callsite_gate.py`): scan `connectors/`, `core/`, `app/`, `api/` for `str(e)`/`str(exc)` inside log method calls. New log sites fail unless added to **`LOG_STR_E_ALLOWLIST`** with a written justification. The survey snapshot (`EXPECTED_STR_E_COUNTS`) classifies persist vs logger vs inert. The gate **self-tests** (synthetic logger vs `save_failure` snippets).

### Consequences (measured 2026-09-12)

Host: Linux primary, CPython **3.13.5**, `postgresql://user:…@host/db` payload.

| Path | Result |
| ---- | ------ |
| `sanitize_log_text` alone | **8.0 µs/call** (n=2000) |
| `logger.warning` + Filter + `NullHandler` | **13.1 µs/call** (n=2000) |
| `logger.warning` + Filter + `FileHandler` | **21.2 µs/call** (n=400) |

Filter cost is small versus I/O. Negative (unchanged): rare legitimate error text matching PII regex is masked.

### References (added)

- `utils/logger.py` — `SanitizeLogFilter`
- `tests/test_logger_pii_filter.py`, `tests/str_e_callsite_gate.py`
- GitHub **#1722**

## Consequences

- **Positive:** SQLite audit DB and logs stay aligned with “inventory tool, not data leak” positioning; regression tests guard CPF/email/password shapes. After #1722, **both** sinks (SQLite and `get_logger`) are centrally sanitized.
- **Negative:** Very rare legitimate error text that happens to match a PII regex will be masked (acceptable trade-off for audit safety).
- **Maintenance:** When adding new **built-in** high-confidence detector patterns intended for log hygiene, consider extending `_pii_regexes_for_log` in `core/validation.py` and updating tests. New `str(e)` **inside a log call** under `connectors/`/`core/`/`app/`/`api/` must update `LOG_STR_E_ALLOWLIST`.

## References

- `core/validation.py` — `redact_pii_for_log`, `sanitize_log_text`, `clean_error`
- `core/database.py` — `save_failure`
- `tests/test_security.py`, `tests/test_database.py`
