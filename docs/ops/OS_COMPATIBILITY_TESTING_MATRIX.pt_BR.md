# Matriz de compatibilidade de SO (expansão do homelab)

**Escopo do produto:** o Data Boar é **agnóstico de plataforma** — **Linux**, **macOS**, **Windows** e **container** estão no escopo. **Este arquivo** trata só do **eixo Linux do homelab** (matriz de distros, `dnf`/`pacman`/`apk`, etc.). Validação em Windows, macOS, FreeBSD e illumos fica no épico **#1171** e em outros ops docs — não aqui.

**Objetivo:** Guiar **quais distribuições Linux** testar o Data Boar no homelab, priorizadas por **relevância em produção**, **disponibilidade de Python 3.12+** e diferenças de **gerenciador de pacotes**. Ajuda a expandir a **cobertura documentada do homelab Linux** além do **caminho de instalação mais documentado** (exemplos Debian/Ubuntu no [TECH_GUIDE.md](../TECH_GUIDE.md)).

**Documento completo (EN, tabelas e comandos):** [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md)

---

## Linha de base documentada (resumo)

- **Caminho de instalação mais documentado:** **Ubuntu 24.04 LTS** / **Debian 13** (recomendado) ou Linux/macOS/Windows recente — conforme [TECH_GUIDE.md](../TECH_GUIDE.md) (§ Requirements and environment preparation).
- **Python:** **3.12+** obrigatório; o **CI** usa o runner padrão do **GitHub Actions** (`ubuntu-latest`) com **3.12 e 3.13** — isso é **infraestrutura de CI**, não limite de plataforma do produto.

**Tier 1 (testar primeiro):** **RHEL 9** / **AlmaLinux 9** / **Rocky 9** (empresarial, `dnf`), **Fedora 40+** (upstream RHEL). **Tier 2:** **Arch** / **Manjaro** / **BigLinux** (`pacman`), **openSUSE Tumbleweed** (`zypper`). **Tier 3:** **Gentoo** (`emerge`, source-based), **Void** / **Alpine** (musl).

## Eixos ortogonais: libc × baseline de CPU (1.7.4.post10)

**libc** (glibc vs musl) e **baseline de ISA** (PyPI `x86-64-v2` vs wheelhouse `x86-64-v1`) são **independentes**. O nó de lab **alpine-emachines** (Celeron 900, Alpine/musl) exercita **os dois** ao mesmo tempo. Container musl em host com AVX valida musl, **não** valida v1.

Release verificado: [wheelhouse-x86-64-v1-2026-07-29](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29). Contrato de instalação em dois passos + inject de `boar_fast_filter`: [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md) §x86-64-v1.

## Matriz `pipx` e `--demo` (1.7.4.post10)

| Caminho | Status | Ação |
| ------- | ------ | ---- |
| **Debian / Fedora / RHEL10 / Void-glibc** | Sem atrito | `pipx install data-boar` |
| **RHEL 8 / RHEL 9** | Passo extra | `dnf install -y python3.12` + `pipx install --python python3.12 data-boar` |
| **Void-musl / Alpine musl / x86-64-v1** | Paridade via wheelhouse v1 | Pasta local + dois passos + inject — [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md) |
| **RHEL/CentOS 7** | Fora de escopo nativo | Somente Docker |

**Sinal de aceite `--demo`:** **26 achados** e `_ML_AVAILABLE=True` em Debian, Fedora, Alma 9, Void-glibc/musl, Alpine cp312/313/314, Debian arm64 (QEMU) e metal Celeron. O processo **não encerra** — espere o relatório em `$TMPDIR/data_boar_demo`.

**Lab-smoke DB/Redis (checklist separado):** Postgres/MariaDB/MSSQL/Oracle **20 achados cada**; Redis **5** — `deploy/lab-smoke-stack/`.

**Config-ref comparável (conectores / arquivos) — [#1368](https://github.com/DataBoar/data-boar/issues/1368):** o `--demo` prova **instalação**, não conectores. Harness versionado em [`deploy/compat-matrix-config-ref/`](../../deploy/compat-matrix-config-ref/) — duas camadas, duas medidas (achados + `scan_failures` por razão), `max_workers: 1`, `adaptive_rate_limit: true`, só `pass_from_env`. Camada 1: **19** achados idênticos em 6 cantos (sem py7zr); com `[compressed]`: **26**. Camada 2 (lab-smoke): 20/20/20/20 e Redis **5** (baseline correta da #1348).

- Fonte operacional: [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md).

**Ordem sugerida:** AlmaLinux 9 → Arch/Manjaro → Void/Alpine (musl) → Gentoo (se houver tempo) → **illumos** (ex. OpenIndiana) / legado **OpenSolaris** só **depois** (Tier 4; OpenSolaris oficial é histórico; preferir **illumos** atual).

**OS/2** (Warp, etc.): **fora de escopo** para o Data Boar — só **museu/hobby**; ver matriz EN (Tier 4).

**Integração:** Use **§1.5** (VMs no portátil) ou **§9** (Proxmox guests) para testar; documente diferenças de **nomes de pacotes** em **`TECH_GUIDE.md`** ou **issues** públicas; detalhes de host/IP só em **`docs/private/homelab/`** — [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md).
