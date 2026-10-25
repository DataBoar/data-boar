# Inventário de pacotes nos hosts do homelab (Data Boar)

**Objetivo:** O repositório e o ambiente de IA **não** veem o que está instalado nas suas máquinas na LAN. Esta página lista o que a **documentação do Data Boar pressupõe** em Linux e aponta **comandos + script** para você gerar o inventário e, se quiser, colar saída **anonimizada** para análise de lacunas.

**Relacionado:** [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) · [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) · [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md)

**Documento completo (EN, tabelas e script):** [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md)

---

## Resumo

- **Baseline Debian/Ubuntu (Zorin, guest Proxmox, etc.):** `python3.12`, `python3.12-venv`, `python3.12-dev`, `build-essential`, `libpq-dev`, `libssl-dev`, `libffi-dev`, `unixodbc-dev` — ver guia em inglês §1.
- **Dependências Python da aplicação:** `uv sync` / `pyproject.toml`; extras (`nosql`, etc.) conforme uso.
- **Inventário:** na raiz do repo, `bash scripts/homelab-host-report.sh` (Linux); o script inclui amostra **somente leitura** de sysctl (`vm.*`), filas de bloco (`scheduler`, etc.) e cpufreq quando existir — útil após tuning de kernel/`/sys`. Guarde em **`docs/private/homelab/reports/`** (ver **`docs/private.example/homelab/reports/README.md`**). No Windows: **`.\scripts\collect-homelab-report-remote.ps1 -SshHost <alias>`** ou **`.\scripts\lab-op-sync-and-collect.ps1`** com **`docs/private/homelab/lab-op-hosts.manifest.json`** (JSON válido, vírgulas entre hosts). **SQLite / logs locais** costumam estar no **`.gitignore`** — não bloqueiam **`git pull`**; o bloqueio vem de **arquivos rastreados** alterados (ver **`git status`** no host). Se o pull falhar, **§4.3** no EN (**stash**, descartar só o script, ou **`-SkipGitPull`**). Envie saída **redigida** + papel do host + conectores que usa.
- **Relatório estendido (postura/hardening):** ver [HOMELAB_HOST_REPORT_EXTENDED.pt_BR.md](HOMELAB_HOST_REPORT_EXTENDED.pt_BR.md).
- **Go / Rust / Zig / Odin / Homebrew:** **opcionais** para o Data Boar (o produto é **Python 3.12+**); o script imprime versões se estiverem no `PATH`. Ver **§2.5** no EN.
- **Lynis:** se aparecer **`db/languages/.../data-boar`** ou **`lynis: not in PATH`**, ver **§4.1** no documento em inglês — o binário costuma ser **`/usr/sbin/lynis`** e o script atualizado resolve isso.
- **Void + `uv sync` / `mysqlclient`:** se o linker disser **`cannot find -lz`**, instalar **`zlib-devel`**, **`pkg-config`**, **`mariadb-devel`** — ver seção **Void Linux** no EN.
- **Debian/Ubuntu/Pi + pacote PyPI `mariadb`:** erro **`mariadb_config: not found`** → **`sudo apt install libmariadb-dev pkg-config build-essential`** — ver bloco após **Debian/Ubuntu** no EN.
