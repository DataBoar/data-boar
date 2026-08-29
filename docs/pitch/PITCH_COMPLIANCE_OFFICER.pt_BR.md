# Pitch CCO / jurídico (General Counsel) — responsabilidade e evidência multi-regime

**English:** [PITCH_COMPLIANCE_OFFICER.md](PITCH_COMPLIANCE_OFFICER.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** Chief Compliance Officer, General Counsel, jurídico corporativo, interlocução de auditoria — **não** substitui o deck do DPO.

---

## Distinto do DPO

O DPO (ou equivalente) é dono da **privacidade operacional** (base legal, processo de DSAR, menores como faixa de detecção). O jurídico e o CCO são donos da **responsabilidade da empresa**, da **defesa em auditoria**, de **programas multi-regime** e da diligência **transacional**. Use [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md) para linguagem de inventário; use **esta** página para **quem responde** e **o que você mostra a um auditor ou comprador**.

Resumo jurídico não técnico canônico: [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md). **Perfis** de framework (configuração, não mágica): [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md). **Não** trate este deck como reprodução desses documentos.

## Aviso forte

O Data Boar **não** decide licitude, **não** notifica regulador, **não** certifica ISO/SOC e **não** emite parecer sobre risco de operação. As saídas são **achados técnicos** com **norm tags** opcionais. Interpretação, sigilo profissional e petições ficam com o jurídico e os oficiais responsáveis.

## Responsabilidade e auditoria

- Artefatos **repetíveis** da sessão (XLSX, YAML de manifesto opcional, JSON de auditoria) sustentam um **rastro do que foi varrido**, não um atestado de saúde.
- Amostragem e timeouts são **configurados pelo operador** — documente-os; eles limitam o que você pode afirmar.
- A responsabilidade compartilhada segue [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md): o cliente é dono da base legal e da aceitação de risco.

## Multi-regime (linguagem de inventário, não certificação)

| Regime (exemplos) | Papel do produto |
| ----------------- | ---------------- |
| LGPD / GDPR | Recomendações e amostras com norm tag — não decisão de adequação |
| PCI DSS | Detecção orientada a padrão/PAN quando configurada — não avaliação QSA |
| SOX / controle interno | **Insumo** de evidência para narrativas de TI — não assertion da administração |
| Setorial (classe BACEN, amostras HIPAA, etc.) | Perfis YAML extensíveis — [compliance-samples/](../compliance-samples/) |

Sinais de colisão (só heurística): [JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md).

## M&A / due diligence

Descoberta limitada em sistemas **acordados** pode alimentar um workstream de diligência (quais classes de dado aparecem **neste** perímetro). **Não** substitui questionários de fornecedor, análise de declarações e garantias nem hold forense. Escopo dos alvos por escrito.

## Próximo passo

- **Privacidade operacional:** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md)
- **Evidência de segurança:** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md)
- **Finanças:** [PITCH_CFO.pt_BR.md](PITCH_CFO.pt_BR.md)
