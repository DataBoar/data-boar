# Talent pool — mini-roteiros de aprendizado opcionais (por arquétipo de papel)

**English:** [TALENT_POOL_LEARNING_PATHS.md](TALENT_POOL_LEARNING_PATHS.md)

**Público:** Mantenedor e colaboradores de confiança que planejam **como ajudar pessoas a crescer** enquanto contribuem com o Data Boar. Este arquivo usa **somente arquétipos de papel** — sem nomes de candidatos, notas ou URLs do LinkedIn (isso fica em **`docs/private/`**).

**Veja também:** [COLLABORATION_TEAM.pt_BR.md](COLLABORATION_TEAM.pt_BR.md), [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md); entradas de planejamento (sem link direto desta camada, ver ADR 0004): `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (cadência de estudo, sequência CWL, suplementos PUCRS), `docs/plans/PLANS_HUB.md`.

---

## 1. Como usar isso com uma pessoa real

1. **Encaixar** a pessoa no arquétipo mais próximo abaixo (pode cobrir dois; escolha um principal).
2. **Onboarding** no eixo **Data Boar** primeiro — PRs pequenos vencem cursos longos.
3. **Aprendizado opcional:** escolher **uma** frente externa por vez (certificação ou curso de extensão) para o progresso aparecer no GitHub e no currículo.
4. **Registro privado:** copiar **`docs/private.example/commercial/candidates/LEARNING_ROADMAP_TEMPLATE.md`** para **`docs/private/commercial/candidates/<slug>/LEARNING_ROADMAP.md`** e preencher metas, datas e notas do dossiê LinkedIn / entrevista — **nunca commitar** essa árvore.

---

## 2. Arquétipo A — Backend Python (scanner, conectores, relatórios)

**Serve para:** Quem entrega features, testes e refatoração em Python.

| Horizonte                                      | Data Boar (repositório)                                                                                                                                                                                                                                         | Carreira / certificações opcionais                                                                                                                                                                                                             |
| ---------                                      | ------------------------                                                                                                                                                                                                                                        | -----------------------------------                                                                                                                                                                                                            |
| **Primeiras 2–4 semanas**                      | [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md), [TESTING.pt_BR.md](TESTING.pt_BR.md), `uv sync`, `scripts/check-all.ps1` ou `pytest`; ler trechos do [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) alinhados à primeira issue (ex.: pipeline core, conectores). | —                                                                                                                                                                                                                                              |
| **Próximo 1–2 trimestres**                     | Responsabilizar por um **recorte vertical fino** (issue → PR → docs/testes).                                                                                                                                                                                    | Se quiserem credibilidade **ciber defensiva** alinhada ao produto: sequência **CWL** em `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` seção 3.2 (**BTF → C3SA**, depois adiante) — **uma trilha paga por vez**. |
| **Tese / narrativa de compliance (se couber)** | Apontar [ACADEMIC_USE_AND_THESIS.pt_BR.md](ACADEMIC_USE_AND_THESIS.pt_BR.md) e `docs/plans/PLAN_LATO_SENSU_THESIS.md` — artefato é o código.                                                                                        | PUCRS **Gestão do Conhecimento e Transformação Digital** reforça narrativa de **governança / gestão do conhecimento**; confirmar oferta no catálogo oficial PUCRS (ver PORTFOLIO seção 3.3).                                                   |

---

## 3. Arquétipo B — API, dashboard ou web full-stack

**Serve para:** Quem mexe em `api/`, dashboard estático, OpenAPI ou HTTP/auth.

| Horizonte                  | Data Boar (repositório)                                                                                                                        | Carreira / certificações opcionais                                                                                                                                             |
| ---------                  | ------------------------                                                                                                                       | -----------------------------------                                                                                                                                            |
| **Primeiras 2–4 semanas**  | Mesma higiene que A; somar caminhos de smoke de API em TESTING; respeitar [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) (sem segredos em UI/docs). | —                                                                                                                                                                              |
| **Próximo 1–2 trimestres** | Issues focadas em dashboard/API; manter PRs **revisáveis** (pequenos).                                                                         | Consciência de **segurança web/API** combina com base CWL; **AZ-900** ou equivalente de nuvem se o CV estiver fraco em cloud (padrão na tabela de certificações do PORTFOLIO). |

---

## 4. Arquétipo C — DevOps, CI, Docker, tooling de release

**Serve para:** Quem prefere workflows, imagens, scripts e gates de CI.

| Horizonte                  | Data Boar (repositório)                                                                                                                                                                                                | Carreira / certificações opcionais                                                                                                                                                                     |
| ---------                  | ------------------------                                                                                                                                                                                               | -----------------------------------                                                                                                                                                                    |
| **Primeiras 2–4 semanas**  | [.github/workflows/](../.github/workflows/), [docs/ops/DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](ops/DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) se mexer em imagens; rodar **`check-all`** antes de sugerir mudanças em workflow. | —                                                                                                                                                                                                      |
| **Próximo 1–2 trimestres** | PRs com escopo: pin de actions, follow-ups Scout, ou runbooks — alinhar com linhas de manutenção em `docs/plans/PLANS_TODO.md` quando possível.                                                              | Certificações **SRE** ou **plataforma** (lista derivada do CV no PORTFOLIO) combinam; manter narrativa de **cadeia de suprimentos** (actions fixas, proveniência) como história de portfólio concreta. |

---

## 5. Arquétipo D — Documentação técnica, narrativa de compliance ou LGPD

**Serve para:** Bons redatores que clareiam **USAGE**, **COMPLIANCE_***, **GLOSSARY** ou runbooks — em geral commits **documentation**, não core do detector.

| Horizonte                  | Data Boar (repositório)                                                                                                                                                                                                                                                            | Carreira / certificações opcionais                                                                                                                                                              |
| ---------                  | ------------------------                                                                                                                                                                                                                                                           | -----------------------------------                                                                                                                                                             |
| **Primeiras 2–4 semanas**  | [docs/README.md](README.md), [.cursor/rules/docs-policy.mdc](../.cursor/rules/docs-policy.mdc), [.cursor/rules/audience-segmentation-docs.mdc](../.cursor/rules/audience-segmentation-docs.mdc) — **sem** novos links para `docs/plans/` a partir de camadas voltadas a comprador. | —                                                                                                                                                                                               |
| **Próximo 1–2 trimestres** | Pares EN + pt-BR onde obrigatório; rodar **`pytest tests/test_docs_pt_br_locale.py`** em `*.pt_BR.md` alterados.                                                                                                                                                                   | PUCRS **Gestão do Conhecimento e Transformação Digital**, **Compliance Criminal** ou **A Escuta dos Excessos** conversam bem com diálogo **DPO/jurídico/compliance** — ver PORTFOLIO seção 3.3. |

---

## 6. Arquétipo E — Revisão de segurança, perfil tipo AppSec

**Serve para:** Quem tria **CodeQL**, risco de dependências ou reportes em **SECURITY.md**.

| Horizonte                  | Data Boar (repositório)                                                                                 | Carreira / certificações opcionais                                                                                                          |
| ---------                  | ------------------------                                                                                | -----------------------------------                                                                                                         |
| **Primeiras 2–4 semanas**  | [SECURITY.pt_BR.md](../SECURITY.pt_BR.md), reproduzir achados localmente, correções mínimas com testes. | —                                                                                                                                           |
| **Próximo 1–2 trimestres** | Alinhar **severidade** e divulgação com o mantenedor; evitar refatoração oportunista.                   | Trilha **CWL** (seção 3.2) é o melhor encaixe; entradas tipo **IBM / Certiprof** já listadas no PORTFOLIO se precisarem de badges iniciais. |

---

## 7. Arquétipo F — QA / expansão de harness de testes

**Serve para:** Quem adiciona cobertura **pytest**, fixtures ou guardas de regressão.

| Horizonte                  | Data Boar (repositório)                                                                              | Carreira / certificações opcionais                                                                       |
| ---------                  | ------------------------                                                                             | -----------------------------------                                                                      |
| **Primeiras 2–4 semanas**  | [TESTING.pt_BR.md](TESTING.pt_BR.md), `scripts/quick-test.ps1`, um módulo por vez.                   | —                                                                                                        |
| **Próximo 1–2 trimestres** | Preferir testes **rápidos e determinísticos**; documentar novos gates em TESTING ou runbooks em ops. | Material **ISTQB** é opcional e genérico; valor no produto é evidência **pytest + CI** no perfil GitHub. |

---

## 8. Checklist curto do mantenedor

- [ ] Arquétipo definido; **primeira issue** é pequena e merge rápido.
- [ ] Arquivo de roteiro **privado** criado a partir do template (se você acompanhar planos por pessoa).
- [ ] No máximo **um** curso/certificação pesada **em andamento** por pessoa, salvo se ela só tiver horas de estudo.
- [ ] Ligar trabalho no **Data Boar** (PRs) ao roteiro privado para carreira e produto ficarem na mesma narrativa.

---

## 9. Checklist de narrativa LinkedIn e ATS (seguro para público)

Use este checklist para melhorar descoberta profissional sem vazar dados privados de clientes:

- Deixe o headline orientado a resultado (engenharia de privacidade, habilitação de compliance, secure-by-design).
- No About/Resumo, separe claramente **o que já existe** do **que está em roadmap**.
- Cite evidências mensuráveis de engenharia (testes, gates de CI, releases, ownership de docs).
- Use palavras-chave por papel (AppSec, privacidade de dados, apoio ao DPO, segurança de APIs, SRE, governança).
- Evite overclaim (nada de "certifica conformidade"; use "apoia evidência e remediação").
- Linke apenas artefatos públicos (docs, release notes, PRs, talks) e mantenha identificadores de clientes em privado.

**Playbook completo** (seções, exportação ATS, contexto de SSI, sementes de keywords por arquétipo): **[`docs/ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md`](ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md)** ([EN](ops/LINKEDIN_ATS_PLAYBOOK.md)).

---

## Revisão

| Data       | Nota                                                           |
| ---------- | ----                                                           |
| 2026-03-27 | Roteiros iniciais por arquétipo + ponte para template privado. |
| 2026-04-01 | Adicionado checklist de narrativa LinkedIn/ATS para perfis públicos. |
| 2026-04-02 | Link para o playbook completo **`LINKEDIN_ATS_PLAYBOOK`** em `docs/ops/`. |
