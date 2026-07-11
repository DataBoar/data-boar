# Matriz de compatibilidade de SO (expansão do homelab)

**Objetivo:** Guiar **quais distribuições Linux** testar o Data Boar no homelab, priorizadas por **relevância em produção**, **disponibilidade de Python 3.12+** e diferenças de **gerenciador de pacotes**.

**Documento completo (EN, tabelas e comandos):** [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md)

---

## Resumo

**Tier 1 (testar primeiro):** **RHEL 9** / **AlmaLinux 9** / **Rocky 9** (empresarial, `dnf`), **Fedora 40+** (upstream RHEL). **Tier 2:** **Arch** / **Manjaro** / **BigLinux** (`pacman`), **openSUSE Tumbleweed** (`zypper`). **Tier 3:** **Gentoo** (`emerge`, source-based), **Void** / **Alpine** (musl).

**Matriz de instalação `pipx` provada (1.7.4.post3):**
- **RHEL 8 e RHEL 9 (inclui Alma):** exigem Python 3.12 explícito no caminho `pipx`:
  - `sudo dnf install -y python3.12`
  - `pipx install --python python3.12 data-boar`
- **RHEL/Alma/Rocky/Oracle 10:** caminho padrão sem atrito (`pipx install data-boar`).
- **Void-glibc:** passa no caminho padrão (PyPI publica wheel `cp314`).
- **Void-musl (py3.14.6):** com toolchain (`xbps-install -S python3-devel gcc gcc-fortran openblas-devel`), `pipx install` funciona e `--demo` fecha em **26 findings** (paridade de runtime com glibc). Sem toolchain, a falha atual fica concentrada no build de source do `scikit-learn==1.9.0`; `numpy` e `pandas` já têm wheel `musllinux` no PyPI, `scipy` não é dependência e `odfpy` é pure Python. Gap remanescente para caminho pipx-puro sem toolchain: wheel `cp314 musllinux` de `scikit-learn` ([#1182](https://github.com/DataBoar/data-boar/issues/1182)).
- **Alpine/musl:** sem wheelhouse adequado, pode cair em build de source e falhar com `metadata-generation-failed`; usar wheelhouse (`--find-links`) ou pré-instalar toolchain:
  - `apk add build-base gfortran openblas-dev`
  - `pipx install data-boar`
- **Paridade de runtime no musl (post3):** com smoke aguardando o fim do scan (sem timeout prematuro), Alpine-musl igualou Debian-glibc com 26 findings. O "13 findings" anterior foi artefato de harness (timeout), não gap de detector/parser.
- **Hosts sem AVX:** caminho recomendado é wheelhouse ou Docker (sem overclaim de caminho padrão).
- **RHEL/CentOS 7:** EOL (repositórios mortos + `requires-python>=3.12` inalcançável) - usar somente Docker.
- Fonte operacional e contexto atualizado: [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md).

**Ordem sugerida:** AlmaLinux 9 → Arch/Manjaro → Void/Alpine (musl) → Gentoo (se houver tempo) → **illumos** (ex. OpenIndiana) / legado **OpenSolaris** só **depois** (Tier 4; OpenSolaris oficial é histórico; preferir **illumos** atual).

**OS/2** (Warp, etc.): **fora de escopo** para o Data Boar — só **museu/hobby**; ver matriz EN (Tier 4).

**Integração:** Use **§1.5** (VMs no portátil) ou **§9** (Proxmox guests) para testar; documente diferenças de **nomes de pacotes** em **`TECH_GUIDE.md`** ou **issues** públicas; detalhes de host/IP só em **`docs/private/homelab/`** — [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md).
