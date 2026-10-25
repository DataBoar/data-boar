# WRB — instantâneo de delta para o próximo e-mail (2026-04-03)

**English:** [WRB_DELTA_SNAPSHOT_2026-04-03.md](WRB_DELTA_SNAPSHOT_2026-04-03.md)

Cole o **parágrafo** (bloco EN no arquivo EN) no e-mail à Corporate-Entity-C **depois** do prompt mestre em [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (ou funda em §2 de [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) antes de enviar). Atualize o **hash de commit** se enviares depois de um merge novo.

---

## Verdade de versão (evitar confusão)

- **`pyproject.toml` / docs** em `main` com meta **1.6.8** (ver `docs/releases/1.6.8.md`).
- **Última tag publicada** no envio: confirmar **`v1.6.8`** em GitHub Releases e tags Docker Hub (`1.6.8`, `latest`).
- Pedir à Corporate-Entity-C para tratar **“desde última entrega mercado”** como **desde a tag `v1.6.8`**, salvo confirmação de tag mais nova.
- **Alterações locais não commitadas** no PC de desenvolvimento — indicar como **ainda não em `origin/main`**; lente separada do release etiquetado.

---

## Nota de re-envio (se o pedido WRB anterior se perdeu)

Cola **depois** do bloco suplementar em inglês (ou logo após *Olá, equipe Corporate-Entity-C* no prompt longo) para quem não tenha fio de e-mail nem memória do pedido anterior.

```text
Short note — re-send: We are sending this WRB request again; an earlier message may not have reached you. Please treat this e-mail (and the linked in-repo briefing paths below) as the single source of truth — we do not assume you retain context from a prior thread. Our last report from you remains the 2026-03-18 delivery; tracking: docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. At send time, please confirm the latest GitHub tag (expected v1.6.8 unless superseded) and use `main` at commit: REPLACE_WITH_SHORT_HASH (run `git rev-parse --short HEAD` before send).
```

*(Você pode traduzir este parágrafo para português no corpo do e-mail se preferir um único idioma na mensagem; o bloco EN acima é o espelho do arquivo `WRB_DELTA_SNAPSHOT_2026-04-03.md`.)*

---

## Relacionado

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — caminhos para revisores.
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — estado do backlog.
- [GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md) — fluxo seguro do pacote (saída em `docs/private/`).
