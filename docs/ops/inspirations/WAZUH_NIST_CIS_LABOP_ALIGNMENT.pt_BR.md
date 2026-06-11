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

### SP 800-63-4 (Diretrizes de Identidade Digital Rev 4) — dados de identidade são PII por definição

**Referência canônica:** [NIST SP 800-63-4](https://pages.nist.gov/800-63-4/) (final esperado 2025–2026; rascunho público disponível).

O SP 800-63-4 define os **dados de identidade** coletados durante a validação de identidade digital como PII. Isso alinha diretamente ao escopo de detecção do Data Boar:

| Conceito SP 800-63-4 | Relevância para o Data Boar |
| --------------------- | --------------------------- |
| Dados de identidade (nome, data de nascimento, endereço, ID nacional) coletados na validação | O Data Boar detecta exatamente essas classes de dados em bancos, sistemas de arquivos e APIs — argumento direto para DPO/CISO em ambientes de validação de identidade |
| Vinculação de atributos de identidade a credenciais | PII próxima a credenciais em session stores, tabelas de BD e compartilhamentos de arquivo está no escopo de varredura do Data Boar |
| Alternativas de identidade que preservam privacidade | A detecção de retenção ou duplicação desnecessária de PII apoia a avaliação desses controles |

**Argumento para DPO/CISO:** "O Data Boar detecta exatamente o que o SP 800-63-4 define como PII de identidade — ele localiza onde esses registros estão antes de você construir um programa de validação ou gestão de credenciais."

### Overlays de Controles SP 800-53r5 para Sistemas de IA — controles de privacidade para IA

**Referência canônica:** Overlay do NIST SP 800-53 Rev 5 para IA (veja a documentação do NIST AI RMF em <https://airc.nist.gov>).

O Overlay de Controles para Sistemas de IA estende os controles de privacidade e segurança do NIST SP 800-53r5 para sistemas de IA. Relevante para o Data Boar:

- **Família PT (Privacy)** — A detecção de sensibilidade do Data Boar suporta evidências para PT-1 (autoridade), PT-2 (propósito), PT-3 (propósitos do processamento de PII).
- **Função Measure do NIST AI RMF** — Executar uma varredura estruturada antes ou durante o treinamento de modelos de IA suporta a função Measure, identificando PII que não deveria estar nos dados de treinamento (postura de governança de dados).

**Argumento para o produto:** "Data Boar como controle preventivo para PII em dados de treinamento — alinha com a função Measure do NIST AI RMF e os controles de privacidade do overlay SP 800-53r5 para IA."

### SP 800-228A (Deploy Seguro de APIs REST — IPD) — item a observar

**Referência canônica:** NIST SP 800-228A Rascunho Público Inicial — comentários públicos encerrados em 2026-07-02; final esperado para o final de 2026.
Ver: <https://csrc.nist.gov/pubs/sp/800/228/a/ipd>

O SP 800-228A se tornará a referência NIST para hardening de APIs REST que tratam dados sensíveis. Relevante após a publicação final:

- A API REST do Data Boar ([docs/TECH_GUIDE.md](../../TECH_GUIDE.md)) lida com resultados de varredura e configuração — autenticação, TLS, rate limiting e filtragem de saída se alinham com a orientação esperada do SP 800-228A.
- O ADR-0065 registra a decisão de adiar o alinhamento formal até a publicação do padrão ([ADR-0065](../../adr/ADR-0065-nist-sp800228a-api-security-reference.md)).

**Ação:** Revisar o texto final do SP 800-228A em relação às rotas em `api/` quando publicado; considerar um novo ADR para alinhamento de hardening de API nesse momento.

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
