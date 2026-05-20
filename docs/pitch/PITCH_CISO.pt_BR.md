# Pitch CISO — liderança de segurança e GRC

**English:** [PITCH_CISO.md](PITCH_CISO.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** CISOs, arquitetos de segurança, líderes de GRC que integram descoberta a programas de controle.

---

## Proposta de valor para segurança

O Data Boar reduz **sprawl desconhecido** de dados pessoais antes de virar material de incidente. Produz evidência técnica **repetível e limitada à sessão** — não substitui SIEM, DLP, IAM nem gestão de vulnerabilidades.

Postura pública de segurança: [SECURITY.pt_BR.md](../SECURITY.pt_BR.md).

## Controles que importam

| Tema | Como o produto apoia |
| ---- | -------------------- |
| **Menor privilégio** | Conectores usam credenciais que você aprova; escopo explícito — [ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md](../ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md) |
| **Integridade da evidência** | Saídas estruturadas (XLSX, YAML de manifesto opcional, JSON de auditoria) para repetibilidade |
| **Detecção determinística** | Regex + padrões + ML supervisionado em termos configurados — pilha auditável vs deriva generativa — [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| **Biometria / categorias especiais** | Narrativa de caso de uso quando habilitada — [use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md](../use-cases/USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md) |

## Postura de integração

- **Deploy:** imagens Docker, amostras compose, validação em laboratório — [DOCKER_SETUP.pt_BR.md](../DOCKER_SETUP.pt_BR.md), [deploy/DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md).
- **JSON executivo:** [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](../GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md) para dashboards estilo matriz de risco.
- **Limite open-core:** descoberta e relatório no repositório; conectores e hardening **enterprise** entram na conversa de compra — não assumidos na documentação pública.

## Operar com segurança

1. Comece em **não produção** ou contas somente leitura quando possível.
2. Limite amostragem e timeouts por classe de alvo — documente no manifesto.
3. Guarde credenciais em cofre/variáveis de sessão — não em repositórios rastreados.
4. Encadeie saídas com **ticketing** e donos de remediação — [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md).

## Perguntas para o DPO na mesma sala

- Qual **perfil de norma** é autoritativo para esta unidade?
- Quais achados exigem revisão **jurídica** antes do ticket?
- Colunas relacionadas a **menores** entram neste sprint?

## Próximo passo

- **Narrativa para conselho:** [PITCH_STAKEHOLDER.pt_BR.md](PITCH_STAKEHOLDER.pt_BR.md)
- **Narrativa de privacidade:** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md)
- **Referência técnica:** [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](../COMPLIANCE_TECHNICAL_REFERENCE.md)
