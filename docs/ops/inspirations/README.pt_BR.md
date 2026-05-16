# Baselines de inspiração (operador)

**English:** [README.md](README.md)

**Comece aqui (hub de navegação):** [INSPIRATIONS_HUB.pt_BR.md](INSPIRATIONS_HUB.pt_BR.md) — descrições curtas + links para cada nota detalhada nesta pasta e pontes relacionadas em `docs/ops/`.

Esta pasta tem **dois** eixos. Em ambos: material externo é **insumo**, não política automática; decisões de produto passam pelo nosso contexto, testes e segurança de rollout.

## Security / GRC

Objetivo: fontes que informam **hardening** e escolhas de roadmap com viés compliance/GRC.

- [Security Now / GRC](SECURITY_NOW.md)
- [Projetos e guias OWASP](OWASP.md)
- [CISA KEV + advisories](CISA_KEV_AND_ADVISORIES.md)
- [Cadeia de suprimentos e sinais de confiança — pt-BR (follow-ups)](SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md) ([nota completa em EN](SUPPLY_CHAIN_AND_TRUST_SIGNALS.md))
- [Wazuh + NIST CSF / CIS — alinhamento lab-op](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md) ([EN](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md))
- [Observabilidade lab-op — links oficiais (nota mental)](LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md) ([EN](LAB_OP_OBSERVABILITY_LEARNING_LINKS.md))
- [Operação de banco enterprise + slots de evidência GRC](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md) ([EN](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md))
- [Qualys Threat Research (blog / TRU)](QUALYS_THREAT_RESEARCH.pt_BR.md)

## Craft de engenharia (pessoas, produtos, narrativa)

Objetivo: **desenvolvedores, times ou canais** cujo ofício, consciência de segurança, produtos entregues, documentação ou narrativa pública (“como pensamos o problema”) informam **como construímos e explicamos** o Data Boar.

- [Inspirações de craft de engenharia](ENGINEERING_CRAFT_INSPIRATIONS.pt_BR.md) — tabela de links + notas curtas; preencher quando o mantenedor acrescentar referências.
- [Craft de engenharia — nota de fonte](ENGINEERING_CRAFT_ANALYSIS.pt_BR.md) — índice da tabela + ponte para a análise profunda.
- [Craft de engenharia — análise profunda](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.pt_BR.md) — temas, imitar/evitar, checklist (paralelo a [SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md](../SECURITY_INSPIRATION_GRC_SECURITY_NOW.pt_BR.md)).

Como usar esta pasta:

1. Ler a nota do eixo certo (security ou craft).
1. Extrair uma ação ou hábito candidato.
1. Decidir: adotar agora, backlog ou rejeitar.
1. Ligar a decisão a um artefato (plano, ADR, doc, teste, workflow).

Mantenha cada baseline enxuto. Acrescente linhas só quando a fonte for **recorrente**.
