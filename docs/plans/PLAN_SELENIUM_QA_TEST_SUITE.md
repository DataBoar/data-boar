# Plan: Selenium-based QA test suite (on-demand, report and recommendations)

**Status:** Deferred
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds a **Selenium-based test suite** that acts as **robots** to validate application usage across different types of **quality assurance**: functional testing, navigation testing, button/interaction testing, API testing, report and heatmap listing and downloads, and stress testing. The suite produces a **short report** and **recommendations** from discoveries. **Execution and download of test results are on-demand** (triggered by you), not part of the default CI or automated runs.

---

## Goals

- **Robot-style QA:** Use Selenium (browser automation) to drive the web UI and, where useful, combine with direct HTTP calls for API coverage. Tests behave as “robots” (repeatable, scripted user flows).
- **Coverage areas:**
- **Functional testing:** Core flows work (e.g. load dashboard, start scan, see status, open config, save config).
- **Navigation testing:** All main pages load (/, /config, /reports, /help, /about); links and redirects behave correctly.
- **Button and form testing:** Buttons (Start scan, Save config, etc.) and form submissions work and show expected feedback.
- **API testing:** Key endpoints (GET /health, /status, /list; POST /scan, /start; GET /report, /heatmap, /reports/{id}, /heatmap/{id}; PATCH sessions) return expected status codes and, where applicable, correct content type or file download.
- **Report and heatmap listing and downloads:** Reports list page shows sessions; download links for Excel report and heatmap PNG work (per session and “latest”); downloaded files are non-empty and have expected extension/type.
- **Stress testing (optional):** Concurrent requests or repeated scan triggers to observe rate limiting, stability, and response times; results recorded for the report.
- **Short report:** After a run, generate a **summary report** (e.g. Markdown or HTML): pass/fail per test or category, duration, and any errors or screenshots (optional).
- **Recommendations:** From discoveries (failures, slow endpoints, flaky flows), produce a short **recommendations** section (e.g. “Fix X”, “Consider adding Y”, “Stress test showed Z”).
- **On-demand:** The suite is **not** run by default in CI. You trigger runs when you want (e.g. `uv run python scripts/run_qa_suite.py` or `uv run pytest tests_qa/ -v --qa-report`). Test results (report + optional artifacts) can be **downloaded or saved locally** (e.g. to `qa_results/` or a timestamped folder) for your review.

---

## Current state

- **Unit/integration tests:** [tests/](https://github.com/FabioLeitao/data-boar/tree/main/tests) use pytest; they hit the API with `TestClient` (no browser). No Selenium or Playwright in the project today.
- **Web app:** FastAPI app in [api/routes.py](../api/routes.py): GET /, /config, /reports, /help, /about; POST /scan, /start, /config; GET /status, /report, /heatmap, /list, /reports/{session_id}, /heatmap/{session_id}, /logs/{session_id}; PATCH /sessions/{session_id}, /sessions/{session_id}/technician; POST /scan_database. Report and heatmap downloads return FileResponse (Excel, PNG).
- **Dependencies:** [pyproject.toml](../pyproject.toml) has no Selenium or browser-automation dependency. The plan will add an **optional** dependency group (e.g. `[qa]` or `[selenium]`) so the main install stays unchanged.

---

## Scope: test categories and examples

| Category              | What is tested                                                                                                                           | How (Selenium vs HTTP)                         |
| --------------------- | ------------------------------------------------------------------------------                                                           | -----------------------                        |
| **Navigation**        | GET /, /config, /reports, /help, /about return 200; page titles/headings present                                                         | Selenium (optional HTTP for speed)             |
| **Functional**        | Dashboard loads; Start scan triggers POST /scan or /start; status updates; config form load/save                                         | Selenium + optional API                        |
| **Buttons / forms**   | “Start scan”, “Save” config; tenant/technician inputs; submit and check response/success message                                         | Selenium                                       |
| **API**               | /health 200; /status 200; /list 200; POST /scan 200/202/429; GET /report, /heatmap 200/404; GET /reports/{id}, /heatmap/{id} 200/400/404 | HTTP (requests/httpx)                          |
| **Report/heatmap**    | /reports page lists sessions; “Download report” / “Download heatmap” links work; file bytes &gt; 0; Excel/PNG content-type               | Selenium (click links, check downloads) + HTTP |
| **Stress (optional)** | N concurrent GET /status or POST /scan; measure 429 and latency; optional load over time                                                 | HTTP (threading/async)                         |

All tests assume the **app is already running** (e.g. `python main.py --config config.yaml --web --port 8088`). The suite does not start the server; you start it before running the QA suite.

---

## Deliverables

- **Test suite location:** Dedicated directory, e.g. `tests_qa/` or `tests/selenium_qa/`, so it is clear these are QA/robot tests and can be excluded from default pytest collection (e.g. by marker or path) if desired.
- **Runner:** Script or pytest entry point to run the QA suite (e.g. `scripts/run_qa_suite.py --base-url <http://localhost:8088> --output qa_results/`) that: (1) runs all QA tests, (2) collects results, (3) writes the short report and recommendations, (4) optionally saves screenshots or artifacts.
- **Report:** Short report file (e.g. `qa_report_YYYYMMDD_HHMMSS.md` or `.html`) with: summary (passed/failed/total), per-category or per-test results, duration, errors, and a “Recommendations” section derived from failures and observations.
- **Download/save:** Test results (report + optional artifacts) are written to a local folder (e.g. `qa_results/` or a path you pass). You can run the suite on demand and open or archive that folder; no automatic upload or CI gate.
- **Optional dependency:** Selenium (and optionally a driver manager, e.g. webdriver-manager) in an extra like `[qa]` or `[selenium]` so `uv sync --extra qa` or `pip install -e ".[qa]"` is required only for running the QA suite.

---

## Implementation phases (to-dos)

### Phase 1: Setup and navigation/API baseline

| #   | To-do                                                                                                                                                                                                | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                | ------ |
| 1.1 | Add optional dependency group (e.g. `[qa]`) with selenium and webdriver-manager (or document manual driver install); document in README or CONTRIBUTING.                                             | ⬜      |
| 1.2 | Create `tests_qa/` (or `tests/selenium_qa/`) with conftest.py: fixture for base URL (e.g. env BASE_URL or default <http://localhost:8088>), optional browser (Chrome/Firefox), and driver lifecycle. | ⬜      |
| 1.3 | Navigation tests: Selenium tests that GET /, /config, /reports, /help, /about; assert status 200 and presence of key elements (e.g. title or main heading).                                          | ⬜      |
| 1.4 | API tests (HTTP): using requests or httpx, test /health, /status, /list; POST /scan (or /start) and GET /status until idle or timeout; assert status codes and JSON shape where applicable.          | ⬜      |
| 1.5 | Runner script or pytest hook: run tests_qa, collect pass/fail and duration; write a simple summary (e.g. to stdout or a stub report file).                                                           | ⬜      |
| 1.6 | Docs: how to run the QA suite (start app, then run script or pytest), optional dependency install, and where results go.                                                                             | ⬜      |

### Phase 2: Buttons, forms, report/heatmap listing and downloads

| #   | To-do                                                                                                                                                                                                                                                                           | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                                                                                           | ------ |
| 2.1 | Button/form tests: Selenium – click “Start scan” (or equivalent), wait for status change or message; config page – fill YAML textarea (optional), click Save, check for success/error message.                                                                                  | ⬜      |
| 2.2 | Reports list: open /reports, assert table or list of sessions; optionally assert sort (date desc/asc) and presence of download links.                                                                                                                                           | ⬜      |
| 2.3 | Report and heatmap downloads: Selenium – click “Download report” and “Download heatmap” for a session (or “latest”); verify file download (size &gt; 0, correct extension). Alternatively use HTTP GET /reports/{id}, /heatmap/{id} and assert Content-Type and content length. | ⬜      |
| 2.4 | Optional: test GET /report and GET /heatmap (latest) and GET /logs, GET /logs/{session_id} for 200/404 and file response.                                                                                                                                                       | ⬜      |
| 2.5 | Tests and runner: ensure all new tests are included in the runner and report.                                                                                                                                                                                                   | ⬜      |

### Phase 3: Report generation and recommendations

| #   | To-do                                                                                                                                                                                             | Status |
| --- | ---------------------------------------------------------------------                                                                                                                             | ------ |
| 3.1 | Report generator: after a run, produce a short report (Markdown or HTML) with: total/passed/failed, duration, list of tests with pass/fail and error message if failed.                           | ⬜      |
| 3.2 | Recommendations: from failed tests and optional heuristics (e.g. “multiple 429” → “review rate limit”), generate a “Recommendations” section (bullet list) in the report.                         | ⬜      |
| 3.3 | Output directory: runner writes report (and optional screenshots/artifacts) to a configurable path (e.g. `--output qa_results/` or env QA_OUTPUT); document how to run and where to find results. | ⬜      |
| 3.4 | Docs: add “QA test suite (on-demand)” to USAGE or CONTRIBUTING – how to trigger, interpret the report, and use recommendations.                                                                   | ⬜      |

### Phase 4: Stress testing and polish

| #   | To-do                                                                                                                                                                                                         | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                         | ------ |
| 4.1 | Stress tests (optional): script or test that sends N concurrent requests (e.g. GET /status or POST /scan) and records status codes (including 429), response times, and any errors; append summary to report. | ⬜      |
| 4.2 | Exclude QA tests from default pytest collection (e.g. pytest.ini or pyproject: exclude tests_qa unless a marker like `-m qa` or path is given), so `uv run pytest` alone does not run Selenium by default.    | ⬜      |
| 4.3 | Final docs and PLANS_TODO update; ensure “run on demand” and “download results” are clearly described.                                                                                                        | ⬜      |

---

## On-demand execution and results

- **Trigger:** You run the suite manually when you want (e.g. after deploying or before a release). Example: `uv run python scripts/run_qa_suite.py --base-url <http://localhost:8088> --output qa_results/` or `uv run pytest tests_qa/ -v --qa-report --qa-output qa_results/`.
- **Prerequisite:** Application must be running (e.g. `python main.py --config config.yaml --web --port 8088`). The plan does not auto-start the server.
- **Results:** Report and optional artifacts are written to the chosen output directory. You can open the report, archive the folder, or share it; there is no automatic upload or CI gate. Download of results is “save to local disk” by default; if a future need for “download from a remote runner” appears, it can be a separate small extension (e.g. zip the output dir).

---

## Dependencies and constraints

- **Optional dependency:** Selenium (and driver manager) only required for who runs the QA suite; main app and default pytest do not depend on it.
- **No CI gate:** The QA suite is not part of the default CI pipeline; it is on-demand. CI can optionally run it in a separate job or nightly if you add it later.
- **Browser:** Prefer headless Chrome or Firefox for reproducibility; driver setup (webdriver-manager or system driver) documented.

---

## Conflict and placement in roadmap

- **No conflicts** with other plans. Additive (new directory, optional dependency, runner script, report).
- **Placement:** Independent; can be done in parallel with any other plan. See [PLANS_TODO.md](PLANS_TODO.md).

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
