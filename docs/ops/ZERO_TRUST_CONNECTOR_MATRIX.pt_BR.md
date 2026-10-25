# Matriz zero trust por conector (baseline de menor privilégio)

**English:** [ZERO_TRUST_CONNECTOR_MATRIX.md](ZERO_TRUST_CONNECTOR_MATRIX.md)

Use esta matriz para definir permissões mínimas e guardrails por classe de conector.

| Classe de conector | Postura de credencial | Limite de escopo | Minimização de dados | Expectativa de auditoria |
| --- | --- | --- | --- | --- |
| Filesystem | Conta de serviço somente leitura | Apenas caminhos aprovados | Limites de amostragem configurados | Log de sessão + manifesto de alvo |
| Banco SQL | Usuário read-only com grants mínimos | Allowlist de schema/tabela explícita | Limites de coluna e linha por política | Evidência de escopo + metadados da execução |
| NoSQL | Papel read-only em coleções selecionadas | Allowlist de coleções | Cap de amostra e máscara de chaves | Escopo de conexão + lista de coleções |
| API/REST | Token com escopos somente leitura | Allowlist de endpoints | Amostragem e sanitização de payload | Escopo de request + classificação de resposta |
| SharePoint/Dataverse | App principal dedicado com leitura mínima | Allowlist de site/lista/tabela | Extrair apenas campos necessários | Escopo de acesso + logs por tenant |
| SMB/NFS | Montagem/usuário read-only | Allowlist de compartilhamento/caminho | Políticas por tipo/tamanho de arquivo | Rastro de montagem/sessão |
| Object storage em nuvem | Papel/política IAM somente leitura | Allowlist de bucket/prefixo | Threshold de amostragem de objetos | Rastro de inventário + ID da execução |

## Controles obrigatórios para qualquer conector

- Credenciais dedicadas (sem superusuário compartilhado).
- Allowlist explícita de alvos por execução.
- Sem material secreto em docs trackeados.
- Metadados de execução armazenados para rastreabilidade.
- Revisão de escopo e credenciais ao menos trimestral.
