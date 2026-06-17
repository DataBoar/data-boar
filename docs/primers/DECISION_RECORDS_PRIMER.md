# Decision records primer — ADR → MADR → UMADR

**Português (Brasil):** [DECISION_RECORDS_PRIMER.pt_BR.md](DECISION_RECORDS_PRIMER.pt_BR.md)

This primer is for **new contributors, maintainers, and auditors** who see `docs/adr/ADR-NNNN-*.md`
files and ask: *what is an ADR, why is the format so strict, and what does the "U" in UMADR mean?*
It anchors vocabulary; the binding rules live in the ADRs themselves.

**Related:** [GLOSSARY.md](../GLOSSARY.md) (§6) · [ADR index](../adr/README.md) · [docs/hubs/INDEX.md](../hubs/INDEX.md)

---

## 1. Why record decisions at all

Code shows **what** the system does; it rarely shows **why** a path was chosen over the
alternatives. Six months later the "why" is lost, and someone re-litigates a settled trade-off or
silently reverts a deliberate constraint. A **decision record** captures the **context**, the
**decision**, and the **consequences** so the reasoning survives the people who were in the room.

---

## 2. ADR — Architectural Decision Record (the origin)

- **Coined by Michael Nygard** in his 2011 post *"Documenting Architecture Decisions."*
- **Idea:** one short, immutable Markdown file per decision, numbered sequentially
  (`ADR-0001`, `ADR-0002`, …), living **next to the code** in version control.
- **Core sections:** *Context* (forces at play), *Decision* (what we chose), *Consequences*
  (what becomes easier or harder), plus a *Status*.
- **Immutable by convention:** you do **not** rewrite history — you **supersede** an old ADR with a
  new one. The trail of superseded decisions is itself valuable.

---

## 3. MADR — Markdown Any Decision Records (the template)

- **MADR** is a widely used **open template and convention** for writing ADRs in Markdown
  (the "Any" generalizes from *architectural* to *any* significant decision).
- It standardizes front-matter and sections (title, status, context/problem, considered options,
  decision outcome, pros/cons) so records are **consistent and tool-friendly** across projects.
- It is a **community standard**, not a product — you adopt and adapt it.

---

## 4. UMADR — this repository's standard (the "U" is for **hUman** / **yoU**)

Data Boar uses **UMADR (Unified MADR)**, defined in
[ADR-0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md). It extends MADR with the
discipline this project needs:

- **Human-in-the-Loop (the "U"):** a decision is only real when a **human decider** ratifies it.
  Agents draft; the operator decides. This is governance, not ceremony.
- **Metadata block:** `Date (UTC)`, `Authors`, `Deciders` — explicit and auditable.
- **Immutable genesis date + Status history:** the original date never changes; every transition
  (Proposed → Accepted → Amended → …) is **appended** as a dated line. History is append-only.
- **Extended status enum:** `Proposed`, `Accepted`, `Amended`, `Deprecated`, `Superseded`, and
  `Quarantined` (a transitory state for a decision whose subject is bracketed pending an explicit
  resolution).
- **Cryptographic inventory:** [ADR-0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
  hashes every ADR into `docs/adr/INVENTORY.txt` and attests it with an SSH signature
  (`INVENTORY.txt.sig` + `allowed_signers`). The hash **barks** (CI detects tampering); the
  signature **bites** (only the owner can re-attest).

---

## 5. Lifecycle at a glance

```text
Proposed ──ratify──► Accepted ──change──► Amended (same decision, refined)
                         │
                         ├──► Deprecated  (no longer recommended)
                         ├──► Superseded  (replaced by ADR-NNNN)
                         └──► Quarantined (transitory; resolves to one of the above)
```

`Quarantined` names the in-between honestly instead of leaving a decision pretending to be settled.

---

## 6. How we author an ADR here

1. **Scaffold:** `pwsh ./scripts/new-adr.ps1 -Title "..." -Summary "..."` (auto-picks the next
   `NNNN`). Fill *Context / Decision / Consequences*.
1. **Index:** add the row to [`docs/adr/README.md`](../adr/README.md).
1. **Inventory:** regenerate `docs/adr/INVENTORY.txt` (`inv-adr`) so the hash matches; CI enforces it.
1. **Human ratifies:** the operator moves `Proposed → Accepted` and the commit is signed.

> Primers themselves are governed too: their taxonomy and home are set by
> [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), which amends
> [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md).

---

## 7. Further reading

- Michael Nygard, *Documenting Architecture Decisions* (2011) — the original ADR post.
- **MADR** project — the Markdown template/convention this repo builds on.
- [ADR-0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) — the UMADR constitution.
- [ADR index](../adr/README.md) — every accepted decision in this repo.
