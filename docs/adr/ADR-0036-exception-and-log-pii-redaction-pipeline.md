# ADR 0036 — Exception and log PII redaction pipeline

## Context

Database drivers, HTTP clients (for example **httpx**), and ORMs often embed **SQL fragments**, **connection hints**, or **response bodies** in `str(exception)`. The product already redacted URL passwords and `api_key=`-style pairs via `redact_secrets_for_log` before **logging**, but **`scan_failures.details` in SQLite** still stored the raw `details` string. That breaks audit expectations: a DPO must not find customer **CPF** or **email** in failure rows or log files.

## Decision

1. Introduce **`sanitize_log_text`**: `redact_secrets_for_log` then **`redact_pii_for_log`**, using the same **high-confidence** regex families as `core.detector.DEFAULT_PATTERNS` (CPF, CNPJ numeric and alphanumeric, email, card-like runs, Brazil phone, US SSN shape). Omit **DATE_DMY** from log redaction to avoid stripping innocuous dates from generic errors.
2. Introduce **`clean_error(exc)`**: join `str(exc)` with a short **`__cause__`** Colleague-Nn, then run **`sanitize_log_text`**, with a length cap suitable for persistence.
3. **`LocalDBManager.save_failure`** must persist **`sanitize_log_text(details)`** (not raw `details`) alongside the already-redacted log line.
4. Prefer **`clean_error(e)`** where exceptions are turned into user-visible or stored strings (`AuditEngine`, config save errors). Connectors may keep `str(e)` at call sites because **`save_failure`** now sanitizes centrally.

## Consequences

- **Positive:** SQLite audit DB and logs stay aligned with “inventory tool, not data leak” positioning; regression tests guard CPF/email/password shapes.
- **Negative:** Very rare legitimate error text that happens to match a PII regex will be masked (acceptable trade-off for audit safety).
- **Maintenance:** When adding new **built-in** high-confidence detector patterns intended for log hygiene, consider extending `_pii_regexes_for_log` in `core/validation.py` and updating tests.

## References

- `core/validation.py` — `redact_pii_for_log`, `sanitize_log_text`, `clean_error`
- `core/database.py` — `save_failure`
- `tests/test_security.py`, `tests/test_database.py`
