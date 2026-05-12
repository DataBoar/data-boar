# Mapa de tópicos da documentação (navegação por preocupação)

**English:** [MAP.md](MAP.md)

Esta página é um **índice por preocupação**: liga perguntas de alto nível (o que importa para **CISO**, **DPO** ou **arquiteto de segurança**) aos guias onde comportamento, chaves de config e limites estão descritos. **Dados de crianças e menores** aparecem **em primeiro** de propósito: o produto trata essa **categoria linguística** como trilha dedicada (detector, prioridade no relatório, amostras — não como rodapé genérico de PII). Use este mapa quando já souber o tema (ex.: menores, hints de jurisdição) e quiser o caminho mais curto sem vasculhar pastas. O índice plano completo continua em **[README.pt_BR.md](README.pt_BR.md)** ([EN](README.md)).

---

## Espinha dorsal de documentação para POC (v1.7.x)

Para **prova de conceito** ou ensaio com parceiro, leia nesta ordem para a documentação densa não esconder o que importa para postura:

1. **[TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md)** ([EN](TECH_GUIDE.md)) — instalação, primeira varredura, portas, visão dos conectores.
2. **Este MAPA** — percorra as tabelas abaixo (menores → jurisdição → pontes de detecção → governança do auditor). Para **tensão multinacional** (narrativa, não assessoria jurídica), leia **[JURISDICTION_COLLISION_HANDLING.pt_BR.md](JURISDICTION_COLLISION_HANDLING.pt_BR.md)** ([EN](JURISDICTION_COLLISION_HANDLING.md)) depois das linhas de jurisdição.
3. **[USAGE.pt_BR.md](USAGE.pt_BR.md)** ([EN](USAGE.md)) — chaves `detection`, `report.jurisdiction_hints`, flags CLI/API/painel.
4. **Governança do auditor (evidência hoje vs lacunas):** **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** (inglês).
5. **Dicas de jurisdição (não são conclusões jurídicas):** **[ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)** (inglês) mais a linha de jurisdição na tabela abaixo.

**Planos de execução e PMO** ficam sob o caminho em texto ``docs/plans/`` no seu checkout; este mapa **não** linka daqui para planos em Markdown de camada de produto ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md) — inglês). Use **[README.pt_BR.md](README.pt_BR.md)** — *Interno e referência* ([EN](README.md)) como entrada deliberada (PLANS_TODO, PLANS_HUB, planos concluídos).

---

## Ganchos de ADR (relevantes para POC, corpos em inglês)

| ADR | Por que importa numa POC |
| --- | ------------------------ |
| [0000](adr/ADR-0000-project-origin-and-adr-baseline.md) | Linha de base: ADRs complementam código e planos; ordem de leitura. |
| [0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md) | Por que o pitch aponta para cá e para **docs/README**, e não direto para ``docs/plans/``. |
| [0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) | Jurisdiction hints: só metadados, voltado a DPO; limites de alegação jurídica. |
| [0035](adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) | Tom do README para stakeholders vs vocabulário opcional de deck em outros docs. |
| [0036](adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md) | Redação de exceções/logs; evidência operacional mais segura em logs e texto no DB. |
| [0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) | Auto-auditoria: o que é comprovável hoje (sessões, trilha de export, wipes) vs lacunas explícitas. |

Índice completo: [adr/README.pt_BR.md](adr/README.pt_BR.md) ([EN](adr/README.md)).

---

## Dados de menores e privacidade infantil (âmbito técnico)

| Pergunta | Leia primeiro | Config / comportamento | Relacionados |
| -------- | ------------- | ------------------------ | ------------- |
| Como o produto marca dados de **possível menor** (DDN/idade), limiares, varredura opcional ampliada e cruzamento? | **[MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md)** ([EN](MINOR_DETECTION.md)) | `detection.minor_age_threshold`, `detection.minor_full_scan`, `detection.minor_cross_reference` | [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) ([EN](SENSITIVITY_DETECTION.md)), [USAGE.pt_BR.md](USAGE.pt_BR.md) seções `detection` / relatório ([EN](USAGE.md)) |
| **FELCA** (Brasil) e posicionamento de suporte **só a metadados**? | **[COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)** — *Padrões auditáveis e de gestão* ([EN](COMPLIANCE_FRAMEWORKS.md)) | Mesmo: flags de menor são para inventário, não verificação de idade | [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](COMPLIANCE_AND_LEGAL.md)) |
| **EUA** COPPA / AB 2273 / CO CPA menores — amostras YAML **técnicas** (norm tags, sem aconselhamento jurídico)? | **[COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)** — tabela de amostras e disclaimers ([EN](COMPLIANCE_FRAMEWORKS.md)) | Arquivos em [compliance-samples/](compliance-samples/) (ex.: `compliance-sample-us_ftc_coppa.yaml`) | [compliance-samples/README.pt_BR.md](compliance-samples/README.pt_BR.md) ([EN](compliance-samples/README.md)) |

O histórico de desenho da detecção de menores está num plano **concluído** em `docs/plans/completed/` no seu checkout (`PLAN_MINOR_DATA_DETECTION`); o guia do operador acima é o ponto de entrada mantido (sem link para planos aqui, por regras de arquitetura da documentação).

---

## Dicas de jurisdição (heurística, só metadados)

| Pergunta | Leia primeiro | Config / comportamento | Relacionados |
| -------- | ------------- | ------------------------ | ------------- |
| O que são **jurisdiction hints**, para quem são e como ativar (CLI, API, painel, YAML)? | **[USAGE.pt_BR.md](USAGE.pt_BR.md)** — busque **jurisdiction_hints** / **Report info** ([EN](USAGE.md)) | `report.jurisdiction_hints`, `--jurisdiction-hint`, corpo do `POST /scan` | [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](COMPLIANCE_AND_LEGAL.md)) |
| Por que não são conclusões jurídicas e o que o ADR fixou? | **[ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)** (inglês) | Índice: [adr/README.pt_BR.md](adr/README.pt_BR.md) ([EN](adr/README.md)) | [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) ([EN](COMPLIANCE_TECHNICAL_REFERENCE.md)) |
| **“Tempestade perfeita”** multinacional — regimes sobrepostos, âncora vs deriva, storyboard portuário? | **[JURISDICTION_COLLISION_HANDLING.pt_BR.md](JURISDICTION_COLLISION_HANDLING.pt_BR.md)** ([EN](JURISDICTION_COLLISION_HANDLING.md)) | Mesmas hints opt-in; **sem** score numérico de colisão no produto ainda | [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md), [use-cases/README.pt_BR.md](use-cases/README.pt_BR.md) ([EN](use-cases/README.md)) — inclui storyboard portuário |

---

## Detecção sensível e profundidade de compliance (pontes)

| Pergunta | Leia primeiro | Notas |
| -------- | ------------- | ----- |
| Regex, ML/DL, overrides, dicas de formato do conector | **[SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md)** ([EN](SENSITIVITY_DETECTION.md)) | Complementa [USAGE.pt_BR.md](USAGE.pt_BR.md) relatório e chaves `detection` ([EN](USAGE.md)) |
| Norm tags, amostras, operação multirregional | **[COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)** ([EN](COMPLIANCE_FRAMEWORKS.md)) | Inclui subseção setor segurador BR e tabela de amostras |
| Encodings, limites de API, postura de evidência (TI / DPO) | **[COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)** ([EN](COMPLIANCE_TECHNICAL_REFERENCE.md)) | Limites operacionais, não aconselhamento jurídico |

---

## Governança do auditor (quem vigia o vigilante?)

| Pergunta | Leia primeiro | Notas |
| -------- | ------------- | ----- |
| Que evidências existem **hoje** (atribuição de varredura, wipes, export, redação de logs)? O que **ainda não** está implementado? | **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** (inglês) | Linha de base honesta para narrativas **CISO / estilo SOC2**; evita prometer log imutável por download de relatório ou por cada POST de config. |
| Alinhamento SRE (health, logs, métricas futuras) | **[OBSERVABILITY_SRE.pt_BR.md](OBSERVABILITY_SRE.pt_BR.md)** ([EN](OBSERVABILITY_SRE.md)) | Aponta para esse ADR no enquadramento “governança do auditor”. |

---

## Higiene de PII na árvore pública (ritual do operador)

| Pergunta | Leia primeiro | Notas |
| -------- | ------------- | ----- |
| Passagem sob demanda: seeds privados, ordem de varredura no **HEAD**, padrões para impedir recorrência | **[PII_REMEDIATION_RITUAL.pt_BR.md](ops/PII_REMEDIATION_RITUAL.pt_BR.md)** ([EN](ops/PII_REMEDIATION_RITUAL.md)) | Palavra-chave de sessão **`pii-remediation-ritual`**; complementa — não substitui — a cadência abaixo. |
| Cadência curta / média / longa, checklist **SAFE**, cuidados com reescrita de histórico | **[PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)** ([EN](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md)) | Guia canônico; **`pii-fresh-audit`** no Windows para prova em clone fresco. |

---

## Relatórios, exportações e saídas em formato GRC

| Pergunta | Leia primeiro |
| -------- | --------------- |
| Como os achados no SQLite viram **Excel**, **heatmap**, **Markdown executivo** (`POC_SUMMARY_*.md`), **YAML de evidência** (`scan_manifest_*.yaml`), **JSON de auditoria** e **CSV/MD de maturidade**? Como gerar de novo o resumo de mesa só com o SQLite (`data-boar-report`)? O que está **planejado** vs **entregue** para **PDF** ligado ao scan? Onde está o contrato **JSON GRC** da matriz de risco? | **[REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md)** ([EN](REPORTS_AND_COMPLIANCE_OUTPUTS.md)) · **[USAGE.pt_BR.md](USAGE.pt_BR.md)** (*Resumo executivo*) ([EN](USAGE.md), seção 5) · **[GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)** ([EN](GRC_EXECUTIVE_REPORT_SCHEMA.md)) |

---

## Arranque a frio do agente Cursor (token-aware)

| Pergunta | Leia primeiro | Notas |
| -------- | ------------- | ----- |
| Chat novo, **pouco contexto**, ou o operador escreveu **`short`** / **`token-aware`** — por onde começar sem reler o **`AGENTS.md`** inteiro? | **[OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** ([EN](ops/OPERATOR_AGENT_COLD_START_LADDER.md)) | Escada **ordenada** em uma tela, router de tarefas, sete regras inegociáveis (homelab **`ssh`** = §7); depois **`CURSOR_AGENT_POLICY_HUB`** / **`TOKEN_AWARE_SCRIPTS_HUB`** conforme a necessidade. |

---

## Onde isso se encaixa

- **Instalação e execução técnicas:** [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) ([EN](TECH_GUIDE.md)) termina com um ponteiro **Topic map** de volta a esta página.
- **Filosofia do produto (evidência em vez de teatro):** [philosophy/THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md) ([EN](philosophy/THE_WHY.md)); limite de retenção em zonas sensíveis: [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md).
- **Glossário (termos por tema):** [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) ([EN](GLOSSARY.md)).

Se faltar um tema neste mapa, inclua uma linha em **MAP.md** e **MAP.pt_BR.md** no mesmo PR.

## Manter hubs alinhados à verdade do repositório

O **sequenciamento de planos** e o **inventário de arquivos de plano** são validados por **`plans_hub_sync.py`** e **`plans-stats.py`** (ver **CONTRIBUTING.md** e pre-commit). **Este MAP** é curado: depois de acrescentar ou alterar linhas do hub, corra **`.\scripts\check-all.ps1`** ou **`.\scripts\lint-only.ps1`** se o diff for só documentação, e siga a skill Cursor **doc-hubs-plans-sync** (`.cursor/skills/doc-hubs-plans-sync/SKILL.md`) para manter **índice de ADRs**, ponteiro de **último ADR** no **AGENTS.md** e **par pt-BR** sincronizados.
