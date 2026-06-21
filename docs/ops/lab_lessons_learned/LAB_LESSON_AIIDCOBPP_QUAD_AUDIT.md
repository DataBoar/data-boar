# Lab lesson — A.I.I.D.C.O.B.P.P. quad-audit pattern

**Português (Brasil):** [LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.pt_BR.md](LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.pt_BR.md)

**Date:** 2026-05-22/23 (session end)
**Protocol:** A.I.I.D.C.O.B.P.P. (see below)
**Status:** Empirically validated in lab production
**Reference ADR:** [ADR-0062](../../adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md)
**Diagram:** [`docs/adr/ADR-0062-diagram.mermaid`](../../adr/ADR-0062-diagram.mermaid)

Recovered from primary Windows dev workstation backup into public archive (GitHub **#992**). Hostname codenames in the original draft were removed per PII policy; topology uses **LAB-NODE-01/02** placeholders aligned with ADR-0062.

---

## What is A.I.I.D.C.O.B.P.P.?

**A**gent
**I**solation
**I**ndependent
**D**ual (expanded to N)
**C**ross-validation
**O**ffband
**B**us
**P**ing
**P**ong

In plain language: independent agent isolation with offband cross-validation via a ping-pong bus.

The canonical pattern name remains **triple-audit** (three original auditors). With a fourth auditor (mobile Claude) the configuration became **quad-audit**, but the protocol filename stays `triple-audit` — it is a pattern name, not a rigid counter. ADR-0062 **Extensibility** documents scaling to N auditors.

---

## Context — why the protocol exists

During wave-656 (PR #658), the Cursor agent exhibited rule-sequencing drift (`.mdc` rules), ignoring imperative scope boundaries. The agent operated autonomously beyond authorization, creating regression risk and off-band token consumption.

IDE-native barriers (Cursor rules, `AGENTS.md`) are necessary but insufficient to contain chronic non-determinism in long autonomous sessions.

**Conclusion:** No single agent — however well instructed — can be the arbiter of its own compliance.

---

## Protocol topology

```
Operator
│   ↓ distributes payload
├── Auditor A: Claude Windows (LAB-NODE-01) — field, repo access
├── Auditor B: Claude Linux  (LAB-NODE-02) — local topology verification
├── Auditor C: Gemini        — structural validation / control tower
└── Auditor D: Claude mobile — aerial view (shallow context)
         ↓ convergence
    Cursor / Git (executor — works only)
```

**Fundamental rule:** Auditors do **not** communicate with each other. The Operator is the physical data bus routing payloads via manual ping-pong.

> LLM consensus ≠ source of truth. The source of truth is the repository.

---

## What we learned

### 1. Blind spots are systematic, not accidental

Three LLMs converged on a wrong ADR filename without consulting the repo. Consensus amplified the error. Only repository verification corrected all three simultaneously.

### 2. Auditors with different context depth are complementary

- Auditors A/B/C were inside the forest — precise on trees, missed forest-level gaps.
- Auditor D (mobile, shallow context) surfaced eight documentary gaps, translation asymmetries, and format weeds the trio missed.
- The combination beats any single auditor.

### 3. Product CI detected PII that LLMs missed

`test_public_tree_no_l14_codename.py` blocked merge of an ADR draft containing real workstation codenames. Three LLM layers missed it; the automated guardrail intercepted before merge.

**Largest empirical validation:** the product detected PII in its own development process.

### 4. Rust guard changed the check-all ritual

A commit added `cargo fmt + cargo check + cargo test` to `check-all.ps1` without documenting rationale. Runtime grew from ~2–3 min to ~6 min, making routine pre-commit impractical and increasing `--no-verify` use.

### 5. ADR-0045 existed but was not consulted

ADR-0061 and ADR-0062 were drafted without the canonical MADR format from ADR-0045 — YAML lint errors, missing required fields, wrong metadata shape.

### 6. Issues created without P labels or milestone

Issues #668–#675 had correct bodies but no P labels or milestone — direct taxonomy contract violation (ADR-0055).

---

## Blameless incident table

| Incident | Root cause | Who caught it |
| --- | --- | --- |
| Real hostname codenames in ADR draft | LLMs did not verify vs repo | CI (`test_public_tree_no_l14_codename.py`) |
| Stale `INVENTORY.txt` hash | ADR fix did not refresh hash | Gemini (after CI log analysis) |
| ADR-0061/0062 off ADR-0045 format | ADR-0045 not consulted | Mobile auditor (aerial) + Windows auditor |
| #668–#675 missing labels/milestone | Manual browser creation | Linux auditor (post-compaction) |
| Rust guard in check-all | Cursor added without documented reason | Windows auditor (git log) |

---

## When to use

- Critical waves (G2/G3) touching security, IP, or architecture
- After autonomous agent scope drift in the prior session
- When long context may bias primary auditors
- **Not** for routine P3/backlog — toil does not pay

---

## Operating steps (summary)

1. Operator defines payload; opens isolated auditor sessions.
2. Ping-pong A ↔ B until convergence; escalate structural review to C; use D for forest-level gaps.
3. Only after auditor convergence → Cursor executes with explicit PASSO / ALLOW gates.
4. CI green → Operator merges (never the agent).
5. Final aerial pass on created artifacts; apply taxonomy if needed; local `check-all` as closing gate.

---

## ROI observed (wave-656 session)

| Metric | Value |
| --- | --- |
| PRs merged | 4 (#658, #665, #666, #667) |
| Issues created | 8 (#668–#675) |
| ADRs produced | 2 (ADR-0061, ADR-0062) |
| PII removed before merge | workstation codenames in ADR draft |
| Forest-level gaps (auditor D) | 8 documentary items |
| Final check-all | 1224 passed, 4 skipped, 0 failed |

For lower-severity future waves, triple-audit (A+B+C) without D is acceptable.

---

## Naming

- **Pattern name:** `triple-audit-offband-pingpong`
- **ADR filename:** `ADR-0062-agent-containment-triple-audit-offband-pingpong.md` — do not rename
- **Quad-audit:** descriptive term for four-auditor configuration, not a separate protocol name

---

## References

- [ADR-0062](../../adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md)
- [ADR-0061](../../adr/ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md)
- [ADR-0045](../../adr/ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR-0055](../../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md)
- [`docs/SECURITY_GOVERNANCE_POSTURE_HUB.md`](../../SECURITY_GOVERNANCE_POSTURE_HUB.md)
- Issues #668–#675 · PRs #658, #665, #666, #667

Roster reconciliation with current harness usage tracks GitHub **#991** (ADR-0062 amendment).
