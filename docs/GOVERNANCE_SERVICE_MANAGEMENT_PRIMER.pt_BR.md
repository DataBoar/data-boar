# Primer de governança e gerenciamento de serviços

**English:** [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md)

**Audiência:** DPO, CISO, diretor de TI, líder de GRC, auditor externo — leitores que já usam [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) para **rótulos de lei de privacidade** e precisam de uma lente de **gerenciamento de serviços** para os mesmos resultados de varredura.

**Não é aconselhamento jurídico.** Esta página explica **como as organizações falam de valor de TI e controles**; **não** certifica resultados ISO, COBIT, ITIL ou BACEN.

---

## Três camadas (não misture)

| Camada | Pergunta que responde | Papel do Data Boar |
| ------ | --------------------- | ------------------ |
| **Privacidade / lei setorial** | Qual estatuto ou regulador se aplica ao tratamento? | **`norm_tag`**, amostras de conformidade, *recommendation overrides* — [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| **Gestão da segurança da informação** | Como o SGSI/PIMS é construído e evidenciado? | Descoberta, achados **somente de metadados**, heatmaps — [COMPLIANCE_FRAMEWORKS.pt_BR.md#normas-auditáveis-e-de-gestão-papel-de-apoio](COMPLIANCE_FRAMEWORKS.pt_BR.md#normas-auditáveis-e-de-gestão-papel-de-apoio) |
| **Governança de TI e gerenciamento de serviços** | Como a TI co-cria **valor durável** com o negócio e prova operação de controle? | **Audit Trail** por sessão, varreduras repetíveis, exportações opcionais **Governance Lens** (Pro/Enterprise — veja [LICENSING_SPEC.md](LICENSING_SPEC.md)); tabelas em [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md) |

O jurídico ainda decide **lei**; o conselho ainda detém **governança**; a TI ainda detém **desenho de serviço**. O produto entrega **evidência técnica** que essas funções consomem sem redigitar planilhas manualmente.

---

## Capacidade organizacional mínima viável (por que “uma varredura anual” falha)

Programas maduros tratam descoberta como **ciclo**, não como projeto:

1. **Planejar** — escopo de *targets*, perfil de conformidade, dono da remediação.
2. **Executar** — **Data Sniffing** delimitado (conectores + amostragem + detecção).
3. **Medir** — artefatos Excel/GRC, heatmaps, JSON executivo opcional ([GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)).
4. **Melhorar** — comparar sessões (`--diff`), fechar lacunas, ampliar escopo.

**Toil** (trabalho manual repetitivo de inventário) é o que esse ciclo automatiza; veja **toil** no [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md). Cron externo em outro host é válido, mas **não** é o único padrão — varredura agendada é item de **roadmap** do produto (por *tier*); até lá, o operador dispara via CLI/API ou orquestrador próprio.

---

## Pilha de frameworks (mapa de referência)

| Framework | Dono típico | Encaixe resumido do Data Boar |
| --------- | ----------- | ----------------------------- |
| **ISO/IEC 38500** | Conselho / executivo | Evidência para princípios de **responsabilidade**, **desempenho**, **conformidade** — não decide pelo conselho |
| **ISO/IEC 27014** | CISO / governança de SI | **Avaliar → Dirigir → Monitorar → Comunicar → Assegurar** alimentados por inventário e Audit Trail |
| **COBIT 2019** | GRC / auditoria | Objetivos de controle (ex.: **APO13**, **DSS05**, **MEA03**) mapeados a achados e relatórios |
| **ITIL 4** | Gerenciamento de serviços | Co-criação de **valor de serviço**; prática de segurança + **melhoria contínua** via comparação de sessões |
| **ISO/IEC 20000-1** | ITSM | Entradas de configuração/conhecimento — *targets* como itens de configuração, export para *sinks* corporativos (Pro) |
| **BACEN Res. 4.893/2021** | Segurança cibernética (fintech BR) | Insumos de política setorial — parear com amostras LGPD; enquadramento Governance Lens Enterprise |

Títulos oficiais e adoção ABNT NBR no Brasil: [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) §10. Tabelas detalhadas: [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md).

---

## Governance Lens (*tier* comercial)

**Governance Lens** é a camada planejada de **narrativa GRC executiva** sobre os outputs Excel/metadados padrão — chaves **Pro** e **Enterprise** no mapa de licenciamento (`governance_lens_pro`, `governance_lens_enterprise`). Traduz achados técnicos para **linguagem de lacuna de controle** para DPO/CISO/auditoria.

Hoje o motor já produz evidência de inventário; a embalagem Lens (brief executivo DOCX/PDF) entrega quando o módulo de relatório estiver disponível. Até lá, use [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) e [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

---

## Documentação relacionada

- [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md) — tabelas por framework
- [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) — regulamentos e amostras
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.md) — narrativa para liderança
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) — catálogo de artefatos
- [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md) — termos ITSM/GRC (§9–10)
