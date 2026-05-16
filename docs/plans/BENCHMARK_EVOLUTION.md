# Benchmark evolution — completão A/B (legacy lab ref vs current)

**Status:** living note — **2026-04-27 session:** SRE fixes landed in `main` (SSH/git stderr, `completaoImageRefs` parsing, benchmark harness defaults). **Wall-clock A/B** from `scripts/benchmark-ab.ps1` was **started** but **did not finish** within the agent tool window (Round A can exceed **60 minutes** on the full multi-host manifest). Fill **Performance** from `benchmark_runs/times.txt` + `benchmark_runs/telemetry.json` after a successful local run. Operator notes (pt-BR): `docs/private/homelab/BENCHMARK_AB_OPERATOR_NOTES_2026-04-27.pt_BR.md`.

**Scope:** Lab orchestration (`lab-completao-orchestrate.ps1`) plus optional **`data-boar-report`** (`python -m cli.reporter`, see [USAGE.md](../USAGE.md) section 5) when the benchmark script is invoked with `-ReportConfigYaml` / `-ReportSessionId`.

---

## 1. Executive Markdown (`data-boar-report`) — required sections (code contract)

The stakeholder Markdown produced by `report.executive_report.generate_executive_report` always includes:

| Stakeholder ask | Markdown heading / block | Role |
| --- | --- | --- |
| **Action Plan (APG)** | `## 4. Plano de ação (APG)` | `### 4.1 Prioridades imediatas (Top 3)` — ranked recommendations; `### 4.2 Inventário por tipo de dado (achado → risco → recomendação técnica)` — full per-pattern inventory. |
| **Audit / methodology evidence** | `## 3. Metodologia e segurança` | Sampling caps, timeout hints, dialect posture (e.g. SQL Server `WITH (NOLOCK)` when applicable), leading SQL comment traceability. |
| **Manifest pointer (audit artefact)** | Footer line | `**Evidência técnica:** \`scan_manifest_<prefix>.yaml\`` — companion YAML emitted with the scan/evidence pipeline (`scan_manifest_*.yaml`). |

So: **APG** = section **4**; **audit evidence** = section **3** (narrative + manifest bullets) **plus** the explicit **`scan_manifest_*.yaml`** reference (and the YAML file itself when the full pipeline runs).

### 1.1 APG examples (contract from tests — not lab PII)

From `tests/test_executive_report.py` (minimal mock `apg_rows`), the generator surfaces **pattern-specific** remediation language in **§4**, for example:

1. **EMAIL / homologation-style masking:** recommended action text includes **"Homologar mascaramento."** (staging / non-prod flows).
2. **CREDIT_CARD / PCI-style handling:** recommended action text includes **"Tokenizar PAN."** (tokenization / PAN handling narrative).

These demonstrate that **v1.7.4-beta** class stacks ship **APG-ready** Markdown when `apg_rows` are populated (SQLite + reporter path); compare to **v1.7.3** product slice where the **`data-boar-report`** CLI path and manifest-forward audit narrative were materially thinner — see §2.

---

## 2. Delivery gain — what the client receives today that v1.7.3 did not ship

| Before (e.g. **v1.7.3** tag on lab clone) | After (current product + benchmark round B) |
| --- | --- |
| **No** `data-boar-report` entrypoint to regenerate **desk-ready executive Markdown** from **SQLite alone** (no new live connector reads). | **`data-boar-report`** (see USAGE): reproducible **executive Markdown** from a fixed `session_id` + config — useful for committees, DPO/CISO packs, and audit **preparation**. |
| Stakeholder narrative tied only to **Excel/heatmap** generation path when reports run. | **APG-aligned** Top 3 + **full per-pattern remediation inventory** in Markdown (patterns and counts — **not** raw table/column/cell samples). |
| Limited **machine-readable** “how we read” evidence alongside the desk doc. | **`scan_manifest_*.yaml`**: sampling/timeouts, `safety_tags`, `audit_trail` / DBA-facing bullets — **governance-adjacent** evidence aligned with [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md). |

Net: the **client** gains a **repeatable, session-scoped governance narrative** (methodology + APG + manifest pointer) **without** re-running scans — that path did not exist as a first-class CLI deliverable on the legacy tag side of the A/B.

---

## 3. KPIs — performance (wall time — completão orchestrator)

**Source of truth after a successful run:** `benchmark_runs/times.txt` and `benchmark_runs/telemetry.json` (written by `scripts/benchmark-ab.ps1`).

| Round | Git ref (lab alignment) | `Measure-Command` / `telemetry.json` | Value (2026-04-27) |
| --- | --- | --- | --- |
| **A — Legacy** | `v1.7.3` on lab repos (`-LabGitRef`), local scripts stay on current branch unless `-LocalLegacyCheckout` | `legacy_total_seconds` | **Not captured** — run exceeded session tool budget during Round A. |
| **B — Current** | e.g. `origin/main` via `-CurrentLabGitRef` | `current_total_seconds` | **Not captured** (Round B not reached in that timed attempt). |

**Isolated gate (for scale, not the full orchestrator):** `lab-op-git-ensure-ref.ps1 -Ref v1.7.3 -Mode Check` completed in roughly **tens of seconds** across the four-host manifest in this workspace — useful as a **lower bound** for the git-alignment slice only.

**Interpretation:** treat published **delta_seconds** from `telemetry.json` as **orchestrator wall time** (SSH, inventory preflight, data-contract + image preflight, host smoke, optional GRC hooks). A swing is **significant** only if repeats cluster on the same manifest and lab day.

---

## 4. Security — “protocols” and scan posture (evidence model)

**Clarification:** `safety_protocol` / `sampling_rate` / `query_timeout` are **not** canonical columns on `scan_sessions` in `core/database.py` (compare `v1.7.3` vs `main` — both use **migrations** for tenant/technician/config hash/jurisdiction hints on `scan_sessions`). Posture for sampling and timeouts lives in:

- **`scan_manifest_*.yaml`**: `safety_tags`, `audit_trail`, scope snapshot, engine signature.
- **Executive Markdown §3**: human-readable condensation of that posture.

| Signal | Where it appears | Legacy vs current (conceptual) |
| --- | --- | --- |
| Sampling row caps / strategy | `safety_tags` / audit narrative | Current stack documents **resolved caps** and **timeout hints** for DB sampling (see `report/scan_evidence.py`, `core/scan_audit_log.py`, `connectors/sql_sampling.py`). |
| Dialect / isolation bullets (e.g. `NOLOCK`, `statement_timeout`) | `audit_trail.dba_facing_summary_pt` + §3 text | **Newer** manifests/tests expect these bullets when SQL Server (or other configured engines) participate — diff `scan_manifest_*.yaml` under `benchmark_runs/v1.7.3/` vs `benchmark_runs/v1.7.4-beta.1/` after a successful capture. |
| Traceability comment on sample SQL | `leading_sql_comment` / §3 | Confirms **attributed** workload in engine telemetry. |

**v1.7.3 “blind” claim:** the **tag-era** desk outputs do **not** carry the same **first-class** `data-boar-report` + manifest-forward audit bundle as today; SQLite **session** tables alone were never the home for `safety_protocol` as a column — avoid over-reading schema diffs without the YAML.

---

## 5. RCA — what blocked / slowed the automated A/B in-session

| Symptom | Root cause | Fix (shipped on `main`) |
| --- | --- | --- |
| `NativeCommandError` / stderr from **`ssh.exe`** (Debian motd, **`git fetch`** progress) under **`$ErrorActionPreference = Stop`** | PowerShell treats native stderr as **error records** when merged naively | **`lab-op-git-ensure-ref.ps1`**: remote git over SSH now uses **`Start-Process`** with redirected stdout/stderr to temp files; **`ssh -q`** on probe lines. |
| **`Test-CompletaoRemoteDockerImage`** parameter binding failure on **`ImageRef`** | `completaoImageRefs` JSON **string** made PowerShell iterate **characters**; odd types slipped into the preflight loop | **`Get-CompletaoImageRefsFromManifest`**: handle **string** root + object `{ref,image}` forms; preflight loop coerces with **`[Convert]::ToString`** before `image inspect`. |
| Benchmark “legacy” checkout broke old scripts | Local **`v1.7.3`** checkout runs **tag-era** scripts without the SSH stderr fix | **`benchmark-ab.ps1`**: default **lab-ref-only** Round A (`-LocalLegacyCheckout` to restore old behaviour). |
| **`Resolve-RepoRoot`** threw “property Path” | **`$MyInvocation.MyCommand.Path`** inside a **nested function** is not the `.ps1` path | Use **`$PSScriptRoot`** for repo root resolution. |

---

## 6. Log / audit consistency (SRE)

After the fixes above, **`lab-op-git-ensure-ref`** logs under `docs/private/homelab/reports/lab_op_git_ensure_ref_*.log` should again contain **full `LABOP_REF_*` transcripts** without the shell aborting mid-host. For **NOLOCK / sampling** language, continue to treat **`completao_*_orchestrate_events.jsonl`**, host smoke logs, and **`scan_manifest_*.yaml`** as the **audit-grade** evidence chain — diff Round A vs Round B folders once `benchmark_runs/` exists.

---

## 7. SQLite file size and row counts (operator checklist — post-run)

**Not asserted without two captured `.db` files:** byte size follows **row counts** in findings tables + optional aggregates.

```text
(Get-Item benchmark_runs/v1.7.3/*.db).Length
(Get-Item benchmark_runs/v1.7.4-beta.1/*.db).Length
```

Compare **and** `SELECT COUNT(*) FROM database_findings` / `filesystem_findings` per `session_id`. Optional: `uv run python scripts/benchmark_sqlite_diff.py <baseline.db> <head.db>`.

---

## 8. Governance matrix (this session)

| Area | Change |
| --- | --- |
| **Lab git alignment** | SSH remote capture hardened for **Stop** mode + noisy stderr. |
| **Image preflight** | Manifest parsing + safe coercion before **`docker/podman image inspect`**. |
| **Benchmark harness** | `telemetry.json` + optional **post-round** local shell RSS snapshot; **PSScriptRoot** fix; default **lab-ref-only** legacy round. |
| **Evidence split** | Tracked **`BENCHMARK_EVOLUTION.md`** stays generic; dated operator runbook in **`docs/private/homelab/`**. |

---

## 9. Readiness verdict (honest)

**Not a “production safer” claim from unfinished wall-clock numbers.** What **did** improve **lab operability and auditability** in this slice: reproducible **git ref checks** without stderr-induced false failures, safer **image ref** parsing, and a **benchmark harness** that separates **lab ref** from **local checkout** (reducing foot-guns). **Product security posture** (sampling, APG, manifests) advanced on **`main` vs v1.7.3** per §1–§2 and `PLANS_TODO` SQL sampling / APG threads — tie-break with **`check-all`** green + your own **`benchmark_runs/`** capture before telling a committee “we measured X% faster”.

---

## 10. Related automation

| Script | Purpose |
| --- | --- |
| `scripts/benchmark-ab.ps1` | Git-aligned A/B, `Measure-Command`, `benchmark_runs/times.txt`, **`telemetry.json`**, copy completao-era logs + optional SQLite / `data-boar-report` output. |
| `scripts/benchmark_sqlite_diff.py` | Table/column diff between two SQLite files (optional `scan_metadata` checklist if present). |

---

## Revision log

| Date | Author | Change |
| --- | --- | --- |
| 2026-04-27 | maintainer + agent | RCA + governance matrix + honest KPI state; APG examples from `tests/test_executive_report.py`; benchmark harness/telemetry notes. |
