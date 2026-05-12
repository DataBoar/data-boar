# Metodologia de compliance — descoberta, risco técnico e campos estilo ROPA

**English:** [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md)

**Público:** DPOs, líderes de segurança, integradores e **estudantes** que alinham trabalho acadêmico de adequação à LGPD com um produto de **inventário técnico**. Esta página é **metodologia e priorização** — não é assessoria jurídica. Para limites legais e artefatos, veja [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md); para frameworks e amostras, [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md). Para **Excel, heatmap, JSON de auditoria, export de maturidade e roadmap de PDF**, veja [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

---

## O que “metodologia” significa no Data Boar

O Data Boar responde a perguntas **técnicas** com **evidência repetível**:

1. **Onde** podem aparecer dados pessoais ou em categorias sensíveis nos alvos configurados?
2. **Quão forte** é o sinal (padrão, sugestão ML/DL, contexto entre tabelas)?
3. **Quais etiquetas orientadas a normas** (`norm_tag`, texto de recomendação) ajudam humanos a alinhar achados ao **seu** mix regulatório?

Isso **não** equivale a declarar **adequação jurídica** (por exemplo, que determinado tratamento é lícito) nem a preencher sozinho todas as colunas de um **registro de atividades de tratamento** (ROPA / enfoque **RIPD** sob a LGPD). A metodologia abaixo mantém essa fronteira explícita e oferece **módulos de verificação** para mapear em aulas, auditorias ou checklists internos — inclusive índices que você mantém fora deste repositório.

---

## Alinhar seu próprio índice de adequação (ex.: modelo Word de diagnóstico)

Muitas organizações e cursos usam um **índice estruturado de adequação ou lacunas** (seções, pesos, colunas de evidência). Se você tiver um modelo privado (por exemplo `diagnostico_indice_adequacao_lgpd_*.docx`), use-o como **fonte de títulos de seção e pesos**; mapeie cada seção a um ou mais **módulos** da tabela abaixo. O repositório público **não** incorpora sílabos proprietários nem texto integral de curso não publicado — guarde o rastro linha a linha em **`docs/private/`** e contribua de volta só **títulos genéricos** ou priorizações adequadas a qualquer operador.

---

## Módulos de verificação (formato produto)

Estes módulos descrevem **o que o software verifica ou sinaliza hoje** (ou em trabalho faseado documentado), não o que o jurídico “homologa”.

| Módulo | Intenção de verificação | Onde ver no produto / docs |
| ------ | ------------------------ | --------------------------- |
| **M1 — Presença e categoria** | Há evidência de dado pessoal ou em categoria especial no escopo, e **qual categoria** (padrão / norm tag)? | Planilhas de achados, `norm_tag`, [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md), [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) |
| **M2 — Severidade técnica** | Qual a urgência de **triagem técnica** (faixa de sensibilidade, texto de prioridade, risco de quasi-identificador / cruzamento)? | Colunas do Excel, planilha “Cross-ref data – ident. risk” quando preenchida, [MAP.pt_BR.md](MAP.pt_BR.md) |
| **M3 — Postura da fonte de dados** | Quais **sistemas** guardaram o dado (produto, protocolo, sinais de transporte) sem copiar conteúdo de célula? | Planilha “Data source inventory” quando habilitada, [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) |
| **M4 — Menores e contextos vulneráveis** | Há **sinais** compatíveis com possíveis campos ligados a menores ou combinações que pedem revisão de política? | [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) |
| **M5 — Tensão jurisdicional** | Metadados sugerem **mais de um** regime plausível para a assessoria priorizar? | [JURISDICTION_COLLISION_HANDLING.pt_BR.md](JURISDICTION_COLLISION_HANDLING.pt_BR.md), [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) |
| **M6 — Governança do auditor** | A organização mostra **quem executou** varreduras e quais artefatos existem para exportação? | [ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) |
| **M7 — Retenção em contexto lacrado / adjacente à alfândega** | A **retenção** de artefatos é **do operador**, sem etiquetas automáticas de “base legal”? | [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) |

**Nível de risco** nesta metodologia significa **risco técnico e de triagem** (exposição, força da categoria, risco de combinação) — **não** substitui seu registro de risco empresarial nem conclusão jurídica.

---

## Colunas estilo ROPA: o que automatizar primeiro

Nomes variam por modelo: **Titular**, **Finalidade**, **Base legal**, **Categoria**, **Prazo de retenção**, **Compartilhamento**, **Medidas de segurança**, **Operador**, **Transferências internacionais**, etc.

**Prioridade sugerida** de automação no Data Boar (e em motores de inventário parecidos):

| Coluna / tema | Automatizar primeiro? | Justificativa |
| ------------- | ---------------------- | --------------- |
| **Categoria dos dados / tipo** | **Sim — já é núcleo** | Encaixa bem: padrões, sugestões ML/DL, `norm_tag`, sensibilidade. |
| **Local / sistema / ativo** | **Sim — alto valor** | Alvo, esquema, tabela, caminho, tipo de conector; “Data source inventory” amplia isso. |
| **Risco técnico / prioridade de triagem** | **Sim — já é núcleo** | Planilhas de recomendação (colunas como “Base legal”, “Risco”, “Prioridade” são **texto orientador**, não base legal afirmada — veja abaixo). |
| **Titular** | **Depois / sobretudo humano** | Inferir *quem* é o titular só pelo nome de coluna é frágil; priorize **categoria** e **local**, depois o DPO preenche titular com conhecimento de processo. |
| **Finalidade** | **Liderado por humano** | Finalidade vem do **processo de negócio** e dos registros de tratamento; futuro opcional: **pistas por metadados** (nomes de coluna, apps) só como *sugestão*. |
| **Base legal** | **Nunca afirmar sozinho** | O motor pode exibir **linguagem de recomendação** alinhada a normas; a **escolha** da base lícita é **jurídico / DPO**. Postura no [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md). |
| **Prazo de retenção** | **Liderado por humano** | Não se deduz de amostras de conteúdo sem política e contexto jurídico. |
| **Compartilhamento / terceiros** | **Parcial** | “Onde mais esse atributo aparece?” (varreduras multi-alvo) apoia **inventário**; contratos e relações jurídicas ficam fora da ferramenta. |
| **Medidas de segurança** | **Parcial** | Sinais técnicos (ex.: TLS vs texto puro, inventário de versão, recomendações de hardening quando existirem) alimentam **security** — não atestam controle ISO 27001 completo. |
| **Transferência internacional** | **Só pistas** | Notas opcionais de jurisdição marcam **tensão** para revisão, não o mecanismo de transferência. |

Para a próxima fatia de **produto**, em geral o maior retorno é: **(1)** exportações mais ricas de **categoria + local**, **(2)** **pistas de finalidade** por metadados (sempre rotuladas como não autoritativas), **(3)** ligação mais clara **entre sistemas** para “mesmo atributo lógico em dois lugares” — ainda **sem** preencher automaticamente **base legal** nem **titular**.

---

## Leitura relacionada

- [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) — o que o produto faz e não reivindica.
- [philosophy/THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md) — postura evidência primeiro.
- [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) — limites, amostragem, timeouts.
