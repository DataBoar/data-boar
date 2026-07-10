# Matriz de compatibilidade de SO (expansão do homelab)

**Objetivo:** Guiar **quais distribuições Linux** testar o Data Boar no homelab, priorizadas por **relevância em produção**, **disponibilidade de Python 3.12+** e diferenças de **gerenciador de pacotes**.

**Documento completo (EN, tabelas e comandos):** [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md)

---

## Resumo

**Tier 1 (testar primeiro):** **RHEL 9** / **AlmaLinux 9** / **Rocky 9** (empresarial, `dnf`), **Fedora 40+** (upstream RHEL). **Tier 2:** **Arch** / **Manjaro** / **BigLinux** (`pacman`), **openSUSE Tumbleweed** (`zypper`). **Tier 3:** **Gentoo** (`emerge`, source-based), **Void** / **Alpine** (musl).

**Gaps de onboarding pipx confirmados (2026-07-09):**
- **Família RHEL9 (Alma/Rocky/Oracle 9):** em alguns hosts o `python3` padrão ainda cai em 3.9; para `pipx`, use Python 3.12 explícito:
  - `sudo dnf install -y python3.12`
  - `pipx install --python python3.12 data-boar`
- **Alpine/musl:** no caminho atual o `scikit-learn` pode cair em build do source e falhar com `metadata-generation-failed` sem toolchain:
  - `apk add build-base gfortran openblas-dev`
  - `pipx install data-boar`
- Fonte operacional e contexto atualizado: [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md).

**Ordem sugerida:** AlmaLinux 9 → Arch/Manjaro → Void/Alpine (musl) → Gentoo (se houver tempo) → **illumos** (ex. OpenIndiana) / legado **OpenSolaris** só **depois** (Tier 4; OpenSolaris oficial é histórico; preferir **illumos** atual).

**OS/2** (Warp, etc.): **fora de escopo** para o Data Boar — só **museu/hobby**; ver matriz EN (Tier 4).

**Integração:** Use **§1.5** (VMs no portátil) ou **§9** (Proxmox guests) para testar; documente diferenças de **nomes de pacotes** em **`TECH_GUIDE.md`** ou **issues** públicas; detalhes de host/IP só em **`docs/private/homelab/`** — [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md).
