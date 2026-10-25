# Completão — biblioteca de prompts do operador (taxonomia + arranques finos)

**English:** [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)

## Objetivo

Separar **três camadas** para não colar um bloco enorme em toda sessão:

1. **Token de sessão (inglês, só na linha 1):** **`completao`** — já definido em **`.cursor/rules/session-mode-keywords.mdc`** e no **[`AGENTS.md`](../../AGENTS.md)**.
2. **Atalho de *tier* (linha 2):** um **código curto** definido nesta página — diz ao assistente qual fatia e qual linha de comando preferir.
3. **Prosa pesada (opcional):** os blocos **A–E** completos no **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** — use quando mudar contratos ou precisar de desvio pontual.

**Automação:** na raiz do repo, **`.\scripts\completao-chat-starter.ps1`** imprime um arranque **mínimo** (**`completao`** + linhas **`tier:`** / às vezes **`semver:`** / **`tag:`**) e um comando sugerido opcional. **`.\scripts\completao-chat-starter.ps1 -Help`** lista os *tiers*. Para outras releases: **`-Tier release-master -ReleaseSemver 1.7.4`** (e **`-GitTag`**, se a tag não for **`v` + semver**).

**Prompt longo privado:** se a narrativa tiver caminhos reais ou preferências, guarde só em **`docs/private/homelab/`** — modelo com placeholders: **[`../private.example/homelab/COMPLETAO_OPERATOR_PROMPT.example.md`](../private.example/homelab/COMPLETAO_OPERATOR_PROMPT.example.md)** (seguro para versionar).

## Taxonomia de *tier* (linha 2 depois de `completao`)

| Código de *tier* | Intenção | O assistente deve… |
| ---------------- | -------- | ------------------- |
| **`tier:smoke`** | Smoke padrão — só orquestrador; clones do LAB como estão salvo **`completaoTargetRef`** no manifest | Correr **`lab-completao-orchestrate.ps1 -Privileged`** (sem **`-LabGitRef`** salvo se você acrescentar na linha 3). |
| **`tier:smoke-main`** | Smoke reprodutível vs **`origin/main`** | Correr **`-LabGitRef origin/main`** (verificação **`lab-op-git-ensure-ref`** antes do smoke). |
| **`tier:smoke-tag`** | Fixar em tag **`vX.Y.Z`** | Correr **`-LabGitRef vX.Y.Z -SkipGitPullOnInventoryRefresh`** — ver **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** (*Target git ref*). |
| **`tier:followup-repo`** | Depois do smoke — *drift* de repo só leitura | Igual ao bloco **B** do **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** (**`lab-op-repo-status.ps1`**). |
| **`tier:followup-poc`** | Fatias pytest POC no Windows | Igual ao bloco **C**. |
| **`tier:followup-cli`** | Avaliação externa / CLI | Igual ao bloco **D** + **[`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`](LAB_EXTERNAL_CONNECTIVITY_EVAL.md)**. |
| **`tier:closure-min`** | Fechamento minimo pos-sessao (mais que smoke, menos que "tudao") | Completar os 3 pendentes principais: (1) repetir CLI soup em pelo menos mais 1 host alem de `lab-node-02`; (2) validar API + dashboard com `GET /health` + `GET /`; (3) consolidar nota privada + lições aprendidas da rodada. |
| **`tier:coverage-plus`** | Cobertura ampliada (ingestoes + scanner + API + dashboard + conectores) | Executar `smoke` + expandir matriz por host/target (FS, DB, API, conectores viaveis), mapear falhas por severidade e abrir plano de correcoes antes do rerun. |
| **`tier:evidence`** | Fechar notas para a próxima sessão | Igual ao bloco **E**. |
| **`tier:release-master-v1-7-3`** | Atalho **congelado** para o checklist **1.7.3** (mesmo objetivo que **`release-master`** com **`semver:1.7.3`**) — **ler** **[`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md`](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md)** ([EN](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md)) **antes** de executar | Igual a **`tier:release-master`** na 1.7.3; mantido para transcrições estáveis |
| **`tier:release-master`** | Checklist-mestre **SRE / release** parametrizado — nas **linhas 3–4** use **`semver:X.Y.Z`** e **`tag:vX.Y.Z`** (ou **`tag:v1.7.2-safe`** quando a tag não for só **`v` + semver**). **Doc:** o starter resolve **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<semver>.md`** se existir, senão **[`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md`](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md)**; ao arquivar release nova, acrescente o par **`.pt_BR.md`** com o mesmo nome base | Rode **`.\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver 1.7.4`** (opcional **`-GitTag …`**); alinhe saídas a **`docs/private/homelab/reports/`** conforme o doc que abrir |

**Sintaxe:** linha 2 = uma linha de *tier*, ex. **`tier:smoke-main`**. Com **`tier:release-master`**, as linhas **3–4** são **`semver:…`** e **`tag:…`** (o **`completao-chat-starter.ps1`** imprime isso). Linhas seguintes opcionais: **`token-aware`**, **`short`**, flags pontuais. **Não** junte branch/versão na **linha 1** — a taxonomia de sessão está em **`session-mode-keywords.mdc`**.

## Arranque fino (exemplo para colar)

```text
completao

tier:smoke-main
```

Depois, na raiz do repo (você ou o assistente):

```powershell
.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main
```

O assistente segue **`lab-completao-workflow.mdc`**, lê **`docs/private/homelab/reports/`** quando existir e **não** pede permissão redundante para SSH/**`-Privileged`**.

## Sequenciamento gradual (v1.7.3) para "completão de verdade"

Use este fluxo quando o objetivo for "descobrir falha em tudo" sem começar com prompt gigante:

1. **Baseline (smoke reproduzível):**

```text
completao

tier:smoke-tag
semver:1.7.3
tag:v1.7.3
```

1. **Fechamento minimo (3 pendencias):**

```text
completao

tier:closure-min
```

1. **Cobertura ampliada (ingestao/digestao/report/API/dashboard/connectores):**

```text
completao

tier:coverage-plus
token-aware
```

1. **Rerun final:** repetir a mesma fatia corrigida (normalmente `tier:coverage-plus`) para confirmar correções e atualizar lições aprendidas.

> **Rerun final "sem args"?** Pode ser sem extras quando você quer repetir exatamente a mesma fatia, mas o mais seguro é explicitar o `tier` usado no ciclo anterior.

## Matriz executável (completao + args)

| Disparo curto | Comportamento esperado | Lições aprendíveis no relatório |
| --- | --- | --- |
| `completao` + `tier:smoke` | Smoke base multi-host com `lab-completao-orchestrate.ps1 -Privileged` | Reachability, ambiente quebrado, gaps de dependência/sudoers |
| `completao` + `tier:smoke-main` | Mesmo smoke, mas com clones alinhados a `origin/main` | Reprodutibilidade vs branch canônica, drift de repo |
| `completao` + `tier:smoke-tag` + `tag:vX.Y.Z` | Smoke congelado por release tag | Regressão por versão, comportamento por release |
| `completao` + `tier:closure-min` | Fecha mínimos: CLI soup em host extra + API/dashboard (`/health` e `/`) + nota privada | Diferenças entre hosts, precedência/config real, lições imediatas |
| `completao` + `tier:coverage-plus` | Cobertura ampliada por matriz host/target (FS/DB/API/conectores), severidade e plano de rerun | Falhas por camada (script/produto/API/conector/docs/dashboard) e priorização de melhorias |
| `completao` + `tier:followup-repo` | Auditoria de drift de clones LAB | Confiabilidade de baseline para próximos ciclos |
| `completao` + `tier:followup-poc` | Fatias POC (`smoke-maturity`, `smoke-webauthn`) | Quebra de features não-funcionais e contrato de segurança |
| `completao` + `tier:followup-cli` | Foco em avaliação CLI/external connectivity | Lacunas de ingestão, conectividade e mensagens operacionais |
| `completao` + `tier:evidence` | Consolidação de evidências e lições em `docs/private/homelab/` | Histórico comparável entre rodadas, backlog acionável |

**Vale o investimento?** Sim, porque reduz carga cognitiva e torna o completão repetível. A regra prática: usar `tier:closure-min` no dia a dia, `tier:coverage-plus` quando a meta for caçar falha estrutural.

## Dicionário de falhas comuns (engenharia de *prompt*)

**Objetivo:** Antes de propor correções, classificar o sinal para que assistentes autônomos (Cursor, Gemini, etc.) **não** troquem camadas. Na dúvida, declarar **as duas** hipóteses e que evidência as separa.

### *Timeout* (rede / transporte)

- **Sinais típicos:** `Connection timed out`, `ConnectTimeout`, `ETIMEDOUT`, `timed out`, comando preso sem *stderr* útil até matar, `ssh` aparentemente parado, perda em `fping` / `ping`, *timeout* de `Invoke-WebRequest`, cliente de base à espera do servidor até estourar tempo.
- **O que normalmente *não* é:** pedido de senha, `Permission denied (publickey)`, ou *traceback* Python apontando linha concreta do **seu** repo no PC de desenvolvimento **antes** de I/O remoto útil.
- **Viés de primeira resposta:** verificar **alcance** (host ligado, *jump host* / VLAN corretos, IP do orquestrador não bloqueado no fail2ban), depois **latência** (redes lentas podem precisar de `ConnectTimeout` maior ou *timeouts* do próprio tool), depois comparar `connectivity_status` e `performance_metrics` em **`lab_result.json`** entre corridas (ver **[`LAB_COMPLETAO_RUNBOOK.pt_BR.md`](LAB_COMPLETAO_RUNBOOK.pt_BR.md)** — *Resumo legível por agente*).

### *Auth* (credenciais / identidade / confiança)

- **Sinais típicos:** `Permission denied (publickey)`, `Authentication failed`, `Host key verification failed`, `Permission denied (password)` em modo interativo, HTTP **401** / **403**, `sudo: a password is required` ou `sudo: no tty` quando esperava `sudo -n`, falhas de confiança TLS / certificado em HTTPS.
- **O que normalmente *não* é:** paragem silenciosa sem mensagem de autenticação (família *timeout*); `SyntaxError` num manifesto local antes de chamada de rede concluir com sentido.
- **Viés de primeira resposta:** corrigir **chaves** / agente (`ssh-add -l`), **known_hosts**, segredos no cofre, **sudoers** estreito no host de lab (modelos ficam **privados** — nunca colar sudoers reais no GitHub público), e **aliases** do manifesto alinhados a `~/.ssh/config`.

### *Parser* / contrato (código / esquema / forma da config)

- **Sinais típicos:** `JSONDecodeError`, erros do *scanner* YAML, `unexpected token`, `SyntaxError`, `jq: parse error`, SQL com **nome de coluna inválido** depois de conectar, orquestrador que falha porque o arquivo de contrato **referenciado** está ausente ou malformado.
- **O que normalmente *não* é:** SSH falha de imediato com *publickey* (família *auth*); *hang* de rede puro sem *frame* de *parser*.
- **Viés de primeira resposta:** validar o **artefato** (JSON / YAML / contrato SQL), **fixar refs** ao comparar corridas, repetir o comando mínimo que falha isolado, e combinar diffs de **`lab_result.json`** com `*_completao_host_smoke.log` desse `sshHost`.

### Etiqueta opcional no *chat* (depois do `tier:…`)

Exemplo:

```text
failure-class:timeout
```

Use **`timeout`**, **`auth`**, **`parser`** ou **`unknown`** quando quiser que o assistente **comece** pelo *playbook* certo em vez de adivinhar.

## Taxonomia de interpretação (severidade por contexto, não só “verde / vermelho”)

**Objetivo:** levar o assistente de “bateu regex de CPF” a “o que esse *match* significa para risco e resposta?” — mais próximo de leitura de achados em consultoria / assurance.

1. **Mesmo token, outro raio de explosão:** padrão de documento de identidade em **log de aplicação *append-only*** (efémero, rotação, leitores com least privilege) **não** é a mesma classe de severidade que o mesmo padrão em export de tabela **`users` / `customers` / registro de titulares`**, *dump* de ticket ou **backup de longa duração** fora do site. Prefira documentar a **classe de local** (fluxo de log vs repositório de identidade vs planilha de marketing vs anexo de ticket) antes de discutir prioridade.
2. **Volume e retenção:** muitos acertos em buffer **efémero** vs poucos em arquivo **durável** mudam retenção e narrativa de processo mesmo com o mesmo regex.
3. **Controlador vs operador de dados:** achado em **fixture de lab sob controlo do operador** vs amostra **representativa de cliente** muda o remédio (purgar corpus de lab vs reenquadrar conector de produção). Amarre ao *capability matrix* do **[`LAB_COMPLETAO_RUNBOOK.pt_BR.md`](LAB_COMPLETAO_RUNBOOK.pt_BR.md)** e a notas **privadas** — **não** invente fatos de cliente.
4. **Amarrar a semântica de *exit*:** depois de classificar o contexto, alinhe o follow-up operacional a **`DATA_BOAR_COMPLETAO_EXIT_v1`** no runbook (infra vs contrato de dados vs código **3** reservado a compliance) para gates de release e **[`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md`](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md)** continuarem legíveis por máquina.

## Quando usar os blocos A–E completos

Use os blocos literais do **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** quando:

- Mudar semântica do **manifest**, caminhos de **sudoers** ou texto de **blast-radius**.
- Precisar de instrução **pontual** (um host, saltar inventário, etc.).
- Estiver a integrar um **humano** que ainda não confia na linha fina de *tier*.

## Ligações

- **Prompt-mestre de checklist de release (arquivo 1.7.3 + *tier* parametrizado):** [COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md) ([EN](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md)); cópias por semver: **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<semver>.md`** (ver **`completao-chat-starter.ps1 -Tier release-master`**)
- **Escada de arranque:** [OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) ([EN](OPERATOR_AGENT_COLD_START_LADDER.md))
- **Personas:** [LAB_OP_HOST_PERSONAS.pt_BR.md](LAB_OP_HOST_PERSONAS.pt_BR.md) ([EN](LAB_OP_HOST_PERSONAS.md))
- **Runbook (inclui `lab_result.json`, Rastro de Auditoria (Audit Trail), contrato de *exit code*):** [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md) ([EN](LAB_COMPLETAO_RUNBOOK.md))
- **Mapa de scripts:** [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md) ([EN](TOKEN_AWARE_SCRIPTS_HUB.md))
