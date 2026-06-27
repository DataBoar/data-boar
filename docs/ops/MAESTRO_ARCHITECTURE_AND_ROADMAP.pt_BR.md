# Maestro — arquitetura, mitologia e roteiro de evolução

**English:** [MAESTRO_ARCHITECTURE_AND_ROADMAP.md](MAESTRO_ARCHITECTURE_AND_ROADMAP.md)

**Relacionado:** [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md) · [COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)

---

## 1. O que é o Maestro

O **Maestro** é o orquestrador central, baseado em personas e orientado por inventário, do **Lab-Op** — o ambiente de homelab do Data Boar. Não é um executor de testes. Não é um pipeline de CI. É um **regente**: lê o inventário privado (a partitura), despacha para handlers especializados, e coleta as evidências de uma performance completa (a completão).

O Maestro existe porque a validação em laboratório — hosts reais, SSH real, contêineres reais, bancos de dados reais, sistemas de arquivos reais, protocolos reais — não pode ser representada totalmente por testes unitários nem pelo GitHub CI. Quando o Data Boar faz um scan num PostgreSQL de produção com nomes de colunas em encoding misto ou num MariaDB com schemas vazios, essa superfície só é exercida no lab. O Maestro torna esse exercício repetível, documentado e comparável entre versões.

### A metáfora

| Termo musical | Significado no Maestro |
| ------------- | ---------------------- |
| Maestro (regente) | `Maestro.ps1` — lê a partitura, controla o andamento e a sequência |
| Chefe de seção *(metáfora: capo di sezione — apenas narrativa)* | **Handlers** `Handle-*.ps1` — cada um lidera sua seção com total autonomia; o termo canônico é sempre **handler** |
| Músico | Nó do lab (aliases do inventário como `<lab-node-a>`, `<lab-node-b>`, …) — o performer |
| Instrumento / Voz (Persona) | O papel que cada nó desempenha: `docker`, `podman`, `baremetal`, `web`, `target_postgres`, … |
| Partitura | `docs/private/homelab/data/inventory.json` — quem toca o quê |
| Apresentação (Completão) | Um ciclo completo em todos os nós, todas as personas, todas as superfícies de alvo |
| Bis (benchmark A/B) | `maestro-benchmark-ab.ps1` — stable vs rc, mesma partitura, duas apresentações |
| Notas de programa | `docs/private/homelab/reports/` — evidência de cada apresentação |

A palavra **completão** é gíria brasileira para "a obra toda feita direito" — uma referência intencional ao contexto cultural do projeto e um lembrete de que o objetivo é **completude**, não perfeição.

---

## 2. Como chegamos aqui — breve histórico

A primeira abordagem de orquestração foi **monolítica**: `lab-completao-orchestrate-hybrid-v173.ps1` e suas variantes (plano-a ao plano-v). Esses scripts codificavam papéis de nós, caminhos de imagem e lógica de benchmark em um único arquivo PowerShell extenso. Funcionavam — mediam o tempo de importação do `boar_fast_filter`, faziam comparações A/B entre v1.7.3 estável e v1.7.4-rc, e produziam streams de eventos JSONL. Mas eram frágeis: cada variante "plano" era um fork artesanal, não um sistema geral.

O **Maestro** foi projetado para substituir todas as 22 variantes hybrid-plano por um único framework:

- **Orientado por inventário:** papéis de nós, caminhos, usuários e capacidades vêm de um manifesto JSON privado — sem hostnames fixos no código rastreado.
- **Despacho baseado em personas:** cada capacidade é encapsulada num arquivo `Handle-<persona>.ps1`, chamado pelo orquestrador com base na entrada do inventário. Adicionar um novo tipo de nó = adicionar um arquivo de handler.
- **Modelo de fases:** Pré-voo (build/sync de artefato) → Despacho (handlers de persona) → Coleta (download de artefatos) → Relatório.
- **Isolamento de PII:** zero hostnames reais, IPs ou contas de usuário no código rastreado; tudo no `inventory.json` privado.

---

## 3. Arquitetura

### 3.1 Mapa de componentes

```
scripts/
  maestro/
    Maestro.ps1                    ← Orquestrador central
    Build-ContainerArtefact.ps1    ← Constrói imagem Docker no dev PC
    Sync-WorkingTree.ps1           ← rsync/scp repo para nó do lab
    Sync-ContainerArtefact.ps1     ← docker save + scp imagem para o nó
    Get-LabStatus.ps1              ← Verificação SSH de pré-voo por nó
    Collect-Artifacts.ps1          ← SCP de métricas/logs do nó
    handlers/
      Handle-baremetal.ps1         ← uv + smoke Python via tmux
      Handle-docker.ps1            ← docker run / compose via tmux
      Handle-dockerswarm.ps1       ← Serviço Docker Swarm via tmux
      Handle-podman.ps1            ← Podman sem root via tmux
      Handle-microk8s.ps1          ← Pod k8s via tmux
      Handle-lxd.ps1               ← Contêiner LXD via tmux
      Handle-web.ps1               ← Health check HTTP (síncrono); portão para load test
      Handle-target_postgres.ps1   ← PostgreSQL sintético via compose
      Handle-target_mariadb.ps1    ← MariaDB sintético via compose
      Handle-target_mongodb.ps1    ← MongoDB sintético via compose
      Handle-target_nfs.ps1        ← Montagem/desmontagem NFS
      Handle-target_sshfs.ps1      ← Montagem/desmontagem SSHFS
      Handle-target_cifs.ps1       ← Montagem/desmontagem SMB/CIFS
  maestro-benchmark-ab.ps1        ← Wrapper A/B (stable vs rc)
  lab-completao-host-smoke.sh     ← Smoke por host (bash, roda em tmux no OS)
  lab-completao-container-smoke.sh ← Smoke de container: detecta Docker/Podman,
                                     sobe Data Boar RC (porta 9002), escreve
                                     ~/.labop-status; chamado pelos handlers
                                     docker/podman via tmux após host smoke
```

### 3.2 Fluxo de execução

```
Maestro.ps1 -Deep -BenchTrack beta -BenchRunId abc123
│
├─ Build-ContainerArtefact.ps1   (uma vez, pré-voo: constrói data_boar:lab)
│
└─ foreach nó em inventory.lab_members
   ├─ Get-LabStatus.ps1          (pré-voo SSH: ATIVO/INATIVO)
   ├─ Sync-WorkingTree.ps1       (rsync ou scp repo para node.path)
   ├─ Sync-ContainerArtefact.ps1 (docker save → scp → docker load, se persona contêiner)
   └─ foreach persona em node.personas (ordem: contêiner primeiro, web por último)
      └─ Handle-<persona>.ps1 @handlerArgs   ← handler em ação
         └─ ssh: tmux send-keys → lab-completao-host-smoke.sh (assíncrono, dentro do tmux)
                                   ou comando direto docker/podman/compose
│
└─ Fase -Collect (Maestro.ps1)
   └─ foreach nó
      └─ Collect-Artifacts.ps1  (scp de métricas de /tmp/databoar_bench/$track/)
```

### 3.3 Taxonomia de handlers (handlers de persona)

Os **handlers** (`Handle-<persona>.ps1`) são os sub-orquestradores especializados — um por tipo de persona. Cada handler possui completamente seu domínio: recebe contexto do Maestro e é totalmente responsável pela performance da sua seção. Nos docs narrativos os handlers são às vezes descritos com a metáfora musical de *capo di sezione* (chefe de seção), mas o termo canônico em código e documentação é sempre **handler**.

Handlers são aditivos — um nó pode ter múltiplos. A entrada do inventário os lista; o Maestro ordena o despacho (personas de contêiner primeiro, `web` por último, outros na ordem de declaração).

| Persona | Handler | O que exerce |
| ------- | ------- | ------------ |
| `baremetal` | Handle-baremetal.ps1 | Data Boar via `uv run` no OS sem contêiner |
| `docker` | Handle-docker.ps1 | Docker CE `docker run` / `docker compose` |
| `dockerswarm` | Handle-dockerswarm.ps1 | Serviço em modo Docker Swarm |
| `podman` | Handle-podman.ps1 | Contêiner Podman sem root |
| `microk8s` | Handle-microk8s.ps1 | Pod Kubernetes via microk8s |
| `lxd` | Handle-lxd.ps1 | Contêiner de sistema LXD |
| `web` | Handle-web.ps1 | Health check HTTP `/health` + alcançabilidade da API; portão para load test |
| `target_postgres` | Handle-target_postgres.ps1 | PostgreSQL sintético (compose), escaneado entre hosts |
| `target_mariadb` | Handle-target_mariadb.ps1 | MariaDB sintético (compose), escaneado entre hosts |
| `target_mongodb` | Handle-target_mongodb.ps1 | MongoDB sintético (compose), escaneado entre hosts |
| `target_nfs` | Handle-target_nfs.ps1 | Montagem NFS |
| `target_sshfs` | Handle-target_sshfs.ps1 | Montagem SSHFS |
| `target_cifs` | Handle-target_cifs.ps1 | Montagem SMB/CIFS |
| `target_oracle` *(roadmap)* | Handle-target_oracle.ps1 | Oracle XE sintético (compose) |
| `loadtest` *(roadmap)* | Handle-loadtest.ps1 | Load test HTTP com Locust após health check |

### 3.4 Contrato do inventário

`docs/private/homelab/data/inventory.json` — nunca rastreado no Git público. Cada entrada `lab_member`:

```json
{
  "hostname": "<alias>",
  "user": "<ssh-user>",
  "ip": "<lan-ip>",
  "path": "<caminho-repo-no-host>",
  "personas": ["docker", "web", "target_postgres"],
  "web_port": 8088,
  "web_scheme": "http"
}
```

### 3.5 Piso min-spec do lab (bare-metal / musl)

Quando personas bare-metal executam `uv`, `maturin` ou stacks ML opcionais em nós de lab com poucos recursos (em especial **SBCs Alpine/musl** medidos na issue **#1003**), duas restrições de build se repetem:

| Restrição | Sintoma | Mitigação |
| --------- | ------- | --------- |
| **crt-static** | `cargo build` cru falha com *"does not support these crate types"* para `cdylib` PyO3 em musl com CRT estático por padrão | O **`maturin`** injeta `RUSTFLAGS="-C target-feature=-crt-static"` automaticamente; `cargo build` sem essa flag falha em musl |
| **sklearn-wheel** | `uv sync` tenta compilar **scikit-learn** from-source em Alpine sem AVX / com pouca RAM | Depende de **wheel pré-buildado** do pipeline **#782 Build-Once** (ou aceitar ML opcional degradado); ver `labop-dep-doctor.sh` e `lab-completao-host-smoke.sh` |

**Paridade login-env (#1003):** sessões SSH e tmux não interativas costumam omitir `~/.local/bin` e `~/.cargo/env` do `PATH`. O Maestro centraliza um prelúdio bash remoto em `Lab-MaestroCommon.ps1` (`Get-MaestroRemoteLoginPathPrelude`) para todos os handlers injetados via tmux; `Handle-web.ps1` e `lab-completao-host-smoke.sh` aplicam o mesmo padrão antes de `uv` / `maturin`; `labop-gate-readiness.sh` sonda `login-env:uv`, `login-env:cargo` e `login-env:maturin` após `_ensure_login_path`.

---

## 4. O conceito de completão — por que importa

Testes de CI usam dados sintéticos em isolamento. A completão testa a **realidade da integração**:

| CI / pytest | Completão |
| ----------- | --------- |
| Corpus sintético controlado | OS real, permissões reais de filesystem, encoding real |
| Uma versão de Python | Múltiplas versões de Python, múltiplas distros |
| Runner hospedado no GitHub | LAN do operador, hardware real, rede real |
| Banco de dados mockado | PostgreSQL / MariaDB / MongoDB ao vivo com dados sintéticos |
| Sem SSH, sem ciclo de vida de contêiner | Pull de contêiner → start → scan → stop completo |
| Sem carga | Scan concorrente + API + dashboard |

Uma completão que passa em todos os nós e todas as personas é a prova de confiança de release mais próxima disponível antes do deploy no cliente.

---

## 5. Bugs conhecidos (confirmados em 2026-05-12)

Veja `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` para análise completa. Resumo:

1. **Bug 1 (crítico):** Todas as chamadas SSH não têm `ConnectTimeout` — podem travar indefinidamente.
2. **Bug 2 (crítico):** Handlers em modo `-Deep` passam `benchmark-rc.yaml` como argumento posicional desconhecido para `lab-completao-host-smoke.sh` — todo run Deep sai com exit 2 silenciosamente; nenhuma métrica é gerada.
3. **Bug 3 (race condition):** A fase `-Collect` roda imediatamente após a injeção assíncrona no tmux, antes do smoke terminar — SCP de artefatos inexistentes.

**Esses três bugs causaram o wait-state de 9 horas observado em 2026-05-12.** Corrigir antes do próximo benchmark.

---

## 6. Como usar o Maestro

### 6.1 Pré-requisitos

1. Hosts do lab acessíveis via SSH do dev PC (chaves no `ssh-agent`).
2. `docs/private/homelab/data/inventory.json` presente.
3. `tmux` rodando em cada host do lab com a sessão `completao` (ou o Maestro criará — ver roadmap do Bug 3).
4. Docker CE / Podman instalados nos hosts com persona de contêiner.

### 6.2 Invocações comuns

> **Importante:** O benchmark A/B completo leva 20–25 minutos. O terminal integrado
> do Cursor encerra processos em background após ~10 minutos. **Execute benchmarks
> longos num terminal PowerShell nativo** (Windows Terminal, `pwsh` fora do Cursor)
> em vez de via shell ou tarefas em background do Cursor.

```powershell
# Completão padrão (smoke apenas, working tree atual)
.\scripts\maestro\Maestro.ps1

# Run de benchmark deep (usa benchmark-rc.yaml, coleta métricas)
.\scripts\maestro\Maestro.ps1 -Deep -BenchTrack beta -BenchRunId "20260513_pos_fix"

# Wrapper token-aware: Deep + monitor loop + Collect (run unitário)
.\scripts\maestro-deep-rc-monitor-collect.ps1

# Benchmark A/B (stable v1.7.3 vs rc v1.7.4) — rodar em terminal PS nativo
.\scripts\maestro-benchmark-ab.ps1 `
  -LegacyRef v1.7.3 -LegacyTrack stable -LegacyWebPort 18088 `
  -CandidateRef "WorkingTree" -CandidateTrack beta -CandidateWebPort 28088 `
  -BenchCompare -RunId "ab_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Coletar artefatos do último run assíncrono
.\scripts\maestro\Maestro.ps1 -Collect
```

### 6.3 Lendo os resultados

Após um run com `-Collect`:
- `docs/private/homelab/reports/` — notas Markdown por run, streams de eventos JSONL, logs de vmstat/iostat/free.
- `docs/private/homelab/reports/MAESTRO_BENCHMARK_AB_*.md` — tabela comparativa dos rounds A/B.
- Por host `/tmp/databoar_bench/<track>/metrics/` — arquivos brutos de métricas (antes da coleta).

Palavra-chave de sessão: **`completao`** no chat do Cursor → roda `lab-completao-orchestrate.ps1 -Privileged` (o wrapper simplificado). **`lab-lessons`** → arquiva notas da sessão.

---

## 7. Roteiro de evolução

### 7.1 Curto prazo (correção de bugs + confiabilidade — H1)

Ver `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` Slices 1–3:

- Corrigir timeouts SSH (Bug 1)
- Corrigir argumento `--bench-config` (Bug 2)
- Adicionar sentinel file + `Wait-CompletaoSmoke.ps1` (Bug 3)
- Criar sessão tmux se ausente (em vez de exigir sessão `completao` pré-existente)

### 7.2 Médio prazo (completude — H2)

- **Persona Locust** (`Handle-loadtest.ps1`) — load test HTTP após health check; delta A/B de RPS/latência. Ver `PLAN_LOCUST_LOAD_TEST_INTEGRATION.md`.
- **Alvo Oracle XE** (`Handle-target_oracle.ps1`) — completar a matriz de conectores SQL.
- **Comparação completa de métricas** — relatório de diff estruturado: paridade de contagem de findings, wall-clock do scan, delta de importação do `boar_fast_filter`, pico de RAM, IO wait.
- **Integração com Ansible** — substituir o provisionamento baseado em `scp` por playbooks Ansible idempotentes para subir o stack de lab.

### 7.3 Longo prazo — Maestro como produto companion autônomo (H3/H4)

O Maestro é arquiteturalmente genérico: qualquer orquestrador SSH orientado por inventário e baseado em personas para validação multi-host. Não está intrinsecamente acoplado ao Data Boar. Caminhos de evolução potenciais:

#### 7.3.1 Ferramenta companion open-source

Extrair o núcleo do Maestro (schema de inventário, despacho de personas, coleta de artefatos) em um módulo PowerShell standalone ou CLI Python que qualquer pessoa pode usar para orquestrar smokes de lab multi-host para qualquer produto. O Data Boar fornece seu próprio pacote de handlers; integradores terceiros escrevem os seus.

#### 7.3.2 Contexto acadêmico (lato sensu / stricto sensu)

O design do Maestro incorpora vários conceitos relevantes para teses de ciência da computação aplicada:

- **Orquestração de testes distribuídos baseada em personas** — um estudo formal da taxonomia de personas como padrão de design para ambientes de lab heterogêneos.
- **Confiança de release baseada em evidências** — Maestro como sistema de "prova de release" orientado ao operador; conectando à integração Rust/PyO3 do `boar_fast_filter` como contrato de performance mensurável.
- **Benchmarking de lab reproduzível** — a metodologia A/B (workdirs isolados, sentinel files, streams de eventos JSONL) como contribuição para a ciência reproduzível na engenharia de software.

Qualquer um desses pode formar um capítulo ou estudo de caso numa tese stricto sensu, fundamentado na base de código do Data Boar como artefato do mundo real.

#### 7.3.3 Contexto comercial

No modelo de engajamento de consultoria (Engajamento A — escritório de advocacia, Engajamento B — distribuidora farmacêutica), o Maestro pode servir como a **ferramenta de validação de entrega** que roda após o deploy de uma instância do Data Boar no cliente:

- Cliente recebe uma imagem Docker → roda `Maestro.ps1` contra o inventário do cliente → a saída da completão é a **evidência de entrega**.
- Futuro: um modo "health check" orientado ao cliente que produz um relatório que a equipe de TI do cliente consegue ler, separado do benchmark completo do homelab.

---

## 8. Alinhamento de nomenclatura e taxonomia

O Maestro se alinha com a mitologia mais ampla do Data Boar:

| Conceito Data Boar | Equivalente no Maestro |
| ------------------ | ---------------------- |
| Data Sniffing (passagem de discovery) | Fase de pré-voo (`Get-LabStatus`) |
| Deep Boring (profundidade de compliance) | Modo `-Deep` (benchmark-rc.yaml, métricas completas) |
| Safe-Hold (parar por falta de evidência) | Inventário ausente → saída hard com exit 1; SSH INATIVO → pular com aviso |
| Audit Trail | `docs/private/homelab/reports/` + stream de eventos JSONL |
| Javali (thoroughness) | Completão — faz um deep boring em cada alvo, cada persona, não deixa nada sem exercitar |

Os Capos são as presas do javali: cada um especializado num substrato específico, coletivamente cobrindo a sopa de dados completa do lab.

---

## 9. Arquivos neste diretório relacionados ao Maestro

| Arquivo | Finalidade |
| ------- | ---------- |
| [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md) | Contrato do operador: o que é a completão, raio de explosão, acesso do assistente |
| [LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md) | Prompts prontos para sessões de agente sem contexto |
| [COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md) | Classificação de falhas, blocos de follow-up, briefs pré-prontos |
| `scripts/maestro/` | Todo o código de handler e orquestrador do Maestro |
| `scripts/lab-completao-host-smoke.sh` | Script de smoke por host (roda em tmux nos hosts do lab) |
| `scripts/maestro-benchmark-ab.ps1` | Wrapper de benchmark A/B |
| `docs/plans/PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` | Correção de bugs + roadmap de matriz de testes completa |
| `docs/plans/PLAN_LOCUST_LOAD_TEST_INTEGRATION.md` | Integração de load test HTTP com Locust |
| `docs/GLOSSARY.md` §12 | Terminologia canônica: Maestro, Capo, completão, persona, handler |
