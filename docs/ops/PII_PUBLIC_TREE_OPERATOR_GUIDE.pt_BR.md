# Guia do operador — PII na arvore publica (canonico)

**English:** [PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md)

**Fonte unica de verdade:** Este arquivo consolida os documentos antigos **`PII_VERIFICATION_RUNBOOK`**, **`PII_DEFINITIVE_REMEDIATION`** e **`GITHUB_FORK_CLONE_VISIBILITY_AND_OPERATOR_AUDIT`**. Esses caminhos permanecem como **redirecionamentos permanentes** para que links e ADRs continuem validos; **edite o procedimento apenas aqui** para evitar drift.

**Público:** Mantenedor / operador com permissão de push no repositório canônico no GitHub (substitui **`OWNER`** pelo usuário ou organização dono do repo — ex.: `OWNER/data-boar`).

**Ritual sob demanda (HEAD + seeds privados, consciente de tokens):** Quando a equipe **decide** rever literais acidentais sem esperar pela próxima cadência de calendário, seguir **[PII_REMEDIATION_RITUAL.pt_BR.md](PII_REMEDIATION_RITUAL.pt_BR.md)** ([EN](PII_REMEDIATION_RITUAL.md)) — palavra-chave de sessão **`pii-remediation-ritual`**. Complementa a Parte I abaixo; **não** substitui o checklist **SAFE** nem **`pii-fresh-audit`** para prova nível release em clone fresco.

---

## 0. Trilha de evidencias (imutavel — nao reescreva o historico)

Estes ADRs registram **decisoes e cronologia**; o texto nao e duplicado aqui:

| ADR | Tema |
| --- | ----- |
| [0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) | Guardrails anti-recorrencia para arquivos rastreados e historico de branch |
| [0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) | Cadencia de verificacao e gate de revisao manual |
| [0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) | CI full-history `pii_history_guard` |

Regra do assistente / Cursor: **`.cursor/rules/public-tracked-pii-zero-tolerance.mdc`**.

---

## Parte I — Cadencia de verificacao (curta / media / longa)

Runbook operacional para verificar PII/dados sensiveis em repositorio publico com cadencia curta, media e longa.

## Gate de revisao manual (obrigatorio)

Antes de marcar qualquer execucao como SAFE, revise os criterios locais/privados que nao ficam em docs versionados.

- [ ] Revisei os criterios locais atuais em `docs/private/security_audit/` (esse caminho **nao** vem no clone publico; use [`docs/private.example/security_audit/`](../private.example/security_audit/README.md) ou outro canal do maintainer).
- [ ] Atualizei seeds locais de allow/deny (se necessario) em notas/arquivos privados.
- [ ] Confirmei que nenhum novo identificador sensivel precisa entrar nos guardrails versionados.

Se algum item estiver desmarcado, **nao** marque SAFE.

## Escopo e objetivo

- Este runbook cobre arquivos tracked e historico Git em **clone fresco**.
- Ele complementa os guardrails (`new-b2-verify`, `pii_history_guard.py`, `test_pii_guard.py`).
- Ele nao substitui classificacao manual para termos contextuais.
- `new-b2-verify.ps1` e somente PowerShell (ideal no PC Windows principal de desenvolvimento/Windows). Em Linux, use o equivalente manual abaixo.

## 0) Pre-condicoes

Executar em clone fresco:

```powershell
cd C:\temp
if (Test-Path .\teste_operator_fresh) { Remove-Item -Recurse -Force .\teste_operator_fresh }
mkdir teste_operator_fresh | Out-Null
cd .\teste_operator_fresh
git clone git@github.com:OWNER/data-boar.git
cd .\data-boar
git status
```

Esperado: working tree limpo em `main`.

### Linux (hosts lab-op)

```bash
cd /tmp
rm -rf teste_operator_fresh
mkdir -p teste_operator_fresh
cd teste_operator_fresh
git clone git@github.com:OWNER/data-boar.git
cd data-boar
git status
```

Esperado: working tree limpo em `main`.

### Bundle privado `security_audit` (ausente apos clone)

`docs/private/` e **gitignored**; um `git clone` normal **nao** cria `PII_LOCAL_SEEDS.txt`. Se `grep` ou `mapfile` falhar com **No such file or directory**, crie o diretorio e copie o exemplo:

```bash
mkdir -p docs/private/security_audit
cp docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edite PII_LOCAL_SEEDS.txt com literais aprovados pelo maintainer (uma por linha).
```

```powershell
New-Item -ItemType Directory -Force -Path docs/private/security_audit | Out-Null
Copy-Item docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edite PII_LOCAL_SEEDS.txt com literais aprovados pelo maintainer (uma por linha).
```

## 1) Short run (semanal / antes de PR sensivel)

```powershell
.\scripts\new-b2-verify.ps1 -TargetUserSegment <USERNAME>
uv run python .\scripts\pii_history_guard.py
uv run pytest tests/test_pii_guard.py -q
# Rode o grep de padrao UC a partir do seu bundle local/privado de criterios.
git grep -n -E "\b(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})\b" -- scripts docs tests .cursor
git grep -n -E "\b[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}\b" -- scripts docs tests .cursor
```

Condicao de PASS: sem match relevante + testes OK.

### Linux (equivalente ao `new-b2-verify.ps1`)

```bash
TARGET_SEGMENT="<USERNAME>"
TARGET_PATH_UPPER="C:\\Users\\${TARGET_SEGMENT}"
TARGET_PATH_LOWER="c:\\users\\${TARGET_SEGMENT}"

git log --all -S "${TARGET_PATH_UPPER}" --oneline
git log --all -S "${TARGET_PATH_LOWER}" --oneline
git grep -n -i -F "${TARGET_PATH_UPPER}" $(git rev-list --all)

uv run python ./scripts/pii_history_guard.py
uv run pytest tests/test_pii_guard.py -q
# Rode o grep de padrao UC a partir do seu bundle local/privado de criterios.
git grep -n -E "\b(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})\b" -- scripts docs tests .cursor
git grep -n -E "\b[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}\b" -- scripts docs tests .cursor
```

## 2) Mid run (mensal)

```powershell
git grep -n -E "linkedin\.com/in/" -- . ":(exclude)docs/private/**"
git grep -n -i -E "c:\\users\\[^\\]+|/home/[^/]+" -- . ":(exclude)docs/private/**"
```

Depois, classificar cada hit como:

- placeholder/teste/exemplo aceitavel; ou
- exposicao real sensivel que exige correcao imediata.

## 3) Long run (trimestral ou pos-incidente)

Rodar checagens de historico completo para seeds de alto risco relevantes para sua politica privada:

```powershell
git log --all -S "C:\Users\<USERNAME>" --oneline
git log --all -S "c:\users\<USERNAME>" --oneline
git log --all -S "/home/<LINUX_USER>" --oneline
git log --all -S "example.com/profile/" --oneline
# Rode a verificacao de seed UC a partir do seu bundle local/privado de criterios.
# Opcional: uma passagem por todas as linhas de docs/private/security_audit/PII_LOCAL_SEEDS.txt:
# .\scripts\run-pii-local-seeds-pickaxe.ps1
```

Mantenha qualquer seed especifica de pessoa/caso apenas em notas/arquivos privados.

## Termos sensiveis ao contexto (classificacao manual)

Alguns termos podem ser permitidos somente em contexto restrito (por exemplo, contexto de carreira/portfolio), e nao em contexto juridico/medico/privado.

Quando esses termos aparecerem:

1. classifique por contexto;
2. registre a decisao em notas privadas;
3. corrija arquivos tracked se o contexto nao for permitido.

## Decisao final de SAFE

Marque SAFE somente se:

- o gate de revisao manual estiver totalmente marcado;
- o short run passar;
- as checagens mid/long nao mostrarem exposicao real;
- os termos contextuais tiverem classificacao manual concluida.

Se algum criterio falhar, o status e NOT SAFE e exige remediacao cirurgica + novo ciclo de validacao.

---

## A. Pré-condições

1. **Backup:** `scripts/run-pii-history-rewrite.ps1` cria um **mirror** na pasta pai do repo antes de reescrever. Mantenha-o até o `main` estar verde e os clones atualizados.
2. **Ferramentas:** `git`, `git-filter-repo` no PATH, `uv` (testes), rede para `origin`.
3. **Árvore limpa** antes da reescrita: commit ou stash de alterações intencionais.

---

## B. Higiene no mesmo dia (sem reescrever histórico)

Quando você só precisa alinhar **arquivos rastreados atuais** e o guard **incremental**:

```powershell
cd C:\caminho\para\data-boar
git fetch origin
git pull origin main
uv sync
uv run pytest tests/test_pii_guard.py tests/test_talent_public_script_placeholders.py tests/test_talent_ps1_tracked_no_inline_pool.py -q
uv run python scripts/pii_history_guard.py
```

**Linux no lab** (sem `uv` no PATH): `python3 -m pytest …` se o pytest estiver instalado, ou instalar `uv` conforme documentação do projecto.

---

## C. Reescrita completa do histórico (destrutiva no remoto após push)

Correr **só** depois de integrar guards + regras de substituição no `main` (este repo inclui `scripts/filter_repo_pii_replacements.txt`).

**Política de host:** **Não** correr este fluxo na estação de trabalho principal **L-series** — usar uma **máquina de lab** acordada (ver **[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md)**). O script **recusa** iniciar sem **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** na sessão PowerShell (nunca como rotina no PC Windows principal de desenvolvimento).

1. **Commit** de todas as alterações rastreadas pretendidas (guards, substituições, docs).
2. No host **que não seja o PC Windows principal de desenvolvimento**, na raiz do repo:

```powershell
$env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS = "1"
.\scripts\run-pii-history-rewrite.ps1
```

3. Inspecione o caminho **`data-boar-history-rewrite-*`** reportado. Se `pytest` e `pii_history_guard --full-history` estiverem verdes, você pode fazer push (mesma variável de ambiente):

```powershell
$env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS = "1"
.\scripts\run-pii-history-rewrite.ps1 -Push
```

4. **Imediatamente após qualquer force-push público:**
   - **Apagar branches remotas obsoletas** no GitHub que ainda apontem para SHAs **pré-reescrita** (senão a CI ou `pii_history_guard --full-history` ainda podem ver blobs antigos).
   - **Cada clone** (teu, lab, colaborador):

```bash
git fetch origin
git reset --hard origin/main
git fetch --prune
```

5. **Forks (ex.: colaborador):** o dono precisa **apagar o fork** ou **recriar / alinhar** com o `main` atual. Você não pode corrigir o object database do fork a partir do upstream.

---

## D. Matriz de verificação (após push)

| Verificação | Comando |
| ----------- | ------- |
| Guard do índice | `uv run pytest tests/test_pii_guard.py -q` |
| Placeholders talent | `uv run pytest tests/test_talent_public_script_placeholders.py tests/test_talent_ps1_tracked_no_inline_pool.py -q` |
| Histórico completo | `uv run python scripts/pii_history_guard.py --full-history` |
| Seeds opcionais | Manter seeds **privados** em `docs/private/security_audit/PII_LOCAL_SEEDS.txt` (fora do Git). Usar `git log --all -S "…"` só na máquina do mantenedor — ver **Parte I** acima. |

---

## E. Editar regras de substituição

- **Arquivo:** `scripts/filter_repo_pii_replacements.txt`
- **Formato:** substituições do `git filter-repo`; linhas `#` são comentários; `regex:…==>…` para padrões.
- **Depois de editar:** volte a rodar a **seção C** (reescrita + testes) antes do próximo force-push.

---

## F. Documentos relacionados

- **Parte III** abaixo — visibilidade de fork vs clone.
- **Parte I** acima — cadência e grep manual.
- [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md) — sem narrativas sensíveis em PR/commit.
- [ADR 0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) — gate de histórico completo na CI.
- [COLLABORATION_TEAM.pt_BR.md](../COLLABORATION_TEAM.pt_BR.md) — fluxo fork / PR do colaborador.

---

## G. O que já está neste repositório (fecho de engenharia)

Isto **já está no `main`** no arco de higiene PII (não refazer salvo mudança de política):

| Item | Onde / comportamento |
| ---- | ---------------------- |
| Scan do índice + caminhos | `tests/test_pii_guard.py` — arquivos rastreados; prefixos permitidos incluem `docs/private.example/` etc. |
| Scan de histórico completo | `scripts/pii_history_guard.py` — ignora linhas `+` sob `docs/private.example/`; placeholder LinkedIn com crase em Markdown; regex SSH ignora estilo `user@myserver.example.com` |
| Placeholders talent | `tests/test_talent_public_script_placeholders.py`, `tests/test_talent_ps1_tracked_no_inline_pool.py` |
| Arquivo de regras `filter-repo` | `scripts/filter_repo_pii_replacements.txt` — válido para `--replace-text` / `--replace-message` |
| Automação de reescrita | `scripts/run-pii-history-rewrite.ps1` — nova reescrita só se mudar regras |
| CI | Workflows correm `pii_history_guard --full-history` após testes (ver ADR 0020) |
| Docs de ops | Este guia (copia canonica unica); nomes legados redirecionam para ca |

**Não substitui:** backups privados teus, revisão externa (ex.: WRB), nem apagar o fork do colaborador.

---

## H. Checklist do operador — executar (assumido obrigatório até estar feito)

Ordem sugerida. **Nenhum passo é opcional** se quiser fecho organizacional, não só “testes verdes num portátil.”

### H.1 Gate completo no PC Windows (clone canônico)

```powershell
cd C:\caminho\para\data-boar
git fetch origin
git pull origin main
.\scripts\check-all.ps1
```

Se falhar, corrige ou abre PR com âmbito fechado antes de declarar higiene de release completa.

### H.2 Confirmar CI no GitHub

1. Abrir `https://github.com/OWNER/data-boar/actions`
2. Confirmar que o último workflow no **`main`** está **verde** (todos os jobs).

### H.3 Lab e clones secundários (máquinas que você controla)

Em **cada** host onde `data-boar` está clonado (outros **lab-op**, estações de trabalho ou SBCs sob o teu controlo — **nomes reais só** em **`docs/private/homelab/`**, não em runbooks públicos):

```bash
cd ~/Projects/dev/data-boar   # ou o teu caminho real
git fetch origin
git reset --hard origin/main
git fetch --prune
```

Depois correr os mesmos guards da **seção D** com `python3` se não houver `uv`:

```bash
python3 scripts/pii_history_guard.py --full-history
```

Instalar `uv` nesses hosts quando fizer sentido para igualar ao Windows.

### H.4 Fork do colaborador (fork público conhecido)

1. Listar forks:

```bash
gh api repos/OWNER/data-boar/forks --paginate --jq '.[] | {owner: .owner.login, full_name, pushed_at, updated_at}'
```

2. **Você** contacta o dono do fork: histórico upstream / guards mudaram; ele deve **apagar o fork** ou **voltar a sincronizar** com o `main` atual (ver **Parte III** e [COLLABORATION_TEAM.pt_BR.md](../COLLABORATION_TEAM.pt_BR.md)).

3. **Você não pode** apagar o fork da conta dele pelo seu login.

### H.5 Varredura na UI do GitHub (issues, PRs, discussions)

A automação **não** reescreve corpos de issue/PR. **Manualmente** pesquisa no repositório no GitHub por padrões que te importem (nomes, caminhos, palavras-chave de caso) e edita ou abre follow-up. **Não** colocar narrativa sensível em issues públicas daqui para a frente ([COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md)).

### H.6 Revisão externa (WRB ou equivalente)

- Usar runbooks e docs de produto **rastreados** como evidência.
- **Não** colar conteúdo do dossier, seeds privados ou detalhes de LAN em issues públicas ou formulários de revisão.

### H.7 Backups privados e estado da aplicação

- Comparar **offline** os seus backups ao comportamento atual **fora** deste repositório; nenhum assistente ou CI audita discos que não estejam no seu fluxo de trabalho.

### H.8 Directórios temporários de clone (higiene)

- Apagar clones temporários criados para inspecionar forks (ex.: `%TEMP%`, `/tmp`) quando o espaço ou a disciplina o exigirem.

### H.9 Opcional: `clean-slate.sh` no lab (várias rodadas até os guards baterem com a intenção)

**Script canônico (árvore privada do operador):** `docs/private/scripts/clean-slate.sh` com **`docs/private/scripts/README.pt_BR.md`** — instalar em **`~/clean-slate.sh`** em cada máquina Linux de lab que controles. **Modelo rastreado (sem segredos):** `docs/private.example/scripts/clean-slate.sh.example` e **`docs/private.example/scripts/README.md`**.

**Nomes:** nos docs públicos do GitHub o exemplo SSH é **`lab-op`**. **Nomes reais de máquinas** na tua LAN ficam **só** em **`docs/private/`** (ver **`PRIVATE_OPERATOR_NOTES.md`** e **`docs/private/homelab/`**), não em runbooks rastreados do produto.

**Não** uses este fluxo destrutivo na estação principal **L-series** — só em **hosts de lab** que controles para esse fim (**[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md)**).

Se usares `~/clean-slate.sh` num host Linux de lab:

1. **Antes:** garanta que **`docs/private/security_audit/PII_LOCAL_SEEDS.txt`** no seu workspace está atualizado (ou define **`PII_SEEDS_FROM_SCP`** no ambiente para o modelo fazer **`scp`** de seeds canônicos de outro host de lab após o clone quando a árvore privada empilhada ainda não existir). O script atualiza **`~/.config/PII/PII_LOCAL_SEEDS.txt`** a partir do caminho no workspace quando existir.
2. **Corre** `~/clean-slate.sh` — é **destrutivo** (remove a árvore local `data-boar` e volta a clonar). Só quando aceitares re-download completo e o custo do guard de histórico completo.
3. **Depois de cada execução**, no clone novo: `python3 scripts/pii_history_guard.py --full-history` (e o teu **`git grep`** / checks de seeds habituais conforme a **seção D**).
4. **Repete** em **cada** host de lab com clone, e **volta a correr** quando **`PII_LOCAL_SEEDS`** ou o **`main`** público mudar, até os guards deixarem de falhar — uma passagem verde não basta.

**Remediação:** fugas no histórico **público** exigem **redação / filter-repo** e follow-up com contribuidores (outras seções); o `clean-slate.sh` valida clones **novos**, não espelhos de terceiros.

### H.10 `clean-slate` e assistentes: gancho de memória (autoauditoria, não simulação)

**Porquê esta subseção:** Operador e assistente **não** devem confundir (a) **narrativa no chat** (“corri clean-slate N vezes”) com (b) um reset **real** + reclone no disco. O valor de auditoria do `clean-slate` é: uma **árvore de trabalho limpa** alinhada ao `origin/main` após download completo — e os guards dizem se a política bate com a realidade.

| Pergunta | Resposta |
| -------- | -------- |
| **Onde está o script?** | **Modelo rastreado:** [`docs/private.example/scripts/clean-slate.sh.example`](../private.example/scripts/clean-slate.sh.example). **Cópia do operador (git privado, não no GitHub):** `docs/private/scripts/clean-slate.sh`. **Texto:** [`docs/private.example/scripts/README.md`](../private.example/scripts/README.md). |
| **Uso em lab Linux** | Instalar em `~/clean-slate.sh` conforme **H.9**. Garantir `docs/private/security_audit/PII_LOCAL_SEEDS.txt` (ou `PII_SEEDS_FROM_SCP`) antes da execução. |
| **Equivalente Windows** | **`scripts/pii-fresh-clone-audit.ps1`** — clone completo sob `%TEMP%`, depois **`uv sync`**, **`pii_history_guard.py --full-history`**, **`pytest tests/test_pii_guard.py`** (ver **[PII_FRESH_CLONE_AUDIT.pt_BR.md](PII_FRESH_CLONE_AUDIT.pt_BR.md)**). Caminho manual: pasta vazia + `git clone` + mesmos comandos da **seção D**. Palavra-chave de sessão: **`pii-fresh-audit`**. |
| **O que valida** | **Clone fresco + guards** — bom sinal de que o **`main` atual** e o histórico (como obtido por fetch) passam a automação. |
| **O que *não* faz** | **Não** remove blobs sensíveis já enviados (usar **Parte II** / `run-pii-history-rewrite.ps1`). **Não** substitui o CI — o CI já corre o guard de histórico completo no push. |

**Quantas vezes correr:** Repetir em cada host controlado quando mudarem **regras dos guards**, **seeds** ou **tabelas de substituição**, até o resultado bater com a **intenção** (mesmo espírito do passo 4 do H.9). Esse ciclo é **legítimo**; “simular” clean-slate no chat sem comandos **não** o é.

**Comportamento por defeito do assistente:** Quando perguntarem se o trabalho de PII “chega”, correr **`uv run python scripts/pii_history_guard.py --full-history`** e **`uv run pytest tests/test_pii_guard.py`** no **workspace real** sempre que possível; **depois** lembrar que um **clone fresco** (Windows: **`pii-fresh-clone-audit.ps1`** ou clone manual; Linux: **`clean-slate.sh`**) é o check periódico mais forte para árvores antigas.

---

## I. Impossível sem ti (limites duros)

| Limite | Porquê |
| ------ | ------ |
| Apagar ou repor o **fork de outra pessoa** | Permissões GitHub |
| **Lista de todos os usuários** que fizeram `git clone` | O GitHub não expõe isso em repos públicos |
| Provar que **Wayback** / cache / mirror de terceiros está limpo | Fora do âmbito do repo |
| **Resultado da WRB** | Processo humano |
| Verificar **bytes de backup privado** | Acesso físico / cofre |
| **Qualquer host de lab** offline | Rede / energia |
| Narrativa **jurídica / RH** | Fora deste runbook |

---

## Parte III — Visibilidade de fork vs `git clone` no GitHub

**Objetivo:** Dizer o que o GitHub expõe (e o que não expõe) sobre forks e clones; use com **Parte II** para limpeza.

## 1. Forks — **auditáveis**

O GitHub expõe **forks públicos** de um repositório público. Dá para listar.

**GitHub CLI** (autenticado):

```bash
gh api repos/OWNER/data-boar/forks --paginate --jq '.[] | {owner: .owner.login, full_name, pushed_at, updated_at}'
```

**Browser:** repositório → **Insights** → **Network** (grafo de forks), ou o contador de **Forks** na página inicial do repo.

**Quem pode ter cópia completa:** a base de objetos Git de cada fork no GitHub, até o dono apagar o fork ou alinhar com o seu `main` atual.

**Sua ação mínima:** identificar cada fork; avisar o dono se um fork desatualizado ainda carrega histórico pré-remediação — ele precisa apagar ou recriar / dar `reset` a partir do seu `main`; **você não apaga o fork de outra conta pelo seu login.**

---

## 2. `git clone` — **não** há auditoria por usuário no GitHub

Para repositório **público**, o GitHub **não** publica:

- lista de usuários do GitHub que rodaram `git clone`
- endereços IP de `git clone` anônimo
- inventário máquina a máquina de clones

**Por quê:** `git clone` em `https://github.com/...` ou `git@github.com:...` **não** gera um “registro de clones” que o dono do repo possa baixar por completo.

**O que existe para o dono (limitado):**

- **Insights → Traffic:** contagens **agregadas** de clones (ex.: por dia), **não** “quem.” A disponibilidade depende do produto GitHub e do seu papel no repo.
- **Stars / watchers** mostram contas que interagiram **nessas ações** — não são equivalentes a clone.

**Quem pode ter cópia completa:** qualquer pessoa que clonou enquanto o histórico antigo estava no `origin` (qualquer máquina, qualquer mirror). Você **não** obtém lista completa pelo GitHub.

**Sua ação mínima:** tratar “clones anônimos” como **fora do alcance** de auditoria exaustiva; focar em **forks visíveis**, **colaboradores que você conhece** e **máquinas que você controla** (ver §4).

---

## 3. Mirrors e CI

- **Mirrors de terceiros** (se existirem) ficam fora da lista de forks do GitHub.
- Checkouts do **GitHub Actions** são efêmeros; não substituem “quem tem clone local.”
- **Caches** longos em outro lugar (proxy corporativo, backup pessoal) não aparecem no GitHub.

---

## 4. Checklist mínimo — **só o que você precisa fazer aí**

| Passo | Ação |
| ----- | ---- |
| 1 | Rodar **`gh api .../forks`** (ou a UI web) e **anotar** cada `full_name` e `pushed_at`. |
| 2 | Para cada fork que ainda importa: **avisar o dono** — alinhar com o `main` atual ou apagar o fork (você não faz isso pelo login dele). |
| 3 | **Inventário de seus próprios dispositivos** onde você (ou quem você confia) clonou o repo: PC dev, notebooks, lab — **liste em notas privadas**, não neste doc público. Em cada um: `git fetch origin && git reset --hard origin/main` quando quiser igualar ao GitHub. |
| 4 | **Opcional:** abrir **Insights → Traffic** no GitHub (se disponível) só para **tendência** — não é lista de quem clonou. |
| 5 | Aceitar que **clones anônimos** de repo público **não** são auditáveis por completo; redução de risco é **histórico canônico reescrito + forks que você enxerga + máquinas conhecidas**. |

---

## Parte III (continuacao) — Relacionados neste guia

- **Parte II** — force-push, `filter-repo`, reset de clone.
- **Parte I** — cadência e seeds locais (arquivos privados).
