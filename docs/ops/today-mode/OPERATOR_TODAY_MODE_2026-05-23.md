# Operator today mode — 2026-05-23

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-23.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-23.pt_BR.md)

**Note:** Drafted at **eod-sync / carryover** after **2026-05-22** — **CI on `main` is red** (fix before feature slices).

**`main` anchor:** merges **#665** (ADR-0061), **#666** (ADR-0062), **#667** (ISSUE_QUEUE_SEQUENCING_MAP); wave **#658** landed earlier. Open PRs: Dependabot **#660–#664**, draft **#365**, **#348**.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git pull origin main` · confirm **`ci.yml`** **green** before deep work — latest push failed on **`chore(agents): apply ADR-0062 and wave-656 learned facts to AGENTS.md`**.
2. **Open PRs:** triage Dependabot batch (**#660–#664**) only after **main** is green; skip **#365** while **DRAFT** unless intentional.
3. **Private stack:** **`.\scripts\private-git-sync.ps1 -Push`** — lab-* + **pCloud** OK; **VC bare `notes-sync.git`** only when **Z:**/**Y:** mounted.
4. **PMO:** **`pmo-view`** — [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) + [PLANS_TODO.md](../../plans/PLANS_TODO.md) Wave 1 row.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — priority **2026-05-23**

| Alvo | Row | Action |
| ---- | --- | ------ |
| **2026-05-23** | **L3** | LinkedIn lab-op Ansible/Docker CE — `deferred` → publish + hub URL |
| **2026-05-23** | **X6 / L7** | Eco **W6** gerúndio — drafts ready; publish after **W6** or same block |
| **Carry from 2026-05-22** | **IG3 / L6 / W5 / W6** | If still `draft`, close or defer with rename + hub update |

See [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md) · **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`**.

---

## Suggested focus (after CI green)

| Priority | Item | Notes |
| -------- | ---- | ----- |
| **P0** | **Fix `main` CI** | Inspect latest **`ci.yml`** run; thin fix PR |
| **Gate** | **#406** | Operator smoke **4 hosts** before stable **1.7.4** tag/Hub |
| **Map** | [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) | **NÃO INICIAR** v1.7.5-beta plugin chain before **#406** closed |
| **P0 product** | **#606** | Plugin hook — blocked by release gate per map |
| **Band A** | **–1 / –1b** | Only if deps or Dockerfile touched today |

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Release | **M-PILOT-READY / #406** | Wave **#656** docs/ADR slices merged; smoke remains operator |
| Governance | **ADR-0061 / #655**, **ADR-0062 / #659** | Merged; **#654** map merged **#667** |
| CI hygiene | **#388 Zizmor enforce** | Still blocked — findings remain; advisory mode |

---

## End of day (**2026-05-23**)

- **`eod-sync`** + **`private-stack-sync`** if private or social hub changed.
- Tomorrow checklist path: **`OPERATOR_TODAY_MODE_2026-05-24.md`** (create at next **eod-sync** if missing).
