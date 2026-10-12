# Primer: RAG (Retrieval-Augmented Generation) — conceitos e limites do Boar

**English:** [RAG_PRIMER.md](RAG_PRIMER.md)

Primer educacional sobre **RAG** para integradores que veem “corpora RAG” em texto de compliance. **Não** ensina a construir produto de banco vetorial.

---

## 1. O que é RAG

**Retrieval-Augmented Generation** combina:

1. **Recuperação** — buscar trechos relevantes em uma base (arquivos, linhas de BD, índice de embeddings).
2. **Geração** — um LLM usa esses trechos como contexto para responder ou resumir.

RAG reduz “alucinação” versus modelo nu **somente quando** a recuperação e o controle de acesso são sólidos. **Não** substitui governança de dados nem descoberta de PII nas fontes.

---

## 2. Como o Data Boar se relaciona (repo público)

| Tópico | Existe aqui? | Ponteiro |
| ------ | ------------ | -------- |
| Inventariar **arquivos/exportações** que podem alimentar corpus RAG | **Sim** — scan de alvos configurados | [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md), [AI_COMPLIANCE_PRIMER.pt_BR.md](AI_COMPLIANCE_PRIMER.pt_BR.md) |
| Embeddings, chunking, vector DB, orquestração de prompt | **Não** em `data-boar` | — |
| API RAG hospedada (AIaaS) | **Não** | [AAS_MODELS_PRIMER.pt_BR.md](AAS_MODELS_PRIMER.pt_BR.md) |

**latent-lynx** (repositório **privado** separado no roster do ecossistema do operador) é o nome usado para experimentação orientada a RAG — **não** documentado nesta árvore pública. Não infira implementação interna a partir do `data-boar`. O alinhamento **latent-lynx#28** segue **aberto** na redação deste primer; trate integração como **pendente**, não entregue.

---

## 3. Checklist honesto

Antes de prometer “pronto para RAG”:

1. Nomeie os **repositórios reais** varridos.
2. Separe achados do **Data Boar** do comportamento do **modelo**.
3. Não prometa índice vetorial ou tuning de retrieval só com este repositório.

---

## 4. Onde ir depois

| Necessidade | Doc |
| ----------- | --- |
| Limites AI Act / camada de dados | [AI_COMPLIANCE_PRIMER.pt_BR.md](AI_COMPLIANCE_PRIMER.pt_BR.md) |
| SaaS vs on-prem | [AAS_MODELS_PRIMER.pt_BR.md](AAS_MODELS_PRIMER.pt_BR.md) |
