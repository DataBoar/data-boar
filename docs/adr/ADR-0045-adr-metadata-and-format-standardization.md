# ADR 0045 — ADR metadata and format standardization

- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-12 — Accepted
- 2026-06-09 — Amended: append-only Status history, immutable Date (UTC), extended status enum (Duplicate of ADR-NNNN), locale en_US, immutability clause — [GitHub #803](https://github.com/FabioLeitao/data-boar/issues/803)
- 2026-06-09 — Amended: UMADR declaration + Obsolete/Quarantined statuses — [GitHub #803](https://github.com/FabioLeitao/data-boar/issues/803)

## Context

Architecture Decision Records are durable governance artifacts in this repository.
They capture trade-offs, constrain future changes, and support auditability.

As the ADR corpus grows, inconsistent metadata or section structure increases review
cost, weakens traceability, and blocks reliable tooling queries (for example:
"list Deferred decisions", "show superseded ADRs", "find decision owner").

The repository already enforces ADR index parity and multiple gate layers
(pre-commit, tests, CI), but ADR document shape is still convention-heavy and not
fully standardized as a decision record contract.

A real edge case (2026-06-09, **ADR 0068** context on the operator temporary primary
Linux dev workstation) exposed gaps that neither Nygard (2011) nor MADR cover by default:
a stale **duplicate file** of an existing decision (pre-0045 naming, no `ADR-` prefix),
MADR-style **mutable `date`** fields that overwrite genesis, and no explicit **en_US-only**
locale rule in the ADR constitution itself.

## Decision

1. **Immutability:** Architecture Decision Records in this repository are **never deleted**.
   When a record is obsolete, wrong, duplicated, or replaced, **only status changes**
   (via append to **Status history** and update of **Status**). Deleting an ADR destroys
   the durable decision trail the format exists to preserve.

2. **UMADR (Unified MADR — in-house extension):** This repository's ADR constitution is
   **UMADR**: MADR/Nygard roots plus **U = Human-in-the-Loop** (single maintainer curator;
   curated mutability **recorded** in Status history, not rigid immutability of body text).
   UMADR adds:
   - **Append-only Status history + immutable genesis `Date (UTC)`** — lifecycle visible
     in the record, not reconstructed from git; status transitions never overwrite genesis.
   - **Extended status enum** for edge cases Nygard/MADR lifecycle models do not separate
     (Duplicate, Obsolete, Quarantined — see below).
   - **No deletion** — status transition only (item 1).
   - **en_US single-tier** — ADRs are technical records, not paired operator docs.
   Full manifesto prose: [PLAN_ADR_GOVERNANCE_LIFECYCLE.md](../plans/PLAN_ADR_GOVERNANCE_LIFECYCLE.md)
   (*UMADR manifesto*).

3. From this ADR forward, repository ADRs must use a MADR/UMADR-aligned structure with
   explicit metadata and canonical sections:

```markdown
# ADR NNNN — Title

- **Date (UTC):** YYYY-MM-DD
- **Authors:** name(s)
- **Deciders:** name(s)
- **Consulted:** name(s) (optional)
- **Informed:** name(s) (optional)

## Status

<current status — see enum below>

### Status history

- YYYY-MM-DD — <event or status label>
- YYYY-MM-DD — Amended: <short reason> (optional)

## Context
## Decision
## Rationale
## Consequences
## Alternatives Considered
## Related Decisions
## References (optional)
```

3. **Metadata / lifecycle (Escola B — Status history append-only):**
   - **`Date (UTC)`** in the metadata block is the **genesis date of the file, immutable**
     (even for a solo author). If missing at creation, anchor **`git log`** first-appearance.
     **Never overwrite** on later edits or status transitions.
   - **`## Status`** holds the **current** status string (what `scripts/inv-adr.ps1` and
     `docs/adr/INVENTORY.txt` read — see [ADR 0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)).
   - **`### Status history`** is **append-only**: one dated line per transition or audit note
     (`YYYY-MM-DD — <event>`). Include `Audit:` lines when a registry problem is understood.
     **Never rewrite** prior lines; only append.

4. **Status enum** (template line for new ADRs; **`## Status`** may hold the plain or
   compound form):

```
[Accepted | Proposed | Deferred | Rejected | Deprecated | Obsolete | Quarantined | Superseded by ADR-NNNN | Duplicate of ADR-NNNN]
```

   Status lifecycle semantics:

   - **Accepted:** In force.
   - **Proposed:** Under review.
   - **Deferred:** Acknowledged and intentionally delayed.
   - **Rejected:** Explicitly not chosen.
   - **Deprecated:** Was valid, no longer recommended (still works; discouraged).
   - **Obsolete:** The **context expired** with **no replacement ADR** (example: temporary
     primary-workstation ADR when the Windows primary returns — mark **Obsolete**, not
     Superseded). Distinct from **Deprecated** (still applicable but discouraged) and
     **Superseded by ADR-NNNN** (explicit successor).
   - **Quarantined:** **Transitional, non-terminal** review hold — the ADR may be harmful
     to follow blindly or needs human review before continued use. **Must resolve** to
     **Accepted**, **Deprecated**, or **Superseded by ADR-NNNN** (not a resting state).
   - **Superseded by ADR-NNNN:** The **decision** was replaced by a newer ADR (must cite
     replacement ADR number in the status string and in Status history).
   - **Duplicate of ADR-NNNN:** A **redundant non-authoritative copy** of the **same**
     decision — hygiene, not a decision change. The authoritative record is **ADR-NNNN**.
     Prefer removing the duplicate **file** from the tree; if retained for audit, assign
     this status and append Status history. Distinct from **Superseded** (new decision).

5. **Filename convention:** ADR files must be named `ADR-NNNN-short-kebab-title.md`
   where `NNNN` is a zero-padded four-digit sequential number. The `ADR-` prefix
   makes ADR files unambiguously identifiable by filename alone. The script
   `scripts/new-adr.ps1` generates compliant filenames automatically.

6. **Locale:** ADRs are authored in **en_US** as technical documents. ADRs have **no**
   pt-BR mirror or paired file (unlike operator-facing docs and the docs README).
   General locale contract for the rest of the repository:
   **`.cursor/rules/docs-pt-br-locale.mdc`** — do not duplicate normative pt-BR rules here.

7. **Curated mutability:** Typo fixes, link updates, and clarifications that do **not**
   change the **Decision** conclusions are allowed in-place. Material changes to what was
   decided require a **new ADR** or an explicit **Amended:** line in Status history plus
   proportionate edits; solo + human-in-the-loop governance may amend in-place when the
   amendment is recorded in Status history (dogfood on this ADR).

## Rationale

1. **Accountability:** Date, Authors, and Deciders establish decision ownership; immutable
   **Date (UTC)** preserves genesis without git archaeology.
2. **Queryability:** Standardized headers and sections allow deterministic search,
   automation, and policy checks; **Status history** exposes tracking **inside** the ADR.
3. **Governance:** Status values make lifecycle explicit instead of implied; append-only
   history beats overwriting a mutable MADR **`date`** field (which hides when a decision
   actually landed).
4. **Traceability:** Related Decisions creates a navigable decision graph; compound
   statuses (`Superseded by`, `Duplicate of`) link to the authoritative ADR number.
5. **Community alignment:** Follows Nygard ADR roots and MADR evolution, formalized as
   **UMADR** with deliberate extensions where neither covers **file duplication**,
   **context expiry without successor**, **transitional quarantine**, or **genesis-date
   preservation**.
6. **No suffixed date fields:** Rejected adding `DateAmended`, `DateSuperseded`, etc. —
   they proliferate and drift; one immutable genesis date + append-only history suffices.
7. **Immutability over deletion:** Deletion is irreversible loss of audit narrative;
   status transitions preserve history for operators, CI, and future contributors.
8. **Human-in-the-Loop:** Solo maintainer may amend the constitution in-place when each
   change appends Status history — readers and agents see *why* without git archaeology.

## Consequences

- **Positive:** Higher consistency and lower cognitive load when creating/reviewing ADRs.
- **Positive:** Easier indexing and tooling for decision governance; Status history visible
  without `git log`.
- **Positive:** `Duplicate of ADR-NNNN`, **Obsolete**, and **Quarantined** give canonical
  responses to real edge cases without deleting files or misusing Superseded/Deprecated.
- **Positive:** **UMADR** names the in-house contract so agents do not re-derive lifecycle
  rules from scattered git history.
- **Negative:** Backfill effort for older ADRs when touched (legacy `- **Status:**` metadata
  still parsed by `inv-adr.ps1` until migrated).
- **Ongoing:** New ADRs should match this structure in the same PR if they deviate.
- **Ongoing:** Repo gates can incrementally validate metadata fields and Status history shape.
- **Tooling:** `scripts/inv-adr.ps1` reads **`## Status`** first (full line, including
  `Duplicate of ADR-NNNN`, plain **`Obsolete`**, or **`Quarantined`**), then falls back to
  legacy `- **Status:**` lines; regenerate `INVENTORY.txt` after any ADR body change.
- **Locale:** ADR corpus stays English-only; pt-BR work remains in paired operator docs per
  **`.cursor/rules/docs-pt-br-locale.mdc`**.

## Alternatives Considered

1. **No explicit standard** (rejected): keeps ambiguity and slows review/search.
2. **Custom local template** (rejected): reinvents well-known community practice.
3. **Guideline without enforcement path** (rejected): high drift risk over time.
4. **Suffixed metadata dates** (`DateAmended`, `DateSuperseded`, …) (rejected): field
   proliferation; append-only **Status history** covers transitions with less drift.
5. **MADR-minimal mutable `date` = last updated, git as audit trail** (rejected): overwrites
   genesis and hides transition timing inside git; contradicts exposing tracking in the ADR.
   *(This was the pre-amendment posture of this ADR; superseded by Escola B above without
   renumbering the ADR file.)*

## Related Decisions

- [ADR 0018 — PII anti-recurrence guardrails](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md)
- [ADR 0020 — CI full-history PII gate](ADR-0020-ci-full-git-history-pii-gate.md)
- [ADR 0030 — Python dependency update closure](ADR-0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem closure](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- [ADR 0056 — Cryptographic ADR inventory](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
- **ADR 0068** (temporary primary Linux workstation — edge-case context; may land via #801)
- GitHub [#803](https://github.com/FabioLeitao/data-boar/issues/803) — amendment tracking issue

## References

- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — consulted 2026-05-12
- [MADR project — adr.github.io/madr](https://adr.github.io/madr/) — consulted 2026-05-12
- [MADR Template Primer (Olaf Zimmermann)](https://www.ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html) — consulted 2026-05-12
- **`.cursor/rules/docs-pt-br-locale.mdc`** — repository locale contract (not duplicated here)
