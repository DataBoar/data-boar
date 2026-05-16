# Canais de notificação do operador — vários meios de contato

**English:** [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md)

**Objetivo:** Quando o **CI falha**, um **job longo termina** ou um **humano precisa voltar** ao Cursor, use **pelo menos dois canais independentes** para um não bloquear o outro (app em DND, conta errada, etc.). Este doc é **política + notas de integração** — **sem segredos** no repositório (tokens em variável de ambiente, `docs/private/` ou **secrets** do GitHub Actions).

**Âmbito:** Alertas para **mantenedor/operador** (você + automações). Notificações de **produto** (fim de scan, etc.) seguem o plano **Notifications** em [PLANS_TODO.md](../plans/PLANS_TODO.md) (ordem 6) — pode reutilizar a mesma lista de canais.

**Política do mantenedor (este repositório):** **Telegram não é usado** para notificações do Data Boar nem para comunicação de projeto com esse ângulo — postura de confiança e escolha do operador. A **única** alternativa de chat ao **Slack** para pings operacionais é o **Signal** (API HTTP via **`signal-cli`** / **signald** em Docker na LAN ou homelab — ver §3 e **[private.example/notify/README.md](../private.example/notify/README.md)**). Não acrescentar workflows baseados em Telegram nem recomendar Telegram para alcance ao operador do Data Boar em docs rastreados.

**Sequenciamento (mantenedor):** Por ora, **só o canal A** — app **GitHub** no celular + watch/e-mail nas configurações — **basta** para PRs, reviews, Dependabot, Security e **Actions com falha**. Quando quiser **redundância** ou alertas no estilo “chat”, use **B** (Slack — já integrado no Actions) e/ou **C** (ponte Signal); o Slack é o fornecedor de menor atrito a partir do GitHub Actions; o Signal é o **segundo chat preferido** se quiser depender menos da UX do Slack. **Este doc é o lembrete de integração** para esses próximos passos.

## Prova rápida “CHAN-OK” (Slack) — 10 minutos, sem mistério

**Objetivo:** sair daqui com a confirmação **“chega no canal e notifica no PC e no iPhone”**.

1. **Webhook + secret (GitHub)**: confirme que existe `SLACK_WEBHOOK_URL` em **GitHub → Settings → Secrets and variables → Actions**.
1. **Canal no Slack**: no canal de ops (ex.: `#data-boar-ops`), tire **silenciar** e ajuste para notificar **All messages** (ou, no mínimo, menções).
1. **Menção forte (recomendado)**: crie a variável **`SLACK_MENTION_USER_ID`** (Settings → **Variables**) com seu **Member ID** (`U…`). Isso faz o ping virar `<@U…>` e o Slack tende a notificar melhor.
1. **Teste manual**: GitHub **Actions → Slack operator ping (manual) → Run workflow**. (Se houver campo `mention_user_id`, use seu `U…` também.)
1. **Critério de sucesso**:
   - Mensagem aparece no canal **e**
   - aparece notificação no **Slack Desktop** **e**
   - aparece notificação no **iPhone** (Slack habilitado em iOS + Focus/DND não bloqueando).

Se a mensagem aparece no canal mas **não** notifica: o problema quase sempre é **config do canal** (silenciado/menções), **Focus/DND**, ou permissões do app no sistema — veja §4.2 D.

---

## 1. Pilha recomendada (menos atrito → mais montagem)

| Prioridade | Canal      | Por quê                                                                                                      | Uso típico                                                                                             |
| ---------- | -----      | -------                                                                                                      | -----------                                                                                            |
| **A**      | **GitHub** | Já ligado ao repositório; **app móvel** para assign, review, **workflow falho**, Dependabot, Security.       | Watch em **data-boar**; falhas em **Actions**; opcional **Issue** aberta por automação com `@mention`. |
| **B**      | **Slack**  | **Webhook** ou bot; fácil com `curl` no GitHub Actions.                                                      | Canal `#data-boar-ops`; secret `SLACK_WEBHOOK_URL`.                                                    |
| **C**      | **Signal** | Privacidade forte; **REST** via **`signal-cli`** / **signald** em **Docker** (dispositivo vinculado / ponte na LAN). | `curl` do Actions ou script local para o endpoint Signal; secrets só no GitHub ou `docs/private/notify/`. |

**Mínimo prático:** **A + B** (GitHub + Slack) corresponde aos workflows atuais. **A + C** (GitHub + Signal só) é válido se publicares a partir de um **runner confiável** ou **script local** na ponte Signal — **Telegram não** substitui esse caminho neste projeto.

### 1.1 Implantação em fases: Slack (Actions) + Signal (segundo chat preferido)

O **Slack** continua a integração **padrão** do GitHub Actions (incoming webhook, um secret). O **Signal** é o **chat não-Slack endossado** para o Data Boar: o mesmo texto curto para um endpoint **REST privado** na LAN (imagem Docker que operas — ver §3).

| Fase  | Canais        | Objetivo                                                                                                                                                                                                                                             |
| ----  | ------        | --------                                                                                                                                                                                                                                             |
| **1** | **A + B**     | Push/e-mail do GitHub + **Slack** (`#data-boar-ops` ou outro): workflow de **ping manual**, workflow **CI falhou**, opcionalmente o mesmo webhook no Data Boar para fim de scan (USAGE).                                                             |
| **2** | **A + B + C** | Somar **Signal** via **ponte HTTP no homelab** (§3) + secret, por exemplo `SIGNAL_NOTIFY_URL` (ou `NOTIFY_SECONDARY_URL` genérico). O mesmo workflow ou script manda **o mesmo texto curto** para Slack **e** Signal quando os secrets existirem. |

**Por que Slack e Signal juntos:** modos de falha independentes (queda do Slack vs tua ponte Signal vs app do GitHub). **Não** usar Telegram como terceiro fornecedor neste repositório.

**Esboço no CI:** um passo/script reutilizável: se `SLACK_WEBHOOK_URL` → `curl` no Slack; se `SIGNAL_NOTIFY_URL` → `curl` na REST do Signal na LAN (ou túnel); falha em um ramo **não** impede o outro (avisar no log e seguir).

---

## 2. GitHub (linha de base recomendada)

- **Watch** no repositório (Actions, Security conforme preferir).
- **Workflow falho:** checks obrigatórios evitam merge silencioso; falhas aparecem no app e e-mail/push.
- **Automação → humano:** job agendado pode **abrir/comentar Issue** (`gh issue create` / API); você recebe notificação **padrão** no iPhone.

**Cursor mobile (companion):** Útil para **chat leve / acompanhamento com o agente** longe do desktop. **Não** substitui o push do **GitHub** para **Actions com falha**, **Dependabot** ou **Security** — mantenha o **canal A** (app **GitHub** oficial + configurações de notificação).

Use **GITHUB_TOKEN** no Actions (permissões no workflow).

---

## 3. Signal (Docker / CLI — avançado)

Configurações comuns usam **`signal-cli`** ou **`signald`** em **Docker**, com **dispositivo vinculado** ou fluxo de registro. O comportamento que descreveu (mensagens como **sua** identidade; “anotação” ao enviar para si / conversa consigo) é um padrão conhecido para **lembretes do operador**.

### Riscos / cuidados

- **Operacional:** reinícios do container, pareamento/QR, recuperação de sessão.
- **Legal / ToS:** imagens auditadas; cumprimento dos termos do Signal.
- **Automação:** o agente no Cursor **não** guarda a sessão Signal; só **runners seus** (servidor em casa, script no laptop, CI com secrets **seus**) devem chamar a API.
- **Descarregar no LAB‑OP:** Rodar a imagem Docker do Signal em **outra máquina do lab** (não no PC de dev) é um bom encaixe: o workstation manda **`curl`** (cabeçalhos + corpo JSON) para a API REST na LAN — o mesmo estilo de integração que **Uptime Colleague-Ma**. Trave o serviço na **rede privada**; URL/token só em **`docs/private/notify/`** (gitignored). Ver **[private.example/notify/README.md](../private.example/notify/README.md)** § *Signal on a different machine*.

**Prioridade:** Para este mantenedor, o Signal é o **único** canal de chat não-Slack usado para pings operacionais do Data Boar — depois do GitHub (**A**) e junto ou em alternativa ao Slack, conforme a tua montagem.

---

## 4. Slack vs Signal (comparação rápida)

|                         | Slack                        | Signal (este projeto)                                      |
| ---                     | ---                          | ---                                                        |
| **Montagem**            | App Slack → Incoming Webhook | **`signal-cli`** / **signald** em Docker; REST na **LAN privada**; ver §3 |
| **A partir do Actions** | `curl` POST JSON no webhook  | `curl` para a URL da ponte + corpo JSON (conforme a imagem); secret `SIGNAL_NOTIFY_URL` etc. |
| **Postura do operador** | Menor atrito no GitHub Actions | **Preferido** como experiência de chat para alguns operadores; **não** Telegram — política no início do doc |

Um passo genérico “notify” pode enviar o mesmo texto ao **Slack** e/ou ao **Signal** se os secrets existirem (`curl` independentes; falha num ramo não bloqueia o outro).

### 4.1 Checklist Slack (canal B)

**Proteção do webhook (Actions Slack que fazem POST):** **Não** coloque `secrets.*` nem `SLACK_WEBHOOK_URL` num `if:` no **nível do job** (o GitHub pode registrar run **fantasma falhado** com zero jobs). O padrão do repositório é: um **passo** lê `SLACK_WEBHOOK_URL` via `env:`, escreve `present=true|false` em `$GITHUB_OUTPUT`, e os passos seguintes usam `if: steps.<id>.outputs.present == 'true'`. **Testes de regressão:** `tests/test_github_workflows.py::test_slack_post_workflows_guard_webhook_secret` (e, quando o arquivo está no `origin`, inclui todos os `slack-*.yml` que fazem POST).

1. No workspace Slack, crie um canal (ex.: **`#data-boar-ops`**).
1. Crie um [**Incoming Webhook**](https://api.slack.com/messaging/webhooks) (app no workspace → escolha o canal → copie a URL do webhook).
1. No GitHub: **Settings → Secrets and variables → Actions → New repository secret** — nome **`SLACK_WEBHOOK_URL`**, valor = essa URL.
1. **Teste:** **Actions → Slack operator ping (manual) → Run workflow** (mensagem opcional). Se o secret não existir, o job fica **skipped** (sem falha).
1. **Menção opcional para push no celular/desktop:** **Variável** de repositório **`SLACK_MENTION_USER_ID`** (member ID do Slack, `U…`) — ver §4.2 D). O ping manual também aceita **`mention_user_id`** para um teste pontual.
1. **CI / Semgrep falhou → Slack (fase 1):** workflow **`Slack CI failure notify`** (`.github/workflows/slack-ci-failure-notify.yml`) corre quando **`CI`**, **`Semgrep`**, **`Gitleaks`**, **`SBOM`** ou **`Dependabot requirements.txt sync`** termina com **`failure`** (regras `workflow_run` do GitHub). Usa **`SLACK_WEBHOOK_URL`**; opcional **`SLACK_MENTION_USER_ID`**. Se o secret não existir, os passos de notify **saltam** sem falhar. **Snapshot privado + receita de pausa:** **§4.1.1**.
1. **Release publicada → Slack (opt-in):** workflow **`Slack release published notify`** (`.github/workflows/slack-release-published-notify.yml`) envia um resumo curto quando uma GitHub Release é publicada. Ative com a variável de repositório **`SLACK_NOTIFY_RELEASE_PUBLISHED=true`**.
1. **PR merged → Slack (opt-in):** workflow **`Slack PR merged notify`** (`.github/workflows/slack-pr-merged-notify.yml`) envia mensagem quando um PR é merged em `main`/`master`. Ative com **`SLACK_NOTIFY_PR_MERGED=true`**.
1. **Digest operacional (manual + agendado opt-in):** workflow **`Slack ops digest`** (`.github/workflows/slack-ops-digest.yml`) aceita `workflow_dispatch` e agendamento em dias úteis. O agendamento só roda com **`SLACK_NOTIFY_DAILY_DIGEST=true`**; o disparo manual funciona sempre que o secret existir.
1. **Produto / fim de scan:** reutilize a mesma URL no **`config.yaml`** ou env do Data Boar (ver [USAGE.pt_BR.md](../USAGE.pt_BR.md) — notificações ao operador); caminho separado dos workflows do Actions acima.
1. **Backlog (opcional):** digest agendado com [scripts/notify_webhook.py](../../scripts/notify_webhook.py) ou export KPI quando quiser resumos EOD/sprint (ver §7).

#### 4.1.1 Slack CI failure notify — contrato (live + snapshot privado + pausa)

**Shipped:** **`.github/workflows/slack-ci-failure-notify.yml`** no **`origin`**. **`tests/test_github_workflows.py`** impõe forma YAML, lista **`workflows:`** upstream e o mesmo **guard de passo de webhook** que nos outros **`slack-*.yml`** que fazem POST.

| Tema | Detalhe |
| ---- | ------- |
| **Live (o GitHub executa)** | **`workflow_run`** em **`completed`**, **`if:`** do job só com **`failure`** do upstream; deteção de **`SLACK_WEBHOOK_URL`** ao nível do passo (`present=true|false` → **`GITHUB_OUTPUT`**); POST quando o secret existe. Nomes de upstream no YAML: **`CI`**, **`Semgrep`**, **`Gitleaks`**, **`SBOM`**, **`Dependabot requirements.txt sync`**. |
| **Snapshot privado (o GitHub não executa)** | **`docs/private/raw_pastes/cursor-incident/slack-ci-failure-notify.yml.old`** — atualize depois de **mudanças intencionais** ao YAML live (copie o YAML já merged) para manter âncora de diff em exercícios de pausa. Índice: **`docs/private/ops/CURSOR_INCIDENT_EVIDENCE_INDEX.pt_BR.md`**. |
| **Pausar de novo** | Retirar **`slack-ci-failure-notify.yml`** de **`.github/workflows/`**, gravar o último YAML em **`.yml.old`**, trocar **`test_slack_ci_failure_notify_workflow_present_and_valid`** por teste de **ausência**, remover **`slack-ci-failure-notify.yml`** da tupla **`names`** em **`test_slack_post_workflows_guard_webhook_secret`**, **`pytest tests/test_github_workflows.py`**, merge. |
| **Religar** | Copiar **`.old`** → **`.github/workflows/slack-ci-failure-notify.yml`**, repor teste de **presença** + entrada **`names`**, **`pytest tests/test_github_workflows.py`**, **`check-all`**, merge. |

### 4.2 Webhook Slack — how-to do operador (pegar URL, guardar, conferir)

**Objetivo:** uma URL de **Incoming Webhook**, guardada como **`SLACK_WEBHOOK_URL`** no GitHub, usada por **`Slack operator ping (manual)`** e **`Slack CI failure notify`**.

#### A) Obter a URL do webhook (Slack, navegador)

1. Entre em [slack.com](https://slack.com) no workspace onde quer os alertas.
1. Abra **[Your Apps](https://api.slack.com/apps)** (`https://api.slack.com/apps`).
1. **Create New App** → **From scratch** → nome (ex.: **`Data Boar notifications`**) → escolha o **workspace** → **Create App**.
1. No menu lateral do app, **Incoming Webhooks** → ligue **Activate Incoming Webhooks** (**On**).
1. **Add New Webhook to Workspace** → escolha o canal (ex.: **`#data-boar-ops`**) → **Allow**.
1. Copie a **Webhook URL** — deve parecer `<https://hooks.slack.com/services/..>.`. **Não** publique em issue, PR nem chat público.

Se o workspace bloquear apps customizados, peça a um admin aprovação ou um fluxo alinhado à política da empresa.

#### B) Onde guardar (canônico + backup opcional)

| Onde                                                     | O que fazer                                                                                                                                                                                                | Por quê                                                                                                                                                                     |
| ----                                                     | -----------                                                                                                                                                                                                | -------                                                                                                                                                                     |
| **GitHub Actions (obrigatório para os workflows de CI)** | **Settings → Secrets and variables → Actions → New repository secret** → nome **`SLACK_WEBHOOK_URL`** (exatamente assim) → cole a URL → **Add secret**.                                                    | O Actions lê esse secret; nada vai parar em arquivo commitado.                                                                                                              |
| **Gerenciador de senhas (opcional)**                     | Ex.: nota segura no Bitwarden: título `GitHub SLACK_WEBHOOK_URL — <repo>`; mesma URL.                                                                                                                      | Recuperação se rotacionar o webhook ou recriar o secret. Ver [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) ([pt-BR](OPERATOR_SECRETS_BITWARDEN.pt_BR.md)). |
| **`config.yaml` / env (opcional, produto)**              | Só se quiser Slack no **fim de scan** num Data Boar a correr — mesma URL em **`notifications`** (ver [USAGE.pt_BR.md](../USAGE.pt_BR.md)). Prefira env ou config **gitignored**; **nunca** commitar a URL. | Caminho separado do GitHub Actions; pode ser o mesmo webhook.                                                                                                               |

**Não** guarde o webhook em: Markdown rastreado, print em ticket, ou só neste chat como única cópia.

#### C) Depois de pronto — onde olhar

| Verificação                  | Onde                                                              | “Certo”                                                                                                                                      |
| -----------                  | ----                                                              | --------                                                                                                                                     |
| Secret existe                | GitHub → **Settings → Secrets and variables → Actions**           | **`SLACK_WEBHOOK_URL`** na lista (valor **oculto** — normal).                                                                                |
| Ping manual                  | **Actions** → **Slack operator ping (manual)** → **Run workflow** | Job **com sucesso** (não **skipped**). **Skipped** costuma ser secret ausente/nome errado ou workflows ainda não na branch que o GitHub usa. |
| Mensagem chegou              | Slack → canal de ops                                              | Mensagem nova com o texto enviado (ou o padrão).                                                                                             |
| CI / Semgrep falhou → Slack | Depois de falhar um workflow listado e com **`SLACK_WEBHOOK_URL`** definido | **Actions** mostra **Slack CI failure notify**; no Slack, texto **“Data Boar — &lt;nome do workflow&gt; falhou”** com link. Se o secret não existir, o job de notify conclui mas o passo de POST salta. |

Se o job manual ficar **skipped**, confira o nome **`SLACK_WEBHOOK_URL`** e se `.github/workflows/slack-operator-ping.yml` está na branch padrão (ou na branch onde você dispara o Actions).

#### D) Mensagem no canal mas sem alerta no celular / Windows

Um **incoming webhook** só **publica no canal**. Isso **não** é o mesmo que **notificação pessoal**: o Slack pode mostrar a mensagem no canal sem **push** no iPhone, Android ou app Windows se:

- O canal estiver **silenciado** ou com notificação só para **menções** / palavras-chave.
- **Agenda de notificações**, **Foco** ou **Não perturbe** estiver bloqueando.
- As permissões do app **Slack** no sistema estiverem desligadas (iOS **Ajustes → Slack → Notificações**, **Foco assistido** no Windows, etc.).

**O que costuma resolver:**

1. **Canal no Slack:** Abra o canal de ops → nome do canal → **Notificações** (ou ajustes do canal) → **Todas as mensagens** / **Cada mensagem nova**, ou pelo menos **tire o silenciar** do canal.
2. **Menção opcional (recomendado para CI + ping manual):** Crie uma **variável** de repositório (GitHub → **Settings → Secrets and variables → Actions** → aba **Variables**) com o nome **`SLACK_MENTION_USER_ID`** e o seu **member ID** do Slack (começa com `U`, ex.: `U0123ABCD`). Onde achar: Slack → seu avatar → **Perfil** → **Mais** → **Copiar ID do membro** (o rótulo pode variar um pouco). Os workflows **`Slack operator ping (manual)`** e **`Slack CI failure notify`** colocam `<@USER_ID>` no início da mensagem para o Slack usar as regras de **menção** (em geral alerta mais forte no celular/desktop do que “qualquer mensagem no canal”). Para testar uma vez sem salvar variável, use o campo **`mention_user_id`** ao rodar o ping manual.
3. **GitHub (canal A):** Instale o app **GitHub** no celular e ative notificações de **Actions** / execuções de workflow em **GitHub → Configurações → Notificações**; no iPhone, confira também **Ajustes → GitHub**. O app **Cursor** no celular **não** substitui o push do GitHub para Actions com falha (ver §2).

**Não** cole seu member ID em issue pública nem em commit; use só a UI de **Variables**.

---

## 5. Padrão multi-canal

1. **Primário:** GitHub (comentário em Issue ou check falho).
1. **Secundário:** **Slack** (webhook) e/ou **Signal** (ponte REST)—**não** Telegram neste repositório.
1. **Redundância reforçada:** **Slack + Signal ao mesmo tempo** (ver §1.1)—mesmo payload nos dois quando quiser **dois fornecedores de chat** além do GitHub.

**Não** commitar webhooks nem tokens; usar **secrets** do GitHub e/ou `.env` no `.gitignore`.

---

## 6. KPI snapshot + notificar (opcional)

**Ritmo editorial X (Slack, estação de trabalho):** o script [scripts/social-x-pace-remind.ps1](../../scripts/social-x-pace-remind.ps1) lê o arquivo gitignored `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (só na árvore do operador; atalho de uma linha em `social_drafts/SOCIAL_HUB.md` não tem tabela) e lista linhas **X** ainda **`draft`** com **Alvo editorial** em ou antes de hoje. Com **`SLACK_WEBHOOK_URL`** no **ambiente local** (mesma URL do Incoming Webhook do GitHub Actions — ver §4.1) e **`-Slack`**, envia um POST ao canal do webhook (ex.: **`#data-boar-ops`**). Opcional **`SLACK_MENTION_USER_ID`**. Agende uma tarefa **diária** no Windows se quiser avisos sem abrir o Cursor. **Cron no GitHub** não lê o seu `docs/private/` — fluxo **local-first**. No chat: token **`x-pace-check`** (lembrar) e **`x-posted`** (validar depois de publicar); ver `docs/private/social_drafts/editorial/OPERATOR_X_PACE_AND_VALIDATION.pt_BR.md`.

Script base: [scripts/kpi-export.py](../../scripts/kpi-export.py) (requer `gh auth`). **Extensão em backlog:**

- Workflow **semanal** ou `workflow_dispatch`: gerar `kpi_snapshot.md`, **artefato**, ou enviar trecho ao **Slack** e/ou **Signal** (nunca Telegram nesta política de mantenedor).
- Evitar commit de snapshots com dados sensíveis; retenção curta de artefatos.

Ver [PLAN_READINESS_AND_OPERATIONS.md](../plans/PLAN_READINESS_AND_OPERATIONS.md) §4.7.

---

## 7. Resumo fim do dia / fim do sprint (SMS, e-mail, chat)

**O que o assistente não faz:** O agente no Cursor **não** envia **SMS** nem **e-mail** para o seu celular ou caixa de entrada. Não há integração com operadora ou SMTP a partir do chat. Qualquer “aviso” precisa rodar no **seu** ambiente: **GitHub Actions**, um **servidor em casa** ou um **script** que você executa na máquina.

## O que dá para montar (padrão recomendado):

| Parte                    | Opções                                                                                                                                                                                                                                                                                          |
| -----                    | ------                                                                                                                                                                                                                                                                                          |
| **Gatilho**              | **`workflow_dispatch`** (“enviar resumo agora”), **cron** (ex.: dias úteis 18h no seu fuso) para fim do dia, ou **no merge de release** / regra de calendário para fim de sprint.                                                                                                               |
| **Resumo curto**         | Primeiras linhas de **`git log`** desde a última tag ou `--since=…`; opcional **`python scripts/plans-stats.py`** para contagens do painel de planos; um parágrafo com “principais ações / principais mudanças” (você ou um modelo preenche).                                                   |
| **Release notes**        | Link para **`docs/releases/X.Y.Z.md`** no `main` (ou **artefato** do workflow); não colar segredos nem URLs internas.                                                                                                                                                                           |
| **Progresso / visão PM** | Colar a tabela **Kanban** de [SPRINTS_AND_MILESTONES.pt_BR.md](../plans/SPRINTS_AND_MILESTONES.pt_BR.md) ou um bloco **Mermaid `gantt`** em **texto puro** na mensagem. O assistente pode **rascunhar** esse Markdown no chat; o **CI** envia — sem copiar na mão se o workflow montar o corpo. |
| **SMS**                  | API **HTTP** (ex.: **Twilio**); **secrets** no GitHub para credenciais; custo e conformidade são **seus**.                                                                                                                                                                                      |
| **E-mail**               | SMTP via Action (ex.: **`dawidd6/action-send-mail`**) ou API REST do provedor; **secrets** para credenciais.                                                                                                                                                                                    |
| **Menos atrito**         | Webhook do **Slack** e/ou **Signal** via `curl` à ponte na LAN (como nas §2–§4) — muitas vezes basta para “fim do dia” sem taxa de SMS.                                                                                                                                                           |

**Twilio (API de SMS — opcional):** **Twilio** é um provedor americano de **CPaaS** (*Communications Platform as a Service*): uma **API HTTP** para enviar **SMS** em vários países sem contrato direto com cada operadora — por isso aparece muito em tutoriais e combina com **GitHub Actions** ou um script **`curl`**. Em geral você paga **por mensagem** (e às vezes por **número de origem**); o valor depende do **país de destino** e do produto — use a página oficial de **[preços de SMS da Twilio](https://www.twilio.com/en-us/messaging/pricing)** (EN) para orçar, **não** um valor fixo neste documento. **Alternativas:** **AWS SNS**, **Vonage** ou **provedores locais** na sua região. Os dados trafegam na infra da Twilio (**EUA** e outros); separar regras de SMS **comercial** de avisos **operacionais pessoais**; envolver **jurídico / DPO** se a organização exigir.

**Separação de escopo:** resumos para **mantenedor** (esta seção) são distintos de notificações de **produto** (scan terminou, webhooks para inquilinos) — ver **Notifications** em [PLANS_TODO.md](../plans/PLANS_TODO.md) (ordem 6).

**Padrão local (Docker + volume):** Rode **signald** / **signal-cli** ou um cliente de SMS **no seu PC ou homelab**. Mapeie **credenciais e dados de sessão** no container com **volumes** apontando para um diretório **fora do Git** — por exemplo **`docs/private/notify/`**, criado a partir do modelo versionado **[private.example/notify/README.md](../private.example/notify/README.md)**. Coloque **`.env`**, estado do Signal e qualquer dado pessoal **só** aí. **Dispare** o envio com um **script que você executa** (ou agendador local); o repositório permanece sem segredos. **Outros colaboradores** repetem o **mesmo arranjo** em **`docs/private/notify/`** com **chaves e números próprios** — nada sensível circula pelo Git.

---

## 8. Documentos relacionados

- [private.example/notify/README.md](../private.example/notify/README.md) — modelo de layout local (copiar para `docs/private/notify/`).
- [BRANCH_AND_DOCKER_CLEANUP.md](BRANCH_AND_DOCKER_CLEANUP.md) — higiene; §7 remote legado.
- [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) — faixa A.
- [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) — `origin` vs legado.
- Cursor: **`.cursor/rules/operator-notification-channels.mdc`** e **`.cursor/skills/operator-notification-channels/SKILL.md`**.

---

*Última atualização: política do mantenedor — sem Telegram para o Data Boar; Signal como única alternativa de chat ao Slack; tabela Slack vs Signal.*
