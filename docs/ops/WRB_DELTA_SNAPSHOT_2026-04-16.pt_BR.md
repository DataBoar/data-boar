# WRB — instantâneo de delta para o próximo e-mail (2026-04-16)

**English:** [WRB_DELTA_SNAPSHOT_2026-04-16.md](WRB_DELTA_SNAPSHOT_2026-04-16.md)

Cole os blocos EN do arquivo [WRB_DELTA_SNAPSHOT_2026-04-16.md](WRB_DELTA_SNAPSHOT_2026-04-16.md) no e-mail à Corporate-Entity-C **depois** do prompt mestre em [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (seções *Report format requested…*, *Reusable request message* e sobretudo **Prompt mestre completo (PT-BR)**). Ou integre na §2 de [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) antes de enviar.

**Ordem sugerida:** (1) *Appreciation lead-in* (opcional, tom de agradecimento) → (2) *English paste block* (âmbito + hash) → (3) *Re-send note* só se um pedido anterior se perdeu.

**Antes de enviar:** rode `git rev-parse --short HEAD` e substitua cada **`REPLACE_WITH_SHORT_HASH`** nos blocos para colar abaixo.

---

## Verdade de versão (evitar confusão)

- **`pyproject.toml` / docs** em `main` com alvo de trabalho **1.6.8** rumo a **1.6.9** quando sair o próximo pacote — ver [PUBLISHED_SYNC.pt_BR.md](today-mode/PUBLISHED_SYNC.pt_BR.md) e [docs/VERSIONING.md](../VERSIONING.md).
- **Última tag publicada no Git** (baseline mercado / Docker / testadores na última verificação): **`v1.6.8`** — ver [PUBLISHED_SYNC.pt_BR.md](today-mode/PUBLISHED_SYNC.pt_BR.md) (reconfirme GitHub Releases + Docker Hub no envio).
- **`main` à frente de `v1.6.8`:** cerca de **211** commits quando este instantâneo foi redigido (rode de novo `git rev-list --count v1.6.8..HEAD` no envio). **Tip do `main`:** substitua **`REPLACE_WITH_SHORT_HASH`** nos blocos abaixo por `git rev-parse --short HEAD` imediatamente antes do envio (os três ângulos no guideline: histórico acumulado → desde último relatório Corporate-Entity-C → desde última **tag** até o **tip** do branch atual).
- Pedir à Corporate-Entity-C para tratar **“desde última entrega mercado”** como **desde a tag `v1.6.8`**, salvo confirmação de tag mais nova no GitHub.
- Se houver **alterações locais não commitadas** no PC de dev, declarar como **ainda não em `origin/main`** — lente separada da release etiquetada.

---

## Blocos EN para colar (anexo opcional ao pedido longo)

*(No arquivo EN: seção **Appreciation lead-in** — opcional; depois **English paste block**; em último lugar **Re-send note** se aplicável. Substitua **`REPLACE_WITH_SHORT_HASH`** antes do envio.)*

---

## Nota de re-envio (se o pedido WRB anterior se perdeu)

Cole **depois** do bloco de apreciação (se usar) e do bloco suplementar em inglês — ou logo após *Olá, equipe Corporate-Entity-C* no prompt longo — para quem não tenha fio de e-mail nem memória do pedido anterior.

```text
Short note — re-send: We are sending this WRB request again; an earlier message may not have reached you. Please treat this e-mail (and the linked in-repo briefing paths below) as the single source of truth — we do not assume you retain context from a prior thread. Our last report from you remains the 2026-03-18 delivery; tracking: docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. At send time, please confirm the latest GitHub tag (expected v1.6.8 unless superseded) and use `main` at commit: REPLACE_WITH_SHORT_HASH (run `git rev-parse --short HEAD` before send).
```

---

## Relacionados

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — caminhos para revisores.
- [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) — **prompt WRB completo** (bloco EN + “Prompt mestre completo” PT-BR).
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — estado do backlog.
- [GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md) — fluxo de bundle seguro (saída em `docs/private/`).
