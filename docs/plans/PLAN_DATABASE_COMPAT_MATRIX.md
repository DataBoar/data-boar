# Plan: Database compatibility matrix (axis B, sparse A×B) (#1237 / #1302)

<!-- plans-hub-summary: Sparse 2D DB compat matrix — axis A platform hosts (does Boar run?) + axis B engines via Podman (does connector ingest?); cloud-lane separate; native-driver intersections only; skip policy never silent; synthetic PII fixtures. -->
<!-- plans-hub-related: PLAN_PACKAGING_EXTRAS.md, PLAN_WHEELHOUSE_DISTRIBUTION.md, PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md -->

- **Status:** Not started (plan scaffold)
- **Date:** 2026-07-22
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H1 (lab proof / connector resilience)
- **GitHub:** [#1237](https://github.com/DataBoar/data-boar/issues/1237) `[test]` · [#1302](https://github.com/DataBoar/data-boar/issues/1302) `[P2][bug][connector]` · epic [#1171](https://github.com/DataBoar/data-boar/issues/1171)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Complements (do not replace):** [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) (platform / install — axis A narrative) · wheelhouse [#1182](https://github.com/DataBoar/data-boar/issues/1182) · abi3 ext [#782](https://github.com/DataBoar/data-boar/issues/782) / **GAP-001**

---

## Problem

Documented compat work to date focuses on **platform install** (wheelhouse, musl/no-AVX, OS matrix): *does Data Boar install and run?* That is **axis A**.

Field bugs (#1299 class → [#1302](https://github.com/DataBoar/data-boar/issues/1302)) show a second failure mode: **connector kwargs / native drivers** never exercised against a **real engine**, so the first live target yields **0 ingestion** (honest report of N target failures, but the worst compliance-scanner false “all clean” story). Remote latency ([#1237](https://github.com/DataBoar/data-boar/issues/1237)) is also unproven if every lab DB is localhost.

A **full cartesian product** of every lab host × every engine is too expensive and mostly redundant. The plan defines a **sparse 2D matrix**: measure platform and engines independently, then add **only** the intersections where **native drivers** risk musl/arm/glibc coupling.

---

## Decision

### Two orthogonal axes

| Axis | Question | Neutral / reference source | Cost model |
| ---- | -------- | -------------------------- | ---------- |
| **A — Platform** | Does the Boar **run** on this host? | FS / CSV / SQLite (stdlib — no native DB driver) | One cell per host |
| **B — Database** | Does the connector **ingest** from this engine? | Each engine × **one** reference platform (Podman on the target farm) | One cell per engine family member |
| **A×B — Intersection (sparse)** | Does a **native** driver install/connect from a hard host to a remote engine? | Only where libc/arch couples to the driver | Few cells (see below) |
| **Cloud-lane** | SaaS / HTTP connectors | Live account or mock — **not** Podman | Separate lane; default `skip:not-worth` unless operator opts in |

**Cost** = `|A| + |B| + |A×B_sparse|` — **not** `|A| × |B|`.

### Axis A — Platform (“does the Boar run?”)

Real lab hosts (role labels already used in public lab lessons). Neutral smoke source: **filesystem / CSV / SQLite**.

| Host role | Distro / arch signal | Why it is on axis A |
| --------- | -------------------- | ------------------- |
| **mini-bt** | Void **glibc** (differentiated distro / xbps) | Non-Debian glibc path |
| **alpine-emachines** | Alpine **musl** + **no-AVX** (two axes on one host) | Min-spec install + CPU floor; wheelhouse / give-back pressure (#1171, #1182) |
| **pi3b** | Debian trixie **arm64** | ARM client path; native-driver risk |
| **T14 / latitude** | **glibc** x86_64 **AVX** | Baseline workstation class |

Axis A does **not** require every SQL engine on every host. Prove runnability with the neutral source; leave engine ingestion to axis B (+ sparse intersections).

### Axis B — Database (“does the connector ingest?”)

Each engine runs on the **target farm** (Podman) and is exercised from **one** reference client platform (baseline glibc x86_64 unless a sparse cell says otherwise).

#### Family 1 — SQL relational (`sql_connector`)

| Engine | Typical Podman image / path | Notes |
| ------ | --------------------------- | ----- |
| PostgreSQL | official / lab compose `pg` | Also remote latency vehicle for #1237 (e.g. hosted Postgres) |
| MySQL | official `mysql` | |
| MariaDB | official `mariadb` | |
| MSSQL | `mcr.microsoft.com/mssql/server` | Field-proven path; timeout kwargs — #1302 |
| Oracle | `gvenzl/oracle-free` (23c) | Thin vs thick mode — see A×B |
| SQLite | local file via `sql_connector` | No Podman; often doubles as axis A neutral |

#### Family 2 — NoSQL document

| Engine | Typical image | Driver posture |
| ------ | ------------- | -------------- |
| MongoDB | official `mongo` | `pymongo` — pure Python → **no A×B cell** |

#### Family 3 — Key-value / cache

| Engine | Typical image | Driver posture |
| ------ | ------------- | -------------- |
| Redis | official `redis` | `redis-py` — pure Python → **no A×B cell** |

#### Cloud-lane (separate — not Podman)

Snowflake, Dataverse, Power BI, generic REST, S3 (and MinIO as S3-compatible lab stand-in when useful). These are **SaaS / HTTP** (or account-bound) paths: **live-account or mock**. They do **not** enter the Podman axis B grid. Default status: `skip:not-worth` (HTTP client is platform-agnostic) unless the operator schedules a live-account run.

### A×B intersection — sparse (native-driver risk only)

Add a cell **only** when the **native** driver can fail to install or link on musl/arm (or when thick mode is glibc-only).

| Driver / mode | Risk hosts | Why a cell exists |
| ------------- | ---------- | ----------------- |
| **pymssql** (FreeTDS) | musl (`alpine-emachines`), arm (`pi3b`) | Native / FreeTDS coupling |
| **psycopg2** (libpq) | musl, arm | libpq binary wheels / compile |
| **oracledb thin** | — | Pure Python → **no** intersection cell (covered by axis B on baseline) |
| **oracledb thick** (Instant Client) | musl, arm | Instant Client is **glibc-only** → expect `skip:client-blocked` or documented N/A on musl/arm |
| **pymongo** / **redis-py** | — | Pure Python → **no** A×B cell |

Example sparse set (illustrative, not exhaustive):

- `alpine-emachines` → remote MSSQL on T14 (`pymssql`)
- `alpine-emachines` → remote Postgres on T14 (`psycopg2`)
- `pi3b` → remote MSSQL / Postgres (same drivers)
- Oracle thick on musl/arm → explicit skip cell with reason (not a silent omit)

### Topology

```text
                    ┌─────────────────────────────────────┐
                    │  T14 — target farm (Podman engines) │
                    │  mssql · gvenzl/oracle-free · pg    │
                    │  mysql · mariadb · mongo · redis    │
                    │  minio (S3-compatible stand-in)     │
                    └──────────────▲──────────────────────┘
                                   │ LAN / real latency
                    ┌──────────────┴──────────────────────┐
                    │  alpine-emachines — client min-spec │
                    │  LIGHT smoke → REMOTE targets on T14│
                    │  (= #1237 real latency, not localhost)│
                    └─────────────────────────────────────┘
```

- **T14** hosts the engine farm (Podman). Baseline AVX/glibc workstation class (**T14 / latitude**) remains the reference client for full axis B sweeps.
- **alpine-emachines** runs **light** client smokes against **remote** T14 engines — validates [#1237](https://github.com/DataBoar/data-boar/issues/1237) (genuine network latency), not loopback.
- Other axis A hosts (mini-bt, pi3b) follow the same pattern when scheduling sparse A×B cells.

### Data policy — synthetic only

Use **synthetic PII fixtures** (fake identifiers aligned with lab synthetic corpora / [PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md)).

Do **not** load or scan a **customer production / field engagement snapshot** into this matrix. Field bugs inform **which drivers and kwargs** to test (#1302); fixtures stay synthetic.

### Skip policy — never silent

Every scheduled cell records an explicit **status**:

| Status | Meaning |
| ------ | ------- |
| `pass` | Cell ran; ingestion / smoke met the bar |
| `fail` | Cell ran; unexpected error or 0 ingestion when data was present |
| `skip:<category>+<reason>` | Cell **intentionally** not run; category + human reason required |

**Categories (closed set):**

| Category | When | Effect |
| -------- | ---- | ------ |
| `client-blocked` | Driver does not install/import on the client host | Becomes a **FINDING** for give-back / wheelhouse (#1182, #782 / GAP-001, #1171) — not a quiet pass |
| `engine-arch-n/a` | Engine not applicable on this client (engine is remote-only; local arch mismatch) | Documented N/A |
| `not-worth` | SaaS / HTTP path; platform-agnostic client | Default for cloud-lane unless live-account scheduled |
| `attempt` | Default — **always try** unless a skip category applies | |

Omitting a cell from the result table without `skip:…` is a **process defect**.

### Cross-refs

| Ref | Role |
| --- | ---- |
| [#1237](https://github.com/DataBoar/data-boar/issues/1237) | Remote SQL latency / resilience (seed) |
| [#1171](https://github.com/DataBoar/data-boar/issues/1171) | Min-spec compat-matrix epic (platform corners) |
| [#1302](https://github.com/DataBoar/data-boar/issues/1302) | Oracle / mssql+pyodbc timeout kwargs; Podman validation |
| [#1182](https://github.com/DataBoar/data-boar/issues/1182) | Wheelhouse for musl/no-AVX gaps (`client-blocked` → give-back) |
| [#782](https://github.com/DataBoar/data-boar/issues/782) / **GAP-001** | `boar_fast_filter` abi3 wheel matrix (platform track; not per-cpXXX DB drivers) |

---

## Execution checklist

| Step | Scope | Status |
| ---- | ----- | ------ |
| 1 | Publish this plan + hub + `PLANS_TODO` entry | ✅ |
| 2 | Inventory T14 Podman engines (mssql, oracle-free, pg, mysql, mariadb, mongo, redis, minio) | ⬜ |
| 3 | Axis B smoke from baseline client: each SQL + mongo + redis with **synthetic** fixtures; ingest > 0 | ⬜ |
| 4 | Axis A neutral smoke (FS/CSV/SQLite) on mini-bt, alpine-emachines, pi3b, T14/latitude | ⬜ |
| 5 | Sparse A×B: pymssql + psycopg2 from alpine-emachines (and pi3b) → remote T14; record pass/fail/`skip:client-blocked+…` | ⬜ |
| 6 | Oracle thin on baseline; thick on musl/arm → explicit skip or fail with Instant Client note | ⬜ |
| 7 | #1237 latency pass: alpine-emachines → remote Postgres (T14 and/or hosted) — timeout/retry notes | ⬜ |
| 8 | #1302 validation: oracle `tcp_connect_timeout` + mssql+pyodbc kwargs against Podman engines | ⬜ |
| 9 | Cloud-lane table rows with default `skip:not-worth` (or scheduled live-account) | ⬜ |
| 10 | Promote durable results into ops matrix / lab lessons (numbers only in tracked docs) | ⬜ |

---

## Acceptance criteria (plan scaffold)

- [x] Plan file exists with `<!-- plans-hub-summary: … -->` and sparse A / B / A×B model.
- [x] Topology documents T14 target farm + alpine-emachines remote light client (#1237).
- [x] Skip policy forbids silent omission; `client-blocked` maps to give-back/wheelhouse findings.
- [x] Synthetic-only data policy (no customer production snapshot).
- [x] Cross-refs #1237, #1171, #1302, #1182, #782/GAP-001.
- [ ] First axis B + sparse A×B evidence rows recorded (follow-up sessions).
