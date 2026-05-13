# Plan: Opt-in network port / service hints (“hidden ingredients” adjacent)

**Status:** Pending
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H2

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md), [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) (Tier 3b / “sniffing for hidden ingredients” umbrella)

## Purpose

Offer an **optional**, **explicitly authorized** capability to probe **already-in-scope or operator-declared** hosts and well-known ports for **lightweight service hints** (e.g. TCP connect + short read / banner-style string, **not** a full port sweep or exploit toolkit). Goal: help teams discover **shadow IT** or **legacy systems** that may hold personal data but were omitted from the formal inventory (“forgotten soup ingredients”), while staying compatible with **zero-trust**, **least privilege**, and **clear contractual scope**.

## Alignment with the product

- **On brand:** Fits the **data soup** narrative—expand **known ingredients** without claiming omniscience. Output is **hints and inventory classifiers**, not legal verdicts.
- **Different from core Boar:** Today the product **ingests configured targets** (DBs, paths, APIs). This plan adds a **bounded network reconnaissance adjunct** that only runs when the operator enables it and constrains scope.
- **See also (passive seed vs active probe):** [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) — **offline exports** (ITSM, monitoring, assessment) mapped to config **breadcrumbs**; no TCP probes unless this plan is enabled.
- **Not a replacement for nmap / ASV / pentest:** Scope is **narrow** (allowed hosts + allowlisted ports + rate limits + timeouts). **No** default internet-wide discovery, **no** exploitation, **no** credential stuffing.

## Worst case: customer has no inventory (servers, services, network map)

Some engagements start with **no reliable CMDB, no exports, and no owner map**. [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) helps when **any** breadcrumbs exist; when there are **none**, this plan is the **optional, last-resort adjunct**: **technician-enabled** TCP connect + short read on **allowlisted** hosts/ports only—**never** on by default and **never** without written scope (ticket/SOW).

**Operational bias (product, not legal advice):** Hints are intentionally **inclusive of candidates** (expect **false positives**): banner/substring matches on well-known ports should be labeled **“candidate — verify”** so humans can **discard noise** rather than assuming silence means “nothing to see.” That supports **discovery completeness** workflows; it does **not** substitute for **legal/regulatory** advice, **DPIA**, or **authority-specific** breach/notification rules—**do not** market this feature as guaranteeing avoidance of **false-negative** regulatory outcomes.

**Guardrails:** Same as the rest of this plan—**allowlists**, caps, audit logs, coordination with SOC/IDS. “Brute force” in the **colloquial** sense (trying many **declared** host:port pairs within caps) is **not** credential brute force or exploitation.

## Zero-trust / min-privilege design principles

1. **Default off:** No probes unless `discovery.network_port_hints.enabled` (name TBD) is true and scope is non-empty.
1. **Positive allowlists only:** Targets must be **explicit**—e.g. list of IPs/hostnames **and/or** CIDR ranges **declared in config** (or CLI), **not** “scan the whole VPC” unless the customer pastes that range deliberately.
1. **Separate from auth to data:** Port hints do **not** bypass database auth; they may suggest “something listens like MySQL” so the operator can **add a proper target** for a full scan.
1. **Rate and concurrency caps:** Hard limits on concurrent connects, total probes per run, and per-host cool-off to avoid looking like DoS.
1. **Auditability:** Log each probe (host, port, outcome, bytes read cap) in existing operator/audit surfaces; include in exported audit trail when that matures.
1. **Enterprise / advanced SKU (optional):** Candidate for **licensed feature pack** (see [LICENSING_SPEC.md](../LICENSING_SPEC.md)); open-core could stay “disabled stub” or “docs only” until policy is set.

## Stakeholders, compliance, and legal

| Audience                          | What to communicate                                                                                                                                                                                                                                                                        |
| --------                          | -------------------                                                                                                                                                                                                                                                                        |
| **Customer decision-makers / IT** | This is **optional asset-discovery support**, scoped by them; outputs are **technical hints** for inventory completeness, not certification of compliance.                                                                                                                                 |
| **DPO / privacy**                 | Probing may reveal **existence** of services that process personal data; treat as **processing metadata** about infrastructure. **Data minimisation:** banner-only or first-N-byte read; **no** storage of raw payloads beyond short hashes/snippets in logs if policy requires redaction. |
| **Security / SOC**                | Coordinate so probes are **expected** on the network; wrong timing can trigger IDS/IPS. Document **source IP** (scanner host) and **schedule**.                                                                                                                                            |
| **Legal / SOW**                   | **Written authorization** for the exact scope (IPs/ports/time window) is mandatory before enabling in regulated engagements. Do not market as covert discovery.                                                                                                                            |

**Product copy:** Avoid language that suggests **evading** customer oversight or “catching them hiding.” Prefer **inventory completeness**, **shadow IT awareness**, and **operator-controlled scope**.

## Proposed technical phases

| Phase | Deliverable                                                                                                                                                                                                                                                                           | Status    |
| ----- | -----------                                                                                                                                                                                                                                                                           | ------    |
| 1     | **Config schema + guardrails:** `discovery.network_port_hints` (or under `targets`-adjacent block): `enabled`, `hosts[]`, `cidrs[]` (optional), `ports[]` (allowlist), `connect_timeout_ms`, `read_max_bytes`, `max_probes_per_run`, `concurrency`. Reject ambiguous “wide” defaults. Optional: **`candidate_label`** / severity defaulting to “verify” (FP-tolerant copy). | ⬜ Pending |
| 2     | **Engine module:** Async or threaded TCP connect with timeout; optional single **read** for banner; map (port, prefix) → **hint label** (e.g. “likely HTTP”, “likely PostgreSQL”, “unknown TCP”). No protocol full parses in v1.                                                      | ⬜ Pending |
| 3     | **Outputs:** New report section or sheet row “**Network service hints**” (host, port, hint, evidence excerpt redacted); link to **Data source inventory** where applicable.                                                                                                           | ⬜ Pending |
| 4     | **CLI / dashboard:** Toggle mirroring other heavy features (`--network-port-hints` or dashboard checkbox) with **WARNING** in stdout/stderr when enabled.                                                                                                                             | ⬜ Pending |
| 5     | **Tests:** Unit tests with localhost mock listener; no flaky real-network dependency in CI.                                                                                                                                                                                           | ⬜ Pending |
| 6     | **Docs:** USAGE + SECURITY (authorized use, IDS notice) + pt-BR sync; cross-link from [SECURITY.md](../SECURITY.md).                                                                                                                                                                  | ⬜ Pending |

## Risks

- **Misuse:** Operators run wide scans without permission → **mitigate** with allowlist-only schema and loud UI warnings.
- **Noise:** Many ports open in prod → **mitigate** with small default port sets and “suggest targets” UX rather than auto-adding credentials.
- **Liability perception:** “Like nmap” → **position** as **inventory helper** with explicit scope; defer aggressive techniques indefinitely.
- **Regulatory copy:** Avoid claims that port hints **prevent** fines or **eliminate** false-negative regulatory risk; emphasize **human review**, **scope**, and **audit trail**.

## YAML schema sketch (draft — not validated by `config.loader` yet)

Place under the **root** config object (same file as `targets`, `api`, `report`, …). **Default:** feature **off** (`enabled: false` or block omitted). **Loader rule (future):** if `enabled: true`, require **non-empty** `hosts` and/or `cidrs` **and** non-empty `ports`; reject configs that would imply “probe everything”.

```yaml
# Optional — entire block may be omitted.
discovery:
  network_port_hints:
    enabled: false
    # Optional free text: SOW reference, ticket ID, or “verbal OK 2026-03-25” — never a substitute for real contract scope.
    authorization_note: ""

    # At least one of hosts / cidrs must be non-empty when enabled (loader validation).
    hosts:

      - "10.0.10.20"
      - "legacy-crm.internal.customer.local"

    cidrs: []
    # Example if customer explicitly pastes a range:
    # cidrs:
    #   - "10.20.0.0/28"

    # Allowlisted TCP ports only (positive list). No “1-65535”.
    ports:

      - 22
      - 80
      - 443
      - 3306
      - 5432
      - 1433
      - 3389
      - 8080
      - 8443

    connect_timeout_ms: 800
    read_max_bytes: 256
    max_probes_per_run: 200
    concurrency: 4
    # Soft guard against IDS noise — exact algorithm TBD.
    min_interval_ms_between_probes_to_same_host: 100

    # Optional named presets for report labels (not OS detection).
    hint_map:

      - port: 443

        label: "likely_tls_http"

      - port: 3306

        label: "likely_mysql_wire"
```

**CLI mirror (future):** e.g. `--network-port-hints` as **master enable** plus optional overrides; must still read **hosts/ports** from config unless a **lab-only** `--network-port-hints-dry-run-localhost** is introduced (out of scope until agreed).

**Normalization:** `config.loader` should resolve hostnames once, dedupe `hosts`, validate CIDR notation, and cap `len(ports) * len(resolved_hosts)` against `max_probes_per_run` **before** any socket call.

## Cross-references

- **Tier 3b / hidden ingredients:** [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) § Tier 3b and Tier 4 (network strings **inside** files vs this plan: **live** port hints).
- **Data source inventory:** Existing report sheet can reference hinted services once a real target is configured.
- **Dashboard HTTPS / trust:** Transport and audit posture in [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md).
- **Audit export:** When [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) **phase 4** ships, consider appending **probe summary counts** (no raw banners) to the same JSON export if this feature is enabled — separate schema bump.
