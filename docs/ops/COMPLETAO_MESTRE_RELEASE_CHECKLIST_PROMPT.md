# Completão — master release checklist prompt (operator archive)

**Português (Brasil):** [COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md)

## Purpose

Preserve the operator’s **full “SRE lead / release validation” chat prompt** for **Data Boar 1.7.3** lab completão **before any run** — as a **frozen reference** you can paste, diff, or trim over time. **Shorthand for fresh chats:** after the first line **`completao`**, use **`tier:release-master-v1-7-3`** (see **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)**) or run **`.\scripts\completao-chat-starter.ps1 -Tier release-master-v1-7-3`**. For **other releases**, use **`.\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver X.Y.Z`** (optional **`-GitTag`**) and, when you archive a new frozen pair, add **`docs/ops/COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<semver>.md`** (+ **`.pt_BR.md`**) — the starter prefers that file when it exists.

## Policy alignment (read before executing)

1. **Primary Windows dev PC (canonical clone):** do **not** run **`git checkout tags/vX.Y.Z`** / mass **`git reset --hard`** on the maintainer’s main working tree from this prompt — see **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**. **LAB-OP clones** on manifest hosts are the intended place for tag alignment; use **`lab-completao-orchestrate.ps1`** / **`lab-op-git-ensure-ref.ps1`** per **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** (*Blast radius*).
2. **Tracked vs private outputs:** do **not** commit **host-specific** inventory or smoke outcomes under **`docs/ops/`** or **`docs/reports/`**. Prefer **`docs/private/homelab/reports/`** (and private session notes) per **`docs/PRIVATE_OPERATOR_NOTES.md`**. If you need a **public-safe** summary stub, keep literals generic.
3. **Synthetic corpus script (repo truth):** the generator lives at **`scripts/generate_synthetic_poc_corpus.py`** (not under **`tests/data/`**). The operator prompt below may say otherwise — treat this path as authoritative.
4. **Cold start + personas:** **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** · **[`LAB_OP_HOST_PERSONAS.md`](LAB_OP_HOST_PERSONAS.md)** stay the mental map for ENT / PRO / edge / bridge.
5. **Session token:** first chat line remains **`completao`** (English-only taxonomy). This document is **not** a substitute for **`session-mode-keywords.mdc`**.

## Lab telemetry and exit codes (`DATA_BOAR_COMPLETAO_EXIT_v1`)

When interpreting **`lab-completao-orchestrate.ps1`** (or companion bash) results **without** re-reading full logs:

| Exit code | Meaning (lab / release gate) |
| --- | --- |
| **0** | Full success for the success-path contract (orchestrator: all hosts completed and connectivity summary is not **degraded**). |
| **1** | Infrastructure / reachability / permission class (SSH probe failure, image pull path blocked, empty DB URL env, DB TCP/auth errors from **`lab_completao_data_contract_check.py`**, orchestrator **degraded** or **completed_with_skips**). |
| **2** | Data or contract shape (YAML/JSON manifest errors, missing required DB columns, clone missing **`lab-completao-host-smoke.sh`** — repo integration drift). |
| **3** | Reserved for **compliance violation** signals when a scanner or policy hook reports a governed breach (not emitted by baseline host smoke today). |

**Machine-readable fields:** **`docs/private/homelab/reports/lab_result.json`** (and **`lab_status.json`**) include **`exit_code_semantic`** (contract id + value + reason + meaning table) and **`audit_trail`** (Windows session user, computer name, PID, optional **`DATA_BOAR_COMPLETAO_INVOKER`** for agent or ticket correlation). See **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)**.

---

## Verbatim operator prompt (v1.7.3 — 2026 archive)

```text
🐗 [PROMPT MESTRE PARA O AGENTE: EXECUÇÃO DO COMPLETÃO v1.7.3]
"Agente, você é o SRE líder do Lab-Op. Sua missão é validar a Release 1.7.3 do Data Boar. A consistência de versões entre os nodes é sua prioridade absoluta. Antes de começar, leia docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md para situar sua memória.

Siga esta sequência utilizando a sessão tmux 'completao' (sudo warm) ativa com -privileged. Você tem permissão de realizar ajustes safe e least privileged necessários nos OSs, serviços e aplicações no Lab-Op, use ansible, opentofu ou comandos de pacote do OS (apt/xbps/winget) conforme necessário.

FASE 0: Teste de go/no-go (Reconhecimento de Terreno)

Avalie se conhece os hardwares do lab-op e se respondem a ICMP.

Confirme acesso via SSH e credenciais no ~/.ssh/config.

Atenção: Consulte docs/ops/LAB_OP_HOST_PERSONAS.md para entender o papel de cada máquina antes de tocar nelas.

Lembre-se: Path canônico no Linux é /home/leitao/Projects/dev/data-boar. No Windows dev workstation (primary), use WSL2.

Temos contratos de sudo passwordless ativos. Use-os.

FASE 1a: Sincronização e Inventário (Anti-Drift)

Git Sync Global: Em todos os nodes (Windows dev workstation, LAB-NODE-02, LAB-NODE-01, LAB-NODE-03, LAB-NODE-04), execute: git fetch --all --tags && git checkout tags/v1.7.3.

Garanta branch main (ou tag v1.7.3) com git pull limpo. O comando git describe --tags deve retornar exatamente v1.7.3.

Fallback de Rede: Se o LAB-NODE-04 ou outro falhar por timeout, use o Windows dev workstation para enviar o repositório via scp -r ou rsync para o nó. Paridade total é mandatória.

Confira no pyproject.toml se a versão descrita é a 1.7.3.

Sincronia de Imagens: Garanta a imagem fabioleitao/data_boar:1.7.3. No LAB-NODE-01 (Podman) e no Windows dev workstation (Docker Swarm/WSL2), force o pull ou verifique o Digest da v1.7.3.

Ajuste LAB-NODE-03: Tente xbps-install -S libmariadbclient-devel. Se falhar, documente e não tente testar o componente DB neste nó, pois o uv sync falhará.

FASE 1b: Registro do Estado Atual

Mapeamento de Recursos: Gere o arquivo docs/ops/LAB_OP_STATE.md.

Catalogue: Hardware/OS, Runtimes (docker, podman, python3, uv, pip).

Se detectar limitações (ex: falta de Python no LAB-NODE-01), autoajuste as fases seguintes respeitando a Persona do host (LAB-NODE-01 = Enterprise/Podman only).

FASE 2a: Setup da Infraestrutura e Dados Sintéticos

Geração de PII (no Windows dev workstation): Utilize o script tests/data/generate_synthetic_poc_corpus.py.

Plano A: uv run python scripts/generate_synthetic_poc_corpus.py --output ./samples

Plano B (Fallback): uv run --with pillow --with openpyxl --with python-docx --with reportlab python scripts/generate_synthetic_poc_corpus.py --output ./samples

Plano C (Pip): pip install pillow openpyxl python-docx reportlab && python scripts/generate_synthetic_poc_corpus.py --output ./samples

Distribuição: Assim que gerados no Windows dev workstation, envie para /home/leitao/samples/ em todos os nodes via scp ou rsync.

Database Stack: No LAB-NODE-02, suba o Swarm (scripts/stack-db.yml) e confirme se os bancos estão prontos.

Mounts: No LAB-NODE-01, prepare o mount de rede para os documentos do LAB-NODE-02 em /mnt/lab-node-02_docs. Valide o mount.

Gestão de Recursos: Se houver gargalo, distribua os DBs entre LAB-NODE-01 e LAB-NODE-02 conforme necessário, adaptando o target dos testes.

FASE 2b: Compartilhamento de Redes e Latência

Prepare protocolos compatíveis (NFS, SMB/CIFS, SSHFS) mesmo nas máquinas lentas (LAB-NODE-04) para validar conectividade e capacidade de operar com latências extremas ou hardware antigo.

FASE 3a: Execução do 'Completão' (SSH/tmux sessão 'completao')

Node LAB-NODE-01 (LMDE 7 - Persona Enterprise): Use estritamente podman run. Mapeie /tmp/config_databoar.yaml, a pasta de samples e a porta da API -p 8080:8080.

Node LAB-NODE-02 (Zorin 18 - Persona Pro): Execute via uv run (source) E via Docker para validar paridade. Escaneie /home/leitao/documents (Cifras) e /var/log.

Node LAB-NODE-04 (Trixie - Persona Legacy): Scan local (/var/log) via Python nativo. Monitore impacto de IO/RAM e colete dmesg/syslog pós-teste em busca de OOM Kills.

Node Windows dev workstation (Win11): Scan via WSL2 e via Windows nativo.

Node LAB-NODE-03 (Void): Scan local de arquivos; ignore DB se a lib-mysql falhou na Fase 1.

FASE 3b: Execução via API e Web

Valide Health Check via curl no status da API.

Inicie escaneamento via API, confirme status de 'scanning' e aguarde o 'idle' para baixar o report.

Rate Limit: Tente comandar sessões com intervalo curtíssimo para confirmar se a proteção anti-pattern no config.yaml bloqueia o abuso.

Security by Design: Verifique presença de security headers e HTTPS onde configurado (especialmente no LAB-NODE-01/LAB-NODE-02).

dashBOARd: Acesse a interface web onde disponível, valide reports e tente injeções simples (SQL-i) nos campos de argumentos para testar sanitização.

FASE 4: Auditoria e Report Final

Heurística: Garanta que cifras de música no LAB-NODE-02 foram classificadas como 'Inócuas'.

Consistência: Verifique se a PII sintética foi detectada igualmente em todas as plataformas.

Erros Propositais: Valide se mensagens de erro (DB offline, IP inválido) são úteis para o operador.

Consolidação: Reúna os resultados em docs/reports/TEST_REPORT_v1.7.3.md.

Sucesso: Se 'ALL GREEN' (paridade total e 0 leaks), declare pronto para o *working line* atual em `pyproject.toml` (ex.: **1.7.4-rc**).

REGRAS OPERACIONAIS CRÍTICAS:

Dispare orquestração via scripts/lab-completao-orchestrate.ps1 quando aplicável.

Gere config.yaml efêmeros em /tmp/ baseados no techguide.md. Inclua o próprio path do repo como target de scan para "comer a própria comida".

Use sudo -v warm. Se o SSH falhar, tente 3x antes de reportar.

Priorize a integridade do Windows dev workstation; ele é sua base de comando. SRE coleta evidências e aprende com as falhas."
```

---

## Related

- **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)** — **`tier:`** shorthand + **`completao-chat-starter.ps1`**
- **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** — contracts, blast radius, slice order
- **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** — copy-paste blocks A–E
