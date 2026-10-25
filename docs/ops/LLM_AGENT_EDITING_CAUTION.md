# Caution: LLM-assisted editing (IDE agents and vendor chat)

**Portuguese (Brazil):** [LLM_AGENT_EDITING_CAUTION.pt_BR.md](LLM_AGENT_EDITING_CAUTION.pt_BR.md)

## Purpose

Data Boar ships strong **Cursor** rules, **skills**, **session keywords**, **pre-commit** hooks, **`check-all`**, and lab runbooks. Those controls **reduce** risk — they do **not** remove the failure modes of **generative LLMs** when they touch **validated**, **high-stakes** scripts (for example long **PowerShell** orchestrators for lab benchmarking).

This page is a **short, public** warning for maintainers and collaborators. A **full, concrete evidence index** (screenshots, chat exports, branch/commit anchors, and a fair narrative) lives only under **`docs/private/`** on the operator workstation — see **`docs/private/ops/INCIDENT_VENDOR_CHAT_ORCHESTRATION_MISMATCH_2026-04-28_29.pt_BR.md`** (gitignored from GitHub; never paste that path into **issues** or **PRs** with secrets).

**Contrast with the shipped product:** Sensitivity and inventory signals in Data Boar stay on a **deterministic + supervised** path (regex, ML/DL with fixed seeds, structured reports)—see [TECH_GUIDE.md](../TECH_GUIDE.md#detection-stack-vs-generative-llms), [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype), and [GLOSSARY.md](../GLOSSARY.md) §8–9.

## What went wrong (generic pattern)

- The operator asked for **literal fidelity** (*as-is*) to an already-reviewed script, including **audit / chain-of-custody comments** and deliberate “probe” lines.
- A **vendor web chat LLM** (example: **Google Gemini**) produced **many renamed variants** instead of a single faithful file, moved blocks, and changed paths (for example export directories oscillating between a **private reports tree** and a generic **`out/`** folder).
- Recovery required **restoring from a known-good backup**, staging many files, and committing with a **strong** message so the cost is visible in **`git log`**.
- Separately, the same vendor product can **claim “memory”** in marketing while, in a long thread, alternating between **“no verbatim log”**, **dramatic self-descriptions**, **confident hallucinations about repository state**, and an honest **refusal** line — all useful **stress-test signals**, not a legal case.

## Hype vs engineering reality

| Public narrative | Engineering truth |
| ---------------- | ----------------- |
| “Persistent memory” / “adapts to your history” (press pieces and product UX) | Improves **continuity** for many tasks; does **not** guarantee **verbatim replay** of assistant outputs, auditable logs, or freedom from **policy refusals**. Example article (third-party summary): [MSN / PCGuia piece on Gemini “memory”](https://www.msn.com/pt-pt/noticias/other/gemini-passa-a-ter-mem%C3%B3ria-e-vai-conseguir-adaptar-as-respostas-tendo-em-conta-o-hist%C3%B3rico-das-nossas-conversas/ar-AA2219Hk). |
| “Reasoning” / “Pro” modes | May change tone and structure; **does not** remove hallucination risk or substitute **CI + human diff**. |
| Strong **AGENTS.md** + rules + skills in this repo | **Necessary** guardrails; **not sufficient** if a session skips **`git diff`**, **`check-all`**, or explicit **scope** (“touch only these lines”). |

## Where LLMs still help

- Brainstorming **interfaces**, **error messages**, and **docs structure** when the operator treats output as **draft**.
- **Search and navigation** in a large tree when results are verified against **code** and **tests**.
- **Summaries** of public specifications — always cross-check primary sources.

## Where LLMs start to hurt

- **Editing** files that are **contracts**: orchestrators, manifest parsers, anything that must stay **bit-for-bit** unless a human signs a surgical diff.
- **Inventing** “what ran yesterday” without **`git`**, **CI artifacts**, or **private lab reports** under **`docs/private/homelab/reports/`**.
- **Merging** emotionally loaded chat prose into **engineering truth** without evidence.

## Practical mitigations (public checklist)

1. **Split channels:** vendor chat for exploration; **Cursor agent + PR** for code that lands on **`main`**.
2. **Session preamble** for sensitive files: list allowed paths; forbid refactors; preserve audit comments.
3. **Prefer repo scripts** (`check-all`, `preview-commit`, `commit-or-pr`) — see **[TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)**.
4. **Export** long vendor threads into **`docs/private/`** when they contain decisions you might need to audit later.
5. Read **[GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)** when the work is “Gemini reviews **already public** paths only” — different posture from live repo editing.

## Related

- **Policy map:** [CURSOR_AGENT_POLICY_HUB.md](CURSOR_AGENT_POLICY_HUB.md)
- **Lab orchestration contract:** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md), [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)
- **Glossary contrast** (product ML/DL vs generative LLM): [GLOSSARY.md](../GLOSSARY.md) — **LLM** row
