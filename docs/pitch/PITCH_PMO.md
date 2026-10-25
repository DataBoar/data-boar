# PMO pitch — delivery, risk, and evidence cadence

**Português (Brasil):** [PITCH_PMO.pt_BR.md](PITCH_PMO.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** PMO leads, programme/project managers, delivery managers who need scan evidence without owning detector internals.

---

## Why this conversation is not the CISO deck

The PMO asks **when**, **who is blocked**, and **what evidence exists for the current increment** — not SIEM replacement or control catalogues. Data Boar produces **session-bound** discovery artefacts so a programme can show progress against **configured targets**, not a promise that every sprint or repository is already heatmapped.

## What the PMO typically asks

| Question | Honest product answer today |
| -------- | --------------------------- |
| Can we see risk by **source** this week? | Yes: findings and heatmaps **by configured source and scan session** — [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) |
| Can we see risk by **team / sprint / git repo**? | **Not yet.** That granularity is tracked as GitHub [#677](https://github.com/DataBoar/data-boar/issues/677). Do not brief the board as if it shipped. |
| Can we trend over time? | Yes: session-over-session **trend** on the same target set |
| Does a green scan mean the increment is “done”? | **No.** A scan is technical evidence for triage, not a substitute for code review, UAT, or legal sign-off |

## Agile cadence (how to use the tool)

1. **Scope the increment:** list systems in this sprint’s scan YAML (`targets`) — coverage is **configured scope**, not the CMDB.
2. **Run a bounded session** (timeouts, sampling, non-prod first).
3. **Export** XLSX / heatmap / optional manifest YAML for the stand-up or risk review.
4. **Ticket** findings to owners — storyboard: [use-cases/USE_CASE_SCAN_AND_REMEDIATE.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.md).
5. **Re-scan** the same targets to show trend, not a new universe of assets.

Executive JSON for downstream GRC/BI: [GRC_EXECUTIVE_REPORT_SCHEMA.md](../GRC_EXECUTIVE_REPORT_SCHEMA.md).

## What this is not

- Not a **code-review** or SAST replacement.
- Not a **blame** report — findings are coordinates and categories, not named culprits.
- Not a **delivery-risk** engine (schedule, budget, RAID logs stay in the PMO tool).
- Not org-wide **asset completeness** — only what you configured.

## Shared responsibility

The PMO owns increment scope, stakeholders, and acceptance. Data Boar owns configured technical reads and structured outputs. Leadership brief: [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md).

## Next step

- **Board:** [PITCH_STAKEHOLDER.md](PITCH_STAKEHOLDER.md)
- **Security controls:** [PITCH_CISO.md](PITCH_CISO.md)
- **Finance exposure:** [PITCH_CFO.md](PITCH_CFO.md)
