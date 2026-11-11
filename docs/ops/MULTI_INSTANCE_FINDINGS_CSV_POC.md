# Multi-instance findings CSV (Phase 0 proof of concept)

**Português (Brasil):** [MULTI_INSTANCE_FINDINGS_CSV_POC.pt_BR.md](MULTI_INSTANCE_FINDINGS_CSV_POC.pt_BR.md)

**What this is:** a small script, [`scripts/multi_instance_findings_poc.py`](../../scripts/multi_instance_findings_poc.py),
that pulls `GET /findings/csv` from several Data Boar instances and merges the rows into one CSV,
adding the provenance the API does not emit (`node_id`, `fetched_at_utc`).

**What this is not:** a centralization feature. It is a documented stopgap for consolidated
review while the hub mode is designed (plan: `docs/plans/PLAN_MULTI_INSTANCE_REPORT_HUB.md`,
issue #2208). Do not describe it to anyone as "central management".

## Why a script is needed

The unified findings CSV has **no node or host column**, and its `id` is a per-node counter.
Concatenating CSVs from two nodes loses where each row came from. In a check on two isolated
synthetic `--demo` instances, **all 26 `id` values overlapped** between the nodes.

## Prerequisites

- Each node exposes its API to the machine that runs the script (`https`; plain `http` is accepted
  only for loopback in lab/demo).
- If a node enforces `api.require_api_key`, put its key in an **environment variable** named
  `DATA_BOAR_NODE_TOKEN_<NODE_ID>` (letters and digits of the id, upper-cased, other characters
  replaced by `_`; `site-a` becomes `DATA_BOAR_NODE_TOKEN_SITE_A`). Tokens are never accepted on
  the command line.

## Run

```bash
export DATA_BOAR_NODE_TOKEN_SITE_A='...'      # only if that node requires a key
uv run python scripts/multi_instance_findings_poc.py \
  --node site-a=https://boar-a.example.internal:8088 \
  --node site-b=https://boar-b.example.internal:8088 \
  --out /secure/location/merged_findings.csv
```

| Option | Meaning |
| ------ | ------- |
| `--node NODE_ID=URL` | Repeat per node. `NODE_ID` is a label you choose (letters, digits, `_`, `.`, `-`; must start with a letter or digit). |
| `--out PATH` | Merged CSV. Must be **outside** the repository tree; an existing file is refused unless `--overwrite`. Created with mode `0600`. |
| `--timeout`, `--max-bytes` | Per-node limits (defaults: 30 s, 64 MiB). |

Output columns: `node_id`, `fetched_at_utc`, then the node columns. Rows are deduplicated on
`(node_id, session_id, id)`. Each node contributes its **latest session only**.

Exit codes: `0` all nodes merged, `2` some nodes failed (the rest were merged), `1` nothing
merged or invalid usage. Failures are reported per node without printing URLs or tokens
(`timeout`, `connection error`, `authentication rejected (HTTP 401/403)`, `no scan session on node
(HTTP 404)`, `redirect received (not followed)`, `unexpected CSV header`).

## Safety notes

- The merged CSV holds **paths and host names**, which are sensitive. Keep it on an encrypted,
  access-controlled location and never commit it.
- Redirects are never followed, so a token cannot be forwarded to another host.
- This PoC does not verify a node's identity beyond TLS: choose `NODE_ID` labels deliberately.

## Verify it locally with synthetic data

Two `--demo` instances on one host **must not share the temp directory**: both use
`<tmp>/data_boar_demo`, and starting the second broke the first in our check (HTTP 500 on
`/findings/csv`, `unable to open database file`). Give each its own `TMPDIR`:

```bash
mkdir -p /tmp/boar-a /tmp/boar-b
TMPDIR=/tmp/boar-a uv run python main.py --demo --port 8101 &
TMPDIR=/tmp/boar-b uv run python main.py --demo --port 8102 &
# wait until both answer 200 on /findings/csv, then:
uv run python scripts/multi_instance_findings_poc.py \
  --node demo-a=http://127.0.0.1:8101 --node demo-b=http://127.0.0.1:8102 \
  --out /tmp/merged_demo.csv
```

Observed on 2026-11-11 (synthetic corpus, two instances): `demo-a` 26 rows, `demo-b` 26 rows,
52 merged rows, exit `0`. These figures describe the demo corpus only; they say nothing about
performance or capacity on real data.

## Limits

Latest session per node only; no scheduling; no cross-node deduplication of the same file seen
by two nodes (that is a modelling decision for the hub phase); no Excel output.
