# Proteção de código e higiene comercial — playbook do operador

**English:** [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](CODE_PROTECTION_OPERATOR_PLAYBOOK.md)

**Objetivo:** Frases **prontas** para orientar um assistente de IA (ou operador humano) em **segurança, exposição de IP e guardrails de rentabilidade** sem gastar contexto com features não relacionadas. Complementa os ponteiros de mantenedor em **Interno e referência** em [README.md](README.md) (**Priority band A**, **TOKEN_AWARE_USAGE** — caminhos em `docs/plans/` na árvore do repositório).

**Regra:** Um **passo** (A1–A7) por sessão, salvo passos triviais. Depois de **A1–A3**, você pode voltar ao ritmo **token-aware** de features, salvo se A4–A7 bloquearem receita ou conformidade.

---

## Mapa de fases (ordem)

| Fase                      | ID | Você faz                                                             | Agente ajuda com                                                                                    |
| ----                      | -- | --------                                                             | -----------------                                                                                   |
| **Dependências**          | A1 | Aprovar/merge de PRs Dependabot no GitHub                            | Triagem, bumps mínimos, testes, correções                                                           |
| **CVEs da imagem**        | A2 | Rodar Docker localmente, aprovar mudanças no Dockerfile              | Interpretação do `docker scout`, base/pins mínimos                                                  |
| **Registry público**      | A3 | UI do Docker Hub: excluir ou documentar tags                         | Atualizar [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) §8, refs Compose/K8s                     |
| **Isolamento do emissor** | A4 | Repo privado [`FabioLeitao/license-studio`](https://github.com/FabioLeitao/license-studio); **nunca** enviar chaves | [LICENSE_STUDIO_SPINOUT.md](ops/LICENSE_STUDIO_SPINOUT.md), checklist, `.gitignore` |
| **Pessoas**               | A5 | Convidar colaboradores no GitHub/GitLab                              | —                                                                                                   |
| **Automação**             | A6 | Aprovar adições de CI                                                | `scripts/license-smoke.ps1` ou job pytest, docs em um PR                                            |
| **Jurídico**              | A7 | Contato com advogado                                                 | Apenas apontar docs: [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) |

---

## Prompts copiar e colar

### A1 — Dependabot / higiene de dependências

> **Priority band A, passo A1 apenas.** Abrir Security → Dependabot deste repositório. Listar alertas abertos por severidade. Para cada upgrade seguro, propor mudança mínima em `pyproject.toml` / lockfiles / `requirements.txt` para manter `.\scripts\check-all.ps1` verde. **Não** iniciar trabalho de feature.

### A2 — Docker Scout / endurecimento da imagem

> **Priority band A, passo A2 apenas.** Revisar o `Dockerfile` na raiz: pacotes desnecessários e tag da base. Assumir que eu rodo `docker scout quickview` localmente — dizer exatamente o que rodar e como interpretar HIGH/CRITICAL. Propor o menor diff no Dockerfile; sem refactors não relacionados.

### A3 — Ciclo de vida de tags no Docker Hub

> **Priority band A, passo A3 apenas.** Comparar [DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) §8 com a lista de tags que eu colar do Docker Hub. Dizer quais tags podem ser apagadas vs quais devem permanecer para parceiros/CI. Atualizar DEPLOY.md + DEPLOY.pt_BR.md; sem mudar código da aplicação.

### A4 — Repositório privado do emissor (sem segredos no público)

> **Priority band A, passo A4.** Ferramenta de emissão no repo privado **`FabioLeitao/license-studio`** (spinout 2026-06-25). Veja [docs/ops/LICENSE_STUDIO_SPINOUT.md](ops/LICENSE_STUDIO_SPINOUT.md): layout, `studio sign`, onde ficam as chaves (nunca no git), link para [LICENSING_SPEC.md](LICENSING_SPEC.md). Sem chaves, sem URLs com tokens.

### A5 — Acesso a parceiros (manual)

> Você faz sem o agente: adicionar colaboradores no repo **privado** do emissor e outros ativos privados. Não colar segredos no chat.

### A6 — Smoke de licença / gancho de CI

> **Priority band A, passo A6 apenas.** Adicionar ou estender `scripts/license-smoke.ps1` (ou um módulo pytest) que prove que modo **open** ainda sobe e modo **enforced** falha rápido sem `.lic` válido em config temporária. Documentar em [TESTING.pt_BR.md](TESTING.pt_BR.md). Um PR focado.

### A7 — Limite legal (manual + advogado)

> **Priority band A, passo A7.** (Você + advogado.) O agente só pode apontar [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) e [LICENSING_SPEC.md](LICENSING_SPEC.md); não redigir texto jurídico vinculante.

---

## Voltar ao ritmo token-aware

Quando A1–A3 estiverem prontos:

> **Resume token-aware pace.** Apenas a próxima linha de **PLANS_TODO** em “What to start next” (veja **Interno e referência** em [README.md](README.md)) — ordem **[N]**; não carregar outros planos.

---

## Documentos relacionados

- [README.md](README.md) — **Interno e referência** lista **PLANS_TODO** e **TOKEN_AWARE_USAGE** (`docs/plans/` no checkout)
- [LICENSING_SPEC.md](LICENSING_SPEC.md)
- [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md)
- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md)
- [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) — seção **Brand, narrative, and experience IP** (mascote, data soup, dashBOARd, aparência UI/relatório, recursos associados) para briefings com assessoria
