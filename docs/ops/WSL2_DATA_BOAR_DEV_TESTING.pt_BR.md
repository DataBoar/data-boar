# Windows WSL2 — desenvolvimento e testes de laboratório com Data Boar

**English:** [WSL2_DATA_BOAR_DEV_TESTING.md](WSL2_DATA_BOAR_DEV_TESTING.md)

**Objetivo:** Tratar o **WSL2** no PC Windows principal de desenvolvimento (notebook típico estilo ThinkPad) como **superfície opcional de execução** adicional ao Windows nativo e aos Linux em laptops (LAB-NODE-01, lab-node-02). **Não** substitui CI nem hosts de homelab; reduz o risco de assumir um único SO ou um único runtime de contentores para como clientes ou integradores rodam o Data Boar.

---

## 1. Por que o WSL2 entra neste projeto

- **Diversidade de execução:** Integradores podem usar `uv run python main.py` no Windows, no WSL, em contentor ou em Linux bare metal. O produto não deve assumir um layout silenciosamente.
- **Path e fim de linha:** Caminhos em YAML, bind mounts e raízes de `file_scan` comportam-se de forma diferente em `C:\...`, `\\wsl$\...` e `/home/...` dentro do WSL.
- **Rede:** Alvos TCP para BDs de laboratório (ver [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md)) devem usar o **IPv4 LAN** do host hub (LAB-NODE-01 ou lab-node-02), não `localhost`, salvo quando o Data Boar e os contentores de BD estão na mesma máquina com portas publicadas.

---

## 2. Setup mínimo (WSL2 Ubuntu ou base Debian)

1. Instalar **WSL2** e uma distro conforme a documentação da Microsoft (mesmo Python major que [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md): **≥3.12**, **3.13** quando disponível).
1. Clonar o repositório no sistema de arquivos **WSL** (evitar I/O pesado em `/mnt/c/...` para `uv sync` e pytest).
1. Instalar **`uv`**, depois na raiz do repo: `uv sync` (acrescentar `--extra nosql`, `--extra compressed` quando alinhar ao smoke completo de lab).
1. Apontar a config de scan aos BDs de lab com o **IP LAN do hub** e portas **55432** / **33306** (ver [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md)).

**Docker dentro do WSL:** Opcional. Com **Docker Desktop** e integração WSL, portas publicadas no Windows podem diferir do Linux “puro”; preferir IPs LAN explícitos para smoke entre hosts. Para política de lab, bastam dois hubs **Docker CE** em **LAB-NODE-01** e **lab-node-02** (sem obrigação de compose no LAB-NODE-03 ou LAB-NODE-04).

---

## 3. O que registar após uma passagem no WSL2

- Nome/versão da distro, `python --version`, e se a corrida usou só **venv nativo** ou integração **Docker Desktop**.
- Qualquer prompt de **firewall** ou **Windows Defender** que bloqueie TCP de saída para a sub-rede de lab (documentar em notas do operador em `docs/private/`, não em inventário rastreado no Git).

---

## 4. Documentos relacionados

- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) — ThinkPad LAB-NODE-01 + Docker CE via baseline Ansible.
- [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md) — Pilha de BD, checklist, política de dois hubs.
- [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) — Playbook de laboratório mais amplo.
- [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md) — `lab-node-01-baseline.yml`, Docker CE, grupo `docker` do operador.

**Última revisão:** 2026-04 — alinhado ao smoke multi-host e à automação de baseline LAB-NODE-01.
