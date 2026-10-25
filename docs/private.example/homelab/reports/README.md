# Homelab host reports (local only — gitignored)

**Purpose:** Store **stdout** from `scripts/homelab-host-report.sh` (run on each Linux host) for **traceability** when you tune kernel, I/O, or stack — alongside your other private notes.

**Naming:** `<SSH-alias-or-hostname>_<YYYYMMDD_HHMM>_homelab_host_report.log` (see parent [README.md](../README.md)).

## Populate from Windows (dev PC with repo + SSH):

```powershell
.\scripts\collect-homelab-report-remote.ps1 -SshHost lab-op
```

**Batch (multiple hosts + `git pull` on canonical clone paths):** save **`docs/private/homelab/lab-op-hosts.manifest.json`** (preferred) from **`../lab-op-hosts.manifest.example.json`**. If only **`lab-op-hosts.manifest.example.json`** exists under `homelab/`, **`scripts/lab-op-sync-and-collect.ps1`** uses it as fallback (with a warning). Then:

```powershell
.\scripts\lab-op-sync-and-collect.ps1
```

**“Completão” (product + runtime smoke, not pytest):** same manifest; optional per-host **`completaoHealthUrl`** (see **`../lab-op-hosts.manifest.example.json`**). From repo root:

```powershell
.\scripts\lab-completao-orchestrate.ps1
```

See tracked **[LAB_COMPLETAO_RUNBOOK.md](../../../ops/LAB_COMPLETAO_RUNBOOK.md)**. Logs: **`completao_<timestamp>_allhosts.log`** and per-host `*_completao_host_smoke.log`. Lessons template: **`COMPLETAO_SESSION_TEMPLATE.pt_BR.md`** next to private `homelab/` when copied.

Repeat per host (`-SshHost` = entry in your `~/.ssh/config`) for single-host flow. Output defaults to **`docs/private/homelab/reports/`** next to this README when you copy the tree from `docs/private.example/`.

## Populate on Linux (repo on host):

```bash
bash scripts/homelab-host-report.sh | tee "docs/private/homelab/reports/$(hostname -s)_$(date +%Y%m%d_%H%M)_homelab_host_report.log"
```

**Redact** LAN IPs, host FQDNs, or serials before sharing logs in chat or email.

### SNMP (UniFi / gateway) — log agendado no Windows (Task Scheduler)

Para gravar a saída do probe SNMP em **arquivo local** (pasta gitignored), sem colocar segredos na tarefa agendada:

1. Crie **`docs/private/homelab/.env.snmp.local`** (nome exato, com o ponto no início), **ou** um arquivo dedicado por equipamento (ex.: **`.env.snmp.LAB-ROUTER-01-se.local`** para LAB-ROUTER-01 SE — mesmo conteúdo que o exemplo). Copie do modelo rastreado: **`docs/private.example/homelab/env.snmp.local.example`** →

   `Copy-Item docs\private.example\homelab\env.snmp.local.example docs\private\homelab\.env.snmp.local`
   Depois edite com os valores reais (ver [CREDENTIALS_AND_LAB_SECRETS.md](../CREDENTIALS_AND_LAB_SECRETS.md)). Se usar um arquivo **não** default, nos testes e no Agendador passe **`-EnvFile "docs\private\homelab\.env.snmp.LAB-ROUTER-01-se.local"`** (ajuste o nome).

1. Teste manualmente na raiz do repo:

   ```powershell
   .\scripts\snmp-LAB-ROUTER-01-lab-probe-to-log.ps1 -WslDistro "Debian" -MaxLines 400
   # com .env dedicado (ex. LAB-ROUTER-01-SE):
   # .\scripts\snmp-LAB-ROUTER-01-lab-probe-to-log.ps1 -EnvFile docs\private\homelab\.env.snmp.LAB-ROUTER-01-se.local -WslDistro "Debian" -MaxLines 400
   ```

   O log fica em **`snmp_LAB-ROUTER-01_probe_YYYYMMDD.log`** nesta pasta. **`-MaxLines`** evita arquivos enormes (walk IF-MIB completo = muitas linhas); use **`-MaxLines 0`** só se quiser dump completo e tiver espaço em disco.

1. **Agendador de Tarefas** (Task Scheduler): nova tarefa → **Disparadores** → novo disparador (ex.: **Diariamente** num horário inicial, ou **Ao iniciar sessão**) → **Avançadas** / opções do disparador:
   - Marque **Repetir tarefa a cada:** **`30 minutos`** (ou **1 hora**, se preferir).
   - **Por um período de:** **Indefinidamente** (ou o intervalo que a UI permitir na tua versão do Windows).
   - Confirme que a tarefa está **habilitada**.
1. **Ações** → **Iniciar um programa**:
   - **Programa:** `powershell.exe`
   - **Argumentos:** `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\<username>\Documents\dev\data-boar\scripts\snmp-LAB-ROUTER-01-lab-probe-to-log.ps1" -WslDistro "Debian" -MaxLines 400`

     (ajuste o caminho do repo; o nome da distro com `wsl -l -v`. Se o alvo for um **`.env` dedicado** (ex. LAB-ROUTER-01-SE), acrescenta **`-EnvFile "…\docs\private\homelab\.env.snmp.LAB-ROUTER-01-se.local"`** antes ou depois dos outros switches.)

   - **Começar em:** `C:\Users\<username>\Documents\dev\data-boar` (raiz do clone **Data Boar**).
1. Execute como **seu usuário** (para ler `.env` e usar WSL); “Executar somente quando o usuário estiver conectado” costuma ser mais simples que serviço sem ambiente.

**Disco:** a cada 30 minutos o log do **mesmo dia** cresce; com **`-MaxLines 400`** limitas cada execução. Apague ou arquive logs antigos em `reports/` quando necessário.

**Privacidade:** esses logs podem incluir nomes de interfaces, contadores e **endereços MAC** — não faça commit; não compartilhe sem redigir.

**CI / GitHub Actions:** ver [SNMP_LAB_TARGETS.pt_BR.md](../SNMP_LAB_TARGETS.pt_BR.md) § CI — *runners* na nuvem **não** alcançam o firewall na LAN; não planeamos workflow padrão no repositório para SNMP ao vivo.

**Public doc index:** [HOMELAB_HOST_PACKAGE_INVENTORY.md](../../../ops/HOMELAB_HOST_PACKAGE_INVENTORY.md) §4.
