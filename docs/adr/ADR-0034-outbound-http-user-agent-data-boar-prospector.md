# ADR 0034 — Outbound HTTP User-Agent: `DataBoar-Prospector/<version>`

- **Status:** Accepted
- **Date (UTC):** 2026-04-08
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar reaches third-party HTTP(S) endpoints when operators configure **REST/API**, **SharePoint**, **Power BI**, or **Dataverse** targets (discovery and sampling, not a generic web crawler). After the product rename ([ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)), the codebase did **not** send a legacy `lgpd-crawler` User-Agent; libraries defaulted to generic strings (for example `python-httpx/...`, `python-requests/...`). That is honest but **weak for supportability**: remote operators, API gateways, and WAF logs cannot tie traffic to this product without reading TLS fingerprints or payload patterns.

## Decision

1. Define a single canonical outbound User-Agent string: **`DataBoar-Prospector/<version>`**, where `<version>` is the same resolved value as **`core.about.get_about_info()`** (installed `data-boar` distribution version, with the same fallback as `_package_version()` when metadata is missing).
2. Implement it in **`core.about.get_http_user_agent()`** and apply it from HTTP(S) connectors that perform outbound discovery (`rest_connector`, `sharepoint_connector`, `powerbi_connector`, `dataverse_connector`), including one-off OAuth token `httpx.post` calls where applicable.
3. **Override:** If a target YAML already supplies a `User-Agent` (case-insensitive key in `headers`), that value wins for the REST/API client so operators can comply with vendor-specific registration or allowlists.

## Consequences

- **Positive:** Logs and dashboards on the remote side can filter on `DataBoar-Prospector`; aligns public identity with **Data Boar** without reusing the old repo name as a wire token.
- **Neutral:** Operators who relied on the previous library-default UA string will see a change in their API logs (expected once per upgrade).
- **Documentation:** [TECH_GUIDE.md](../TECH_GUIDE.md) (REST/API section) points operators at the default UA and the `headers` override; this ADR plus `core/about.py` remain the source of truth.

## References

- `core/about.py` — `get_http_user_agent()`, `_package_version()`
- `connectors/rest_connector.py`, `connectors/sharepoint_connector.py`, `connectors/powerbi_connector.py`, `connectors/dataverse_connector.py`
- [ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)
- [ADR 0035](ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) — README executive pitch stays separate from optional deck vocabulary (**Data Sniffing** / **Deep Boring**); wire identity here vs prose boundaries there.
