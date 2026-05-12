# Relatórios e saídas orientadas a compliance

**English:** [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md)

**Público:** CISOs, DPOs, integradores e **estudantes** que precisam de um só lugar para ver como artefatos técnicos de **varredura** (SQLite, metadados por linha) viram entregáveis **legíveis por humanos** — sem tratar o produto como suite GRC corporativa completa.

**Veja também:** [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md) (módulos de verificação e limites estilo ROPA), [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) (postura jurídica), [MAP.pt_BR.md](MAP.pt_BR.md) (navegação por preocupação).

---

## O que já existe vs o que está planejado

| Saída | Estado | Notas |
| ----- | ------ | ----- |
| **Excel (XLSX)** por sessão de varredura | **Entregue** | Artefato tabular principal: achados, report info, tendências quando há histórico, planilhas opcionais de cruzamento e revisão sugerida — ver abaixo. |
| **Markdown executivo (`POC_SUMMARY_*.md`) + YAML de evidência (`scan_manifest_*.yaml`)** | **Entregue** | Gravados junto ao XLSX quando `generate_report` roda. O Markdown é adequado a *stakeholders* externos: padrões e contagens agregadas, seção de **metodologia e segurança**, **Top 3** APG e **inventário completo por padrão** (remediação); sem nomes de coluna/tabela/caminho nem amostras de célula. O YAML consolida amostragem, timeouts e bullets DBA/SRE. Para gerar só o Markdown a partir do SQLite: **`data-boar-report`** — [USAGE.pt_BR.md](USAGE.pt_BR.md) (seção 5; [EN](USAGE.md)). |
| **Heatmap PNG** | **Entregue** | Imagem de densidade associada à sessão. |
| **Relatórios HTML** / views do dashboard | **Entregue** | Uso pelo operador; tier e config podem aplicar. |
| **JSON de trilha de auditoria** (`--export-audit-trail`) | **Entregue** | Snapshot legível por máquina (resumo de sessões, log de wipe, runtime trust, transporte do dashboard, **contagens de integridade da maturidade**). Versão de esquema: ver `core/audit_export.py` e [ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md). |
| **POC de autoavaliação de maturidade** (questionário no dashboard) | **Entregue (com portão)** | Com `api.maturity_self_assessment_poc_enabled` e tier permitindo: respostas no SQLite com HMAC opcional por linha; **download CSV e Markdown** via `GET /{locale}/assessment/export?format=csv|md` — não é um PDF único combinado com o scan. |
| **PDF executivo (“estilo GRC” a partir dos achados do scan)** | **Planejado** | Nome de feature **Pro** em `core/licensing/tier_features.py` (`report_pdf`); ainda **não** há gerador sob `report/`. Mantenedores seguem o âmbito pela árvore de planos internos (caminho texto `docs/plans/`, arquivo **`PLAN_PDF_GRC_REPORT.md`**) a partir de **docs/README** — *Interno e referência*; este doc **não** liga para lá ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)). |
| **JSON executivo GRC (contrato de matriz de risco)** | **Parcial (Python)** | Especificação + exemplo: [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) ([EN](GRC_EXECUTIVE_REPORT_SCHEMA.md)), [../schemas/grc_executive_report.v1.example.json](../schemas/grc_executive_report.v1.example.json). Classe consolidadora **`report.grc_reporter.GRCReporter`** monta o *payload* a partir de linhas fornecidas pelo chamador; **densidade** opcional usa **`core.intelligence`** (`calculate_risk`, `PII_MAPPING`) e **`report.grc_risk_taxonomy`** (`LgpdDensityRiskConfig`; ingestão completa SQLite ainda *roadmap*). Viewer executivo opcional em **Streamlit**: instale com ``uv sync --extra grc-dashboard`` e rode ``streamlit run app/dashboard.py`` (caminho alternativo: variável de ambiente ``DATA_BOAR_GRC_JSON``). **Exportação XLSX + PDF** a partir do mesmo JSON: ``uv run python scripts/export_reports.py --input <caminho-do-v1.json>`` (grava ``*_remediation.xlsx`` e ``*_executive.pdf`` ao lado do *input*, salvo ``--xlsx`` / ``--pdf``); implementação **`report.grc_export_multiformat`**. |

---

## Pipeline: dos achados à “linguagem do CISO”

1. A **varredura** grava linhas **só com metadados** no SQLite (`database_findings`, `filesystem_findings`, `scan_failures`, tabelas de sessão, cruzamento agregado opcional, inventário de fonte de dados opcional — quando existir para a sessão).
2. **`generate_report`** (`report/generator.py`) lê essas linhas e monta:
   - Planilha **Executive summary** (visão agregada).
   - Planilhas **Database findings** / **Filesystem findings** (detalhe colunar: alvo, localização, padrão, sensibilidade, `norm_tag`, texto de recomendação quando configurado).
   - **Report info** (sessão, versão, notas opcionais de jurisdição quando habilitadas — heurística, não conclusão jurídica).
   - Planilhas opcionais: **Trends**, **Cross-ref data – ident. risk**, **Suggested review (LOW)**, **Data source inventory**, **Scan failures**.
3. A imagem do **heatmap** é gravada junto ao workbook.
4. **Markdown executivo + manifesto** (`POC_SUMMARY_*.md`, `scan_manifest_*.yaml`) são *best-effort*: falha **não** bloqueia o XLSX (ver [USAGE.pt_BR.md](USAGE.pt_BR.md), bloco *Resumo executivo*; [EN](USAGE.md), seção 5).
5. **Operadores** combinam Excel + heatmap + **JSON de trilha** opcional e **Markdown de mesa** opcional para governança e **preparação** a auditoria — ainda sem substituir assessoria ou fluxo GRC enterprise.

---

## Exportações de maturidade (separadas do XLSX do scan)

O POC de **maturidade organizacional** é uma linha **paralela**: respostas e rubrica viram **CSV** ou **Markdown** para download. São **sinais auto declarados** (aviso no export), não determinação de adequação jurídica pelo produto.

Resumos de integridade dessas respostas também podem entrar no JSON do **`--export-audit-trail`** (`maturity_assessment_integrity`), alinhados ao dashboard/`GET /status` — ver ADR 0037.

---

## Futuro “PDF único” e JSON que o alimenta (direção de desenho)

**Contrato JSON GRC (matriz para CISO/DPO):** antes ou em paralelo ao PDF, usar o *payload* de **matriz de risco** descrito em [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) para React/Streamlit/motores de relatório partilharem uma forma **auditável** (`report_metadata`, `executive_summary`, `compliance_mapping` como *hints*, `detailed_findings`, `recommendations`).

Quando existir **PDF ligado ao scan**, um **contrato de dados** razoável tende a juntar:

- **Fatia de achados:** contagens agregadas, severidades principais, sinalizadores de tensão jurisdicional (só metadados), heatmap incorporado ou por referência.
- **Fatia de governança:** subconjunto do payload de `build_audit_trail_payload` (versão de esquema, versão da app, lista de sessões, campos de integridade).
- **Fatia de maturidade (opcional):** resumo de rubrica de um batch escolhido + aviso — **sem** “base legal” automática a partir do nome do conector.

**Coordenação com LLM externo (ex.: Gemini):** usar o **JSON estável** do `--export-audit-trail` e os **CSV/MD exportados** como insumo para **rascunhar** texto; manter **tabelas e pontuação canónicas** no repositório. Não colar segredos nem PII bruto nos prompts.

---

## Guardrails de produto (preenchimento automático de inventário)

**Inferência de titular** (ex.: “tripulante vs motorista” só por coluna ou contexto de sistema) e **“base legal”** automática amarrada a nome de produto (ex.: sistemas aduaneiros) têm **alto risco** de falso positivo e de **mensagem jurídica enganosa**. A metodologia pública é expor **categorias, local, tensão e prioridade de triagem** e deixar **base legal e papel do titular** com **DPO / assessoria** — ver [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md) e [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md). Se no futuro houver modelos de texto **sugeridos**, têm de ser **explicitamente não autoritativos** e opt-in.

---

## Onde configurar e testar

- **Diretório e comportamento do relatório:** [USAGE.pt_BR.md](USAGE.pt_BR.md) — chaves `report` ([EN](USAGE.md)).
- **Markdown executivo a partir do SQLite:** [USAGE.pt_BR.md](USAGE.pt_BR.md) — comando `data-boar-report` (bloco *Resumo executivo*; [EN](USAGE.md), seção 5).
- **Caminho do pack de maturidade e portão:** [USAGE.pt_BR.md](USAGE.pt_BR.md) — `api.maturity_self_assessment_poc_enabled`, `api.maturity_assessment_pack_path` ([EN](USAGE.md)).
- **Validação sintética / laboratório:** [TESTING_POC_GUIDE.pt_BR.md](TESTING_POC_GUIDE.pt_BR.md) para corpus e notas tipo SBOM para revisores — não substitui este mapa de saídas.
