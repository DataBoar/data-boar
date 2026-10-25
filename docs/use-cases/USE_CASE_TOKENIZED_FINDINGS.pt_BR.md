# Use case — Findings tokenizados para compartilhamento seguro

**English:** [USE_CASE_TOKENIZED_FINDINGS.md](USE_CASE_TOKENIZED_FINDINGS.md)

**Somente ilustrativo** — não é assessoria jurídica. Exige plugin **Enterprise** de tokenização/remediação (plano `docs/plans/PLAN_REMEDIATION_INTERFACE.pt_BR.md`, GitHub **#601**).

---

## Problema

Exportações de findings (por exemplo **JSONL**) costumam incluir campos **`sample`** com **fragmentos reais de PII** para validar confiança do detector. Isso impede compartilhar o mesmo relatório com auditores externos, reguladores, parceiros ou SOC offshore sem redação manual.

> Não posso mostrar o relatório de findings para o auditor porque ainda tem dado pessoal vivo.

---

## Antes e depois (conceitual)

| Modo | Exemplo de campo `sample` | Risco |
| ---- | ------------------------- | ----- |
| **Hoje** | `123.456.789-00` (padrão de ID nacional real) | PII exposta em toda cópia do relatório |
| **Com tokenização FPE** | `871.234.156-99` (mesmo formato, titular diferente) | Estrutura do relatório preservada; ferramentas downstream seguem funcionando |

**Criptografia format-preserving (FPE)** mantém comprimento e classe de caracteres para validadores, regex e dashboards continuarem realistas sem expor o titular.

---

## Audiências e benefícios

| Audiência | Benefício | Gancho regulatório típico |
| --------- | --------- | ------------------------- |
| **DPO / privacidade** | Evidências para regulador sem titulares em anexos | LGPD art. 46; GDPR art. 25 |
| **CISO / SOC** | Alimentar SIEM/tickets com forma do finding, não PII em logs | SOC 2 CC6.1 |
| **Auditor externo** | Revisar escopo e densidade com amostras realistas | ISO 27001 / SOC 2 |
| **Engenharia** | Depurar local e classe do detector sem ver titulares | Minimização need-to-know interna |

---

## Como habilitar (produto)

1. Rode discovery e produza findings conforme [USAGE.pt_BR.md](../USAGE.pt_BR.md).
1. Configure export **Enterprise** para invocar plugin de **tokenização** em `sample` (e outros campos configurados) antes de gravar ou compartilhar.
1. Mantenha tokens **reversíveis** só onde política e custódia de chaves permitirem; use tokens **irreversíveis** para pacotes só de auditoria quando exigido.

Rastreio de implementação: GitHub **#601** (plano `docs/plans/PLAN_REMEDIATION_INTERFACE.pt_BR.md`).

---

## Documentos relacionados

- [USE_CASES_HUB.pt_BR.md](USE_CASES_HUB.pt_BR.md)
- [USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md)
- [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md)
