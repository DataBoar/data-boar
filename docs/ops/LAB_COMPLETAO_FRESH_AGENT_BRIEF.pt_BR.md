# Completão no lab — brief para agente Cursor novo (copy-paste)

### 🧠 REGRAS DE OURO PARA O AGENTE (v1.7.3)

- **Zero Drift de Config:** Gere arquivos `config.yaml` efêmeros em `/tmp/` para cada nó, baseando-se estritamente em **`docs/TECH_GUIDE.md`** (referência técnica canônica no repo; não inventar chaves).
- **Sudo Warmth:** Utilize a sessão `tmux` chamada **`completao`**, que já possui `sudo -v` ativo em todos os nós em que esse fluxo se aplica.
- **LAB-NODE-01 Restriction:** No host **LAB-NODE-01**, não tente usar `python` ou `uv`. Use estritamente **`podman run`** para o runtime do produto.
- **Data Soups:** No **LAB-NODE-02**, suba a stack de bancos via **Swarm** antes de iniciar os scans de DB.

**English:** [LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)

**Quando usar:** Quando você abre um **chat novo** **sem contexto** e **quer** que o assistente **execute** o **completão** como nos **contratos** do repo (`lab-completao-workflow.mdc`, `LAB_COMPLETAO_RUNBOOK.md`).

**Uso fino no dia a dia:** **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md`](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)** ([EN](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)) — linha **`completao`** + atalho **`tier:…`** + **`scripts/completao-chat-starter.ps1`**; mantenha os blocos **A–E** deste arquivo para a prosa completa quando ajustar contratos.

## Contrato de raio de explosão (não negociável — o assistente **não** “esquece”)

| Onde | Nunca (Git destrutivo / clean-slate no clone canônico) | Sempre OK no completão |
| ---- | -------------------------------------------------------- | ------------------------ |
| **PC dev principal** (ThinkPad **L-series**, este repo no Cursor) | **`git reset --hard`**, **`git clean -fdx`**, **`clean-slate`**, reescrita de histórico na cópia de trabalho **principal** | **`git pull`**, merge, branch, stash; auditorias só em **`%TEMP%`** |
| Hosts **LAB-OP** no **`lab-op-hosts.manifest.json`** (SSH **`repoPaths`**) | N/A — clones devem seguir o GitHub | **`git fetch` / `pull --ff-only`**, **`lab-op-git-align-main.ps1`**, **`lab-op-git-ensure-ref`**, **`-AlignLabClonesToLabGitRef`**, **`lab-op-repo-status.ps1 -PullFfOnly`** — rodar **de forma autónoma** a partir dos scripts no PC dev; **não** pedir ao operador para “ir host a host” à mão se o script já faz SSH |
| **Imagens de contêiner** (Docker / Swarm / Podman / Kubernetes) | N/A para o Git do PC dev principal | **Voltar a puxar** do **Docker Hub** (ou registry); **`docker pull`**, atualizar stack — **normal** |

Tabela completa: **`LAB_COMPLETAO_RUNBOOK.md`** (*Raio de explosão* / *Blast radius*). Política do PC principal: **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md`**.

## Pré-condições (estação do operador)

- **Mesmo** PC Windows de desenvolvimento, **mesmo** clone, **terminal integrado do Cursor** (não um “datacenter de IA” à parte).
- **`docs/private/homelab/lab-op-hosts.manifest.json`** presente (cópia a partir de **`docs/private.example/homelab/lab-op-hosts.manifest.example.json`** quando preciso). Em hosts em que o Data Boar **roda** **só** via **Docker Swarm / Podman** (sem **`uv`** no metal), defina **`completaoEngineMode`:** **`container`** (ou **`completaoSkipEngineImport`:** **`true`**) para o smoke **não** tratar **`uv`** ausente como falha — ver **`LAB_COMPLETAO_RUNBOOK.md`** (*Hosts só com contêiner*).
- **Revisão LAB reproduzível (recomendado):** chave opcional na raiz **`completaoTargetRef`** no manifesto (ex.: **`origin/main`** ou **`vX.Y.Z`**) e/ou **`-LabGitRef`** em **`lab-completao-orchestrate.ps1`** para o smoke no host rodar num commit **conhecido** — ver **`LAB_COMPLETAO_RUNBOOK.md`** (*Ref Git alvo para completão reproduzível*). Com **tag** de release, use **`-SkipGitPullOnInventoryRefresh`** para o refresh de inventário não dar **`git pull`** para **`main`** nos clones antes do **ensure-ref**.
- **`ssh`** para os hosts do manifesto funciona nesse terminal (chaves / `~/.ssh/config`).
- Opcional: **sudoers estreito** para **`sudo -n`** nos Linux — ver **`LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md`** e **`LABOP_COMPLETÃO_SUDOERS*.md`** (gitignored).

## Ler primeiro (ordem)

0. **Opcional (chat novo / token-aware):** **[`OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md`](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)** ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)) — escada num ecrã + router de tarefas; depois **[`LAB_OP_HOST_PERSONAS.pt_BR.md`](LAB_OP_HOST_PERSONAS.pt_BR.md)** ([EN](LAB_OP_HOST_PERSONAS.md)) para ENT / PRO / edge / ponte vs Ansible + knobs do manifest.
1. **[`AGENTS.md`](../../AGENTS.md)** — linha do Quick index **Completão no lab** e token **`completao`**.
2. **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** — contratos, scripts, **ordem de fatias**, cobertura de capacidades, automação + aprendizados.
3. **`.cursor/rules/lab-completao-workflow.mdc`** — política sempre ativa (SSH, **`-Privileged`**, sem perguntas ociosas sobre SSH, proteção **L-series**, matriz doc+código, timeouts/FP-FN).

## Token de sessão (inglês)

**Escreva** **`completao`** no chat para alinhar o âmbito a **`session-mode-keywords.mdc`**. Nos blocos copy-paste, deixe **só** esse token na **primeira linha** — não acrescente branch/versão na mesma linha (taxonomia de sessão).

## Modos de sessão (escolha um)

| Modo | Objetivo | O que os **scripts do repo** executam de uma vez | O que ainda depende **de você** (config / serviços / segredos) |
| ---- | -------- | ---------------------------------------------- | -------------------------------------------------------------- |
| **Só smoke** | LAN + clone + probes de runtime + logs | **`lab-completao-orchestrate.ps1 -Privileged`** (inclui preflight → pode executar **`lab-op-sync-and-collect.ps1`**; opcional **`completaoTargetRef`** / **`-LabGitRef`** → **`lab-op-git-ensure-ref`** antes do smoke) | Manifesto, SSH, opcional **`completaoTargetRef`**, opcional **`completaoHealthUrl`**, opcional sudoers para **`sudo -n`** |
| **Estendido** | Igual ao smoke + validação mais funda (CLI, BDs, API, fatias pytest POC) | **Não há** um único script que cubra tudo — seguir **ordem de fatias** em **`LAB_COMPLETAO_RUNBOOK.md`** em passos ou chats | YAML privado (ex. padrão **`config.complete-eval.yaml`**), **`lab-smoke-stack`** levantado onde precisar, env para API key / JWT / WebAuthn, browser para UX FIDO2 manual |

**Âmbito honesto:** A fatia 1 (orchestrator) **por si** **não** faz deploy completo de sintéticos em BDs, scans comparativos nem prova ponta a ponta JWT/WebAuthn/browser. Isso está **documentado** em **`SMOKE_*.md`**, **`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`**, **`TECH_GUIDE.md`**, **`SECURITY.md`** — passos **orientados pelo assistente**, não um comando mágico.

## Checklists opcionais

### Só smoke (primeira fatia útil mínima)

- [ ] Manifesto existe e **`sshHost`** / **`repoPaths`** estão corretos.
- [ ] (Recomendado para corridas comparáveis) Definir **`completaoTargetRef`** (ex.: **`origin/main`** ou release **`vX.Y.Z`**) e/ou passar **`-LabGitRef`**; usar **`-SkipGitPullOnInventoryRefresh`** quando a ref for uma **tag**.
- [ ] Hosts só contêiner têm **`completaoEngineMode`:** **`container`** (ou **`completaoSkipEngineImport`**) onde aplicável.
- [ ] (Opcional) **`completaoHealthUrl`** por host se **`main.py --web`** estiver no ar e acessível a partir do PC dev.
- [ ] **Execute** **`.\scripts\lab-completao-orchestrate.ps1 -Privileged`** na raiz do repo; leia os logs em **`docs/private/homelab/reports/`**.
- [ ] Anexar achados materiais em **`docs/private/homelab/`** (ex.: **`COMPLETAO_SESSION_YYYY-MM-DD.md`** ou modelo **`COMPLETAO_SESSION_TEMPLATE.pt_BR.md`**).

### Estendido (vários passos; mesmo chat ou chats seguintes)

- [ ] Checklist **só smoke** feito (ou saltado com motivo nas notas privadas).
- [ ] **`lab-op-repo-status.ps1`** se os clones puderem estar atrás / apareceu **`MISSING_SCRIPT`** antes.
- [ ] Fundir **telemetria recente** em **`LAB_SOFTWARE_INVENTORY.md`** / **`OPERATOR_SYSTEM_MAP.md`** e atualizar **`Lab inventory as-of`** / **`<!-- lab-op-inventory-as-of: ... -->`** (ver **`docs/private.example/homelab/README.md`**).
- [ ] Scans de FS no Linux: cópias **`config.lab-fs-*.example.yaml`** + **`main.py`** **no host** segundo o runbook — não a partir do Windows salvo mounts.
- [ ] Avaliação CLI a partir do PC dev: **`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`** + YAML **privado** (caminhos do operador).
- [ ] API/web: processo **`main.py --web`**, **`curl`** / **`completaoHealthUrl`**, browser conforme preciso; **`SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md`** para TLS/API key.
- [ ] No **PC dev**: **`.\scripts\smoke-maturity-assessment-poc.ps1`**, **`.\scripts\smoke-webauthn-json.ps1`** — subconjuntos **pytest**; **não** substituem **`check-all.ps1`** nem prova FIDO2 completa no browser.
- [ ] **Registre** **evidência** (timeouts, FP/FN vs sintéticos, confiança em caminhos reais) em **`docs/private/homelab/`**; ligue lacunas de produto a **`PLANS_TODO.md`** / issues quando fizer sentido.

## Antes do orchestrator (automático)

O **`lab-completao-orchestrate.ps1`** executa primeiro o **`lab-completao-inventory-preflight.ps1`** (frescura **15 dias** por padrão nos privados **`LAB_SOFTWARE_INVENTORY.md`** + **`OPERATOR_SYSTEM_MAP.md`**; dispara **`lab-op-sync-and-collect.ps1`** se estiver velho). **Leia** esses inventários quando existirem — **`LAB_COMPLETAO_RUNBOOK.md`** (*Frescura do inventário*). Desligar: **`-SkipInventoryPreflight`**.

## Primeiro comando (padrão)

Na **raiz do repo** no Windows:

```text
.\scripts\lab-completao-orchestrate.ps1 -Privileged
```

Depois **leia** **`docs/private/homelab/reports/`** (`completao_*_allhosts.log`, `*_completao_host_smoke.log` por host).

## Fatias sequenciais (não saltar sem motivo)

**Siga** **`LAB_COMPLETAO_RUNBOOK.md`** — **Ordem de fatias recomendada**, **Cobertura de capacidades**, **Reutilização de automação e registro de aprendizados**. Camadas extra usam os **smokes** e **docs** indicados nesse runbook. **Docs em inglês + código** são a fonte de verdade do comportamento.

## Não fazer

- Dizer que o assistente **não** chega ao lab por **SSH a partir deste PC** quando o **`ssh`** funciona — ver **`homelab-ssh-via-terminal.mdc`**.
- Pedir **de novo** permissão SSH / **`-Privileged`** ou **“devo alinhar os clones LAB?”** se o operador já pediu **completao** — scripts de alinhamento atingem **só** hosts do manifesto, não o PC Windows principal — ver **`operator-direct-execution.mdc`** e *Contrato de raio de explosão* acima.
- Correr **`git reset --hard`**, **`clean-slate`** ou reescrita de histórico no clone **canônico** no **PC principal** — **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md`**. (Contraste: **`repoPaths`** em LAB podem usar scripts de alinhamento — **não** é o PC dev principal.)
- **Segredos** ou identificadores LAN no **GitHub público**; notas só em **`docs/private/homelab/`**.
- Prometer **FIDO2 no browser**, **JWT de licenciamento completo** ou prova **“secure by design”** só com scripts — documentar **o que foi executado** vs **`SMOKE_*.md`** / **`SECURITY.md`**.

---

## Bloco copy-paste A — primeira fatia (smoke + logs)

Chat **novo** sem contexto (após pré-condições). O texto do bloco está em **inglês** para alinhar ao assistente; o cabeçalho **`Session mode: smoke-only`** referencia este arquivo.

**Ref vs versão:** **`origin/main`** é a **ponta do branch** no remoto, não um semver. A **string de versão do produto** em **`pyproject.toml`** nessa ponta é a que o commit **`main`** referencia depois do **`git fetch`** — confirme no PC dev com **`git show <ref>:pyproject.toml`** (ex.: **`origin/main`**) quando precisar do valor exato. No **completão de rotina**, trate a **ponta do `main` no GitHub** como “atual”, salvo se você fixar um **release específico** com **`-LabGitRef vX.Y.Z`** (ou **`completaoTargetRef`** no manifesto). Uma **tag remota** só vale se existir; caso contrário use **`-LabGitRef origin/main`** para alinhar os clones LAB ao mesmo tip que o **`main`**.

**Onde definir a ref:** mantenha a **linha 1** do bloco copy-paste **só** com **`completao`**. Altere o **passo 1** abaixo (valor de **`-LabGitRef`**), não a linha 1.

**Sanidade `git` / `gh` (PC dev antes do completão):** rode **`git fetch origin`**, depois **`git rev-parse HEAD`** e **`git rev-parse origin/main`** — devem coincidir se o teu **`main`** local está sincronizado com o GitHub. **`gh repo view`** serve para metadados (branch padrão, nome); **não** substitui o **`git`** para identidade de commit. Alterações locais **não commitadas** não mudam **`origin/main`**; os hosts LAB seguem a ref **remota**, não alterações unstaged no working tree.

**Scripts vs GitHub:** depois de correções de workflow entrarem no **`main`**, corre **`git pull`** neste clone no PC dev antes de **`lab-completao-orchestrate.ps1`**, para o orchestrator usar a mesma revisão de **`scripts/*.ps1`** que **`origin/main`**. A saída do terminal no chat pode **cortar** em corridas longas; usa **`docs/private/homelab/reports/`** (`lab_op_git_ensure_ref_*.log`, `completao_*`) como fonte de verdade. Cada bloco de repo em **`lab_op_git_ensure_ref_*.log`** deve terminar com **`LABOP_REF_OK`** ou **`LABOP_REF_MISMATCH`** (ou **`LABOP_REF_UNRESOLVED`**); se não, lê as linhas git/SSH acima no mesmo arquivo.

### Bloco A — exemplos de `-LabGitRef` (editar só o passo 1)

| Objetivo | Passo 1 |
| -------- | ------- |
| Clones LAB = **ponta do `main` no GitHub** (padrão no bloco abaixo) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main` |
| Clones LAB = **tag** `vX.Y.Z` (ex.: smoke de release) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef vX.Y.Z -SkipGitPullOnInventoryRefresh` |
| Sem verificação de ref (smoke no que estiver checkout nos LAB) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged` — omitir **`-LabGitRef`** (ou **`-SkipLabGitRefCheck`** se o manifesto tiver **`completaoTargetRef`**) |

Para **tag**, **`-SkipGitPullOnInventoryRefresh`** evita que o **`lab-op-sync-and-collect`** avance os clones LAB para o **`main`** mais recente durante o refresh de inventário — ver **`LAB_COMPLETAO_RUNBOOK.md`** (*Ref Git alvo*).

```text
completao

You are in the data-boar repo on my Windows dev PC. Read AGENTS.md (Quick index: Lab completão), then docs/ops/LAB_COMPLETAO_RUNBOOK.md, and follow .cursor/rules/lab-completao-workflow.mdc. Use the integrated terminal — same SSH reachability as my shell.

Session mode: smoke-only (see docs/ops/LAB_COMPLETAO_FRESH_AGENT_BRIEF.md).

LAB git target: match GitHub main — run orchestrator with -LabGitRef origin/main (runs lab-op-git-ensure-ref Check before host smoke). The product version at that ref is whatever **`pyproject.toml`** declares there (confirm with **`git show origin/main:pyproject.toml`**); do not assume a fixed semver unless I pinned a release tag. If ensure-ref fails, LAB clones are not at origin/main (align per LAB_COMPLETAO_RUNBOOK.md).

1) From repo root run: .\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main
2) Summarize docs/private/homelab/reports/ logs (no secrets in chat if sensitive).
3) Read docs/private/homelab/OPERATOR_SYSTEM_MAP.md and LAB_SOFTWARE_INVENTORY.md when present; reconcile host-smoke with documented roles (container-only manifest hosts are not "missing uv" defects).
4) Document material findings under docs/private/homelab/ (timeouts, latency, FP/FN vs synthetic, confidence on real paths). Do not expand to full CLI/DB/browser/API proof unless I ask in a follow-up.

Do not ask redundant permission for SSH or -Privileged. Do not claim the lab is unreachable from this workspace. Protect my primary Windows dev workstation per docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md.

If something fails, print the actual error and what I must fix (e.g. sudoers, manifest, missing uv on native hosts, LAB clone behind origin/main), then stop — I will fix and ask you to retry. Do not demand bare-metal uv on container-only manifest hosts (completaoEngineMode: container).
```

---

## Bloco copy-paste B — após fatia A (alinhamento de repo, só leitura)

```text
completao follow-up — repo alignment

Same repo and terminal as before. Run .\scripts\lab-op-repo-status.ps1 from repo root. Summarize per-host git state vs origin/main. If MISSING_SCRIPT appeared in past completão logs, point to LAB_COMPLETAO_RUNBOOK.md (align clones). Do not run lab-op-git-align-main.ps1 unless I explicitly ask (destructive on lab clones). Document under docs/private/homelab/.
```

---

## Bloco copy-paste C — estendido: smokes POC pytest no PC dev (sem segredos LAN)

```text
completao follow-up — Windows POC pytest smokes

From repo root run: .\scripts\smoke-maturity-assessment-poc.ps1 then .\scripts\smoke-webauthn-json.ps1
Summarize pass/fail. These are pytest subsets per docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md and SMOKE_WEBAUTHN_JSON.md — not a full browser FIDO2 demo and not a substitute for .\scripts\check-all.ps1.
```

---

## Bloco copy-paste D — estendido: padrão CLI eval (precisa config privada)

```text
completao follow-up — CLI eval

Read docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md. If I have a private config path under docs/private/homelab/, run uv run python main.py --config <path> only after read_file confirms the YAML exists; redact secrets in chat. If no config exists, stop and list what I must provide. Document findings under docs/private/homelab/.
```

---

## Bloco copy-paste E — pacote de evidência (documentação / próxima sessão)

```text
completao follow-up — evidence pack

Consolidate what we proved this session: commands run, log paths under docs/private/homelab/reports/, inventory as-of dates, pass/fail matrix, gaps vs LAB_COMPLETAO_RUNBOOK.md slice order. Suggest one PLANS_TODO.md row or issue title only if a product gap is confirmed — no public PII.
```

## Um agente novo consegue?

**Em grande parte sim** no modo **só smoke**, com workspace deste repo e bloco **A**. O **estendido** é **vários passos** de propósito — use **B–E** ou chats novos para não misturar âmbito. **Nenhum** assistente **inventa** chaves SSH, **LAB-ROUTER-01** ou **sudoers** — continua **do lado do operador**.

## O que melhorar fora deste arquivo

- Manter **manifesto** e YAML **privados** atualizados.
- Depois de cada completão, **uma linha** em **`PLANS_TODO.md`** ou **issue** quando houver lacuna de produto confirmada.
