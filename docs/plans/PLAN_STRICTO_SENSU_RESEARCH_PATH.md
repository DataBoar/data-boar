# Plan: Stricto sensu research path (M.Sc. and PhD) on top of Data Boar

**Status:** Deferred
**Date:** 2026-03-18
**Authors:** Fabio Leitao
**Priority:** H3

<!-- plans-hub-summary: M.Sc./PhD research lines using Data Boar as experimental platform—detection, evidence, methodology; revisit when programs/advisors near. -->

**Synced with:** `long-term-product-and-academic-roadmap` and [PLAN_LATO_SENSU_THESIS.md](PLAN_LATO_SENSU_THESIS.md)

This plan outlines how to evolve the existing application and documentation into **one or more stricto sensu research lines** (M.Sc. and eventually PhD). It focuses on **questions, methodology, and experimental infrastructure**, not on shipping new product features directly.

---

## 1. Candidate research questions

**Goal:** Identify 1–2 focused, researchable questions that use the app as a platform.

### To-dos (Candidate research questions)

| #   | To-do                                                                                                                                                                                   | Status    |
| -   | -----                                                                                                                                                                                   | ------    |
| 1.1 | Draft a short list (3–5) of possible research questions (EN/PT-BR) around detection quality (regex vs ML vs DL), compliance evidence modelling, and risk reduction under ISO/IEC 27005. | ⬜ Pending |
| 1.2 | For each candidate question, write a brief feasibility note: data needed, metrics, expected contribution, and whether it fits better as M.Sc. or PhD scope.                             | ⬜ Pending |
| 1.3 | Select 1–2 priority questions to pursue first (one “minimum viable” for M.Sc., one stretch for PhD).                                                                                    | ⬜ Pending |

---

## 2. Experimental infrastructure

**Goal:** Prepare the app and surrounding assets so they can support repeatable experiments.

### To-dos (Experimental infrastructure)

| #   | To-do                                                                                                                                                           | Status    |
| -   | -----                                                                                                                                                           | ------    |
| 2.1 | Identify which existing features and reports will be used as experimental outputs (e.g. detection logs, inventory sheets, crypto & controls, cross-ref risk).   | ⬜ Pending |
| 2.2 | Define what extra logging or export is minimally needed for experiments (e.g. anonymised ground truth labels, confusion matrices) without compromising privacy. | ⬜ Pending |
| 2.3 | Sketch a plan for synthetic/anonymised datasets that approximate real corporate environments (formats, connectors, norms), to be used across experiments.       | ⬜ Pending |

---

## 3. Methodology and metrics

**Goal:** Outline research methods and evaluation criteria suitable for stricto sensu work.

### To-dos (Methodology and metrics)

| #   | To-do                                                                                                                                                                                                | Status    |
| -   | -----                                                                                                                                                                                                | ------    |
| 3.1 | For each priority research question, propose 1–2 methodologies (e.g. design science + experimental evaluation, controlled experiments with synthetic corpora, comparative studies with other tools). | ⬜ Pending |
| 3.2 | Define candidate metrics (precision, recall, F1, coverage of controls, audit preparation time, qualitative feedback from practitioners) and how to measure them.                                     | ⬜ Pending |
| 3.3 | Enumerate main threats to validity (dataset bias, limited connectors, synthetic vs real data) and potential mitigations.                                                                             | ⬜ Pending |

---

## 4. Early publications and advisor outreach

**Goal:** Create stepping stones (papers, proposals) and a narrative to discuss with potential advisors.

### To-dos (Early publications and advisor outreach)

| #   | To-do                                                                                                                                                                  | Status    |
| -   | -----                                                                                                                                                                  | ------    |
| 4.1 | From the lato sensu work, identify 1–2 slices that could become short papers (architecture, evaluation of detection strategies, compliance evidence framework).        | ⬜ Pending |
| 4.2 | Draft a 2–3 page “research proposal” that summarises the app, the problem space, the chosen research question(s), and the planned methodology.                         | ⬜ Pending |
| 4.3 | Prepare a concise overview (1–2 pages or slide deck) to present to potential advisors at institutions like PUC-Rio, highlighting prior work and planned contributions. | ⬜ Pending |

---

## 5. Long-term thesis structures

**Goal:** Keep a rough blueprint for how M.Sc. and PhD theses might be structured.

### To-dos (Long-term thesis structures)

| #   | To-do                                                                                                                                                                                        | Status    |
| -   | -----                                                                                                                                                                                        | ------    |
| 5.1 | Draft a high-level chapter outline for a possible M.Sc. thesis based on one priority research question.                                                                                      | ⬜ Pending |
| 5.2 | Draft a high-level chapter outline for a possible PhD thesis that builds on the M.Sc. work and expands to broader questions (e.g. formalising compliance evidence, integrating risk models). | ⬜ Pending |

---

## 6. Artifacts and evidence sources

For research proposals and advisor outreach:

- **Platform:** This repo (Data Boar) and Docker image `fabioleitao/data_boar`.
- **Portfolio:** `docs/private/From Docker hub list of repositories.md` (data_boar, wildfly_t1r, uptk) for prior work and infra/observability context.
- **Personal/academic:** CV, TCC, LinkedIn in `docs/private/` (git-ignored). See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3.

---

## 7. Long-term alignment: product roadmap and academic work

**Goal:** Keep an explicit bridge so ongoing Data Boar development remains **usable as research infrastructure** (not only as a CV line).

**Still aligned (horizon):** The product’s core threads—**multi-layer detection** (rules vs ML/DL), **compliance/evidence-oriented reporting**, **inventory and scope** from heterogeneous “data soup,” optional **organizational maturity** instruments ([PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md), commercial)—map naturally to stricto sensu themes: **comparative evaluation of models**, **governance/technical evidence**, **repeatable benchmarks**, and **human-in-the-loop** maturity vs automated findings. Next-wave **N3** (“academic-to-market evidence stream”) in [PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md](PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md) is the product-side counterpart.

**When to revisit with deeper sessions (e.g. higher-context or post–Priority band A):** Literature pass on detection/evaluation in regulated contexts; narrowing 1–2 thesis questions; designing **public-safe** synthetic corpora or ablation protocols; advisor-facing one-pager. Token-aware batching: [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md). Private career sequencing stays in [PLAN_FOUNDER_SRE_CAREER_AND_PRODUCT_ALIGNMENT.md](PLAN_FOUNDER_SRE_CAREER_AND_PRODUCT_ALIGNMENT.md) (full text under `docs/private/`).

### To-dos (Alignment checkpoint — optional)

| #   | To-do                                                                                                                                      | Status    |
| --- | -----                                                                                                                                      | --------- |
| 7.1 | Once per year (or when enrollment/advisor timeline firms up): re-read this section + **N3** + [PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md) §3; adjust priority questions in §1 if the shipped product shifted capabilities. | ⬜ Pending |

---

## 8. Sync notes

- This plan is **exploratory** and academic; it does not impose product work on the current roadmap.
- Use it as a living document when you move closer to applying for M.Sc./PhD programs or start pilots with advisors.
