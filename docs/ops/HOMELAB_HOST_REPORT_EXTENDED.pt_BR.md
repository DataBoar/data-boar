# Relatório de host do homelab (estendido) — hardening + sinais de inventário

**English:** [HOMELAB_HOST_REPORT_EXTENDED.md](HOMELAB_HOST_REPORT_EXTENDED.md)

## Objetivo

Capturar um snapshot **alto sinal** de cada host do LAB-OP (pacotes + postura de segurança) de forma:

- repetível,
- revisável,
- segura para compartilhar em formato **redigido**,
- e que funcione em distros diferentes (Debian-family + Void + outras).

Isto complementa a página focada em pacotes: [HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md](HOMELAB_HOST_PACKAGE_INVENTORY.pt_BR.md).

## O que é coletado (alto nível)

O script `scripts/homelab-host-report.sh` roda **no host** e tenta coletar:

- OS/kernel + CPU/memória
- Python/uv/pip (pré-requisitos do runtime)
- presença do Docker + info básica (se instalado)
- banners: `/etc/issue`, `/etc/issue.net`, `/etc/banner.net`
- subconjunto do config efetivo do OpenSSH (`sshd -T` quando disponível)
- postura do firewall:
  - `ufw status` quando existir UFW (Debian/Ubuntu/LMDE)
  - `nft list ruleset` (trecho) quando existir `nft` (ex.: Void Linux)
- fail2ban, sshguard (status + sinais mínimos)
- usbguard (regras/dispositivos quando disponível)
- regras do auditd e head do AIDE (quando disponível)
- Kernel + sinais de tuning (para validar postura de performance/segurança sem surpresas):
  - `/proc/cmdline` (parâmetros de boot)
  - valores selecionados de `sysctl` (quando `sysctl` existir)
  - head dos arquivos de config de `sysctl` (`/etc/sysctl.conf`, `/etc/sysctl.d/*.conf`)
  - `ulimit -a` + `/etc/security/limits*`
  - pistas de fila de block device (`scheduler`, `rotational`, `nr_requests`, etc.)
  - head de `/etc/udev/rules.d/*.rules`

O script faz coleta **best-effort** e pula seções que não existirem naquele host.

## Recomendações por classe de máquina (dirigido pelo operador; controlado por variáveis)

A ideia é manter a automação **decidível por variáveis**, para uma máquina nova não receber tunings “de surpresa”.

Isto são **recomendações** baseadas nos últimos host reports do LAB-OP, boas práticas comuns de Linux, e o perfil de hardware/OS.

### Classe: Raspberry Pi 3B (pouca RAM, SD/eMMC, Debian)

- **I/O scheduler**: prefira `mq-deadline` em `mmcblk*` (latência estável); evite forçar BFQ em SD sem testar.
- **Deep scans**: evite `--deep` (Lynis quick audit pode ser pesado); `--privileged` ok.
- **Memória**: prefira **zram swap** (pequeno); swappiness pode ser maior que em desktops (depende do workload).
- **Nota**: se `sysctl` não existir, instale `procps` para auditar tuning de forma consistente.

### Classe: <lab-host-2> (Void, x86_64, SATA SSD, “utility box”)

- **I/O scheduler**: BFQ pode fazer sentido em SATA SSD quando a latência interativa importa; não aplique BFQ em NVMe.
- **Queueing**: considere defaults modernos (`net.core.default_qdisc=fq`) se a distro ainda estiver em `pfifo_fast`.
- **Sysctls de hardening** (baseline seguro): garantir `fs.protected_fifos=1` e `fs.protected_regular=2` (se o kernel suportar).

### Classe: Lab x86_64 principal (Ubuntu-family desktop/server, SATA SSD, Docker Swarm manager)

- **I/O scheduler**: `mq-deadline` é um padrão seguro para SATA SSD.
- **Rede**: `fq_codel` como qdisc padrão é um bom baseline; evite mudanças agressivas de TCP sem medir.
- **Host Docker**: evite limites `nofile` baixos para serviços; prefira overrides por unit do systemd (em vez de mexer global em `limits.conf`).

### Classe: Estação de desenvolvimento (LMDE, NVMe, BTRFS criptografado)

- **I/O scheduler**: prefira `none` para NVMe (padrão do kernel).
- **Memória**: zram é opcional (você tem 16 GiB); habilite só se tiver motivo (hibernação não é atendida por zram).
- **Segurança vs usabilidade**: mantenha tuning mínimo, a menos que exista benchmark/motivo claro.
- **Nota**: se `sysctl` não existir, instale `procps` para auditar tuning de forma consistente.

### “Kits de variáveis” sugeridos (exemplo)

Isto é só ilustrativo (não é imposto automaticamente). Use host/group vars para optar:

```yaml
# ops/automation/ansible/inventory.ini (ou group_vars/ / host_vars/)
#
# lab-sbc (exemplo ARM):
#   lab_node_01_zram_enable: true
#   lab_node_01_zram_max_mb: 512
#
# <lab-host-2>:
#   lab_node_01_zram_enable: true
#   lab_node_01_zram_size_percent: 25
#
# lab-op (lab x86 principal):
#   lab_node_01_install_docker_ce: true
#   lab_node_01_docker_swarm_init: true
#
# lab-workstation (exemplo portátil dev):
#   lab_node_01_zram_enable: false
```

## Como rodar (em cada host)

Na raiz do repo (no host):

```bash
bash scripts/homelab-host-report.sh
```

Para habilitar probes privilegiados best-effort usando `sudo -n` (não interativo), passe:

```bash
bash scripts/homelab-host-report.sh --privileged
```

Salve em arquivo e depois redija antes de compartilhar:

```bash
bash scripts/homelab-host-report.sh | tee "homelab_host_report_$(date +%F).log"
```

## Bloco privilegiado (opcional)

Algumas seções exigem root para fidelidade total (ex.: `sshd -T`, `/etc/audit/rules.d/*.rules`).

O script tenta `sudo -n` (não interativo). Se o host exigir senha, rode uma vez:

```bash
sudo -v
bash scripts/homelab-host-report.sh --privileged | tee "homelab_host_report_$(date +%F).log"
```

Para um padrão de sudoers safe-by-default (restrito ao comando de report), veja:

- [LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md](LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md)

## O que redigir

Antes de compartilhar logs fora de `docs/private/`:

- hostnames / domínios
- IPs de LAN
- paths de home se forem identificáveis
- qualquer segredo em configs (tokens, chaves)

