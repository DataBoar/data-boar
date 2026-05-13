# Lab-OP CAPEX/OPEX & Procurement (tracked, no prices)

**Status:** Pending
**Date:** 2026-04-02
**Authors:** Fabio Leitao
**Priority:** H2

**Purpose:** Provide one procurement decision spine for Lab-OP that covers **all major spending fronts** (hardware, storage, networking, power, HVAC, software/subscriptions, tokens, and training) while preserving financial detail in private notes only.

**Scope policy:**
- This tracked plan keeps **priorities, rationale, dependencies, and decision criteria**.
- **Real prices, supplier links, serials, local constraints, and negotiations** stay only in `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md` (gitignored).

**Related plans and docs:**
- [PLANS_TODO.md](PLANS_TODO.md)
- [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md)
- [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)
- [PLAN_READINESS_AND_OPERATIONS.md](PLAN_READINESS_AND_OPERATIONS.md)
- [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md)
- [LAB_OP_SHOPPING_LIST_EXAMPLE.md](../ops/LAB_OP_SHOPPING_LIST_EXAMPLE.md)

## 1) Procurement principles (budget-safe)

1. **Protect runway first:** prioritize spend that reduces incident risk, downtime, or blocked delivery.
2. **Measure before buying:** baseline current bottlenecks (thermal, power, RAM, I/O, uptime, alert fatigue).
3. **Prefer reversible increments:** staged upgrades over all-at-once replacement.
4. **Automate what creates recurring toil:** every repeated manual pain is OPEX leakage.
5. **Avoid duplicate stacks by default:** one strong path per capability before parallel tools.

## 2) Priority lanes (P0 / P1 / P2)

### P0 — Prioritario (stability and risk reduction)

- **Power and electrical safety**
  - Validate branch capacity, breaker map, and realistic peak load envelope.
  - Confirm whether utility load-increase request is required before adding sustained loads.
- **Core host reliability**
  - Resolve storage health blockers, failed drives, and pending repairs before expansion buys.
  - Prioritize RAM/storage upgrades only where current hosts are proven bottlenecks.
- **Network survivability baseline**
  - Preserve secure remote access path and firewall posture.
  - Keep one clear minimum-viable redundancy path for WAN and management access.
- **Backup and recovery floor**
  - Guarantee at least one tested restore path for critical operator assets and runbooks.
- **Cooling as protection, not comfort-only**
  - Treat HVAC decisions as hardware longevity and operational continuity controls.

### P1 — Necessario (throughput and operational maturity)

- **Observability maturity**
  - Expand metrics/logging in sequenced phases after baseline stability.
  - Prioritize high-signal telemetry over dashboard quantity.
- **Capacity headroom**
  - Add compute/storage where evidence shows sustained pressure.
  - Standardize host classes for easier maintenance and spare planning.
- **Security hardening expansion**
  - Continue optional hardening rollout across hosts once baseline checks are green.
- **Workflow cost control**
  - Reduce recurring spend by consolidating overlapping SaaS/tools where feasible.
- **Training with direct execution impact**
  - Sequence trainings that immediately improve delivery quality or sales readiness.

### P2 — Sonhos (strategic upside after runway-safe baseline)

- **Infrastructure redundancy beyond minimum viable**
  - Higher-grade HA for WAN, gateway, and compute orchestration.
- **Premium observability/security stacks**
  - Broader SIEM/APM depth once P0/P1 are stable and used effectively.
- **Comfort and expansion upgrades**
  - Additional HVAC/energy optimization beyond immediate risk controls.
- **Advanced experimentation**
  - Optional tooling and labs for future product lines and thesis/research tracks.

## 3) Domain-by-domain optimization map

### 3.1 Compute hosts (laptops, servers, SBCs, VMs)
- Keep an explicit role for each host class: operator workstation, lab services, edge/light node.
- Upgrade only when one of these is true: repeated saturation, blocked roadmap tasks, or risk concentration.
- Prefer compatible, reusable parts and spare strategy over one-off exotic SKUs.

### 3.2 Storage and backups
- Repair and health-validate current assets before net-new storage purchases.
- Separate performance storage from backup/archive responsibilities.
- Define retention tiers and restore RTO/RPO targets before capacity expansion.

### 3.3 Network and access
- Keep segmentation and firewall intent documented and testable.
- Prioritize management-plane stability and secure remote access continuity.
- Evaluate redundancy in router/gateway and internet paths by business impact, not by topology complexity alone.

### 3.4 Power, solar, and utility envelope
- Track real consumption windows and peak behavior prior to major electrical changes.
- Model incremental growth scenarios (current baseline, near-term, and stress case).
- Use measured data to decide: utility upgrade now, defer, or stage with local mitigations.
- Keep a hard dependency Colleague-Nn: meter/contract validation -> UPS sizing -> utility increase request.

### 3.5 HVAC and environment
- Compare keep/repair/replace options by total operational impact: thermal stability, noise, efficiency, maintainability.
- Prefer decisions backed by measured thermal behavior during real workloads.
- Use phased rollout if one unit can stabilize current risk while larger upgrades are deferred.

### 3.6 Security and resilience tooling
- Prioritize controls that prevent high-impact failure modes first.
- Keep optional components opt-in until host capacity and operational discipline are proven.
- Tie each new control to an owner, runbook, and validation checkpoint.

### 3.7 Software, licenses, subscriptions, tokens, training
- Maintain a single recurring-cost inventory with owner and renewal month.
- Remove overlaps and underused seats before adding new subscriptions.
- Treat token budgets as production resources with explicit monthly caps and outcomes.
- Prioritize training that accelerates client delivery, hardening confidence, or evidence generation.

### 3.8 Product-facing cloud cost exposure (future connectors)
- When object storage connectors evolve, separate **Lab-OP cost** from **customer cloud runtime cost**.
- Define who pays variable cost components (egress, API calls, storage operations, retention).
- Keep this boundary explicit to avoid hidden OPEX in delivery estimates.

### 3.9 Engineering platform OPEX (CI and maintenance)
- Track CI runtime pressure and matrix sprawl as recurring engineering cost.
- Prefer targeted quality gates that preserve safety while containing unnecessary runner minutes.
- Reassess tooling overlap in security/lint pipelines before adding net-new paid tooling.

## 4) CAPEX/OPEX decision gates (before purchase approval)

For each candidate acquisition, record:
- **Why now:** objective pain/risk and affected workflow.
- **What happens if deferred 30/60/90 days:** quantified downside.
- **Dependency map:** prerequisites and blockers.
- **Cheaper equivalent path:** reuse/repair/reconfigure option considered.
- **Build vs buy decision:** self-hosted versus SaaS trade-off and operator burden.
- **Operational burden:** setup, maintenance, monitoring, and replacement complexity.
- **Success metric:** what must improve after adoption.

If these fields are not clear, the item stays in backlog.

## 5) Execution cadence (procurement rhythm)

1. Refresh host facts and reports.
2. Re-rank P0/P1/P2 based on current evidence.
3. Promote only a small number of items into the active spend window.
4. Execute one coherent procurement batch at a time.
5. Re-measure outcomes before approving next batch.

## 5.1 Monthly execution model (budget windows)

Use one monthly cycle with four fixed windows:

- **W1 - Evidence and triage**
  - Refresh private inventory, host reports, and recurring-cost table.
  - Confirm what changed since last month (failures, saturation, incidents, renewals).
- **W2 - Decision and freeze**
  - Build a strict shortlist (`P0` first, limited `P1`, `P2` default freeze).
  - Run decision gates for each candidate and freeze out-of-scope items.
- **W3 - Procurement and implementation**
  - Execute one coherent batch only (for example: power + backup, or network + access).
  - Capture implementation notes and owner.
- **W4 - Verification and postmortem**
  - Validate expected outcomes against success metrics.
  - Record what worked, what drifted, and what rolls into next month.

## 5.2 Budget window policy (guardrails)

- **Default freeze policy:** if an item is not explicitly promoted in `W2`, it stays deferred.
- **P0 reserve:** keep a protected portion of budget for safety/reliability incidents.
- **Change cap:** avoid multiple unrelated procurement tracks in the same month.
- **No-evidence no-spend:** if measurement is missing, do not approve spend.
- **Rollback mindset:** prefer choices with reversible impact and low lock-in.

## 5.3 Monthly output package (what must exist)

At month close, produce these artifacts:

- Updated private recurring-cost table (renewals, cuts, additions).
- `P0/P1/P2` ranking snapshot for the next cycle.
- Implemented batch log (what was bought/changed and why).
- Outcome check (metrics improved or not, with next actions).
- Deferred backlog note (what was intentionally postponed).

## 6) Public vs private split (hard rule)

- **Tracked docs (`docs/`)**
  - Priorities, architecture rationale, decision criteria, and non-sensitive checklists.
- **Private docs (`docs/private/`)**
  - Prices, supplier choices, negotiations, serials, utility account constraints, photos, and local runbooks.

## 7) Initial action list (next practical slice)

- Create/refresh a private recurring-cost inventory table (subscriptions, licenses, tokens, training).
- Confirm current storage status and repair/replace decision points in private inventory.
- Capture measured thermal and power baseline for current operating profile.
- Reconcile network redundancy options with real incident impact.
- Select a strict P0 subset for the next budget cycle, then defer everything else by default.

## 7.1 First monthly cycle bootstrap (immediate)

To start now without overcomplicating:

1. Open a new private monthly sheet (`YYYY-MM`) in the shopping master.
2. Pick at most **3 P0 items** for this cycle.
3. Allow at most **2 P1 candidates** as optional if P0 remains under control.
4. Keep all `P2` frozen for this cycle unless a blocker is removed.
5. End month with a short outcome review and carryover list.

## 8) Status

- **State:** Active planning and budget discipline anchor.
- **Implementation policy:** This plan guides sequencing and spending decisions; technical implementation continues in domain-specific plans and runbooks.

