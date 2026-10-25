# Stale feature-flag audit — 2026-04-27

> **Trigger:** Slack handoff `[CLEANUP PROTOCOL: STALE FEATURE-FLAG REMOVAL]`
> from the **SRE Automation Agent** (channel `C0AN7HY3NP9`, message
> `1777310318.237219`).
>
> **Branch (audit deliverable):** `cursor/sre-automation-agent-protocol-84a1`.
> The agent did **not** push to any third-party PR branch; this is the audit
> echo that lives on its own slice, by the same rule used for
> `PR_SECURITY_AUDIT_2026-04-27.md` (PR #234).

## TL;DR (Slack-shareable)

- :broom: **CLEANED FLAGS:** *(none)* — the codebase has **no stale feature
  flags eligible for surgical deletion** at 2026-04-27 16:08 UTC.
- :checkered_flag: **WINNING PATH:** *(no rewiring needed)* — every
  conditional branch the protocol could touch is still a **first-class
  configuration knob** or an **active open-core boundary**, not a vestigial
  rollout gate.
- :shield: **PARITY CHECK:** Production behaviour is unchanged — this PR is
  **documentation + a small regression guard**. Zero impact on database
  locks, scan paths, or scoring (see [§3](#3-defensive-architecture-zero-database-impact)).
- :gear: **STATUS:** *Candidate Found: Manual Review Required* — the
  Step-3 safety rule from the protocol applies (see [§4](#4-why-the-protocol-aborted-step-3-safety-rule)).
  Followed-up by adding a **regression guard test** so an unannounced
  Statsig / LaunchDarkly / Unleash / Flagsmith / Split.io SDK cannot land
  silently in a future PR.

---

## 1. Method (Julia Evans-style — what we actually grepped)

The protocol identifies "stale flag" candidates from three signal classes.
Each was searched against the index of `main` at this branch's base, plus
the working tree.

### 1.1 Third-party flag SDKs (the primary target)

```text
ripgrep -i  'statsig|launchdarkly|launch_darkly|unleash|flagsmith|ldclient|split\.io'  →  0 files
```

Cross-checked against `pyproject.toml`, `requirements.txt`, `pylock.toml`,
and the cargo manifests under `rust/` — none of those vendors are wired in.
That alone is the bulk of the protocol's *primary* scope.

### 1.2 Internal config toggles (the looks-like-a-flag class)

```text
ripgrep '_enabled|_disabled' --type py
ripgrep 'enable_pro|enable_pro_prefilter|use_density|use_all|use_ntlm'
```

| Symbol | Where | Class |
| ------ | ----- | ----- |
| `api.maturity_self_assessment_poc_enabled` | `config/loader.py`, `api/routes.py`, `tests/test_api_assessment_poc.py` | **Operator-tunable POC gate.** |
| `detection.aggregated_identification_enabled` | `core/aggregated_identification.py`, `tests/test_aggregated_identification.py` | **Detection-mode toggle.** |
| `report.jurisdiction_hints_enabled` | `tests/test_jurisdiction_hints.py` | **Report toggle.** |
| `fuzzy_enabled=` | `core/...`, `tests/test_fuzzy_column_match.py` | **Per-call argument** (not a runtime gate). |
| `RATE_LIMIT_ENABLED` | `config/loader.py` (env), `tests/test_rate_limit_api.py` | **Operator env / config knob.** |
| `enable_pro` / `enable_pro_prefilter` | `pro/prefilter.py`, `core/discovery_orchestrator.py` | **Open-core boundary** (active refactor — PR #246, ADR 0044). |
| `use_density` (`use_lgpd_density_risk`) | `scripts/generate_grc_report.py` | **CLI argument** to a developer-facing script. |
| `use_all` (file-extension wildcard) | `connectors/{webdav,smb,sharepoint,filesystem}_connector.py` | **Per-call extension expansion.** |

None of these match the protocol's definition of "stale". They are all
**explicitly documented user-facing knobs** (YAML, env, or function
parameters). Removing them would break documented behaviour and break the
regression suite.

### 1.3 Dead conditional branches near env reads

```text
ripgrep 'os\.(getenv|environ\.get)\b'  →  every hit reviewed
```

The interesting envs are all **active**: `DATA_BOAR_LICENSE_*` (licensing
guard, ADR 0044 in flight), `DATA_BOAR_DASHBOARD_TRANSPORT` /
`DATA_BOAR_DASHBOARD_INSECURE_OPT_IN` (HTTPS posture, `core/dashboard_transport.py`),
`DATA_BOAR_SQL_SAMPLE_LIMIT` / `DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS` /
`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT` /
`DATA_BOAR_MSSQL_TABLESAMPLE_SYSTEM_PERCENT` (relief valves —
[`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) §2),
`DATA_BOAR_MATURITY_INTEGRITY_SECRET` (HMAC seal),
`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`,
`DATA_BOAR_MACHINE_SEED`,
`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS` (opt-in destructive guard,
covered by `tests/test_primary_windows_destructive_repo_ops_guard.py`).

No env reads gate a "100 % rolled out" path that could be safely deleted.

---

## 2. Sidequest protection (the open-PR shield)

Per the protocol: *"If a flag is touched in an open PR, ABORT cleanup for
that specific flag to avoid merge hell."*

`gh pr list --state open` at audit time:

| PR | Title | Touches flag-shaped code? |
| -- | ----- | ------------------------- |
| **#246** | `feat(licensing): unified feature_gate facade for the open-core boundary (ADR 0044)` | **Yes — the whole tier_features / feature_gate module.** |
| **#243** | `docs(plans): RFC Slice 5 — Enterprise Hardening (gap analysis + reprioritization)` | Documentation overlap with tier roadmap. |
| **#235 / #236 / #232** | Pro vs OpenCore detector / report doctrine slices | Touches `pro/` and `core/detector.py`. |
| **#244** | `feat(report): DPO/CISO action-plan layer — LGPD/GDPR mapping + risk heatmap` | Touches `report/` (jurisdiction-hints area). |
| **#240** | `fix(security): close protocol-relative open-redirect in WebAuthn login safe_next_path` | Touches webauthn settings (env-based gate). |
| **#238** | `fix(security): drop bogus T-SQL OPTION (MAX_EXECUTION_TIME) on MSSQL sampling` | Touches MSSQL sampling (relief-valve area). |
| **#234** | `docs(ops): SRE security audit of open PRs (2026-04-27)` | Sister audit; same protocol family. |
| **#233** | `fix(ci): move SLACK_WEBHOOK_URL guard out of job-level if:` | CI surface only. |

**Conclusion:** every reachable candidate is "touched in an open PR".
The safety check **abort**s for each one.

---

## 3. Defensive Architecture (zero database impact)

This audit ships **two changes** and zero behaviour change:

1. `docs/ops/sre_audits/STALE_FEATURE_FLAG_AUDIT_2026-04-27.md` (this file)
   plus its pt-BR sibling.
2. `tests/test_no_third_party_feature_flag_sdks.py` — read-only, parses
   `pyproject.toml` / `requirements.txt` / `pylock.toml` and grepss the
   tracked Python tree for known-vendor markers.

Per [`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../inspirations/DEFENSIVE_SCANNING_MANIFESTO.md):

- **No DDL, no temp objects, no shared locks.** The new test never opens a
  customer connection — it parses files.
- **No `ORDER BY` on auto-sampling.** Not applicable; no sampling code is
  touched.
- **Coverage over truthfulness:** the test is allowed to *miss* a
  zero-day vendor name (it has a finite list), but it must not lie about
  what it found. We list the vendors checked **explicitly** in the test
  module so a future operator can extend the list with a one-line PR.

Per [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../inspirations/THE_ART_OF_THE_FALLBACK.md):

- The test reads each manifest with **`encoding="utf-8"`** and tolerates
  missing files (empty repo, partial checkout) by **degrading to a clear
  diagnostic** rather than throwing `FileNotFoundError`. That is the
  "diagnostic on fall" rule.

---

## 4. Why the protocol aborted (Step-3 safety rule)

The Slack protocol's Step 3 says:

> *"If the removal requires changing more than 3 related files to "fix"
> the architecture, it is too complex for automation. ABORT and report
> as 'High Risk Manual Cleanup'."*

The only *partial* candidate the agent found was the open-core
boundary — `pro/prefilter.py::get_prefilter(enable_pro=...)` plus its
caller in `core/discovery_orchestrator.py` plus the licensing tier map.
Cleaning that up properly involves at least:

1. `pro/prefilter.py`
2. `core/discovery_orchestrator.py`
3. `core/licensing/tier_features.py`
4. `core/licensing/runtime_feature_tier.py`
5. `tests/test_prefilter_contract.py`
6. `tests/test_tier_features_open_core_subscription.py`

That is **already** the subject of PR #246 (`feat(licensing): unified
feature_gate facade for the open-core boundary (ADR 0044)`). Touching it
from this audit branch would create exactly the merge-hell the Sidequest
Protection rule was written to prevent.

→ **Abort. Report. Echo.** — exactly what the protocol prescribes.

---

## 5. Anti-regression seatbelt (what *did* ship)

`tests/test_no_third_party_feature_flag_sdks.py` enforces:

1. The dependency manifests (`pyproject.toml`, top of `requirements.txt`,
   relevant section of `pylock.toml`) do **not** contain the substrings
   `statsig`, `launchdarkly`, `ldclient`, `unleash`, `flagsmith`, or
   `splitio` (case-insensitive, on dependency-name lines only).
2. No tracked **Python source file** (excluding `tests/`, `docs/`, and
   this audit's own paths) imports those vendors.

If a future PR wants to introduce one of those SDKs, the test will fail
loudly and force the author to (a) add an ADR, (b) update the test's
allow-list explicitly, and (c) pair the change with a documented rollout +
sunset plan. That is the seatbelt the protocol asked for, encoded as code.

---

## 6. Recommended next moves (operator-facing, GTD)

| # | Owner | Action |
| - | ----- | ------ |
| 1 | Maintainer | Land **PR #246** (open-core `feature_gate` facade, ADR 0044) — that is the *real* "winning path" for the tier-gate consolidation. |
| 2 | Maintainer | Re-run this audit as a 30-day cron once #246 lands; expect more candidates because the boundary will be uniform. |
| 3 | Contributors | If you add a new third-party flag SDK, update **both** `tests/test_no_third_party_feature_flag_sdks.py` **and** `docs/adr/` (new ADR) in the same PR. |

---

## 7. Form note (LMDE-style bug-fix issue inspiration)

Form-wise, this audit follows the same shape used in
[`linuxmint/live-installer#177`](https://github.com/linuxmint/live-installer/issues/177)
and
[`linuxmint/live-installer#178`](https://github.com/linuxmint/live-installer/issues/178):
exact reproduction (the grep commands above), the smallest claim that
matches the evidence ("no stale flags eligible"), the safety rule that
stopped the agent (Step 3), and the regression guard that prevents
recurrence.

---

*Generated by the Data Boar SRE Automation Agent on 2026-04-27, slice
`cursor/sre-automation-agent-protocol-84a1`. Companion (pt-BR):
[`STALE_FEATURE_FLAG_AUDIT_2026-04-27.pt_BR.md`](STALE_FEATURE_FLAG_AUDIT_2026-04-27.pt_BR.md).*
