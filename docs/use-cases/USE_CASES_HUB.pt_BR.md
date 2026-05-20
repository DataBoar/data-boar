# Hub de use cases — Data Boar

**English:** [USE_CASES_HUB.md](USE_CASES_HUB.md)

Ponto de entrada para **cenários concretos de produto** (discovery, hand-off de remediação, evidência de compliance). Cada arquivo funciona sozinho; leia em sequência para a história completa **escanear → remediar → provar**.

Os **storyboards de workshop** (narrativas por setor para pré-vendas) continuam em [README.md](README.md) ([EN](README.md)).

**Decks executivos** (stakeholder, DPO, CISO): [pitch/INDEX.pt_BR.md](../pitch/INDEX.pt_BR.md) ([EN](../pitch/INDEX.md)).

---

## Discovery e remediação

| Use case | Resumo |
| -------- | ------ |
| [USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md) | Pipeline discovery-to-remediation com audit trail imutável |
| [USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](USE_CASE_TOKENIZED_FINDINGS.pt_BR.md) | Relatório de findings compartilhável com tokens no formato do dado, sem PII real |

## Categorias sensíveis

| Use case | Resumo |
| -------- | ------ |
| [USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md](USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md) | Descobrir e governar biometria (LGPD art. 11 / GDPR art. 9) |

## Storyboards por setor (workshop)

| Hub | Resumo |
| --- | ------ |
| [README.pt_BR.md](README.pt_BR.md) | Portuário, jurídico, pharma, EdTech, MSP, seguros, RPO, imobiliário, ONG e fluxos relacionados |

## Implementação (maintainers)

| Item | Resumo |
| ---- | ------ |
| `docs/plans/PLAN_REMEDIATION_INTERFACE.pt_BR.md` | Contrato de plugin Enterprise pós-scan; GitHub **#601**, **#606** |

---

## Ritual anti-drift (3 passos)

1. Crie ou atualize **`docs/use-cases/USE_CASE_<NOME>.md`** (e espelho **`.pt_BR.md`**).
1. Registre a linha **neste hub** e, quando couber, na tabela de [README.pt_BR.md](README.pt_BR.md).
1. Rode **`.\scripts\check-all.ps1`** (ou **`lint-only`** em fatia só de docs).

---

## Documentos relacionados

- [pitch/INDEX.pt_BR.md](../pitch/INDEX.pt_BR.md) — decks executivos por papel
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md)
- [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md)
- [USAGE.pt_BR.md](../USAGE.pt_BR.md)
