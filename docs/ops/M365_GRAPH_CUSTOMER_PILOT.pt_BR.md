# Leitor Microsoft Graph: roteiro de piloto para o administrador do cliente (pt-BR)

**English:** [M365_GRAPH_CUSTOMER_PILOT.md](M365_GRAPH_CUSTOMER_PILOT.md)

**Situação:** o leitor `sharepoint_online` (modo delegado) foi testado **só contra um Microsoft Graph simulado**. A prova com conta real cobre um **OneDrive pessoal** ([#2260](https://github.com/DataBoar/data-boar/issues/2260)) e **ainda não rodou**. Ele **não** foi validado em tenant de trabalho ou escola nem contra SharePoint Online. Um piloto no cliente é, portanto, uma **avaliação**: registre o que acontecer e não afirme nada além disso. Contexto e referências da Microsoft: [TECH_GUIDE.pt_BR.md, "Microsoft 365 via Graph"](../TECH_GUIDE.pt_BR.md#microsoft-365-via-graph).

Use placeholders em chamados e anotações: `<APP_CLIENT_ID>`, `<TENANT_ID>`, `user@example.com`. Nunca cole identificadores reais, tokens ou códigos numa issue do Data Boar.

## 1. Permissões mínimas

| O quê | Valor |
| --- | --- |
| Tipo de permissão | Só **delegada** (uma pessoa entra). Nenhuma permissão de aplicativo. |
| Permissões do Microsoft Graph | `Files.Read` e `offline_access` (refresh token). Nada mais; remova `User.Read` se o portal acrescentar. |
| Credenciais no aplicativo | **Nenhuma**: nem client secret, nem certificado. "Permitir fluxos de cliente público" = Sim. |
| Quem entra | Um usuário do piloto cujo OneDrive tenha uma pasta de teste com arquivos sintéticos. |
| Onde a varredura roda | Uma varredura única da CLI num terminal (`python main.py --config ...` ou `docker run -it`). O dashboard web, a API e os agendadores não conseguem entrar. |

Antes do piloto, confira duas configurações do tenant (as duas são decisão do administrador, não do Data Boar):

1. **Consentimento do usuário:** se os usuários podem consentir em aplicativos, e de quais publicadores ([configurar o consentimento do usuário](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/configure-user-consent)). O Data Boar **não tem publicador verificado**; se o aplicativo for multitenant e registrado fora do seu tenant, os usuários provavelmente não vão conseguir consentir, e o administrador concede o consentimento ([verificação do publicador](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview), [conceder consentimento de administrador](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/grant-admin-consent)). Registrar o aplicativo no seu próprio tenant evita o consentimento entre tenants.
2. **Fluxo de device code:** o acesso condicional pode bloqueá-lo ([bloquear fluxos de autenticação](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-block-authentication-flows)). Se estiver bloqueado, o leitor delegado não roda; uma exceção restrita ao usuário do piloto é decisão sua. O modo app-only, sem pessoa ([#2262](https://github.com/DataBoar/data-boar/issues/2262)), está planejado, não entregue.

## 2. O que o leitor lê, e o que não lê

**Lê:**

- Só a pasta definida em `root_folder` (ou `root_folder_id`) no OneDrive **do usuário que entrou** (`drive: me`), e as subpastas, percorridas por id de item.
- Só arquivos cuja extensão está na lista de varredura configurada, até `max_file_bytes` cada. O conteúdo é baixado para um diretório temporário privado, varrido e apagado.

**Não lê:**

- Nada fora dessa pasta. Atenção: **a permissão sozinha permitiria mais**: `Files.Read` dá ao token leitura do drive inteiro do usuário e dos arquivos compartilhados com ele ([referência de permissões](https://learn.microsoft.com/en-us/graph/permissions-reference)). A restrição à pasta é imposta **pelo leitor**, não pela Microsoft.
- Atalhos para outros drives, pacotes (como blocos de anotações do OneNote), itens marcados como malware, itens apagados e itens de outro drive. Eles são ignorados e informados como contagens, sem nomes.
- Drives de outros usuários, sites do SharePoint, Teams, e-mail ou calendários. Ele não grava nada.

**O que ele guarda:** achados com um caminho de exibição como `onedrive:/<pasta>/<arquivo>`, nome do arquivo, padrão e sensibilidade. Sem id de item, nome de conta, e-mail ou URL de download. Os tokens ficam na memória durante a varredura e nunca vão para disco, log ou relatório.

## 3. Passos do piloto

1. Registre o aplicativo (ou use o aplicativo do fornecedor) com as configurações da seção 1.
2. Crie uma pasta de teste no OneDrive do usuário do piloto e coloque nela só arquivos sintéticos.
3. No host da varredura, escreva uma configuração **fora de qualquer repositório**. Todas as chaves são obrigatórias (sem default; chave ausente falha com `config_error` citando a chave; referência: [USAGE.pt_BR.md](../USAGE.pt_BR.md)). Os valores abaixo são da nuvem global da Microsoft; uma nuvem soberana usa os próprios hosts ([TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md#microsoft-365-via-graph)). O sufixo do host de download de um tenant de trabalho é uma hipótese não confirmada: se o leitor recusar um download com `scope_violation`, anote só o sufixo informado.

   ```yaml
   targets:
     - name: pilot-onedrive
       type: sharepoint_online
       auth:
         mode: delegated
         tenant: <TENANT_ID>
         client_id: <APP_CLIENT_ID>
         login_host: login.microsoftonline.com
         scopes: "https://graph.microsoft.com/Files.Read offline_access"
       graph:
         base_url: https://graph.microsoft.com/v1.0
       download_host_suffixes: [.sharepoint.com]
       drive: me
       root_folder: /DataBoar-Pilot
       max_depth: 32
       max_file_bytes: 104857600
       page_size: 200
       max_pages_per_folder: 10000
       http_timeout_seconds: 30
       throttle_max_wait_seconds: 120
   ```

   Aprove os dois hosts como operador, fora do YAML: `DATA_BOAR_CREDENTIAL_STRICT=1` e `DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS=<host de login>,<host do Graph>`. Sem o modo estrito, nada os aprova além do formato.

4. Rode `python main.py --config <arquivo>` num terminal; o usuário do piloto segue as instruções impressas (endereço e código) num navegador.
5. Compare o relatório com os arquivos sintéticos que você colocou. Registre o resultado como aconteceu (rodou, falhou ou bloqueado, e por quê).

## 4. Revogar o acesso depois do piloto

- **Administrador:** em Aplicativos empresariais, reveja e revogue as permissões concedidas ao aplicativo, para a organização ou para o usuário do piloto ([rever permissões concedidas a aplicativos empresariais](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-application-permissions)), e depois apague o aplicativo empresarial se ele não for mais necessário ([apagar um aplicativo empresarial](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/delete-application-portal)). Se foi você quem registrou o aplicativo, apague o registro.
- **Usuário com conta pessoal da Microsoft:** remova o aplicativo em [account.live.com/consent/Manage](https://account.live.com/consent/Manage).
- Apague a pasta de teste, o arquivo de configuração e o relatório local se não forem mais necessários.
