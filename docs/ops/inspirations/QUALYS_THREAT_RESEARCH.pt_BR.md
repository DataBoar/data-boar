# Nota de fonte — Qualys Threat Research (blog / TRU)

**English:** [QUALYS_THREAT_RESEARCH.md](QUALYS_THREAT_RESEARCH.md)

Links principais:

- [Blog Qualys — Vulnerabilities & Threat Research](https://blog.qualys.com/category/vulnerabilities-threat-research/)
- Exemplo (divulgação coordenada, kernel / LSM): [CrackArmor: falhas críticas no AppArmor permitem escalação local para root](https://blog.qualys.com/vulnerabilities-threat-research/2026/03/12/crackarmor-critical-apparmor-flaws-enable-local-privilege-escalation-to-root) (março de 2026) — classe *confused deputy* no AppArmor, urgência de patch, limites de confiança relevantes para containers; o post comenta também o ritmo de atribuição de CVE upstream.

Por que a fonte ajuda:

- **Pesquisa de ameaças** em formato longo, com resumo executivo, impacto e detalhe técnico — referência de **enquadramento** de risco de kernel/infra para operadores.
- Reforça que camadas de endurecimento **padrão** (ex.: perfis LSM) ainda exigem **cadência de patch** do fornecedor e monitoramento — disciplina análoga para scanners, containers e hosts de homelab.

Como consumimos:

- Como **inspiração** para priorizar patch de Linux/kernel onde o Data Boar ou dependências rodam (runners de CI, homelab, orientações em documentação).
- Cruzar com boletins da sua distribuição; não tratar blog de fornecedor como única autoridade para o threat model do produto.

Cuidados:

- Conteúdo **alinhado ao fornecedor** (menções a produtos Qualys); extrair lições **técnicas e de processo**, não texto comercial.
- Detalhes de exploração podem ser retidos na divulgação; siga os avisos de segurança da distribuição para versões acionáveis.
