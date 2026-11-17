# Leitor Microsoft Graph em modo delegado: runbook da Fase 0 (pt-BR)

**English:** [M365_GRAPH_DELEGATED_RUNBOOK.md](M365_GRAPH_DELEGATED_RUNBOOK.md)

**Issues:** [#2260](https://github.com/DataBoar/data-boar/issues/2260) (Fase 0, prova real) e [#2261](https://github.com/DataBoar/data-boar/issues/2261) (o leitor `sharepoint_online`). Épico [#2206](https://github.com/DataBoar/data-boar/issues/2206).

**Situação:** a Fase 0 está **pendente**. O leitor está implementado e testado **só contra um Microsoft Graph simulado**. Nada neste repositório prova ainda que ele lê um OneDrive real.

**O que a Fase 0 pode provar, e o que não pode.** A Fase 0 roda o leitor contra o **OneDrive pessoal do operador**, numa pasta sintética, com uma pessoa entrando por device code. Ela prova **só o OneDrive pessoal**. Ela **não** prova SharePoint Online, tenant de trabalho ou escola, políticas de acesso condicional de um tenant, acesso app-only (sem pessoa) nem throttling real. Nada disso pode ser afirmado a partir da Fase 0.

---

## 1. O que o leitor faz

- Tipo `sharepoint_online`, somente leitura, tier **Enterprise**.
- Uma pessoa entra pelo fluxo OAuth de **device code**: cliente público, **sem client secret**, escopos `Files.Read` e `offline_access`.
- A entrada só é permitida numa **varredura única da CLI, rodada num terminal**. O dashboard web, a API e qualquer agendador nunca fazem a entrada; um alvo disparado por eles falha com `auth_required`.
- `Files.Read` dá ao token leitura do **drive inteiro**. Quem restringe a varredura ao `root_folder` é o leitor, não o token: ele resolve a pasta uma vez e só anda pelos ids dos itens abaixo dela. Atalhos para outros drives (`remoteItem`), pacotes, itens marcados como malware ou apagados e itens de outro drive são ignorados e contados.
- Os tokens ficam **só na memória**, durante a varredura. Nada é gravado em disco. O refresh token vale cerca de 90 dias e não fica preso à pasta; por isso nunca é guardado.

## 2. Registrar o aplicativo (operador)

Faça no centro de administração do Microsoft Entra (Registros de aplicativo). Nunca copie nenhum identificador deste passo para o repositório, uma issue ou o arquivo de evidência.

1. **Onde:** se a sua conta Microsoft pessoal não conseguir registrar um aplicativo sem um tenant Entra (não confirmado), crie um tenant gratuito só para hospedar o registro. Quem entra na varredura continua sendo a sua conta pessoal.
2. **Tipos de conta:** "Somente contas pessoais da Microsoft" ("Personal Microsoft accounts only").
3. **URI de redirecionamento:** nenhuma. O device code não usa (a Fase 0 confirma; se a entrada falhar pedindo uma, anote o código do erro e informe).
4. **Autenticação:** "Permitir fluxos de cliente público" ("Allow public client flows") = **Sim**. Com **Não**, o endpoint de token falha com `invalid_client` (AADSTS7000218).
5. **Permissões de API:** Microsoft Graph, **delegada**, `Files.Read`. Se o portal acrescentar `User.Read`, remova. O `offline_access` é pedido na entrada.
6. **Certificados e segredos:** não crie **nada**. Nem client secret, nem certificado.
7. Anote o **ID do aplicativo (cliente)** num lugar privado. Ele vai na configuração efêmera da seção 4.

## 3. Preparar a pasta sintética (operador)

1. Gere arquivos sintéticos **fora do repositório**:

   ```bash
   uv run python scripts/generate_synthetic_poc_corpus.py --output /tmp/m365-phase0-corpus --scenario happy
   ```

2. No seu OneDrive, crie uma pasta como `/DataBoar-Sintetico` e envie alguns dos arquivos de texto gerados (por exemplo `.txt` e `.csv`). Use só conteúdo sintético.
3. Guarde as cópias locais: a evidência compara nome, tamanho e SHA-256 dos arquivos locais com o que o leitor lista.

## 4. Configuração efêmera (fora do repositório)

Crie um arquivo de configuração **fora do repositório** (por exemplo `/tmp/m365-phase0.yaml`). **Todas as chaves são obrigatórias**; não há default, e chave ausente falha com `config_error` citando a chave (referência das chaves: [USAGE.pt_BR.md](../USAGE.pt_BR.md)). O client ID não é segredo, mas identifica o seu registro: mantenha este arquivo fora de qualquer repositório, issue ou evidência.

```yaml
targets:
  - name: onedrive-sintetico
    type: sharepoint_online
    auth:
      mode: delegated
      tenant: consumers                     # contas pessoais
      client_id: <APP_CLIENT_ID>            # não é segredo, mas nunca vai para commit
      login_host: login.microsoftonline.com
      scopes: "https://graph.microsoft.com/Files.Read offline_access"
    graph:
      base_url: https://graph.microsoft.com/v1.0
    download_host_suffixes: [.files.1drv.com, .microsoftpersonalcontent.com]
    drive: me
    root_folder: /DataBoar-Sintetico
    max_depth: 32
    max_file_bytes: 104857600
    page_size: 200
    max_pages_per_folder: 10000
    http_timeout_seconds: 30
    throttle_max_wait_seconds: 120
report:
  output_dir: /tmp/m365-phase0-report
sqlite_path: /tmp/m365-phase0-report/audit.db
```

Recomendado: deixe o operador aprovar os dois hosts, fora do YAML: `export DATA_BOAR_CREDENTIAL_STRICT=1` e `export DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS=login.microsoftonline.com,graph.microsoft.com`. Sem o modo estrito, nada aprova os hosts além do formato.

## 5. Rodar a varredura num terminal

```bash
uv run python main.py --config /tmp/m365-phase0.yaml
```

No Docker, o contêiner precisa de terminal (`-it`) e da configuração:

```bash
docker run -it --rm \
  -v /tmp/m365-phase0.yaml:/data/m365-phase0.yaml:ro \
  -v /tmp/m365-phase0-report:/tmp/m365-phase0-report \
  <imagem do data-boar> main.py --config /data/m365-phase0.yaml
```

O leitor escreve uma linha na saída de erro padrão (em inglês):

```text
To sign in to Microsoft for target 'onedrive-sintetico', open https://microsoft.com/devicelogin and enter the code <CÓDIGO>. The code expires in 15 minutes.
```

Abra o endereço num navegador, digite o código, entre com a sua conta pessoal e aceite o consentimento. A tela de consentimento deve pedir só a leitura dos seus arquivos e a manutenção do acesso (anote o que ela mostra, sem identificadores). Depois a varredura segue sozinha.

## 6. Evidência

Registre o resultado em `docs/ops/evidence/M365_PHASE0_<data>.md` **como aconteceu**: rodou, falhou ou bloqueado, e por quê. Se o registro do aplicativo não estiver disponível, o resultado é "bloqueado: sem registro do app".

1. **Listagem pelo leitor** (custa um device code a mais, porque é outro processo):

   ```bash
   uv run python - <<'PY'
   from config.loader import load_config
   from connectors.sharepoint_online_connector import SharePointOnlineConnector, enable_interactive_sign_in
   target = load_config("/tmp/m365-phase0.yaml")["targets"][0]
   enable_interactive_sign_in()
   for e in SharePointOnlineConnector(target, None, None).list_scope():
       print(e.display_path, e.size, e.skipped_reason or "")
   PY
   ```

2. **Os mesmos arquivos locais:** nome, tamanho e SHA-256 (`sha256sum /tmp/m365-phase0-corpus/<arquivos>`).
3. **Resumo do relatório:** quantidade de achados por arquivo e padrão.

Roteiro da Fase 0:

| Id | O que a conta real prova | Se falhar |
| --- | --- | --- |
| P0-1 | Registro de conta pessoal com fluxos de cliente público = Sim aceita device code com `tenant: consumers` | anote o código AADSTS; revise a seção 2 |
| P0-2 | A tela de consentimento pede só leitura de arquivos e manutenção do acesso | revise escopos e este runbook |
| P0-3 | O endpoint de token devolve refresh token; anote o `expires_in` observado (nunca o token) | revise o tratamento do refresh |
| P0-4 | Device code funciona sem URI de redirecionamento | acrescente a URI à seção 2 |
| P0-5 | O host real de download termina num sufixo da allowlist (`.files.1drv.com` ou `.microsoftpersonalcontent.com`); anote só o sufixo | o leitor recusa o download (`scope_violation`); a allowlist precisa de revisão do desenho antes do merge |
| P0-6 | `list_scope()` lista só a pasta sintética, com nomes e tamanhos iguais aos locais | bloqueia o merge |
| P0-7 | (opcional) um atalho para outra pasta aparece como ignorado | revise a regra de atalho |
| P0-8 | O relatório tem os achados esperados do conteúdo sintético | bloqueia o merge |
| P0-9 | Nenhuma falha `skipped` com `other_drive` numa pasta sintética comum | a regra do id de drive precisa de revisão do desenho antes do merge |

**Nunca** escreva no arquivo de evidência, numa issue ou num commit: id do tenant, client ID, id de drive ou de item, e-mail, nome da conta, URL de download, token, o código do usuário, nem captura de tela que mostre qualquer um deles.

## 7. Revogar o acesso depois

1. Remova o aplicativo da sua conta Microsoft pessoal em [account.live.com/consent/Manage](https://account.live.com/consent/Manage). Tenants de trabalho ou escola: ver [TECH_GUIDE.pt_BR.md, "Microsoft 365 via Graph"](../TECH_GUIDE.pt_BR.md#microsoft-365-via-graph).
2. Apague o registro do aplicativo (e o tenant temporário, se você criou um só para isto).
3. Apague a pasta sintética e os arquivos e o relatório temporários locais.

## 8. Erros comuns

| Falha (`reason`) | Causa provável |
| --- | --- |
| `auth_required` | A varredura não rodou num terminal, ou rodou pelo dashboard web, pela API ou por um agendador. A entrada delegada precisa de uma pessoa; varredura sem pessoa precisa do modo app-only ([#2262](https://github.com/DataBoar/data-boar/issues/2262), ainda não disponível). |
| `auth_failed` "token endpoint error invalid_client (AADSTS7000218)" | "Permitir fluxos de cliente público" está em Não. |
| `auth_failed` "Microsoft sign-in was declined" ou "code expired" | O consentimento foi recusado, ou o código não foi digitado a tempo. Rode de novo. |
| `auth_failed` num tenant de trabalho ou escola | O tenant pode bloquear o device code por acesso condicional (política gerenciada pela Microsoft). Este runbook cobre só contas pessoais. |
| `config_error` citando `#2262` | `auth.mode: app_only` ou `drive` diferente de `me`: ainda não disponível. |
| `scope_violation` "download host not allowlisted" | O host real de download não está na allowlist. Anote só o sufixo e informe (P0-5). |
| `skipped` "N items skipped: ..." | Itens fora das regras (atalhos, pacotes, outro drive). Só contagens, sem nomes. |
