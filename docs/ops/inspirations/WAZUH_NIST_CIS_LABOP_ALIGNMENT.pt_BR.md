# Documentação Wazuh, NIST CSF, CIS Controls — aprendizado no lab-op e alinhamento ao Data Boar

**English:** [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md)

**Nota de fonte:** só documentação **primária** estável (sem reposts em rede social nem pacotes de planilhas como política). Use ao planejar monitoração **LAB-OP** / homelab e quando **compradores** perguntarem como o Data Boar se encaixa em linguagem de frameworks.

---

## Documentação oficial Wazuh (orientação)

**Pontos de entrada:**

- [Getting started](https://documentation.wazuh.com/current/getting-started/index.html)
- [Components](https://documentation.wazuh.com/current/getting-started/components/index.html) — **Wazuh indexer**, **Wazuh server**, **Wazuh dashboard**, **Wazuh agent**
- [Installation guide](https://documentation.wazuh.com/current/installation-guide/index.html)
- [Deployment options](https://documentation.wazuh.com/current/deployment-options/index.html) — Docker, Kubernetes, Ansible, instalação offline, etc.

**Capítulos de casos de uso que cruzam preocupações do Data Boar / lab** (plataforma estilo SIEM — **não** é o nosso produto):

- [Monitoramento de integridade de arquivos](https://documentation.wazuh.com/current/getting-started/use-cases/file-integrity.html)
- [Análise de logs](https://documentation.wazuh.com/current/getting-started/use-cases/log-analysis.html)
- [Detecção de vulnerabilidades](https://documentation.wazuh.com/current/getting-started/use-cases/vulnerability-detection.html)
- [Resposta a incidentes](https://documentation.wazuh.com/current/getting-started/use-cases/incident-response.html)
- [Conformidade regulatória](https://documentation.wazuh.com/current/getting-started/use-cases/regulatory-compliance.html)
- [Segurança de contêineres](https://documentation.wazuh.com/current/getting-started/use-cases/container-security.html)
- [Gestão de postura](https://documentation.wazuh.com/current/getting-started/use-cases/posture-management.html)

**Hábito no lab-op:** seguir a **versão** que você instalar, preferir **TLS** e **menor privilégio** conforme os guias da Wazuh; manter inventário específico de hosts em **`docs/private/homelab/`** (gitignored — ver **`AGENTS.md`**). O script **`scripts/lab-op-sync-and-collect.ps1`** é o caminho em lote no repositório quando existir manifest — **não** substitui ler a documentação de instalação da Wazuh.

---

## NIST Cybersecurity Framework (CSF) 2.0 — como usar o vocabulário

**Referência canônica:** [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) (CSF 2.0 traz **Govern** explícito junto de Identify, Protect, Detect, Respond, Recover).

| Função CSF | Neste repositório / prática do operador | Escopo do produto (Data Boar) |
| ---------- | ---------------------------------------- | ------------------------------ |
| **Govern** | ADRs, disciplina de revisão, backlog de branch protection ([WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md)) | Alegações honestas em [SECURITY.md](../../SECURITY.md) / [COMPLIANCE_AND_LEGAL.md](../../COMPLIANCE_AND_LEGAL.md) |
| **Identify** | Lockfile, Dependabot, roadmap SBOM ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) | Evidência para descoberta de **dados** e conteúdo sensível — não inventário enterprise completo de ativos |
| **Protect** | Actions com SHA fixo ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-chain-pins.md)), permissões mínimas em workflow | Orientação de deploy seguro; endurecimento do ambiente continua com o cliente |
| **Detect** | CI + Semgrep/CodeQL, Slack opcional em falha | Saída do scanner; **não** é SOC 24×7 |
| **Respond** | Checklist de incidente no ecossistema ([SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md](SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md) — bloco adiado) | Runbooks do cliente são do cliente |
| **Recover** | **Testar** backup/restauração do estado crítico do lab-op (processo adiado; mesmo bloco) | Idem — resiliência operacional depende do deploy |

Use a linguagem do CSF em conversas **comerciais/técnicas** para **posicionar** controles que de fato existem; evite implicar **certificação** ou cobertura total do CSF sem programa explícito de compliance.

---

## CIS Controls — lente de priorização

**Referência canônica:** [CIS Controls](https://www.cisecurity.org/controls) (salvaguardas priorizadas; úteis para times **enxutos** não se dispersarem).

**Alinhamento aproximado (exemplos, não mapeamento para certificação):**

- **Inventário e controle de ativos / software** → inventário de dependências e imagem ([ADR 0003](../../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md), `uv.lock`, Dependabot).
- **Configuração segura** → hosts endurecidos no lab-op; caso de uso Wazuh **configuration assessment** como **verificação**, não feature do Data Boar.
- **Gestão de logs de auditoria** → Wazuh no lab-op para revisão centralizada; logging da aplicação Data Boar no deploy é do operador.
- **Defesas contra malware** → endpoint nos workstations e servidores; fora do núcleo do repositório salvo doc explícita.

---

## Relacionado no repositório

- [LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md](LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md) — Grafana / Loki / Graylog / OpenSearch / traces / alternativas estilo Dynatrace (favoritos lab-op)
- [SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md](SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md) — confiança, cadeia de suprimentos, postura adiada
- [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md) — cultura de operação de banco vs **slots de evidência** em planilhas GRC (exportações Data Boar)
- [WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) — linha de backlog deste eixo
- [HOMELAB_VALIDATION.pt_BR.md](../HOMELAB_VALIDATION.pt_BR.md) — fumaça em segundo ambiente (quando aplicável)
