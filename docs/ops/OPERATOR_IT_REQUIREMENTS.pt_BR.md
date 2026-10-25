# Guia do operador: O que pedir à TI (permissões mínimas)

**English:** [OPERATOR_IT_REQUIREMENTS.md](OPERATOR_IT_REQUIREMENTS.md)

**Veja também:** [USAGE.pt_BR.md](../USAGE.pt_BR.md) (configuração), [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) (problemas de autenticação).

Este documento auxilia **prestadores de serviço e operadores** que implantam ou operam o Data Boar e precisam **solicitar acesso à equipe de TI**. Ele descreve as **permissões mínimas** necessárias para cada tipo de fonte (bancos de dados, compartilhamentos, APIs etc.), **o que não precisamos** e uma **breve justificativa**, para que você possa solicitar acesso com o mínimo de privilégios e alinhar-se a políticas de zero-trust ou restritivas.

---

## Por que permissões mínimas importam

- **Zero-trust e política:** Muitas organizações aplicam zero-trust ou IAM restrito. Pedir direitos amplos (ex.: admin, acesso total ao banco ou escrita em shares) pode levar à rejeição ou tornar a ferramenta **incompatível** com essas políticas.
- **Confiança e auditoria:** TI e segurança tendem a aprovar pedidos **somente leitura e escopados**. Pedir demais pode reduzir a confiança e gerar revisão mais pesada.
- **Defesa do acesso mínimo:** O Data Boar apenas **descobre estrutura** (schemas, tabelas, colunas, nomes de arquivos) e **lê uma amostra pequena** de conteúdo para detecção de sensibilidade. Ele **não grava, não exclui e não altera** dados nem metadados. Não precisa de direitos de DBA, propriedade de share ou funções de admin—apenas o necessário para **listar** e **ler** dentro do escopo acordado.

Use as seções abaixo como **checklist** ao preparar seu pedido à TI. Onde a organização usar nomes diferentes (ex.: “Leitor” vs “Função somente leitura”), mapeie nossas necessidades para a função mais próxima e deixe claro que **não é necessária escrita nem admin**.

---

## Tabela resumo: acesso mínimo por tipo de fonte

| Tipo de fonte           | O que pedir à TI (mínimo)                                                                                   | O que **não** precisamos                      |
| -----------------       | ------------------------------------------------------------------------------------------                  | --------------------------------------------- |
| **Sistema de arquivos** | Leitura + listagem no(s) caminho(s) que varremos (ex.: conta de serviço somente leitura em `/data/audit`)   | Gravar, excluir, executar, admin              |
| **Bancos SQL**          | Função somente leitura: SELECT nas tabelas alvo; metadados (listar schemas/tabelas/colunas)                 | INSERT/UPDATE/DELETE, DDL, backup, admin      |
| **MongoDB**             | Leitura no banco: listar coleções, find (ler documentos)                                                    | Gravar, drop, admin                           |
| **Redis**               | Comandos: SCAN (e conexão). Nenhum comando de escrita                                                       | SET, DEL, FLUSH, CONFIG, admin                |
| **SMB / CIFS**          | Leitura + listagem no share/caminho (ex.: permissão Ler share, listar pasta, ler arquivos)                  | Gravar, excluir, alterar permissões           |
| **WebDAV**              | Leitura + listagem (PROPFIND, GET) no caminho base                                                          | PUT, DELETE, PROPPATCH, escrita               |
| **SharePoint**          | Ler pasta e arquivos (ex.: “Exibir” ou “Ler” no site/pasta); baixar conteúdo do arquivo                     | Editar, excluir, gerenciar site               |
| **NFS**                 | Leitura + listagem no ponto de montagem (igual a filesystem; montagem geralmente feita pela TI)             | Gravar, excluir, bypass de root squash        |
| **REST / API**          | Acesso GET aos endpoints que varremos; token com somente leitura ou escopo mínimo                           | POST/PUT/DELETE, escopo admin                 |
| **Power BI**            | Leitura na API do Power BI (ex.: “Ler todos os datasets” ou leitura do workspace); escopo OAuth do conector | Publicar, editar relatórios, admin            |
| **Dataverse**           | Leitura de tabelas/entidades (ex.: leitura do ambiente ou da tabela); escopo OAuth da API Dataverse         | Criar/atualizar/excluir, admin                |

---

## 1. Sistema de arquivos

- **Pedir:** Leitura e listagem no(s) **caminho(s) exatos** configurados no alvo filesystem (ex.: `/data/audit`, `D:\Compliance\Scan`). A conta que executa o scanner (ou a conta de serviço configurada) deve ter **leitura** e **listar diretório** nesse caminho e, se a varredura for recursiva, nos subdiretórios.
- **Não precisamos:** Gravar, excluir, executar ou ser proprietário. Não precisamos de acesso ao restante da máquina além do caminho configurado.
- **Por que basta:** Só abrimos arquivos para **leitura**, lemos uma **amostra** do conteúdo (ver `file_scan.sample_limit`) e rodamos a detecção de sensibilidade. Nenhum arquivo é alterado ou apagado. Limitar o caminho na config mantém o escopo mínimo; você pode pedir à TI que restrinja a conta a esse caminho.

---

## 2. Bancos de dados SQL (PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, SQLite)

- **Pedir:** Um usuário/função **somente leitura** que possa:
- **Listar** schemas (quando aplicável), tabelas e colunas (acesso a metadados/catálogo).
- **SELECT** nas tabelas (ou schemas) que você pretende varrer.
- Sem INSERT, UPDATE, DELETE ou DDL (CREATE/ALTER/DROP). Sem backup/restore, sem admin.
- **Exemplos concretos:**
- **PostgreSQL:** Função com `CONNECT` no banco e `SELECT` nas tabelas (ou schema) a varrer; ou `pg_read_all_data` se for estritamente necessário (ainda somente leitura). Evitar `pg_read_all_settings` e superusuário.
- **MySQL / MariaDB:** Usuário com `SELECT` e metadados (ex.: `SHOW` ou acesso a `information_schema` dos bancos que varremos). Sem `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`.
- **SQL Server:** Usuário com `db_datareader` (ou `SELECT` em tabelas específicas) e permissão para ler metadados (ex.: `sys.tables`, `sys.columns`). Sem `db_datawriter`, sem `db_owner`.
- **Oracle:** Usuário com `SELECT` nas tabelas/schemas alvo e `SELECT_CATALOG_ROLE` (ou equivalente) só se necessário para listar objetos. Sem DBA, sem escrita.
- **Não precisamos:** Nenhum privilégio de escrita, DDL, backup, replicação ou admin do servidor.
- **Por que basta:** Usamos as APIs de metadados do motor para descobrir schemas/tabelas/colunas e executamos **SELECT** com **LIMIT** pequeno por coluna para amostrar valores. Achados são metadados (tabela/coluna, tipo de padrão); não armazenamos conteúdo completo das linhas. Somente leitura é suficiente e alinhada a zero-trust.

---

## 3. MongoDB

- **Pedir:** Usuário com **leitura** no(s) banco(s) que varremos: `listCollections`, `find` (usamos limite pequeno por coleção). Sem `insert`, `update`, `delete`, `drop` ou `createCollection`.
- **Não precisamos:** Gravar, drop ou funções admin (ex.: `root`, `dbAdmin`).
- **Por que basta:** Listamos coleções e executamos `find().limit(n)` para amostrar documentos. Só lemos nomes de campos e valores amostrais para detecção; não persistimos documentos inteiros.

---

## 4. Redis

- **Pedir:** Conexão e uso **somente leitura**. Usamos **SCAN** para iterar nomes de chaves e rodar detecção nos nomes (e opcionalmente tipos). Se houver ACLs no Redis, uma função que permita **SCAN** e opcionalmente **TYPE**; **não** SET, DEL, FLUSH, CONFIG ou outros comandos de escrita/admin.
- **Não precisamos:** Nenhum comando de escrita ou administrativo.
- **Por que basta:** Só precisamos ler nomes de chaves (e opcionalmente tipos) para detectar padrões sensíveis; não precisamos ler nem armazenar valores para a lógica que entregamos. Somente leitura mantém o impacto mínimo.

---

## 5. Compartilhamentos SMB / CIFS

- **Pedir:** **Leitura** e **listagem** no share (ou no caminho específico do share) que varremos. Em geral: permissão “Ler” no share e “Listar conteúdo da pasta” + “Ler” na(s) pasta(s). A conta (ex.: usuário de domínio ou conta de serviço) deve poder abrir arquivos para leitura e listar conteúdo do diretório.
- **Não precisamos:** Gravar, excluir, alterar permissões ou “Controle total”.
- **Por que basta:** Listamos arquivos no caminho, abrimos cada arquivo para **leitura**, extraímos uma amostra de texto (igual ao filesystem) e rodamos a detecção. Nenhum arquivo é gravado ou apagado. Solicite apenas o share/caminho necessário para a TI poder escopar a permissão.

---

## 6. WebDAV

- **Pedir:** **Leitura** e **listagem** no caminho base: PROPFIND (listar) e GET (ler conteúdo do arquivo). Sem PUT, DELETE, PROPPATCH ou outros métodos de escrita.
- **Não precisamos:** Gravar, excluir ou lock.
- **Por que basta:** Listamos recursos, baixamos conteúdo com GET e aplicamos a mesma lógica de varredura de arquivos do filesystem. Somente leitura é suficiente.

---

## 7. SharePoint

- **Pedir:** **Exibir** ou **Ler** no site ou pasta que varremos: listar arquivos na pasta e baixar conteúdo (ex.: “Obter conteúdo do arquivo” / `$value`). Muitas vezes “Visitantes do site” ou “Ler” é suficiente para a biblioteca/pasta alvo.
- **Não precisamos:** Editar, excluir, gerenciar site ou controle total.
- **Por que basta:** Usamos a API REST para listar arquivos e GET do conteúdo e rodamos a detecção de sensibilidade. Sem upload nem modificação.

---

## 8. NFS

- **Pedir:** O caminho que varremos costuma ser um **ponto de montagem local** que a TI (ou o host) já montou. A conta que executa o scanner precisa de **leitura** e **listagem** nesse mount (igual ao filesystem). Se a TI controla os exports NFS, solicite export somente leitura para o host de auditoria, se possível.
- **Não precisamos:** Gravar, excluir ou root/sudo para bypass de squash.
- **Por que basta:** Usamos a mesma lógica do conector de filesystem no caminho montado; leitura e listagem são suficientes.

---

## 9. Alvos REST / API

- **Pedir:** Acesso **GET** às URL(s) que varremos (base_url + paths ou discover_url). Se a API usar tokens, solicite um token com **somente leitura** ou o **escopo mínimo** que permita GET nesses endpoints. Sem POST/PUT/DELETE a menos que a API seja só para descoberta e não enviemos dados no body.
- **Não precisamos:** Escopo de escrita, escopo admin ou escopo além dos endpoints que chamamos.
- **Por que basta:** Só fazemos requisições GET, parseamos a resposta (ex.: JSON) e rodamos detecção em chaves e valores amostrais. Nenhum dado é enviado à API exceto o necessário para autenticação (ex.: pedido de token OAuth).

---

## 10. Power BI

- **Pedir:** Acesso **leitura** na API do Power BI: ex. “Ler todos os datasets” ou leitura nos workspaces/datasets que varremos. Nosso conector usa o escopo `<https://analysis.windows.net/powerbi/api/.defaul>t` (Azure AD). A TI deve conceder ao registro do app a permissão mínima do Power BI que permita listar workspaces/datasets e executar consultas somente leitura (ex.: Execute Queries para amostragem).
- **Não precisamos:** Publicar, editar relatórios/datasets ou admin.
- **Por que basta:** Listamos datasets e tabelas, executamos pequenas consultas DAX para amostrar dados e rodamos a detecção. Acesso somente leitura à API é suficiente.

---

## 11. Dataverse / Power Apps

- **Pedir:** Acesso **leitura** ao ambiente e às tabelas (entidades) que varremos: ex. leitura do ambiente ou “Ler” nas tabelas alvo. O escopo OAuth costuma ser o recurso Dataverse (ex.: `https://<org>.crm.dynamics.com/.default`). O registro do app deve ter a função mínima que permita ler metadados e linhas das tabelas.
- **Não precisamos:** Criar, atualizar, excluir ou system admin.
- **Por que basta:** Listamos tabelas e amostramos linhas via Web API para detecção. Sem escritas.

---

## Checklist para seu pedido à TI

Ao enviar o pedido, você pode incluir:

1. **Escopo:** Caminho(s), banco(s), share(s) ou URL(s) base de API que acessaremos.
1. **Identidade:** A conta ou app (ex.: conta de serviço, app Azure AD) que será usada.
1. **Acesso necessário:** “Somente leitura e listagem” (ou a linha da tabela resumo acima para essa fonte).
1. **O que não precisamos:** “Sem gravar, excluir ou admin.”
1. **Justificativa:** “Varredura de conformidade / descoberta de dados: descobrir e amostrar conteúdo para detecção de sensibilidade; sem modificação de dados nem exportação de conteúdo completo; achados são só metadados (local e tipo de padrão).”

Se a TI pedir justificativa por escrito, você pode indicar este documento e o fato de que a aplicação foi desenhada para operar com **mínimo de privilégios**, de modo a permanecer compatível com zero-trust e políticas IAM restritivas.

---

## Última atualização

Documento criado. Atualizar quando novos conectores ou requisitos de permissão forem adicionados.
