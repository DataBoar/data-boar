# Relatório executivo GRC — contrato JSON e matriz de risco (desenho)

**English:** [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md)

**Público:** CISO, DPO, integradores que montam **dashboards** (React, Streamlit, etc.) ou **PDF** (ReportLab, fpdf2, etc.) a partir de **metadados de varredura** do Data Boar, traduzindo **bits** em **risco de negócio**, sem tratar o produto como suite GRC enterprise completa.

**Ver também:** [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) (o que já existe), [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md) (*norm tags* e triagem), [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) (postura jurídica — **não** é assessoria), [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) (**GRC**).

**Exemplo (só placeholders):** [../schemas/grc_executive_report.v1.example.json](../schemas/grc_executive_report.v1.example.json)

**Viewer de referência (opcional):** após ``uv sync --extra grc-dashboard``, rode ``streamlit run app/dashboard.py`` na raiz do repositório (caminho alternativo: variável de ambiente ``DATA_BOAR_GRC_JSON``). Funções puras em ``app/grc_dashboard_model.py`` para testes e reutilização sem Streamlit.

---

## 1. Objetivos de desenho

1. **Matriz de risco, não só lista de erros:** cada linha de **`detailed_findings`** traz **contexto de ativo**, **severidade ou `risk_score`**, **categorias de PII** (contagens — **nunca** valores brutos neste JSON) e **prioridade de remediação**.
2. **Metadados auditáveis:** **`report_id`** estável, **`scan_date`** em UTC, **`scanner_version`**, texto de **`scope`** alinhado ao que foi configurado (*targets*, limites, *jurisdiction hint* quando usado).
3. **Dois consumidores:** o mesmo *payload* alimenta **UI interativa** e **PDF** (resumo executivo primeiro).
4. **Mapeamento de compliance não autoritativo:** `compliance_mapping` lista **candidatos** para oficina; **jurídico / DPO** decide aplicabilidade. O produto **não** determina sozinho base legal.

---

## 2. Forma JSON de topo (contrato `data_boar_grc_executive_report_v1`)

| Bloco | Função |
| ----- | ------ |
| **`schema_version`** | *String*, ex.: **`data_boar_grc_executive_report_v1`**. Só sobe com mudança quebradiça de campos ou semântica. |
| **`report_metadata`** | Identidade da corrida: **`report_id`**, opcional **`client_display_name`** (rótulo do operador; pode sair redigido nas exportações), **`scan_date`** (ISO-8601 UTC), **`scanner_version`**, **`scope`**, opcional **`session_id`** ligando ao SQLite. |
| **`executive_summary`** | Agregados: **`total_records_scanned`** (ou unidade definida na implementação), **`pii_instances_found`**, **`critical_assets_at_risk`**, **`compliance_score`** (0–100 **heurístico** — fórmula documentada; **não** é nota de adequação jurídica), **`risk_level`** (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`). |
| **`compliance_mapping`** | Listas como **`lgpd_articles_hint`** / **`gdpr_articles_hint`** — códigos curtos derivados de *norm tags* e tabelas de metodologia; opcional **`mapping_confidence`**. |
| **`detailed_findings`** | Vetor da **matriz de risco** (seção 3 na versão EN). |
| **`recommendations`** | Ações priorizadas: **`id`**, **`priority`**, **`action`**, **`estimated_effort`**, **`regulatory_impact_note`** (hipótese para oficina com DPO, **não** previsão de sanção). |

---

## 3. `detailed_findings[]` — linha da matriz

Cada elemento deve bastar para **uma linha do one-pager do CISO** e para **fila de triagem do DPO**. Alinhar nomes de campo à versão EN; resumo:

| Campo | Tipo | Notas |
| ----- | ---- | ----- |
| **`asset_id`** | string | *Slug* estável; sem segredos. |
| **`asset_class`** | string | Ex.: `database_table`, `filesystem_tree`. |
| **`data_category`** | string | `personal` (dado pessoal comum), `sensitive` (categorias especiais no estilo LGPD art. 11 quando o *pipeline* classifica), ou `unknown`. No consolidador de referência (`report/grc_reporter.py`), `sensitive` **aumenta** o `risk_score` frente a sinais iguais nos outros eixos. |
| **`risk_score`** | número | 0–100: nota **final** após peso de categoria (e futuros ajustes). Alimenta **`executive_summary`** (`compliance_score`, `risk_level`, contagem de ativos críticos). |
| **`risk_score_input`** | número | Transparência: entrada numérica **antes** do ajuste por `data_category` (igual a `risk_score` quando não há *bump*). O `GRCReporter` em Python **emite** o campo; exportadores mínimos podem omitir se precisarem de JSON mais enxuto. |
| **`impact_score`** / **`likelihood_score`** | número | Eixos 0–100 para **mapa de calor** Impacto × Probabilidade. Se a consultoria não informar ambos, o consolidador deriva valores padrão a partir de `risk_score` (ver §3.1 na versão EN). |
| **`heatmap_quadrant`** | string | Um de `impact_high_likelihood_high`, `impact_high_likelihood_low`, `impact_low_likelihood_high`, `impact_low_likelihood_low` — limiar **50** em cada eixo na implementação de referência. |
| **`pii_types`** | vetor | `type`, `count`, `exposure` — só metadados. |
| **`location_summary`**, **`violation_desc`**, **`norm_tags`**, **`remediation_priority`** | — | Igual à versão EN; `violation_desc` permanece **técnica**, sem afirmar ilícito como fato. |
| **`nist_csf_function_hint`** | vetor de strings | **Opcional, non-breaking.** Códigos curtos do **NIST CSF 2.0** (ex.: `"GV"`, `"ID.AM"`, `"PR.DS"`) derivados de `norm_tags` por uma **tabela versionada e shipped** (`report/nist_csf_mapping.yaml`). **Indício heurístico, não conclusão de conformidade** (ver §3.3 e [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)). **Omitido** quando nenhum `norm_tag` mapeia — nunca vetor vazio. |
| **`regulatory_impact`** | string | Frase de **negócio / oficina jurídica** por linha (ex.: artigos candidatos, enquadramento de risco administrativo). **Não** é conclusão jurídica automática; **jurídico / DPO** valida. Pode ser string vazia. |

**Severidade sensível ao contexto:** o mesmo perfil de **`pii_types`** pode implicar **`risk_score`** diferente quando **`asset_class`** é log *append-only* versus repositório de identidade — ver **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md`](ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)**.

### 3.1 Mapa de calor (Impacto × Probabilidade)

*Dashboards* podem plotar **`impact_score`** × **`likelihood_score`**. Enquanto não houver modelo próprio de probabilidade (maturidade de controles, janela de exposição), o **`GRCReporter`** preenche eixos padrão a partir do `risk_score` consolidado — ver **`default_heatmap_axes_from_risk`** na versão EN e no código. Substitua por dados do *engagement* quando existirem.

### 3.2 Densidade de risco alinhada à LGPD (campos opcionais por linha)

Com **`lgpd_density=LgpdDensityRiskConfig(...)`** em **`GRCReporter.add_finding`** / **`add_detailed_finding`**, o **`risk_score`** vem de **`report.grc_risk_taxonomy`**: tabela **identificadores (10)** / **financeiros_gov (30)** / **sensitive (80)** / **infantil (100)** por unidade contada, fórmula **Σ(count × peso)**, escala 0–100 com **`cap_raw`** padrão **2500** (ajustável). Campos extras: **`risk_density_raw`**, **`risk_density_scaled_cap`**, **`risk_density_breakdown`** (inclui **`risk_category`**: ``IDENTIFIER`` / ``FINANCIAL`` / ``SENSITIVE`` / ``CHILD_DATA`` vindo de **`core/intelligence`**), **`risk_density_taxonomy_version`**, **`dominant_risk_taxonomy`** — ver tabela e fórmulas na versão EN (§3.2). **Não** é classificação jurídica automática; **DPO/jurídico** valida rótulos e pesos por contrato.

### 3.3 *Hint* opcional de função **NIST CSF 2.0** (non-breaking)

CISOs costumam raciocinar pelas *Functions* do **NIST CSF 2.0** (Govern, Identify, Protect, Detect, Respond, Recover). Para um *dashboard* ou PDF **filtrar findings por função CSF** sem alterar o contrato, cada linha de `detailed_findings[]` **pode** carregar um vetor **opcional** de códigos curtos:

| Campo | Tipo | Notas |
| ----- | ---- | ----- |
| **`nist_csf_function_hint`** | vetor de strings | Códigos CSF 2.0 — **Function** (`"GV"`, `"ID"`, …) ou **Function.Category** (`"ID.AM"`, `"PR.DS"`). Ordem canônica **GV, ID, PR, DE, RS, RC**. Presente só quando ao menos um `norm_tag` mapeia. |

**Onde fica o mapeamento (versionado e shipped — não hard-coded):** `report/nist_csf_mapping.yaml` (`mapping_version`, ex.: `nist_csf_2_0_hint_v1`). Mapeia substrings de `norm_tag` para códigos CSF — mesmo modelo dos **article hints** (§4) e dos perfis [compliance-samples/](compliance-samples/). O consolidador `report/grc_reporter.py` deriva o *hint* de `norm_tags`; o *loader* é `report/nist_csf_hints.py`.

**Local do disclaimer (ADR-0025):** para cada linha continuar um vetor simples de códigos, o disclaimer heurístico e a versão da tabela aparecem **uma vez** em `compliance_mapping` (emitidos só quando ao menos um finding carrega o *hint*):

| Chave em `compliance_mapping` | Significado |
| ----- | ----- |
| **`nist_csf_function_hint_method`** | Ex.: `heuristic_norm_tag_to_csf_v1`. |
| **`nist_csf_mapping_version`** | Versão da tabela shipped. |
| **`nist_csf_function_hint_disclaimer`** | Em linguagem clara: **indício, não conclusão de conformidade nem atestado de controle** ([ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)); CISO/DPO valida. |

**Non-breaking:** campo **opcional aditivo** — `schema_version` continua `data_boar_grc_executive_report_v1`; consumidores que ignoram chaves desconhecidas não são afetados. **Escopo:** apenas NIST CSF 2.0 (sem COBIT/SOC 2/ISO aqui). O posicionamento tri-nível em **prosa** (NIST CSF / SANS / ISO 27035) é o complemento textual; este campo é o complemento **estruturado** que faz o artefato *carregar* a tag CSF.

---

## 4. Lógica de mapeamento (artefatos Data Boar → este JSON)

Contrato para quem implementar o gerador. Um consolidador de primeira mão existe em **`report/grc_reporter.py`** (`GRCReporter`); categorias de risco em inglês e ``calculate_risk`` em **`core/intelligence.py`**; rótulos de camada GRC e escala 0–100 em **`report/grc_risk_taxonomy.py`**. Ingestão completa de linhas SQLite e PDF continuam evolução futura.

| Origem | Destino |
| ------ | ------- |
| Linha de **sessão** SQLite | **`report_metadata`**, contexto opcional do resumo. |
| Linhas **`database_findings` / `filesystem_findings`** | **`detailed_findings`** e agregações do **`executive_summary`**. |
| **`report.recommendation_overrides`** no *config* | **`recommendations`** quando configurado. |
| Heatmap / densidade da sessão | Referências visuais opcionais no resumo. |
| **`--export-audit-trail`** (`core/audit_export.py`, [ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)) | Versão da app / anexo de integridade ou *runtime trust*. |
| **`lab_result.json`** do completão | Por padrão **fora** do JSON GRC do cliente; uso **interno** de garantia de ambiente de varredura. |

**`compliance_score`:** documentar fórmula junto do código gerador; divulgar no rodapé do PDF/dashboard que é **heurística**.

**Dicas de artigos:** mapear `norm_tag` + tabelas versionadas (YAML/CSV com amostras de compliance), sem codificar “verdade jurídica” em comentários.

---

## 5. *Checklist* de entrega (CISO / DPO)

1. Confirmar que **`scope`** corresponde à **carta de escopo** ou ao **enquadramento** acordado (sistemas dentro/fora).
2. Tratar **`compliance_mapping`**, o **`regulatory_impact`** de cada linha e o **`regulatory_impact_note`** das recomendações como **ponto de partida** de oficina. **Não** tratar texto modelo sobre multas ou artigos como **assessoria verificada** sem revisão jurídica.
3. Manter **PII bruta** fora deste JSON; anexos redigidos ou dashboard com controlo de acesso.
4. Versionar **`schema_version`** nas notas de release quando campos mudarem.
5. Conferir **`data_category`** (`personal` vs `sensitive`) contra o **inventário de dados** e a análise jurídica; o classificador do produto é **indício**, não decisão definitiva de LGPD art. 11.

---

## 6. Evolução

As implementações devem gravar **`schema_version`**: **`data_boar_grc_executive_report_v1`** e notas de migração nas *release notes* quando a forma mudar. Referência de construção: **`report.grc_reporter.GRCReporter`**. O arquivo de especificação em **`docs/GRC_EXECUTIVE_REPORT_SCHEMA*.md`** permanece o **contrato estável** para integradores; o *roadmap* PDF permanece descrito no hub interno de documentação (ver [README.pt_BR.md](README.pt_BR.md) — *Internal and reference*).
