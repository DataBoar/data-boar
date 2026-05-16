# Architecture Decision Records (ADR)

**English:** [README.md](README.md)

Notas curtas e duradouras que registram **por que** o projeto escolheu um caminho — não só *o que* o código faz. Complementam o **índice da documentação** ([README.pt_BR.md](../README.pt_BR.md) — *Interno e referência* aponta a árvore de planos) para contexto de backlog, e [TESTING.pt_BR.md](../TESTING.pt_BR.md) (o que a CI exige).

## Convenção

| Item          | Regra                                                                                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------                                    |
| **Local**     | Esta pasta: **`docs/adr/`**                                                                                                                                                   |
| **Nome**      | **`ADR-0000-...`** opcional (baseline / meta); **`ADR-0001-titulo-kebab-curto.md`**, **`ADR-0002-...`** para decisões substantivas — incrementar a cada ADR; título estável após o merge. |
| **Idioma**    | **Arquivos numerados (`ADR-0000-*.md`, `ADR-0001-*.md`, …) ficam só em inglês** (texto canônico, como os planos em `docs/plans/`). Este README tem pt-BR.                             |
| **Formato**   | Preferir seções: **Context**, **Decision**, **Consequences**, **References** (estilo MADR serve). Manter em uma ou duas telas.                                                |
| **Quando**    | Comportamento relevante à segurança, trade-offs de docs/ferramenta que voltam a incomodar contribuidores, ou o que não queremos “apagar” sem registro.                        |

## Índice

| ADR  | Título                                                                                                                        | Status |
| ---- | ----------------------------------------------------------------------------------------------------------------              | ------ |
| 0000 | [Project origin and ADR baseline](ADR-0000-project-origin-and-adr-baseline.md)                                                    | Aceito |
| 0001 | [Markdown fix script, MD029, and semantic step lists](ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md)              | Aceito |
| 0002 | [Operator-facing security and technical docs](ADR-0002-operator-facing-security-and-technical-docs.md)                            | Aceito |
| 0003 | [SBOM roadmap — CycloneDX then Syft](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)                                                | Aceito |
| 0004 | [Information architecture — external-tier docs must not link into `plans/`](ADR-0004-external-docs-no-markdown-links-to-plans.md) | Aceito |
| 0005 | [CI and GitHub Actions supply chain — pinned SHAs and pinned uv CLI](ADR-0005-ci-github-actions-supply-chain-pins.md)              | Aceito |
| 0006 | [Operator today-mode layout and published-release sync](ADR-0006-operator-today-mode-layout-and-published-sync.md)                 | Aceito |

## Docs relacionados

- [ADR 0034](ADR-0034-outbound-http-user-agent-data-boar-prospector.md) (EN) — User-Agent HTTP(S) de saída **`DataBoar-Prospector/<versão>`** para conectores de descoberta (REST/API, SharePoint, Power BI, Dataverse); override por `headers` no YAML do alvo.
- [ADR 0035](ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) (EN) — bloco executivo do README (pitch para gestores) separado de rótulos opcionais de deck (**Data Sniffing** / **Deep Boring**); contrato em `tests/test_readme_stakeholder_pitch_contract.py`.
- [ADR 0036](ADR-0036-exception-and-log-pii-redaction-pipeline.md) (EN) — pipeline `sanitize_log_text` / `clean_error` e `scan_failures.details` redigido (sem vazar PII de exceções de driver/HTTP no SQLite ou em logs).
- [ADR 0037](ADR-0037-data-boar-self-audit-log-governance.md) (EN) — **governança do auditor**: o que já existe (sessões SQLite, export audit trail, logs, WebAuthn), lacunas explícitas (sem log imutável por download de relatório / por POST de config) e direção futura.
- [ADR 0038](ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) (EN) — **ambiguidade jurisdicional**: o produto **alerta** e ajuda a **inventariar tensão** (várias hints / sinais conflitantes em metadados); **não** escolhe lei aplicável nem base legal; guia [JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md).
- [ADR 0039](ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) (EN) — **retenção e postura de evidência** em contextos de **recinto / adjacência alfandegária**: operador dono de retenção de artefatos; produto **não** implementa prazos legais nem “flag” automática de exceção; filosofia pública em [THE_WHY.pt_BR.md](../philosophy/THE_WHY.pt_BR.md).
- [ADR 0040](ADR-0040-assistant-private-stack-evidence-mirrors-default.md) (EN) — **espelhos do repo privado empilhado** (`docs/private/`): assistente **atualiza todos** os destinos alcançáveis (lab + bare no volume cifrado quando existir) quando o pedido já implica alinhar/sync/higiene; **sem** perguntas retóricas de backup.
- [ADR 0041](ADR-0041-lab-completao-data-contract-preflight.md) (EN) — **preflight de contrato de dados** no completão (opcional): YAML + env com URL SQLAlchemy; valida colunas exigidas **antes** do smoke SSH por host; ver [LAB_COMPLETAO_RUNBOOK.pt_BR.md](../ops/LAB_COMPLETAO_RUNBOOK.pt_BR.md).
- [ADR 0042](ADR-0042-lab-lessons-learned-archive-contract.md) (EN) — **arquivo público de lições de lab**: snapshots datados em **`docs/ops/lab_lessons_learned/`** + hub **`LAB_LESSONS_LEARNED.md`**; token de sessão **`lab-lessons`** e regra situacional **`lab-lessons-learned-archive.mdc`**; ponte para **`PLANS_TODO.md`**.
- [ADR 0044](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) (EN) — Dependabot passa a usar **`package-ecosystem: "uv"`**: PRs movem `pyproject.toml` + `uv.lock` juntos (operador faz **`uv export`** para regenerar `requirements.txt` conforme [ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md)); evita o vermelho determinístico do guard `tests/test_dependency_artifacts_sync.py`.
- [ADR 0053](ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md) (EN) — pin explícito de **`ebcdic<2`** (cadeia `extract-msg`) + `ignore` no Dependabot para major impossível.
- [ADR 0054](ADR-0054-chardet-pinned-by-cyclonedx-bom.md) (EN) — pin dev de **`chardet<6`** (cadeia `cyclonedx-bom` / SBOM) + `ignore` de major no Dependabot.
- [ADR 0043](ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md) (EN) — **amostragem SQL por coluna**: filtro **`IS NOT NULL`** antes do teto de linhas; hook **`sql_sampling`** para evolução (metadados / `TABLESAMPLE`); env opcional **`DATA_BOAR_SQL_SAMPLE_LIMIT`**; plano [`PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md`](../plans/PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md).
- [ADR 0032](ADR-0032-maturity-assessment-batch-history-sqlite.md) (EN) — histórico por **batch** do questionário de maturidade no HTML do dashboard (agregação SQLite + tabela; RBAC/tenant **não** — ver [#86](https://github.com/FabioLeitao/data-boar/issues/86)).
- [ADR 0033](ADR-0033-webauthn-open-relying-party-json-endpoints.md) (EN) — WebAuthn **RP** aberto (biblioteca `webauthn`): endpoints JSON em `/auth/webauthn/` por trás de `api.webauthn.enabled`; sem lock-in de vendor; UI do dashboard ainda não exige login (fase **#86**).
- [ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md) (EN) — fechamento de atualização Python num único passe (`pyproject.toml` → lock → `requirements.txt`, `uv sync`, gate completo, SBOM/ADR quando aplicável); qualquer origem (CI, bots, review) usa o mesmo fluxo.
- [ADR 0031](ADR-0031-pypi-packaging-hatchling-flat-layout.md) (EN) — empacotamento PyPI com **Hatchling** (layout plano explícito), script **`scripts/pypi-publish.ps1`**, entry point **`data-boar`** → `main:main`.
- [ADR 0029](ADR-0029-cursor-markdown-preview-guardrail-and-lab-smoke-ansible-hook.md) (EN) — guardrail Cursor (preview Markdown em aba) + playbook Ansible `lab-smoke-stack-init-perms`; ver [CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md](../ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md) e [LAB_SMOKE_MULTI_HOST.pt_BR.md](../ops/LAB_SMOKE_MULTI_HOST.pt_BR.md).
- [ADR 0028](ADR-0028-lab-external-connectivity-eval-playbook.md) (EN) — playbook rastreado para avaliação de conectividade **externa** (APIs públicas, BD somente leitura com política); sem segredos no Git; ver [LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md](../ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.pt_BR.md).
- [ADR 0026](ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) (EN) — *jurisdiction hints* opcionais (DPO, heurística, só metadados no Report info); não conclusão jurídica; ver [USAGE.md](../USAGE.md) e [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md).
- [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) (EN) — limites **Pro / Enterprise** documentados em `LICENSING_OPEN_CORE_AND_COMMERCIAL`; claims JWT ilustrativos em `LICENSING_SPEC`; enforcement ainda não no runtime; exemplos com nome ficam em `docs/private/`.
- [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) (EN) — posicionamento de **compliance**: evidência e inventário, **não** motor de **conclusão jurídica**; alinhado a [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md).
- [ADR 0024](ADR-0024-enterprise-discovery-three-complementary-tracks.md) (EN) — descoberta enterprise em **três trilhos complementares** (planos + narrativa; sem promessa legal); ver `docs/plans/PLAN_*` citados no ADR.
- [ADR 0022](ADR-0022-public-glossary-compliance-and-platform-terms.md) (EN) — glossário público: leis de conformidade, papéis (ex.: DPO), termos de plataforma (SRE, TLS, OAuth2); definições curtas; detalhe nos docs canônicos.
- [ADR 0021](ADR-0021-public-web-presence-dns-alias-and-hosting.md) (EN) — presença web pública: alias DNS (CNAME), host canônico, TLS, forma de hospedagem (marketing vs produto).
- [ADR 0020](ADR-0020-ci-full-git-history-pii-gate.md) (EN) — a CI executa `pii_history_guard.py --full-history` com checkout completo (`fetch-depth: 0`).
- [CONTRIBUTING.pt_BR.md](../../CONTRIBUTING.pt_BR.md) — fluxo do contribuidor; menciona MD029 e o script de correção.
- [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) · [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) — entradas para operadores ([ADR 0002](ADR-0002-operator-facing-security-and-technical-docs.md), EN).
- [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — §6 (MD029), §7 (ADRs), SBOM. *(EN.)*
- [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../ops/WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) — follow-ups de workflow ([ADR 0005](ADR-0005-ci-github-actions-supply-chain-pins.md) sobre pin de Actions/uv).
- [.cursor/rules/markdown-lint.mdc](../../.cursor/rules/markdown-lint.mdc) — quando rodar `fix_markdown_sonar.py` e renumeração pós-script.
- [.cursor/rules/audience-segmentation-docs.mdc](../../.cursor/rules/audience-segmentation-docs.mdc) — links externos vs internos; [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md) (texto canônico em inglês).

## Índice geral da documentação

Veja [docs/README.pt_BR.md](../README.pt_BR.md) para o mapa completo.
