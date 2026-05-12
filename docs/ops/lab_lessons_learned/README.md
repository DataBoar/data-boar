# LAB lessons learned — dated public archive

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

## Purpose

This directory holds **immutable, dated** snapshots of lab QA / SRE evidence (metrics, checkpoint behaviour, benchmark numbers) that are safe for **public Git**. It mirrors the idea of **`docs/plans/completed/`**: history stays **segregated** and **addressable by filename**, while the **rolling hub** remains one click away at **[`../LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md)**.

## Naming contract

| Artifact | Rule |
| -------- | ---- |
| **Dated snapshot** | `LAB_LESSONS_LEARNED_YYYY_MM_DD.md` (calendar date of the **session end** in the operator timezone used for the write-up; **one file per session** unless the operator explicitly splits). |
| **Hub** | [`docs/ops/LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md) — short **current** narrative + archive index + **follow-up** pointers into **`docs/plans/PLANS_TODO.md`**. |
| **Private completão narrative** | `docs/private/homelab/COMPLETAO_SESSION_*.md` — hostnames, LAN, operator commentary; **never** copy those verbatim into this archive. |

## Ritual (when a session produces new evidence)

1. **Copy** the current body of [`LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md) into a **new** `LAB_LESSONS_LEARNED_YYYY_MM_DD.md` here (or copy-then-edit if the hub already holds the new draft).
2. **Trim** the hub to a short summary + links to this file and to sprint / integrity docs as needed.
3. **Open or update** rows in **`docs/plans/PLANS_TODO.md`** when a lesson implies tracked work (then run `python scripts/plans-stats.py --write`).
4. After **completão**, keep using **`docs/private/homelab/COMPLETAO_SESSION_*.md`** for full context; add **public** numbers or pass/fail summaries here only when they belong in the product tree.

## Contract record

Architecture and automation posture: **[ADR 0042](../../adr/ADR-0042-lab-lessons-learned-archive-contract.md)**.

Session token (situational Cursor rule): **`lab-lessons`** → **`.cursor/rules/lab-lessons-learned-archive.mdc`**.
