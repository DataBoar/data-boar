# Test suite

Tests for **Data Boar**: API, core logic, connectors, config, reports, and quality/security guards. Install identity: [CONTRIBUTING.md](../CONTRIBUTING.md#repository-and-install-identity-data-boar).

## Quick run

```bash
uv run pytest -v -W error
```

All tests must pass with **no errors or warnings**. See **[docs/TESTING.md](../docs/TESTING.md)** for:

- Full run options and requirements
- What each test module covers
- Quality and security-related tests (SonarQube, OpenAPI, docs)
- CI and CodeQL

## Optional real-world text samples (maintainer corpus)

For **local** experiments (scanner, subtitles, OCR, “entertainment-style” text heuristics), Portuguese **cifras / tablaturas / letras** are useful:

- **Public repo:** [FabioLeitao/cifras](https://github.com/FabioLeitao/cifras) — clone to a path **outside** this product repo (or keep a small copy under `tmp/` / gitignored) and point scans at it. Prefer **not** vendoring large lyric bodies into **committed** fixtures unless licensing is explicit.
- **Third-party sites** (e.g. [cifraclub.cc](https://cifraclub.cc)): often **copyright + ToS** on song text — OK for **personal** local checks; **avoid** scraping into **CI** or committing full pages as repo fixtures without rights.

## Test files (summary)

| File                                | Purpose                                                                 |
| ------                              | --------                                                                |
| `test_aggregated_identification.py` | Quasi-identifier aggregation, category mapping, report                  |
| `test_api_key.py`                   | Optional API key (X-API-Key / Bearer), /health public                   |
| `test_api_scan.py`                  | POST /scan and audit trigger                                            |
| `test_audit.py`                     | Sensitivity detection (CPF, email, religion, etc.)                      |
| `test_connector_timeouts.py`        | Configurable timeouts: normalized config, REST/SQL/MongoDB/Redis wiring |
| `test_csp_headers.py`               | CSP and security headers on HTML endpoints                              |
| `test_data_scanner.py`              | Connector registry (filesystem, DB, API)                                |
| `test_database.py`                  | Config normalization, DB manager, sessions, wipe                        |
| `test_docs_markdown.py`             | README/USAGE/SECURITY exist, structure, links                           |
| `test_docs_pt_br_locale.py`         | `*.pt_BR.md` avoid European Portuguese markers (pt-BR audience)         |
| `test_learned_patterns.py`          | Learned patterns collect/write                                          |
| `test_logic.py`                     | Audit logic, lyrics/tablature downgrade                                 |
| `test_minor_detection.py`           | Minor detection heuristics and report                                   |
| `test_ml_engine.py`                 | ML scanner (SonarQube S6709, S6973, S117)                               |
| `test_rate_limit_api.py`            | Rate limit 429, min_interval, disabled default                          |
| `test_report_recommendations.py`    | Recommendations, overrides, executive summary                           |
| `test_report_trends.py`             | Trends sheet, report info (tenant/technician)                           |
| `test_routes_responses.py`          | API contract: 400/404/429, OpenAPI, session_id                          |
| `test_security.py`                  | SQL injection, path traversal, ORM session_id, YAML safe_load           |
| `test_sonarqube_python.py`          | SonarQube guards: constants, regex, helpers, no bare except             |
| `test_sql_connector.py`             | SQL connector discover, skip schemas, fallback                          |

Each module has a docstring at the top describing its scope; individual tests have docstrings where useful.
