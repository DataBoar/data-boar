# Operações de banco enterprise e evidência GRC — padrões para alinhamento ao Data Boar

**English:** [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md)

**Nota de fonte:** sintetiza **documentação estável de fornecedor** e **temas recorrentes** em discurso público Oracle-DBA / DBRE (backup, alta disponibilidade, patching, segregação). **Não** copia texto de posts de terceiros nem trata grades de infográfico no LinkedIn como **requisito automático** de produto. **Ponteiros nomeados de talent pool** ficam em **`docs/private/commercial/`** (gitignored) se você quiser contexto de roster fora do repositório canônico.

---

## Por que isso fica ao lado das notas NIST/CIS e Wazuh

Times de **operação de banco** e pacotes de **templates GRC** falam dialetos diferentes: RTO/RPO, janelas de mudança e “teste de restore” de um lado; RACI, registros de auditoria e planilhas de risco de terceiros do outro. O Data Boar está sobretudo em **descoberta de dados e evidência** (onde há informação sensível). Mapear os três evita **superestimar** (“substituímos o DBA”) e mostra **onde exportações** podem **preencher colunas** se o cliente definir o schema.

---

## Referências primárias estáveis (Oracle — enquadramento de backup / recovery)

Use isso em vez de depender de scrape de rede social para ensinar o time:

- [Oracle Database Backup and Recovery User’s Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/bradv/) (base conceitual da disciplina **backup e recovery** orientada a RMAN na documentação Oracle).

Temas que voltam em treinamento de praticantes e em discurso público (incluindo HA, patching, validação de standby):

- **Restore comprovado** vale mais que “fazemos backup” — mesma ideia do **disciplina de recuperação** adiada em [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.pt_BR.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.pt_BR.md) / [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md).
- **Controle de mudança** e caminhos de **rollback** para risco de schema/deploy — paralelo à **disciplina de revisão** de `.github/workflows` e merges de dependência.
- **Nível de patch** e consciência de **cadeia de suprimentos** (patch verificado) — alinha a **incidente no ecossistema** e hábito de **pin por SHA** ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-Colleague-Nn-pins.md)).
- **Segregação** (prod vs não prod, menor privilégio para admin) — organizacional; o Data Boar apoia **evidência** de **exposição de dados**, não desenho de IAM de SO/DB.

---

## Grades de templates “must-have” cyber / GRC (infográficos em rede social)

Listas que circulam como **pacotes Excel** (dashboard de incidente, rastreador de patch, scorecard de terceiros, registro de achados de auditoria, mapeamento KPI/KRI, etc.) são **modelos mentais úteis**, não contrato para o Data Boar.

| Classe de template (genérico) | O que o Data Boar **pode** contribuir com honestidade | O que fica fora do escopo do produto |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------- |
| **Achados / evidência de auditoria** | Exportações que mostram **onde** conteúdo relevante à política foi encontrado (caminho, tipo, amostra de política) — **anexo** a uma linha de achado se o cliente mapear campos | Severidade de **disponibilidade de banco** ou controle de **rede** |
| **Inventário de dados / tratamento** | Saída de descoberta apoia **Identify** para **dados** (ver tabela NIST CSF na nota Wazuh) | CMDB completo ou ciclo de vida de **ativo** |
| **Risco de terceiros / fornecedor** | Evidência de que **subprocessadores** ou **cópias** de dados apareceram em escopo de varredura (quando aplicável) | Nota financeira ou jurídica do fornecedor |
| **Patch / gestão de vulnerabilidade** | `pip-audit`, Dependabot, roadmap SBOM ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) para **nossa** stack | Cadência de RU Oracle / patch de DB |
| **Dashboard de incidente / IR** | Timestamps e exportações para eventos de **scanner** ou **pipeline** se o cliente integrar logs | Triagem SOC nível 1 para alertas de DB |

**Aprendizado bidirecional:** se compradores pedirem repetidamente **coluna X** numa exportação, isso é **sinal** para produto/docs (campo em CSV/JSON/API), não motivo para clonar um workbook de 36 abas no repositório.

---

## Melhorias de produto e documentação a considerar (adiadas — não implementadas nesta nota)

- Documentar narrativa mínima de **pacote de evidência**: quais artefatos acompanham um scan para consumidores **DPO / auditoria** (alinhado à honestidade em [COMPLIANCE_AND_LEGAL.md](../../COMPLIANCE_AND_LEGAL.md)).
- Trecho opcional de **playbook do operador**: como **anexar** saída do Data Boar a uma **linha GRC** existente do cliente (só processo; sem ferramenta obrigatória).
- Manter **runbooks Oracle / MSSQL / NoSQL** como escopo do **cliente** ou **parceiro** (ex.: DBA), salvo se o produto passar a entregar agentes de DB explicitamente.

---

## Relacionado no repositório

- [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md) — vocabulário CSF/CIS e **Detect/Recover** no lab
- [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.pt_BR.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.pt_BR.md) — confiança, postura adiada
- [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) — backlog
