# Primer: Retrieval-Augmented Generation (RAG) — concepts and Boar boundaries

**Português (Brasil):** [RAG_PRIMER.pt_BR.md](RAG_PRIMER.pt_BR.md)

Educational primer on **RAG** for integrators who see “RAG corpora” in compliance text. It does **not** teach how to build a vector database product.

---

## 1. What RAG means

**Retrieval-Augmented Generation** combines:

1. **Retrieval** — fetch relevant chunks from a knowledge base (files, DB rows, embeddings index).
2. **Generation** — an LLM uses those chunks as context to answer or summarise.

RAG reduces “hallucination” versus a bare model **only when** retrieval quality and access control are sound. It does **not** replace data-governance or PII discovery on the underlying stores.

---

## 2. How Data Boar relates (public repo)

| Topic | Shipped here? | Pointer |
| ----- | ------------- | ------- |
| Inventory **files/DB exports** that might feed a RAG corpus | **Yes** — scanning configured targets | [TECH_GUIDE.md](../TECH_GUIDE.md), [AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md) (Art. 10 / data layer) |
| Embeddings, chunking, vector DB, prompt orchestration | **No** in `data-boar` | — |
| Hosted RAG API (AIaaS) | **No** | [AAS_MODELS_PRIMER.md](AAS_MODELS_PRIMER.md) |

**latent-lynx** (separate **private** repository in the operator ecosystem roster) is the named home for RAG-oriented experimentation — **not** documented in this public tree. Do not infer its internals from `data-boar`. Cross-repo alignment work **latent-lynx#28** remains **open** at the time of this primer; treat integration as **pending**, not shipped.

---

## 3. Honest operator checklist

Before claiming “RAG-ready” for a customer:

1. Name the **actual stores** scanned (share paths, bucket exports, DB tables).
2. Separate **Data Boar findings** from **model** behaviour (no model eval in core).
3. Do not promise vector-index or retrieval tuning from this repository alone.

---

## 4. Where to go next

| Need | Doc |
| ---- | --- |
| AI Act / data-layer limits | [AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md) |
| SaaS vs on-prem | [AAS_MODELS_PRIMER.md](AAS_MODELS_PRIMER.md) |
