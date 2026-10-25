# Checklist de governança para amostras de conformidade

**English:** [OPERATOR_GOVERNANCE_CHECKLIST.md](OPERATOR_GOVERNANCE_CHECKLIST.md)

Use este checklist quando ativar ou atualizar uma amostra regional de conformidade.

## 1) Escopo e finalidade

- Defina os sistemas e domínios de dados incluídos neste ciclo de varredura.
- Registre exclusões explícitas e o motivo de cada exclusão.
- Confirme a finalidade operacional (inventário, triagem, preparação de remediação, preparação de auditoria).
- Confirme o responsável de jurídico/compliance que revisará este ciclo.

## 2) Minimização de dados e limites

- Defina limites de amostragem adequados ao ambiente.
- Confirme que a estratégia de varredura não duplica PII bruto em arquivos ad hoc.
- Valide destino de relatórios e controles de acesso.
- Confirme política de retenção e descarte de outputs e banco local.

## 3) Qualidade de perfil e norm tags

- Confirme que a amostra selecionada corresponde à jurisdição desejada.
- Revise `norm_tag` e texto de recomendação antes de varreduras em produção.
- Adicione overrides específicos da organização quando necessário.
- Mantenha nota de mudança quando a semântica do perfil for ajustada.

## 4) Credenciais e menor privilégio

- Use credenciais dedicadas e somente leitura quando possível.
- Restrinja acesso de rede apenas aos alvos aprovados.
- Evite credenciais amplas compartilhadas entre conectores não relacionados.
- Confirme que o armazenamento de segredos segue a política do operador (sem segredos em docs trackeados).

## 5) Evidência e rastreabilidade

- Guarde identificadores de sessão e timestamps de execução.
- Exporte e arquive trilhas de auditoria quando necessário.
- Registre versão do app e perfil de config usado em cada execução relevante.
- Registre quem aprovou escopo e quem revisou achados.

## 6) Decisão e escalonamento

- Defina o que dispara remediação imediata.
- Defina o que exige escalonamento para jurídico/compliance.
- Defina o que pode ser aceito temporariamente com dono e data de revisão.
- Não deixe achados de alto risco sem dono no backlog silencioso.

## 7) Cadência de revisão

- Revalidar perfis críticos ao menos trimestralmente.
- Revalidar antes de auditorias de alto impacto ou marcos com regulador.
- Revalidar quando houver mudança material de texto legal ou guia do regulador.
- Revalidar após mudanças relevantes de conectores ou perfil de detecção.

## Docs relacionados

- [README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [../COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](../COMPLIANCE_FRAMEWORKS.md))
- [../COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](../COMPLIANCE_AND_LEGAL.md))
- [../USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
