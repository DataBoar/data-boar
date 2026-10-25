# WRB — instantâneo de delta para o próximo e-mail (2026-03-31)

**English:** [WRB_DELTA_SNAPSHOT_2026-03-31.md](WRB_DELTA_SNAPSHOT_2026-03-31.md)

Cola o **parágrafo** da seção seguinte no e-mail à Corporate-Entity-C **depois** do prompt mestre em [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (ou integra na seção 2 de [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) antes de enviar). Atualiza o **hash de commit** se enviares após um merge novo.

---

## Verdade das versões (evitar confusão)

- O **`pyproject.toml`** / docs em **`main`** apontam para **1.6.7** (vê `docs/releases/1.6.7.md`).
- A **última tag publicada** é **`v1.6.7`**, com GitHub Release e Docker Hub alinhados (`1.6.7` e `latest`).
- Pede à Corporate-Entity-C para tratar **“desde a última entrega etiquetada”** como **desde a tag `v1.6.7`**, salvo confirmarem tag mais recente no GitHub.

---

## Bloco para colar (PT-BR)

```text
Contexto complementar (2026-03-31):

Desde a tag v1.6.7, temos apertado workflow do operador e higiene de Docker sem mexer no comportamento central de varredura do produto. Deltas relevantes incluem: notas de integração MCP (Docker Desktop + Docker Hub) com disciplina token-aware (segredos nunca versionados, orientação de privilégio mínimo do PAT); nota de troubleshooting do Docker Hub MCP (expectativa de formato de token); novo runbook do operador e guardrail do Cursor para usar o assistente “Gordon” (insumo, não ordem; sem segredos; transformar conselho em teste/doc/script e rodar gates do repo); e atualizações contínuas do catálogo de inspirações de craft de engenharia que moldam o tom da documentação (não viram política automática).

Manter as três lentes temporais separadas. Para “desde a última release etiquetada”, usar v1.6.7 como baseline (última release publicada) e separar trabalho ainda não publicado em `main`, se houver. (Se preciso, referenciar o hash do commit mais recente do main no momento do envio.)
```

---

## Relacionado

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md)
- [PLANS_TODO.md](../plans/PLANS_TODO.md)
