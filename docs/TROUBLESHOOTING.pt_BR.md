# Resolução de problemas (Data Boar)

**English:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Esta página traz **dicas curtas** para problemas comuns. Para **análise de causa raiz e correções passo a passo**, use os documentos de aprofundamento linkados. Operadores (incluindo consultores e clientes que licenciam o app) podem usar este guia para resolver problemas de conectividade, credenciais e implantação antes da próxima varredura.

---

## Onde ver o que deu errado

- **Relatório Excel — planilha "Scan failures":** Cada alvo com falha tem **Target**, **Reason** (ex.: `unreachable`, `auth_failed`, `timeout`), **Details** (mensagem da exceção) e **Suggested next step** (dica curta gerada pela aplicação). Comece por aqui após uma execução.
- **Dashboard:** Contagem de "Scan failures" e sessões recentes; baixe o relatório da sessão para abrir a planilha Scan failures.
- **Log de auditoria:** `audit_YYYYMMDD.log` (caminho no config ou no diretório de saída dos relatórios). Download em **Reports → sessão → Download log** ou API `GET /logs/{session_id}`. Contém entradas de conexão e falha com nome do alvo e texto do erro.
- **Respostas da API:** `POST /scan` retorna 409 se já houver varredura em andamento; 429 se os limites de taxa forem excedidos. Endpoints de sessão/relatório retornam 404 com mensagem clara quando a sessão ou o relatório não existir.

A aplicação mapeia **reasons** de falha para um **Suggested next step** no relatório (ex.: "Target did not respond. Check network connectivity…"). Se isso não bastar, use os documentos de aprofundamento abaixo.

---

## Dicas rápidas por motivo de falha

| Reason (no relatório)                       | O que verificar primeiro                                                                                                                                                                        | Documento de aprofundamento                                                                                           |
| ----------------------                      | --------------------------                                                                                                                                                                      | -----------------------------                                                                                         |
| **unreachable**                             | Rede do host/container de auditoria até o alvo: DNS, roteamento, firewall, VPN. Para Docker: veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md). | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md) · [Docker](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)     |
| **auth_failed** / **authentication_failed** | Credenciais (usuário/senha, token, OAuth client_id/secret). Evite enviar a mesma credencial no header e no body.                                                                                | [Credenciais e autenticação](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md)                                           |
| **permission_denied**                       | O scanner precisa de acesso de leitura ao recurso (share, DB, API). Execute como usuário/conta de serviço com permissão ou ajuste permissões.                                                   | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                                                                |
| **timeout**                                 | Alvo lento ou inacessível; valor de timeout muito baixo. Aumente o timeout no config (por alvo ou global); tente em horário de menor uso.                                                       | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                                                                |
| **error** (genérico)                        | Veja **Details** no relatório. Frequentemente config (host, port, URL ausentes) ou dependência opcional ausente (ex.: `.[shares]` para SMB).                                                    | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md) · [Credenciais](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) |

---

## Arquivos `.doc` legados: nome do arquivo vs texto do corpo

Varreduras em filesystem **sempre** usam **caminho e nome do arquivo**. O **texto do corpo** para a extensão `.doc` usa a biblioteca opcional **`mammoth`** (instale o extra **`legacy-doc`**: `pip install -e ".[legacy-doc]"` ou `uv sync --extra legacy-doc`).

**O que você ganha:** O mammoth lê **Office Open XML empacotado em ZIP** (a mesma família de contêiner que `.docx`). Isso cobre alguns `.doc` reais que são OOXML de fato, ou que foram renomeados.

**Limitação:** O `.doc` **binário Word 97-2003** (arquivo composto OLE) **não** é ZIP; o mammoth em geral **não** abre, então a **amostra de conteúdo fica vazia** e só o nome/caminho entra nos achados. Se você precisa de evidência de compliance no corpo desses arquivos, converta para `.docx` (ou outro formato suportado) antes da varredura, ou planeje outra rota de ingestão — o produto **não** chama LibreOffice por subprocesso (escopo deste slice conforme issue/plan).

---

## Docker: conectar a dados remotos a partir do container

Muitas implantações usam a **imagem Docker**. O container precisa conseguir alcançar seus bancos de dados, shares de arquivos (NFS/SMB) e APIs.

- **Bancos remotos:** Use o **IP ou FQDN do host** do servidor de DB no config (não use `localhost` a menos que o DB rode no mesmo container). No host, teste com `psql`, `mysql` ou similar; no container, garanta que a rede do container alcance esse host (geralmente não é preciso host networking; em alguns ambientes use `host.docker.internal`).
- **NFS/SMB a partir do container:** Duas abordagens comuns: (1) **Montar o share no host** e fazer bind mount desse caminho no container (ex.: `-v /mnt/nfs-share:/data/shares`), depois usar um alvo **filesystem** em `/data/shares`; (2) **Usar alvos NFS/SMB** no config e garantir que a rede do container alcance o servidor NFS/SMB (instale `.[shares]` na imagem; abra firewall para portas NFS/SMB). Para passos e armadilhas, veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).
- **DNS:** Se o config usar hostnames, o container precisa resolvê-los (mesmo DNS do host ou `--dns`). Veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).

---

## O Data Boar é útil para sua organização?

- **Com consultor treinado:** Um consultor pode instalar, configurar e ajustar o Data Boar na sua rede; definir credenciais e alvos; executar varreduras e interpretar relatórios. É a forma de menor risco quando a maturidade de TI/conformidade/DPO ainda está crescendo.
- **Só licença (autoatendimento):** Você pode rodar o app sozinho: siga [TECH_GUIDE](TECH_GUIDE.pt_BR.md), [USAGE](USAGE.pt_BR.md) e [deploy/DEPLOY](deploy/DEPLOY.pt_BR.md). Use este guia de resolução de problemas e os documentos de aprofundamento quando tiver falhas de conectividade ou credenciais. Para ambientes complexos (muitas fontes, firewall rígido, SSO/OAuth), ainda se recomenda suporte de consultoria.
- **Docker:** A maioria das implantações usa o container; a conexão com DBs remotos e com NFS/SMB está documentada no deploy e nos documentos de troubleshooting acima.

---

## Documentação de aprofundamento (causa raiz e passos de correção)

| Tópico                         | Descrição                                                                                        | English                                                                            | Português (pt-BR)                                                                              |
| --------                       | -----------                                                                                      | ---------                                                                          | -------------------                                                                            |
| **Conectividade**              | Rede, DNS, firewall, timeouts; DB/API/share inacessível; permission_denied                       | [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md)                 | [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                 |
| **Credenciais e autenticação** | API key no header vs body; Basic/Bearer/OAuth; credenciais conflitantes; lockouts                | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) |
| **Implantação Docker**         | Rodar em container; NFS/SMB a partir do container; DB remoto a partir do container; DNS; volumes | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)   | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)   |

**Índice da documentação:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
