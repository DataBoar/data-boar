# Testing

**Português (Brasil):** [TESTING.pt_BR.md](TESTING.pt_BR.md)

This document describes how to run the test suite and what each test module covers. All tests must pass with **no errors or warnings** (`-W error`). CI runs the same command on every push and pull request.

## Running tests

From the project root:

```bash
# Full suite (recommended; uses pyproject.toml addopts including -W error)
uv run pytest -v -W error

# Or rely on addopts only
uv run pytest -v

# Run a single test file
uv run pytest tests/test_routes_responses.py -v -W error

# Run tests matching a keyword
uv run pytest -v -W error -k "session_id"

# Optional: lint gitignored docs/private/ (Markdown + any *.ps1 / *.sh there)
uv run pytest -v -W error --include-private
# Or: set INCLUDE_PRIVATE_LINT=1 (same effect for markdown + private script checks)
```

**Optional — `docs/private/`:** By default **markdown lint** and **script syntax** tests **skip** the gitignored **`docs/private/`** tree. To include it locally (e.g. after editing private notes), pass **`pytest --include-private`** or set **`INCLUDE_PRIVATE_LINT=1`**. To fix Markdown there: **`uv run python scripts/fix_markdown_sonar.py --include-private`** (or the same env var). CI does **not** set this flag.

**Requirements:** Python **3.12 or 3.13** (see `CONTRIBUTING.md` / `SECURITY.md`), dependencies installed (`uv sync --group dev` or `pip install -e .` plus dev tools). The **dev** group includes **`rapidfuzz`** so fuzzy-column tests run; core runtime does not require it unless you enable `sensitivity_detection.fuzzy_column_match` (optional extra **`detection-fuzzy`**). No external services are required; tests use temporary configs and in-memory or temporary SQLite where needed.

## Test modules overview

| Module                                        | Purpose                                                                                                                                                                                                                                                                                                                                |
| --------                                      | --------                                                                                                                                                                                                                                                                                                                               |
| **test_aggregated_identification.py**         | Category mapping, aggregation rules, and report output for quasi-identifier aggregation (LGPD/compliance).                                                                                                                                                                                                                             |
| **test_api_key.py**                           | Optional API key: when `api.require_api_key` is true, X-API-Key or Bearer required; GET /health remains public.                                                                                                                                                                                                                        |
| **test_api_assessment_poc.py**                | GRC maturity self-assessment POC: `/{locale}/assessment` HTML + POST, YAML pack, tier and **`licensing.mode: enforced`** JWT `dbtier` gates, export and history — internal plan reference: `docs/plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md`.                                                                                                                                                                                                                                                     |
| **test_api_scan.py**                          | POST /scan triggers a full audit using the loaded config; session and background behaviour.                                                                                                                                                                                                                                            |
| **test_audit.py**                             | Sensitivity detection: CPF, email, religion, political affiliation, low-sensitivity classification.                                                                                                                                                                                                                                    |
| **test_audit_export.py**                      | JSON audit trail export: **`maturity_assessment_integrity`** object matches DB verify helper (`verify_maturity_assessment_integrity`).                                                                                                                                                                                                  |
| **test_csp_headers.py**                       | Security headers and Content-Security-Policy on dashboard and help pages (no `unsafe-inline` in script-src).                                                                                                                                                                                                                           |
| **test_pii_guard.py**                         | **Guardrail:** every file in the Git index is scanned for PII literals/regex that belong only in gitignored **`docs/private/`**; optional external **`docs/private/pii-patterns.txt`** extends the built-in list. Also flags AWS/GitHub/Slack/Stripe keys, PEM headers, Bearer tokens. Prevents recurrence of PII committed to tracked trees. |
| **test_confidential_commercial_guard.py**     | **Policy:** `git ls-files` must not list **`docs/private/`**, **`.cursor/private/`**, or any **`docs/.../commercial/...`** path outside **`docs/private.example/commercial/`**; tracked **`docs/`** basenames must not match internal pricing-study tokens (see module docstring). Pre-commit hook **confidential-commercial-guard**.  |
| **test_data_scanner.py**                      | Connector registry: filesystem, database (Postgres), API, unknown target resolution.                                                                                                                                                                                                                                                   |
| **test_format_length_hint.py**                | Connector CHAR/VARCHAR length hint → MEDIUM **`FORMAT_LENGTH_HINT_ID`** (declared-type parsing, integer-like and email-length heuristics) — Plan §4.                                                                                                                                                                                    |
| **test_rest_connector_format_hint.py**        | REST connector: JSON scalar → **`connector_data_type`** (`BIGINT`, `VARCHAR(n)` capped by `max_varchar`) feeding the Plan §4 format-length hint.                                                                                                                                                                                        |
| **test_database.py**                          | Config normalization (empty, legacy, rate_limit, scan.max_workers), LocalDBManager, sessions, wipe.                                                                                                                                                                                                                                    |
| **test_detector_entertainment_regression.py** | **Regression:** ML-only classification must not return ``HIGH`` + ``ML_DETECTED`` in lyrics / OSS Markdown / cifra / **interleaved chord+lyric** contexts; patched ``predict_proba`` exercises ``ML_POTENTIAL_ENTERTAINMENT`` (see module docstring). Runs under ``check-all.ps1``.                                                    |
| **test_github_workflows.py**                  | Operator Slack workflows under **`.github/workflows/`** parse as YAML; asserts **`slack-ci-failure-notify.yml`** **`workflow_run`** shape, upstream **`workflows:`** list, and the same **Slack webhook step guard** as other **`slack-*.yml`** that POST (see [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1). Does **not** POST to Slack (needs GitHub + secret).                         |
| **test_docs_markdown.py**                     | Documentation quality: README and docs/USAGE exist, have a title and key content; relative links resolve; SECURITY.md has content.                                                                                                                                                                                                     |
| **test_readme_stakeholder_pitch_contract.py** | README stakeholder block (before **Technical overview** / **Visão técnica**) keeps **Sniffing with judgment** / **Farejando com critério** headings and excludes deck-only labels **Data Sniffing** / **Deep Boring** — [ADR 0035](../docs/adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md).                                      |
| **test_about_version_matches_pyproject.py**   | Version metadata matches `pyproject.toml`; outbound HTTP **User-Agent** is **`DataBoar-Prospector/<version>`** — [ADR 0034](../docs/adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md).                                                                                                                                         |
| **test_learned_patterns.py**                  | Learned patterns: collect (sensitivity, pattern, filesystem), write YAML, exclusions.                                                                                                                                                                                                                                                  |
| **test_logic.py**                             | Audit logic: CPF in content, lyrics/tablature downgrade, backward compatibility of scan results.                                                                                                                                                                                                                                       |
| **test_minor_detection.py**                   | Minor detection: age/DOB heuristics, possible_minor flag, config wiring, report prioritization.                                                                                                                                                                                                                                        |
| **test_maturity_assessment_integrity.py**     | HMAC row sealing helpers, golden vector, SQLite tamper detection, integrity secret loading — [core/maturity_assessment/integrity.py](../core/maturity_assessment/integrity.py).                                                                                                                                                         |
| **test_markdown_lint.py**                     | SonarQube/markdownlint-style rules on project `.md` / `.mdc` files (including `.cursor/`). Excludes `private/` by default; opt-in **`--include-private`** or **`INCLUDE_PRIVATE_LINT=1`** for **`docs/private/`**. See [Running tests](#running-tests).                                                                                |
| **test_ml_engine.py**                         | MLSensitivityScanner: random_state seed (S6709), hyperparameters (S6973), local variable naming (S117), predict behaviour.                                                                                                                                                                                                             |
| **test_rate_limit_api.py**                    | Rate limiting: 429 when max concurrent scans or min_interval exceeded; disabled by default for legacy configs.                                                                                                                                                                                                                         |
| **test_report_path_safety.py**                | Report/heatmap `FileResponse` paths under `report.output_dir`: containment (CodeQL py/path-injection), basename allowlists, rejects paths outside configured dir.                                                                                                                                                                      |
| **test_report_recommendations.py**            | Report recommendations, overrides, executive summary, min_sensitivity, possible_minor row/priority, config_scope_hash.                                                                                                                                                                                                                 |
| **test_report_trends.py**                     | Trends sheet and report info (tenant, technician) in generated reports.                                                                                                                                                                                                                                                                |
| **test_routes_responses.py**                  | API contract and OpenAPI: invalid session_id → 400; 429/400/404 documented in OpenAPI; config page uses template constant.                                                                                                                                                                                                             |
| **test_scripts.py**                           | Shell/PowerShell script checks: `prep_audit.sh` bash syntax (`bash -n`, non-Windows), shebang and explicit `exit 1`; `scripts/commit-or-pr.ps1` PowerShell parse (Parser::ParseFile) and param block / ValidateSet. Opt-in **`--include-private`**: `*.ps1` / `*.sh` under **`docs/private/`**. See [Script testing](#script-testing). |
| **test_security.py**                          | SQL injection resistance (identifier escaping), path traversal (session_id validation), ORM-only session_id use, YAML safe_load.                                                                                                                                                                                                       |
| **test_sonarqube_python.py**                  | SonarQube-style guards: session_id regex (\\w + re.ASCII), response constants, report constants, connector/sql refactor helpers, no bare except in key modules.                                                                                                                                                                        |
| **test_sql_connector.py**                     | SQL connector: dialect skip-schema sets (Oracle, PostgreSQL casefold, MSSQL/Snowflake upper), `should_skip_schema`, discover (SQLite fallback), `_discover_fallback_no_schemas`, sparse-column sample (non-null SQL).                                                                                                                                                                  |
| **test_sql_sampling.py**                      | `SamplingManager` / `ColumnSamplePlan` (labels + `human_strategy`), `SqlColumnSampleQueryBuilder` dialect SQL (`IS NOT NULL`, Oracle ROWNUM, MSSQL `TOP` + `WITH (NOLOCK)` — never emits the bogus T-SQL `OPTION (MAX_EXECUTION_TIME)`, PostgreSQL `TABLESAMPLE SYSTEM` when large + env **`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT`**), `column_sample_sql_for_cursor` (5-tuple incl. human hint), `resolve_sql_sample_limit` + **`DATA_BOAR_SQL_SAMPLE_LIMIT`**, **`resolve_statement_timeout_ms_for_sampling`**.                                                                                                                                                                    |
| **test_sql_table_row_estimate.py**            | Dictionary-only approximate row counts (`estimate_table_rows`); SQLite returns `None` without `COUNT(*)`.                                                                                                                                                                                                                           |
| **test_sampling_policy.py**                   | `SamplingPolicy.get_effective_sample_limit` precedence: per-table → per-target → `fnmatch` patterns → global; `normalize_config` **`sql_sampling`** block.                                                                                                                                                                                                                                                                                                                                           |
| **test_config_sql_sampling_files.py**         | `sql_sampling_file` / `sql_sampling_files` fragment merge (inline wins), merge order, `config_path` requirement for expansion, path escape rejection, `get_effective_limit` alias.                                                                                                                                                                                                                                                                                                                  |
| **test_pwsh_venv_activate_docs.py**           | **Docs guard:** tracked `.md` / `.mdc` must not spell the contiguous **`.venv`…`Scripts`…extensionless `activate`** path for PowerShell (pwsh *not recognized*). Prefer **`Activate.ps1`** or **`uv run`** — see **CONTRIBUTING.md**.                                                                                              |
| **test_webauthn_rp.py**                       | WebAuthn Phase 1a (vendor-neutral JSON): `/auth/webauthn/*` when `api.webauthn.enabled`, registration/authentication options and verify, status, logout; negative paths (no creds, duplicate registration, bad state); startup failure without token secret; disabled config returns 404. Subset: `scripts/smoke-webauthn-json.ps1`. See ADR 0033. |
| **test_webauthn_session_cookie.py**           | Signed post-verify session cookie helpers (`itsdangerous`) used by the WebAuthn JSON flow.                                                                                                                                                                                                                                              |
| **test_webauthn_html_gate.py**                | WebAuthn HTML session gate and CSRF for dashboard HTML routes when `api.webauthn` is enabled (Phase 1b, GitHub #86).                                                                                                                                                                                                                    |
| **test_html_csrf.py**                         | HTML CSRF token helpers (`issue_html_csrf_token` / `verify_html_csrf_token`): tamper and cross-secret rejection (WebAuthn Phase 1b).                                                                                                                                                                                                    |
| **test_rbac.py**                              | Dashboard RBAC (GitHub #86 Phase 2): opt-in `api.rbac` with a Pro-tier JWT gate.                                                                                                                                                                                                                                                       |
| **test_licensing.py**                         | Optional commercial licensing (open by default): JWT verify, tier claims, signature helpers. Subset: `scripts/license-smoke.ps1`.                                                                                                                                                                                                       |
| **test_licensing_fingerprint.py**             | Machine fingerprint (`compute_machine_fingerprint`): deterministic 64-hex digest from hostname + `DATA_BOAR_MACHINE_SEED`; changes when the seed changes. Subset: `scripts/license-smoke.ps1`.                                                                                                                                          |

## Quality and security-related tests

These tests encode **SonarQube** or **API contract** rules so that regressions are caught in CI:

- **test_routes_responses.py** – Ensures HTTP status codes (400, 404, 429) are both implemented and declared in the OpenAPI schema (SonarQube S8415). Validates invalid `session_id` returns 400 and that the config page responds correctly.
- **test_sonarqube_python.py** – Ensures constants instead of duplicated literals (S1192), session_id pattern with `re.ASCII` (S5856), refactored helpers in connector_registry and sql_connector (S3776), no bare `except:` in key modules (S5706), no `len(...) >= 0` (S3981), cognitive complexity cap in that file (S3776), and TLS 1.2+ where `ssl.create_default_context()` is used (S4423).
- **test_ml_engine.py** – Ensures ML scanner has random_state seed (S6709), required hyperparameters (S6973), and local variable naming (S117).
- **test_docs_markdown.py** – Ensures key docs exist, have minimal structure, and internal links in README and docs/USAGE resolve (no broken links).
- **test_readme_stakeholder_pitch_contract.py** – Guards the README executive pitch against internal deck vocabulary drift ([ADR 0035](../docs/adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md)).
- **test_about_version_matches_pyproject.py** – Version alignment plus outbound **`DataBoar-Prospector/<version>`** User-Agent ([ADR 0034](../docs/adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md)).
- **test_markdown_lint.py** – Ensures all project Markdown and rule/skill files (`.md`, `.mdc`, including under `.cursor/`) pass MD009, MD012, MD024, MD036, MD051, MD060, MD031, MD034. See [Markdown lint](#markdown-lint) below.
- **test_pwsh_venv_activate_docs.py** – Ensures contributor docs do not reintroduce the **pwsh** mistake of invoking the extensionless **activate** shim under **`.venv\Scripts\`** (see **CONTRIBUTING.md**).
- **test_security.py** – Ensures SQL identifier escaping prevents second-statement execution (SQL injection), session_id pattern rejects path traversal and SQL-like payloads, database layer uses ORM for session_id (no raw interpolation), and YAML config uses safe_load (no code execution). See [SECURITY.md](../SECURITY.md#resistance-to-common-vulnerabilities).
- **test_report_path_safety.py** – Ensures report and heatmap download paths stay under `report.output_dir` and match allowlisted basenames (GitHub CodeQL **py/path-injection**). Run after changes to path handling in `api/routes.py`.

**Browser / E2E (future):** The suite already exercises the **HTTP API** (`test_api_scan.py`, `test_routes_responses.py`, etc.). **Playwright** or **Selenium** would add true UI flows (dashboard clicks); prefer expanding API tests first, then add one browser runner in CI when a critical path is not API-visible.

When adding or changing API behaviour, config schema, or quality rules, update the relevant test module and keep this document in sync.

**Cursor:** The project includes a rule (`.cursor/rules/quality-sonarqube-codeql.mdc`) and a skill (`.cursor/skills/quality-sonarqube-codeql/SKILL.md`) so that when editing Python or markdown, the agent avoids SonarQube/CodeQL violations and runs these quality tests after changes. When adding a new quality rule, add a test that enforces it, then update the rule and skill with the rule id and guidance, and keep this document in sync.

### Script testing

Scripts are validated for **syntax and structure** only; no root or network is required:

- **prep_audit.sh** – On non-Windows: `bash -n prep_audit.sh` (syntax check). On all platforms: tests assert shebang and use of explicit `exit 1` when not root (Sonar-style best practice). The script is intended to run as root and install packages; tests do not execute it.
- **scripts/commit-or-pr.ps1** – PowerShell parse via `Parser::ParseFile` (no execution, no git calls). Tests also assert a `param` block with `ValidateSet('Preview','Commit','PR')`. Sonar-style fixes in the script: `git add -- $f`, `git commit -m "$Title" -m "$Body"` (quoted arguments).
- **`docs/private/`** (opt-in) – With **`pytest --include-private`** or **`INCLUDE_PRIVATE_LINT=1`**, every **`*.ps1`** under **`docs/private/`** is parse-checked; on non-Windows, **`*.sh`** there gets **`bash -n`**. Skipped when the flag/env is off or the directory is missing.

### Markdown lint

Project `.md` files (excluding `.venv`, `.cursor`, `.git`, etc.) are checked for SonarQube/markdownlint-style rules so CI catches regressions:

- **MD009** – No trailing spaces at end of line.
- **MD012** – No multiple consecutive blank lines (max one).
- **MD024** – No duplicate heading text in the same file (headings inside fenced code blocks are ignored).
- **MD036** – No standalone emphasis-only line used as a heading (use `##` instead of `**Bold**`; labels with colons and long sentences are ignored).
- **MD051** – Link fragments (anchors) must not contain spaces.
- **MD060** – Fenced code blocks use consistent markers (all ` ``` ` or all `~~~`).
- **MD031** – Blanks around fences: a blank line is required before and after each fenced code block.
- **MD034** – No bare URLs: wrap in angle brackets (`<url>`) or use `[text](url)`; URLs inside backticks or code blocks are ignored.
- **MD060 (table)** – Table column style “aligned” (pipes align with header). Apply `uv run python scripts/fix_markdown_sonar.py` to fix MD007, MD009, MD012, MD029, MD032, MD036, MD047, and MD060 across tracked trees; add **`--include-private`** or **`INCLUDE_PRIVATE_LINT=1`** to include **`docs/private/`**.

Run the check as part of the full suite: `uv run pytest tests/test_markdown_lint.py -v -W error`.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs:

- **Lint (pre-commit)** – On **Python 3.12**: **`uv run pre-commit run --all-files`** (same as **`.pre-commit-config.yaml`**: Ruff check + format, **plans-stats** `--check`, markdown lint, pt-BR locale, confidential-commercial guard). Locally: **`uv run pre-commit install`** so **`git commit`** runs the bundle. **`tests/test_github_workflows.py`** asserts **`ci.yml`** still runs **`pre-commit run --all-files`** (regression guard).

1. **Test** – `uv run pytest -v -W error` on Ubuntu for **Python 3.12 and 3.13** (matrix, `fail-fast: false`).
1. **Dependency audit** – `uv run pip-audit` after `uv sync` (Python 3.12).
1. **SonarQube / SonarCloud** – Code quality and security analysis when `SONAR_TOKEN` is set; uses Python 3.12 after tests pass. See [SonarQube / SonarCloud](#sonarqube--sonarcloud) below.

Code scanning (CodeQL) is in `.github/workflows/codeql.yml` and analyzes Python for security and quality findings. See the repository **Security** tab for CodeQL alerts.

### Operator Slack workflows (not live-tested in pytest)

Posting to Slack requires **GitHub Actions** plus repository secret **`SLACK_WEBHOOK_URL`**. **`tests/test_github_workflows.py`** checks shipped **`slack-*.yml`** files (including **`slack-ci-failure-notify.yml`** on the default branch) for parse shape and the **step-level** webhook guard — see [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1.

| Workflow (Actions UI name)       | File                               | Purpose                                      |
| ------------------------------   | ---------------------------------- | -------------------------------------------- |
| **Slack operator ping (manual)** | `slack-operator-ping.yml`          | `workflow_dispatch` smoke test               |
| **Slack CI failure notify**      | `slack-ci-failure-notify.yml`      | `workflow_run` after listed upstream workflows **`failure`** (posts when secret is set) |

Operator setup: [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1 ([pt-BR](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)).

### SonarQube / SonarCloud

Analysis is driven by [`sonar-project.properties`](../sonar-project.properties) at the repo root. **The same file is used in two places:**

- **Locally (Cursor / VS Code):** The SonarQube extension in your IDE uses this config when you run analysis from the editor (e.g. “Run SonarQube analysis”). That’s how code quality is checked on your machine. The extension talks to your SonarQube server or SonarCloud and shows issues in the editor.
- **In CI:** GitHub Actions has no Cursor or IDE extensions. The workflow runs the SonarScanner (same tool, same config) so every push/PR is analyzed and the quality gate applies. So CI does not “use” the Cursor extension; it runs the scanner directly using this same `sonar-project.properties`.

Keeping one `sonar-project.properties` in the repo keeps local (extension) and CI in sync. To enable the CI step:

- **SonarCloud:** Add a secret `SONAR_TOKEN` (create a token at [sonarcloud.io](https://sonarcloud.io)). Ensure `sonar.projectKey` and `sonar.organization` in `sonar-project.properties` match the project you create in SonarCloud (project key is often `organization_repo`).
- **SonarQube Server:** Add secrets `SONAR_TOKEN` and `SONAR_HOST_URL` (e.g. `<https://sonarqube.your-company.co>m`). For a **self-hosted** instance on a home lab (Docker, tokens, reverse proxy, and how to make GitHub Actions reach it), see **[SONARQUBE_HOME_LAB.md](ops/SONARQUBE_HOME_LAB.md)** ([pt-BR](ops/SONARQUBE_HOME_LAB.pt_BR.md)).

The pipeline is intended to be followed for all reported issues (bugs, vulnerabilities, code smells, and security hotspots). Fix or justify findings; add or adjust tests where rules are encoded in the repo (e.g. `test_sonarqube_python.py`, `test_markdown_lint.py`, `test_scripts.py`) so that the same issues do not reappear. New findings from SonarQube should be addressed the same way: fix, add tests if the rule is in scope, and document in [TESTING.md](TESTING.md) or [CONTRIBUTING.md](../CONTRIBUTING.md) where relevant.

### Using extension issues to fix and prevent (automation)

The **same issues** the Cursor SonarQube extension shows come from the SonarQube/SonarCloud server. You can use them to fix code and prevent reintroduction in an automated way:

1. **Understand and fix**
   - **In the IDE:** Use the extension to see issues (file, line, rule, message). Fix them by hand or with the help of an agent that reads the same list.
   - **Machine-readable list:** Run `scripts/sonar_issues.py` (see below) to fetch the current issues from the API. The script prints one line per issue: `file:line:rule:severity:message`. Use this output to drive fixes (e.g. feed it to a script or an agent that applies fixes for known rule types).

1. **Prevent reintroduction (already automated)**
   - **CI:** The Sonar job in `.github/workflows/ci.yml` runs the same analysis on every push/PR. The quality gate fails if new issues appear or the gate condition is not met, so problematic changes are blocked before merge.
   - **Tests:** Critical rules are encoded in pytest (`test_sonarqube_python.py`, `test_markdown_lint.py`, `test_scripts.py`, etc.). Even without running Sonar, CI runs these tests, so regressions for those rules are caught even if Sonar is not configured.

1. **Fetching the issue list (script)**
   - From the repo root, with `SONAR_TOKEN` set (and optionally `SONAR_HOST_URL` for a SonarQube server):
     - `uv run python scripts/sonar_issues.py` — prints one line per issue; exit code 1 if there are issues (so you can `scripts/sonar_issues.py || true` to just list, or fail a script when issues exist).
     - `uv run python scripts/sonar_issues.py --json` — prints the full API JSON.
   - The script reads `sonar.projectKey` from `sonar-project.properties`, so it stays in sync with the extension and CI. Use this list to fix issues and to feed automation (e.g. an agent that “fix all issues from this list”).

## Maturity self-assessment POC smoke (gate 1)

For the **pytest subset** for the maturity self-assessment POC (API routes, integrity, DB batch summaries, audit-export parity; internal plan: `docs/plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md`), run from the repo root:

```powershell
.\scripts\smoke-maturity-assessment-poc.ps1
```

This runs `tests/test_api_assessment_poc.py`, `tests/test_maturity_assessment_integrity.py`, `tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first`, and `tests/test_audit_export.py::test_build_audit_trail_maturity_integrity_matches_verify` only. **Does not** replace **`.\scripts\check-all.ps1`** before merge. **Operator browser checklist:** [docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md](ops/SMOKE_MATURITY_ASSESSMENT_POC.md) §D.

## Licensing smoke (Priority band A6)

For a **fast** check of JWT / licensing helpers (no network), run from the repo root:

```powershell
.\scripts\license-smoke.ps1
```

This runs `tests/test_licensing.py` and `tests/test_licensing_fingerprint.py` only. Optional: add the same command as a CI job for recurring commercial posture checks (maintainers: **Priority band A** context lives under **Internal and reference** in [README.md](README.md) and in [SECURITY.md](../SECURITY.md)).

## See also

- **Documentation index** (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- [CONTRIBUTING.md](../CONTRIBUTING.md) – Local setup and workflow; run tests before opening a PR.
- [SECURITY.md](../SECURITY.md) – Supported versions and dependency audit.
- [docs/USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)) – API and config behaviour covered by the tests.
