# External connectivity evaluation (public datasets, APIs, read-only DBs)

**Português (Brasil):** [LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md)

**Purpose:** Reproducible **lab** checks that Data Boar **connectors** behave sensibly against **third-party** HTTP APIs and (where allowed) **read-only** SQL/NoSQL endpoints. Complements **[LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)** (LAN-owned stacks) and **CI** — it does **not** replace them.

**Scope:** Tracked doc stays **vendor-neutral** and **free of LAN hostnames, IPs, passwords, and operator strategy**. Copy templates from **`docs/private.example/homelab/`** into **`docs/private/`** and fill secrets there. **Never** commit credentials or RNAcentral-style public reader passwords into Git.

---

## 1. What Data Boar can exercise here

| Connector area | Config `type` / `driver` | Typical use in this eval |
| -------------- | ------------------------ | ------------------------- |
| REST/HTTP JSON | `api` or `rest`, `base_url` + `paths` | Public demo APIs (GET JSON). |
| PostgreSQL / MariaDB / MySQL | `database` + SQLAlchemy driver | Read-only public DBs **only** where ToS allows; prefer **local Docker** or **[postgres-sample-dbs](https://github.com/neondatabase/postgres-sample-dbs)** loaded on **your** host. |
| MongoDB | `database`, `driver: mongodb` | Local **`deploy/lab-smoke-stack/docker-compose.mongo.yml`** (recommended) or your own instance. |
| Filesystem | `filesystem` | Repo **`tests/data/compressed`**, **`tests/data/homelab_synthetic`**, password-protected samples per **[GLOSSARY.md](../GLOSSARY.md)** (*password-protected archive or document*). |

**Not in scope for “public internet” eval:** Abusing rate limits, scraping sites without API contracts, or storing third-party payloads in reports beyond metadata/findings policy.

---

## 2. Taxonomy (shorthand)

| Tag | Meaning |
| --- | ------- |
| **E2E-OK** | Reachable; connector completes; findings or clean negative as expected. |
| **E2E-FAIL-EXPECTED** | Deliberate bad host, port, or credentials — used to validate **`scan_failures`**, timeouts, and operator-facing messages. |
| **E2E-SKIP** | Blocked by firewall, ToS, or offline third party — not a product defect. |

Run **at least two** categories per session (e.g. one **OK** + one **FAIL-EXPECTED**) so results are not confused with transient outages.

---

## 3. Reference resources (links only; no secrets here)

| Kind | Example (verify ToS before use) |
| ---- | -------------------------------- |
| REST demo API | [restful-api.dev](https://restful-api.dev/) — public `GET` endpoints (rate limits apply). |
| Postgres samples (clone/load locally) | [neondatabase/postgres-sample-dbs](https://github.com/neondatabase/postgres-sample-dbs). |
| Rankings / lists | [db-engines.com ranking](https://db-engines.com/en/ranking); blog roundups (e.g. [DataCosmos — free DBs for test](https://www.datacosmos.com.br/en/post/5-free-database-to-test-and-develop)) — **not** endorsements. |
| Read-only public Postgres (science) | [RNAcentral public Postgres](https://rnacentral.org/help/public-database) — **credentials are on the provider page**; do not paste into Git; respect usage policy. |
| Kaggle datasets | [kaggle.com/datasets](https://www.kaggle.com/datasets) — download under their rules; use as **filesystem** targets after extract. |
| SQL sample lists | Third-party blogs (e.g. Red9, Software Testing Magazine lists) — treat as **pointers**, not guarantees. |
| NoSQL tooling (not Data Boar substitutes) | [NoSQLBench](https://docs.nosqlbench.io/introduction/), [NoSQLUnit](https://www.methodsandtools.com/tools/nosqlunit.php) — load/generation tools; useful **around** scans, not replacements for **`pytest`**. |
| MongoDB samples | [MongoDB sample datasets (Atlas)](https://www.mongodb.com/resources/basics/databases/sample-database) — cloud terms apply; local Docker preferred for fixed lab. |

**Azure / Fabric community examples** (e.g. AdventureWorks connection strings on forums) change over time — prefer **local restore** or **your** Azure tenant with explicit approval.

---

## 4. Intentional failure cases (good for technician runbooks)

Configure targets that **must** fail:

- **TCP impossible:** reserved documentation IP (e.g. `192.0.2.1`) on a closed port, or `localhost` on **wrong** port with **no** listener.
- **Auth wrong:** database target with user `invalid_user` / password `invalid` against **your** lab container.
- **HTTP timeout:** pathologically low `read_timeout_seconds` against a known-slow or non-responding URL (document expected timeout finding).

Document outcomes in **`scan_failures`** / session logs so **TROUBLESHOOTING_MATRIX**-style guidance stays accurate.

---

## 5. Password-protected Office / PDF / archives

- **Behaviour:** Without a supplied password, encrypted payloads are **not** readable — expect **false negatives** for hidden text; see **GLOSSARY** and **USAGE** limitations.
- **Lab:** Use **`file_passwords`** (or env) per **TECH_GUIDE** when testing unlock paths; keep password lists **private** or gitignored.

---

## 6. Firewall (generic steps; no real IPs)

On a **Linux hub** that must accept LAN DB clients:

- **UFW (example pattern):** allow **only** lab subnet to **published** DB ports — e.g. `ufw allow from <LAB_SUBNET> to any port 55432 proto tcp` after **`deploy/lab-smoke-stack`** ports; reload UFW. Replace `<LAB_SUBNET>` in **private** notes.
- **nftables:** equivalent `accept` rule for `tcp dport { 55432, 33306 }` from `LAB_SUBNET`; **drop** from WAN.

**Windows:** use **Windows Defender Firewall** advanced rules for inbound Docker-published ports when LAN clients connect.

Exact commands with **your** CIDR belong in **`docs/private/homelab/`**, not here.

---

## 7. Automation in this repo

| Artifact | Role |
| -------- | ---- |
| **`scripts/lab-external-smoke.ps1`** | Quick **reachability** checks (HTTP GET, optional TCP) from the operator PC — **not** a full Data Boar scan. |
| **`deploy/lab-smoke-stack/docker-compose.mongo.yml`** | Optional local MongoDB for **`driver: mongodb`** scans. |
| **`docs/private.example/homelab/config.external-eval.example.yaml`** | Template — copy private, add secrets locally. |
| **`.cursor/skills/lab-external-connectivity-eval/SKILL.md`** | Token-aware reproduction for assistants. |

Chat token: **`external-eval`** (see **`.cursor/rules/session-mode-keywords.mdc`**).

---

## 8. PRD-readiness signal?

**Partial only.** Passing this eval shows **connectors + messaging** under real network variance and **controlled** failures. **Production readiness** still requires **[HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md)**, **[SECURITY.md](../SECURITY.md)** posture, release notes, and customer-specific config — not a single external smoke.

---

## 9. Related docs

- [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) — LAN multi-host DB + FS.
- [TROUBLESHOOTING_MATRIX.md](../TROUBLESHOOTING_MATRIX.md) — DB/network errors.
- [USAGE.md](../USAGE.md) — `api` / `database` targets.
- ADR [0028](../adr/ADR-0028-lab-external-connectivity-eval-playbook.md) — why this playbook exists.
