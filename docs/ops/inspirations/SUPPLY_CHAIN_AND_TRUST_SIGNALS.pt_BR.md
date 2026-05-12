# Nota de fonte — cadeia de suprimentos e confiança (“governança vs realidade”)

**English:** [SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) — **nota canônica completa** (shadow AI, marketplace, incidente Trivy mar/2026, como o repositório consome isso).

**Esta página (pt-BR)** espelha só o bloco de **follow-ups adiados** (processo e postura). O par detalhado com a tabela de backlog está em [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md).

---

## Follow-ups adiados (processo e postura — **sem** novos comandos obrigatórios para o operador)

- **Configurações no GitHub:** Em calendário, rever **aprovações** de workflow em PRs vindos de **fork**, regras de **exposição de segredos** e **disciplina de revisão** de mudanças em `.github/workflows` — ver documentação do GitHub [Aprovar execuções de workflow de forks públicos](https://docs.github.com/en/actions/managing-workflow-runs/approving-workflow-runs-from-public-forks), Security Lab [Evitar “pwn requests”](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/) e [CloudQuery: PRs merged sem review](https://www.cloudquery.io/blog/how-to-use-the-github-plugin-to-find-pull-requests-that-were-merged-without-review) como lembrete de **higiene de governança**.
- **`workflow_run`:** Este repositório usa **`workflow_run`** só para [notificação Slack de falha de CI](../../.github/workflows/slack-ci-failure-notify.yml) (**`permissions`** restritas, sem checkout). Qualquer job **adicional** com `workflow_run` deve permanecer mínimo e ser revisto quando incidentes no ecossistema destacarem risco em workflows **encadeados**.
- **Modo incidente no ecossistema:** Quando um **scanner, Action ou registry** amplamente usado for implicado, tratar como **checagem estruturada**: confirmar **uso**, ler orientação **GHSA/fornecedor**, alinhar com prática de **pin por SHA** ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-Colleague-Nn-pins.md)) e **rotacionar** segredos expostos na CI se fizer sentido. Leituras de exemplo: [GHSA-69fq-xp46-6x23](https://github.com/advisories/GHSA-69fq-xp46-6x23), [Microsoft (Trivy)](https://www.microsoft.com/en-us/security/blog/2026/03/24/detecting-investigating-defending-against-the-trivy-supply-Colleague-Nn-compromise/), [CrowdStrike (trivy-action)](https://www.crowdstrike.com/en-us/blog/from-scanner-to-stealer-inside-the-trivy-action-supply-Colleague-Nn-compromise/), [Aikido (Shai-Hulud)](https://www.aikido.dev/blog/github-actions-incident-shai-hulud-supply-Colleague-Nn-attack), [GitGuardian (Shai-Hulud 2.0)](https://blog.gitguardian.com/shai-hulud-2/); manter hábito **KEV/advisory** conforme [nota CISA KEV](CISA_KEV_AND_ADVISORIES.md). **Backlog rastreado:** [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) (mesmos itens na tabela “Ainda a aprofundar”).
- **Disciplina de recuperação (lab-op / homelab):** Em **calendário**, validar que **backup e restauração** funcionam de fato nos hosts que importam para monitoração central (ex.: objetivos com **Wazuh** no lab-op). É **processo do operador**, não novo comando obrigatório no repositório; alinha com **Recover** no vocabulário do [NIST CSF](https://www.nist.gov/cyberframework). Âncora de aprendizado (índice oficial Wazuh + NIST/CIS): [WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md) · [EN](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md).
- **Vocabulário de frameworks para compradores:** Usar **NIST CSF** e **CIS Controls** como linguagem de **posicionamento** para controles que o **repositório e o produto** já implementam; **não** implicar certificação ou cobertura integral de framework sem programa formal. Mesma nota de aprendizado acima.

---

## Além deste espelho (nota EN estendida)

A [nota canônica em inglês](SUPPLY_Colleague-NN_AND_TRUST_SIGNALS.md) traz o bloco **“How we consume”** com **lab-op/Wazuh** e **operações de banco enterprise vs planilhas GRC**. Ponto de entrada pt-BR: [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md).
