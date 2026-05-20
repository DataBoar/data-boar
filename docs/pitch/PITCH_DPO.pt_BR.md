# Pitch DPO — liderança de privacidade e compliance

**English:** [PITCH_DPO.md](PITCH_DPO.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** DPOs, jurídico de privacidade, líderes de compliance (LGPD, GDPR, PIPEDA, programas multinacionais).

---

## Papel da ferramenta no seu programa

O Data Boar **apoia** a governança de privacidade — não decide licitude, prazos de retenção nem desfecho de notificação de incidente. Acelera **inventário e evidência** para seu escritório focar em interpretação, aceite de risco e narrativa para reguladores.

Resumo jurídico não técnico: [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md).

## Alinhamento a frameworks (configuração, não mágica)

Tags de norma embutidas e amostras cobrem LGPD, GDPR, CCPA, HIPAA, GLBA e perfis extensíveis (UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, 152-FZ e outros) via [compliance-samples/](../compliance-samples/).

| Necessidade | Onde olhar |
| ----------- | ---------- |
| Mesclar perfil YAML regional | [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| Texto de recomendação por norma | `report.recommendation_overrides` em [USAGE.pt_BR.md](../USAGE.pt_BR.md) |
| Sinais de tensão multinacional (heurística) | [JURISDICTION_COLLISION_HANDLING.pt_BR.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md) |

## DSAR e direitos do titular

O produto ajuda a **localizar** categorias de dados pessoais e **documentar** o escopo da varredura — **não** automatiza respostas legais, verificação de identidade nem prazos legais.

Padrão prático:

1. Defina alvos ligados aos sistemas de interesse do titular.
2. Execute descoberta delimitada com logs de sessão auditáveis.
3. Exporte achados e mapas de calor para revisão jurídica — não exfiltração em massa por padrão.

Storyboard: [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md).

## Menores e categorias sensíveis

Quando habilitado, o motor sinaliza **possíveis** colunas relacionadas a crianças e cruza com achados de identificador ou saúde — linguagem de inventário para revisão do **Art. 14 da LGPD** e **Art. 8 do GDPR**, sem automação de consentimento parental.

Guia do operador: [MINOR_DETECTION.pt_BR.md](../MINOR_DETECTION.pt_BR.md).

## Evidência defensável em workshop

- Recomendações com tag de norma para triagem (não parecer jurídico).
- Contexto de **tendência** entre sessões.
- Markdown executivo opcional e `scan_manifest_*.yaml` junto ao XLSX — ver [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

## O que dizer ao CISO e ao conselho

- **Responsabilidade compartilhada:** seu escritório detém base legal e interpretação; a plataforma detém leituras técnicas configuradas e saídas estruturadas.
- **Sem exagero:** passar numa varredura não prova conformidade; produz **sinais técnicos priorizados**.

## Próximo passo

- **Resumo executivo:** [PITCH_STAKEHOLDER.pt_BR.md](PITCH_STAKEHOLDER.pt_BR.md)
- **Controles de segurança:** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md)
- **Achados tokenizados:** [use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md)
