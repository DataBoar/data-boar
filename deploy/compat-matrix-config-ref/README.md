# `compat-matrix-config-ref` — comparable `config.yaml` across corners (#1368)

Companion to the OS `--demo` matrix in
[`docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md`](../../docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md).
While the `--demo` matrix proves **install and dependencies**, this harness proves what
it **does not touch**: the post-GA fix surface (post3→post10) — archives, connectors,
latency, throttler.

> **"The matrix closed" means install, not connectors.** Those are orthogonal axes.
> The 10-point `--demo` matrix does not execute a single line of connector code.

## Why this lives under `deploy/` (not vault-only, not inside `lab-smoke-stack/`)

| Option | Verdict |
| --- | --- |
| **Vault only + repo pointer** | Rejected — acceptance needs a **versioned, cloneable** harness; design invariants must survive without operator-local notes. |
| **`deploy/lab-smoke-stack/`** | Rejected as home — layer 1 is an **OS-corner filesystem** run (wheelhouse / Podman / metal). Nesting it under the DB Compose bundle implies the wrong owner. |
| **`docs/ops/` alone** | Rejected — YAML + runnable shell are deploy-time assets, not prose. |
| **`deploy/compat-matrix-config-ref/`** (here) | **Chosen** — sibling of `lab-smoke-stack/`: layer 2 *targets* that stack; layer 1 stays independent; discoverable next to other deploy harnesses. |

Operator session notes / raw corner transcripts may still live in the private vault; this
directory is the **canonical tracked source**.

## Two layers, for a reason

| Layer | File | Credential | Runs where |
| --- | --- | --- | --- |
| **1 — files** | `config-files.yaml` | **none** | any corner, including the Celeron floor |
| **2 — databases** | `config-db.yaml` | `pass_from_env` only | corners with LAN reach to `lab-smoke-stack` |

Layer 1 is what produces the **comparable number**. If it required credentials, it would
stop running on the most constrained corners — exactly the ones that matter most.

## Three design decisions (do not “optimize” these away)

### 1. Comparable output has TWO measures, not one

1. **findings** by sensitivity
2. **`scan_failures` BY REASON**

For this family of fixes, **absence of error is not a result**. The result is the failure
staying **visible when it should occur**. A scan that “passes clean” is exactly the symptom
[#1354](https://github.com/DataBoar/data-boar/issues/1354) and
[#1348](https://github.com/DataBoar/data-boar/issues/1348) attack — and what produced, in
the field, *“7 findings become 1, and `scan_failures` with 0 rows”*.

### 2. `max_workers: 1`

The matrix floor is **single-core** (Celeron 900). Comparability requires the **same
parallelism** on every corner. This is **not** a performance tweak.

### 3. `adaptive_rate_limit: true` even on local targets

On purpose — to prove that enabled does **not** change the **RESULT**, only the pace
([#1320](https://github.com/DataBoar/data-boar/issues/1320)).

## Corpus: fixtures from this repo

Extracted from `origin/main` (`tests/data/`), **once**, and mounted read-only into each
corner — same bytes everywhere, checked by SHA-256. Per-corner extraction would open
space for silent divergence — the failure mode this config exists to catch.

| Fixture | Role |
| --- | --- |
| `sample1.zip` · `sample3.tgz` | normal compressed read (#828, #1250, #1257) |
| `sample2.7z` | needs extra `[compressed]` (py7zr) — see finding below |
| `sample4.tar.bz2` | **gzip with a lying extension** → `archive_type_mismatch` (#1354 Part A) |
| `homelab_synthetic/` | baseline PII/ML findings, including `DOB_POSSIBLE_MINOR` |

`sample3.tgz` and `sample4.tar.bz2` have the **same bytes and size**. The lying extension
is **deliberate** — bait for content-type detection.

## Measured baselines (2026-07-29) — do not re-run to “prove” the PR

### Layer 1 — identical on 6 points

debian, fedora, alpine cp312, alpine cp314, void-musl, and **metal** alpine-emachines
(Celeron 900):

```
19 findings | archive_unsupported=1 · archive_type_mismatch=1
```

A corner with extra `[compressed]` (py7zr) gave **26** and only `archive_type_mismatch=1`.

**Exact delta: 7 findings** = contents of `sample2.7z`, unreadable without py7zr.

The point to keep: the 7 lost findings do **not** vanish silently — they become
`archive_unsupported` in `scan_failures`. Capacity degraded, and the product **said** it
degraded. `archive_type_mismatch` appeared on **every** corner — first field exercise of
#1354 Part A outside unit tests.

### Layer 2 — after #1369 sidecars + #1370 Oracle fix

Against `deploy/lab-smoke-stack`:

| Engine | Findings | `scan_failures` |
| --- | ---: | --- |
| Postgres | 20 | none |
| MariaDB | 20 | none |
| MSSQL | 20 | none |
| Oracle | 20 | none |
| Redis | **5** | none |

Redis **5** is the **correct** baseline, not a defect: the seed exists to expose #1348
(connector uses `GET` only; PII in hash/list/set must not appear until the fix).

## Usage

```sh
# Layer 1 — one corner (data-boar on PATH)
sh deploy/compat-matrix-config-ref/run-config-matrix.sh [work-dir]

# Layer 1 — all container corners; corpus mounted read-only
# musl corners need: export WHEELHOUSE_DIR=/path/to/wheelhouse-x86-64-v1
bash deploy/compat-matrix-config-ref/run-across-corners.sh

# Layer 2 — copy config-db.yaml, set REPLACE_WITH_LAB_HOST_IP, export env.example
# passwords via pass_from_env, then:
#   data-boar --config ./config-db.local.yaml
# Compare findings per engine + scan_failures BY REASON (same two measures).
```

`config.lab-smoke.example.yaml` remains the **quick smoke** copy (inline example
passwords for the synthetic stack). This directory is the **comparable matrix** contract
(`max_workers: 1`, throttler on, `pass_from_env` only, dual measures).

## Pitfalls already paid (do not repeat)

- **`--demo` does not return** — runs the scan and leaves the API listening on
  `127.0.0.1:8088`. These scripts use `--config`, which **returns**.
- **`--demo` report** goes under `$TMPDIR/data_boar_demo`; with `--config` it respects
  `report.output_dir`.
- **`--platform linux/amd64` explicit** on every `podman run` — without it a local tag
  may be another architecture and the corner runs emulated (30+ min stuck — measured).

## Related

- Seeds / Compose: [`deploy/lab-smoke-stack/`](../lab-smoke-stack/)
- OS install matrix: [`docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md`](../../docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md)
- Issues: [#1368](https://github.com/DataBoar/data-boar/issues/1368) · [#1354](https://github.com/DataBoar/data-boar/issues/1354) · [#1348](https://github.com/DataBoar/data-boar/issues/1348) · [#1320](https://github.com/DataBoar/data-boar/issues/1320) · [#1237](https://github.com/DataBoar/data-boar/issues/1237)
